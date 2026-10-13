"""Local-only design app. CAD exports are serialized because OpenCascade uses global state."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from threading import Lock
import json, tempfile, traceback, argparse, webbrowser, os
from geometry import validate, mesh, make_solid, PRESETS, STYLES
from bulb import BULBS, make_bulb
from exports import export_options, stl_export, cad_export
from nx_export import nx_status, parasolid_export
import chandelier

ROOT=Path(__file__).resolve().parent
CAD_LOCK=Lock()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT/"public"),**kwargs)
    def send_data(self,data,kind="application/json",status=200,filename=None,triangles=None):
        if not isinstance(data,bytes): data=json.dumps(data,allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type",kind)
        self.send_header("Content-Length",str(len(data)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        if filename: self.send_header("Content-Disposition",f'attachment; filename="{filename}"')
        if triangles is not None:self.send_header("X-Mesh-Triangles",str(triangles))
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass
    def do_GET(self):
        if urlparse(self.path).path=="/api/chandelier":
            return self.send_data(dict(defaults=chandelier.DEFAULT,layouts=chandelier.LAYOUTS,nx=nx_status()))
        if urlparse(self.path).path=="/api/config":
            return self.send_data(dict(app="lampshade-studio",presets=PRESETS,styles=STYLES,bulbs=BULBS,nx=nx_status()))
        if urlparse(self.path).path.startswith("/api/thumbnail/"):
            style=urlparse(self.path).path.rsplit("/",1)[-1]
            if style not in PRESETS:return self.send_data({"error":"Unknown style."},status=404)
            return self.send_data(mesh(PRESETS[style],thumbnail=True))
        super().do_GET()
    def do_POST(self):
        try:
            # Prevent other websites from issuing local compute requests.
            origin=self.headers.get("Origin")
            if origin and origin != f'http://{self.headers.get("Host")}':
                return self.send_data({"error":"Origin not allowed."},status=403)
            if self.headers.get("Content-Type","").split(";")[0] != "application/json":
                return self.send_data({"error":"JSON required."},status=415)
            size=int(self.headers.get("Content-Length",0))
            if not 0<size<=16384: raise ValueError("Invalid request size.")
            raw=json.loads(self.rfile.read(size))
            if self.path=="/api/chandelier/preview":
                if not CAD_LOCK.acquire(blocking=False):
                    return self.send_data({"error":"An export is running. Adjust again after it finishes to refresh the preview."},status=409)
                try:return self.send_data(chandelier.preview(raw))
                finally:CAD_LOCK.release()
            if self.path=="/api/chandelier/bom":
                from chandelier_assembly import bom_csv
                return self.send_data(bom_csv(chandelier.layout(raw)),"text/csv; charset=utf-8",filename="chandelier-bom.csv")
            if self.path=="/api/chandelier/export":
                if not isinstance(raw,dict): raise ValueError("A chandelier design is required.")
                if not CAD_LOCK.acquire(blocking=False):
                    return self.send_data({"error":"Another export is being built. Please try again when it finishes."},status=409)
                try:
                    fmt=raw.get('format','step')
                    with tempfile.TemporaryDirectory(prefix='chandelier-') as temp:
                        data,layout=chandelier.export(raw,fmt,temp)
                    return self.send_data(data,{'step':'application/step','stl':'model/stl','brep':'application/octet-stream','x_b':'application/octet-stream','x_t':'application/octet-stream'}[fmt],
                        filename=f"chandelier-{layout['parameters']['layout']}-{len(layout['bars'])}-bars.{fmt}")
                finally: CAD_LOCK.release()
            p=validate(raw)
            if self.path=="/api/preview":
                return self.send_data(mesh(p))
            if self.path in ("/api/export","/api/bulb-export"):
                bulb_export=self.path=="/api/bulb-export"
                fmt,quality=export_options(raw)
                # The separate bulb guide retains its explicitly labelled STEP output.
                if bulb_export:fmt="step"
                if not CAD_LOCK.acquire(blocking=False):
                    return self.send_data({"error":"Another export is being built. Please try again when it finishes."},status=409)
                try:
                    triangles=None
                    if fmt=="stl":
                        data,triangles=stl_export(p,quality)
                    else:
                        solid=make_bulb(p) if bulb_export else make_solid(p)
                        target=(p["bulbDiameter"],p["bulbDiameter"],p["bulbHeight"]) if bulb_export else (p["boxWidth"],p["boxDepth"],p["height"])
                        with tempfile.TemporaryDirectory(prefix="lampshade-") as temp:
                            if fmt in ('x_b','x_t'):
                                data,validation=parasolid_export(solid,temp,fmt,target)
                            else:data=cad_export(solid,Path(temp)/f"shade.{fmt}",fmt,target)
                    filename=f'bulb-reference-{p["bulbType"]}-e27.step' if bulb_export else f'lampshade-{p["style"]}-{p["boxWidth"]:g}x{p["boxDepth"]:g}x{p["height"]:g}-{p["exportMode"]}.{fmt}'
                    return self.send_data(data,{"step":"application/step","stl":"model/stl","brep":"application/octet-stream","x_b":"application/octet-stream","x_t":"application/octet-stream"}[fmt],filename=filename,triangles=triangles)
                finally: CAD_LOCK.release()
            self.send_data({"error":"Not found."},status=404)
        except (ValueError,TypeError) as error:
            self.send_data({"error":str(error)},status=400)
        except Exception:
            traceback.print_exc()
            self.send_data({"error":"The export could not finish. Reduce the twist or texture depth and retry."},status=500)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8766)
    parser.add_argument("--open",action="store_true")
    args=parser.parse_args()
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    (ROOT/".server.pid").write_text(str(os.getpid()))
    print(f"Lampshade Studio: http://127.0.0.1:{args.port}",flush=True)
    if args.open: webbrowser.open(f"http://127.0.0.1:{args.port}")
    server.serve_forever()
