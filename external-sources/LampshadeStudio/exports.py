"""Checked binary STL meshes and OpenCascade CAD exports, in millimetres."""
from pathlib import Path
import math
import struct
import numpy as np
from geometry import rings, fit_grid, inward, exact_bounds

STL_QUALITY = {"lite": 4, "balanced": 8, "fine": 12}


def export_options(raw):
    fmt=raw.get("exportFormat","step")
    quality=raw.get("stlQuality","balanced")
    if fmt not in ("step","stl","brep","x_b","x_t"):
        raise ValueError("Choose STEP, STL, BREP or Parasolid.")
    if quality not in tuple(STL_QUALITY):
        raise ValueError("Choose Lite, Balanced or Fine STL quality.")
    return fmt,quality


def shade_mesh(p,quality):
    """Closed material mesh: caps for vase envelope, annular rims for hollow shade."""
    grid=fit_grid(rings(p,resolution=STL_QUALITY[quality]),p)
    n=len(grid[0]); levels=len(grid)-1
    if min(math.hypot(x,y) for row in grid for x,y,z in row)<p["wall"]+1:
        raise ValueError("The fitted shade is too narrow for this wall. Increase the envelope or reduce the wall.")
    vertices=[pt for row in grid for pt in row]
    faces=[]
    for j in range(levels):
        for i in range(n):
            a=j*n+i; b=j*n+(i+1)%n; c=a+n; d=b+n
            faces.extend(((a,b,d),(a,d,c)))
    if p["exportMode"]=="hollow":
        offset=len(vertices)
        vertices.extend(pt for row in inward(grid,p["wall"]) for pt in row)
        faces.extend((c+offset,b+offset,a+offset) for a,b,c in tuple(faces))
        for i in range(n):
            j=(i+1)%n
            faces.extend(((i,i+offset,j),(j,i+offset,j+offset)))
            a=levels*n+i; b=levels*n+j
            faces.extend(((a,b,a+offset),(b,b+offset,a+offset)))
    else:
        top_centre=len(vertices); vertices.append((0,0,p["height"]))
        for i in range(n):
            faces.append((top_centre,levels*n+i,levels*n+(i+1)%n))
        if p["base"]=="socket":
            # Compatibility with early saved designs: a blind recess in the bottom.
            r=p["hole"]/2
            if any(math.hypot(x,y)<=r for x,y,z in grid[0]):
                raise ValueError("The fitted bottom is too small for this socket recess.")
            start=len(vertices)
            for z in (0,p["baseThickness"]):
                vertices.extend((r*math.cos(i*2*math.pi/n),r*math.sin(i*2*math.pi/n),z) for i in range(n))
            ceiling=len(vertices); vertices.append((0,0,p["baseThickness"]))
            for i in range(n):
                j=(i+1)%n; a=start+i; b=start+j; c=a+n; d=b+n
                faces.extend(((i,a,j),(j,a,b),(a,d,b),(a,c,d),(ceiling,d,c)))
        else:
            bottom_centre=len(vertices); vertices.append((0,0,0))
            for i in range(n):faces.append((bottom_centre,(i+1)%n,i))
    return np.asarray(vertices,dtype=np.float32),np.asarray(faces,dtype=np.int32)


def check_mesh(vertices,faces,target):
    if not np.isfinite(vertices).all() or not len(faces):
        raise ValueError("The STL mesh contains invalid coordinates.")
    actual=np.ptp(vertices,axis=0)
    if not np.allclose(actual,target,atol=.01,rtol=0):
        raise ValueError("STL envelope validation failed.")
    # Every edge must occur exactly twice with opposite directions: no open seams.
    edges=faces[:,[[0,1],[1,2],[2,0]]].reshape(-1,2)
    canonical=np.sort(edges,axis=1)
    _,inverse,counts=np.unique(canonical,axis=0,return_inverse=True,return_counts=True)
    directions=np.where(edges[:,0]<edges[:,1],1,-1)
    if not (counts==2).all() or np.any(np.bincount(inverse,weights=directions)):
        raise ValueError("The STL mesh has an open or inconsistent seam.")
    triangles=vertices[faces].astype(np.float64)
    crosses=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    lengths=np.linalg.norm(crosses,axis=1)
    if (lengths<1e-10).any():raise ValueError("The STL mesh contains a collapsed triangle.")
    volume=np.einsum('ij,ij->',triangles[:,0],np.cross(triangles[:,1],triangles[:,2]))/6
    if volume<=0:raise ValueError("The STL mesh has an invalid volume.")
    return crosses/lengths[:,None]


def stl_export(p,quality):
    vertices,faces=shade_mesh(p,quality)
    normals=check_mesh(vertices,faces,(p["boxWidth"],p["boxDepth"],p["height"]))
    records=np.zeros(len(faces),dtype=np.dtype([("normal","<f4",3),("vertices","<f4",(3,3)),("attribute","<u2")]))
    records["normal"]=normals; records["vertices"]=vertices[faces]
    header=f'Lampshade Studio | mm | {quality} | {p["exportMode"]}'.encode().ljust(80,b' ')
    return header+struct.pack('<I',len(faces))+records.tobytes(),len(faces)


def cad_export(solid,path,fmt,target):
    """Round-trip the real file before returning it to the user."""
    import cadquery as cq
    path=Path(path)
    if fmt=="step":
        cq.exporters.export(solid,str(path),exportType="STEP")
        imported=cq.importers.importStep(str(path)).val()
    elif fmt=="brep":
        if not solid.exportBrep(str(path)):raise ValueError("BREP export failed.")
        imported=cq.Shape.importBrep(str(path))
    else:raise ValueError("Unknown CAD format.")
    if not imported.isValid() or len(imported.Solids())!=1 or imported.Volume()<=0:
        raise ValueError(f"{fmt.upper()} validation failed. Try a simpler design.")
    x0,y0,z0,x1,y1,z1=exact_bounds(imported)
    if any(abs(a-b)>.01 for a,b in zip((x1-x0,y1-y0,z1-z0),target)):
        raise ValueError(f"{fmt.upper()} envelope validation failed. Please try a simpler design.")
    return path.read_bytes()
