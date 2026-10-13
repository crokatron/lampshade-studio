"""Shared geometry for the preview and OpenCascade STEP builder. Units: mm."""
import math
from bulb import clearance

DEFAULT = dict(style="spiral", height=200, bottom=116, top=116, bulge=30,
               twist=45, ribs=56, depth=1.8, lobes=5, wave=0, rows=12,
               base="open", hole=40, baseThickness=1.4, lineWidth=0.6, layerHeight=0.2,
               boxWidth=180, boxDepth=180, wall=0.8, exportMode="hollow",
               profile="classic",section="round",texture="ribs",shoulder=0.22,
               bands=5,bandDepth=8,weaveRows=22,sway=0,swayCycles=1,roundness=4,
               bulbType="st64",bulbDiameter=64,bulbHeight=140,bulbZ=15,bulbClearance=5,
               bulbVisible=True,bulbOrientation="upright")
PRESETS = {
    "spiral": DEFAULT,
    "wave": {**DEFAULT, "style": "wave", "height": 160, "bottom": 100,
             "top": 94, "bulge": 15, "twist": 100, "ribs": 72,
             "depth": 0.9, "wave": 9},
    "facet": {**DEFAULT, "style": "facet", "height": 180, "bottom": 116,
              "top": 116, "bulge": 17, "twist": 0, "ribs": 24,
              "depth": 5, "rows": 12,"texture":"facet"},
    "silk": {**DEFAULT,"style":"silk","boxWidth":210,"boxDepth":210,"height":190,
             "bottom":88,"top":70,"bulge":43,"ribs":18,"depth":4.5,"twist":10,
             "sway":22,"swayCycles":1.5},
    "lantern": {**DEFAULT,"style":"lantern","boxWidth":160,"boxDepth":160,"height":220,
                "bottom":110,"top":110,"bulge":2,"profile":"lantern","bands":5,
                "bandDepth":11,"twist":0,"ribs":56,"depth":1.2},
    "orbit": {**DEFAULT,"style":"orbit","boxWidth":180,"boxDepth":180,"height":230,
              "bottom":118,"top":110,"bulge":5,"profile":"helix","bands":4,
              "bandDepth":12,"texture":"woven","ribs":36,"depth":1.1,
              "weaveRows":22,"twist":12},
    "woven": {**DEFAULT,"style":"woven","boxWidth":138,"boxDepth":138,"height":250,
              "bottom":98,"top":98,"bulge":25,"profile":"capsule","texture":"woven",
              "ribs":48,"depth":1.6,"twist":0,"weaveRows":26},
    "square": {**DEFAULT,"style":"square","boxWidth":160,"boxDepth":160,"height":240,
               "bottom":140,"top":140,"bulge":-6,"section":"square","texture":"woven",
               "ribs":48,"depth":1.1,"weaveRows":24,"twist":75,"roundness":4.5},
    "bloom": {**DEFAULT,"style":"bloom","boxWidth":200,"boxDepth":200,"height":180,
              "bottom":74,"top":146,"bulge":13,"ribs":42,"depth":0.7,"lobes":7,
              "wave":12,"twist":22,"sway":7,"swayCycles":1},
    "dune": {**DEFAULT,"style":"dune","boxWidth":190,"boxDepth":155,"height":235,
             "bottom":116,"top":94,"bulge":17,"ribs":22,"depth":3.2,"lobes":3,
             "wave":6,"twist":-25,"sway":26,"swayCycles":0.75},
    "hourglass": {**DEFAULT,"style":"hourglass","boxWidth":160,"boxDepth":160,"height":225,
                  "bottom":150,"top":150,"bulge":-23,"ribs":32,"depth":1.4,
                  "texture":"woven","weaveRows":18,"twist":-35},
}
STYLES = {
    "spiral":dict(name="Spiral",description="Fine ribs on a gently swelling body.",group="Essentials"),
    "wave":dict(name="Wave",description="Broad twisting folds with fine fluting.",group="Essentials"),
    "facet":dict(name="Facet",description="Crisp triangular relief and angular shadows.",group="Essentials"),
    "silk":dict(name="Silk folds",description="Soft pleats that meander over a rounded form.",group="Flowing"),
    "lantern":dict(name="Lantern",description="Stacked cushions crossed by slender ribs.",group="Sculptural"),
    "orbit":dict(name="Orbit",description="A rolling helical form with woven relief.",group="Sculptural"),
    "woven":dict(name="Woven capsule",description="Rounded shoulders and a fine diamond texture.",group="Textured"),
    "square":dict(name="Twisted square",description="A soft square section turning through space.",group="Sculptural"),
    "bloom":dict(name="Bloom",description="An opening, petal-like silhouette.",group="Flowing"),
    "dune":dict(name="Dune",description="Shifting folds over an asymmetric-looking oval.",group="Flowing"),
    "hourglass":dict(name="Hourglass",description="A pinched waist with crossing diamond relief.",group="Textured"),
}
LIMITS = dict(height=(60,350), bottom=(50,260), top=(50,260), bulge=(-40,60),
              twist=(-180,180), ribs=(12,80), depth=(0,12), lobes=(2,12),
              wave=(0,20), rows=(4,24), hole=(10,100), baseThickness=(0.6,4),
              lineWidth=(0.35,1.4), layerHeight=(0.08,0.4), boxWidth=(40,400), boxDepth=(40,400),wall=(0.4,3),
              shoulder=(0.1,0.4),bands=(2,8),bandDepth=(0,18),weaveRows=(6,32),
              sway=(0,40),swayCycles=(0.5,3),roundness=(2,6),
              bulbDiameter=(30,150),bulbHeight=(70,250),bulbZ=(-250,400),bulbClearance=(0,30))

def validate(raw):
    if not isinstance(raw, dict):
        raise ValueError("Design must be an object.")
    style=raw.get("style","spiral")
    if not isinstance(style,str) or style not in PRESETS:
        raise ValueError("Unknown shade style.")
    p = {**PRESETS[style], **{k:v for k,v in raw.items() if k in DEFAULT}}
    if p["style"] not in PRESETS or p["base"] not in ("open", "socket") or p["exportMode"] not in ("hollow","solid"):
        raise ValueError("Unknown shade style or base.")
    if p["profile"] not in ("classic","capsule","lantern","helix") or p["section"] not in ("round","square") or p["texture"] not in ("ribs","woven","smooth","facet"):
        raise ValueError("Unknown profile, cross-section or surface texture.")
    if p["bulbType"] not in ("st64","a60") or p["bulbOrientation"] not in ("upright","pendant") or not isinstance(p["bulbVisible"],bool):
        raise ValueError("Unknown bulb settings.")
    for key,(low,high) in LIMITS.items():
        v=p[key]
        if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or not low<=v<=high:
            raise ValueError(f"{key} must be between {low} and {high}.")
    for key in ("ribs","lobes","rows","bands","weaveRows"):
        if p[key] != int(p[key]):
            raise ValueError(f"{key} must be a whole number.")
        p[key]=int(p[key])
    detail=p["ribs"]*math.radians(p["sway"])*p["swayCycles"]
    if p["texture"]=="woven":detail+=p["weaveRows"]
    if p["texture"] in ("woven","ribs") and detail>60:
        raise ValueError("This combination is too dense. Reduce fold sway, sway cycles, weave rows or ribs.")
    # The conservative lower radius bound also prevents self-intersecting contours.
    if min(p["bottom"],p["top"])/2 + min(0,p["bulge"]) - p["depth"] - p["wave"] < 8:
        raise ValueError("This combination narrows the shade too much. Increase the diameter or reduce depth.")
    if p["base"]=="socket":
        if p["hole"] / 2 + 3 > p["bottom"]/2 - p["depth"] - (p["wave"] if p["style"]=="wave" else 0):
            raise ValueError("Leave at least 3 mm between the socket opening and the smallest base radius.")
        layers=p["baseThickness"]/p["layerHeight"]
        if abs(layers-round(layers)) > 0.001:
            raise ValueError("Base thickness must be a whole number of layers. Adjust thickness or layer height.")
    return p

def radius(p,t):
    blend=math.sin(math.pi*t)
    if p["profile"]=="capsule":
        shoulder=p["shoulder"]
        edge=min(t,1-t)
        blend=math.sin(math.pi/2*min(1,edge/shoulder))
    result=(p["bottom"]*(1-t)+p["top"]*t)/2 + p["bulge"]*blend
    if p["profile"]=="lantern":
        result+=p["bandDepth"]*(1-math.cos(2*math.pi*p["bands"]*t))/2
    return result

def surface_radius(p,phi,t):
    r=radius(p,t)
    if p["section"]=="square":
        power=p["roundness"]
        r/=(abs(math.cos(phi))**power+abs(math.sin(phi))**power)**(1/power)
    phase=phi+math.radians(p["sway"])*math.sin(2*math.pi*p["swayCycles"]*t)
    r+=p["wave"]*math.cos(p["lobes"]*phase)
    if p["profile"]=="helix":
        # The envelope fades at both rims, leaving flat, open ends for CAD interfaces.
        r+=p["bandDepth"]*(1-math.cos(2*math.pi*p["bands"]*t-phi))/2*math.sin(math.pi*t)**0.5
    if p["texture"]=="ribs":
        r+=p["depth"]*math.cos(p["ribs"]*phase)
    elif p["texture"]=="woven":
        # Crossing sinusoidal relief, never holes or disconnected strands.
        r+=p["depth"]*math.cos(p["ribs"]*phase)*math.cos(2*math.pi*p["weaveRows"]*t)
    return r

def rings(p, preview=False, thumbnail=False, resolution=None):
    facet=p["texture"]=="facet"
    count=p["ribs"] if facet else max(128,p["ribs"]*8)
    levels=p["rows"] if facet else (100 if preview else 40)
    if not facet:
        if p["texture"]=="woven":levels=max(levels,p["weaveRows"]*8)
        if p["profile"] in ("lantern","helix"):levels=max(levels,p["bands"]*16)
        # Wavy ribs need sufficient vertical samples to follow their actual angular motion.
        if p["texture"] in ("woven","ribs"):
            motion=p["ribs"]*math.radians(p["sway"])*p["swayCycles"]
            levels=max(levels,math.ceil(motion*6+(p["weaveRows"]*8 if p["texture"]=="woven" else 0)))
        if thumbnail:
            count=max(96,p["ribs"]*6)
            levels=max(48,math.ceil(levels*.75))
        if resolution is not None:
            # Direct STL sampling: fixed, predictable density without CAD tessellation.
            count=max(24*resolution,p["ribs"]*resolution if p["texture"]!="smooth" else 0)
            detail=p["ribs"] if p["texture"] in ("ribs","woven") else p["lobes"]
            motion=detail*math.radians(p["sway"])*p["swayCycles"]
            twist_cycles=detail*abs(p["twist"])/360
            weave=p["weaveRows"] if p["texture"]=="woven" else 0
            levels=max(12*resolution,math.ceil(resolution*(weave+motion+twist_cycles)),
                       p["bands"]*resolution*2 if p["profile"] in ("lantern","helix") else 0)
    result=[]
    for j in range(levels+1):
        t=j/levels
        pts=[]
        for i in range(count):
            phi=2*math.pi*(i+(0.5*(j%2) if facet else 0))/count
            if facet:
                r=surface_radius(p,phi,t)+p["depth"] * (1 if (i+j)%2==0 else -1)
            else:
                r=surface_radius(p,phi,t)
            theta=phi+math.radians(p["twist"])*t
            pts.append((r*math.cos(theta),r*math.sin(theta),t*p["height"]))
        result.append(pts)
    return result

def fit_grid(grid,p):
    xs=[v[0] for row in grid for v in row]; ys=[v[1] for row in grid for v in row]
    cx=(max(xs)+min(xs))/2; cy=(max(ys)+min(ys))/2
    sx=p["boxWidth"]/(max(xs)-min(xs)); sy=p["boxDepth"]/(max(ys)-min(ys))
    return [[((x-cx)*sx,(y-cy)*sy,z) for x,y,z in row] for row in grid]

def inward(grid,wall):
    return [[(x*(1-wall/math.hypot(x,y)),y*(1-wall/math.hypot(x,y)),z) for x,y,z in row] for row in grid]

def mesh(p,thumbnail=False):
    grid=fit_grid(rings(p,True,thumbnail),p)
    n=len(grid[0]); m=len(grid)-1
    positions=[v for row in grid for pt in row for v in pt]
    triangles=[]
    for j in range(m):
        for i in range(n):
            a=j*n+i; b=j*n+(i+1)%n; c=(j+1)*n+i; d=(j+1)*n+(i+1)%n
            triangles.extend((a,b,d,a,d,c))
    return dict(positions=positions,triangles=triangles,bottom=grid[0],top=grid[-1],
                stats=dict(width=p["boxWidth"],depth=p["boxDepth"],height=p["height"]),
                bulb=clearance(p,grid) if not thumbnail else None)

def loft_solid(grid,facet):
    import cadquery as cq
    from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
    from OCP.Approx import Approx_IsoParametric
    if facet:
        faces=[]; n=len(grid[0])
        for j in range(len(grid)-1):
            for i in range(n):
                a,b,c,d=grid[j][i],grid[j][(i+1)%n],grid[j+1][i],grid[j+1][(i+1)%n]
                for tri in ((a,b,d),(a,d,c)):
                    faces.append(cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(*x) for x in tri],close=True)))
        faces.append(cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(*x) for x in reversed(grid[0])],close=True)))
        faces.append(cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(*x) for x in grid[-1]],close=True)))
        solid=cq.Solid.makeSolid(cq.Shell.makeShell(faces))
    else:
        # Fixed correspondence preserves the designed twist; automatic wire matching can untwist it.
        loft=BRepOffsetAPI_ThruSections(True,False,1e-6)
        loft.CheckCompatibility(False)
        loft.SetMaxDegree(3)
        loft.SetParType(Approx_IsoParametric)
        for row in grid:
            # Uniform shared knots avoid enormous knot unions across differently shaped rings.
            edge=cq.Edge.makeSpline([cq.Vector(*x) for x in row],periodic=True,parameters=list(range(len(row)+1)))
            loft.AddWire(cq.Wire.assembleEdges([edge]).wrapped)
        loft.Build()
        if not loft.IsDone():
            raise ValueError("Could not build this shape. Reduce twist or texture depth.")
        solid=cq.Shape.cast(loft.Shape())
    return solid

def exact_bounds(solid):
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    box=Bnd_Box()
    BRepBndLib.AddOptimal_s(solid.wrapped,box,False,False)
    return box.Get()

def fit_solid(solid,p):
    import cadquery as cq
    x0,y0,z0,x1,y1,z1=exact_bounds(solid)
    sx=p["boxWidth"]/(x1-x0); sy=p["boxDepth"]/(y1-y0); sz=p["height"]/(z1-z0)
    return solid.transformGeometry(cq.Matrix([[sx,0,0,-(x0+x1)*sx/2],
       [0,sy,0,-(y0+y1)*sy/2],[0,0,sz,-z0*sz],[0,0,0,1]]))

def make_solid(p):
    import cadquery as cq
    facet=p["texture"]=="facet"
    grid=fit_grid(rings(p),p)
    if min(math.hypot(x,y) for row in grid for x,y,z in row)<p["wall"]+1:
        raise ValueError("The fitted shade is too narrow for this wall. Increase the envelope or reduce the wall.")
    solid=loft_solid(grid,facet)
    if p["exportMode"]=="hollow":
        inner=loft_solid(inward(grid,p["wall"]),facet)
        # Shared flat end planes let the boolean produce annular rims and open ends.
        solid=solid.cut(inner)
    solid=fit_solid(solid,p)
    if p["base"]=="socket" and p["exportMode"]=="solid":
        pocket=cq.Solid.makeCylinder(p["hole"]/2,p["baseThickness"]+0.01,cq.Vector(0,0,-0.01))
        solid=solid.cut(pocket)
    if not solid.isValid() or len(solid.Solids())!=1 or solid.Volume()<=0:
        raise ValueError("This design did not produce a valid closed solid. Try less twist or depth.")
    return solid
