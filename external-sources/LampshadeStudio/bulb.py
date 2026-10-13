"""Dimensioned E27 bulb proxies. Glass outlines are illustrative, not manufacturer CAD."""
import math

BULBS={
    "st64":dict(name="Edison ST64 · E27",diameter=64,height=140,
        source="https://www.lighting.philips.co.uk/consumer/p/led-filament-bulb-clear-60w-st64-e27/8719514323919"),
    "a60":dict(name="Standard A60 · E27",diameter=60,height=106,
        source="https://www.assets.lighting.philips.com/is/content/PhilipsLighting/comf6981535-pss-global"),
}

def outline(p):
    """Return radius,z points. Nominal E27 cap: 27 mm diameter, schematic 26 mm length."""
    diameter=p["bulbDiameter"]; height=p["bulbHeight"]
    # Shape-preserving interpolation: the width and overall height are authoritative;
    # these intermediate glass contour stations are illustrative.
    if p["bulbType"]=="st64":
        stations=[(0,.43),(.12,.49),(.32,.70),(.53,.92),(.65,1),(.79,.98),(.89,.87),(.96,.60),(1,0)]
    else:
        stations=[(0,.45),(.10,.48),(.25,.66),(.43,.92),(.58,1),(.73,.94),(.86,.76),(.95,.47),(1,0)]
    x=[v[0] for v in stations]; y=[v[1]*diameter/2 for v in stations]
    y[0]=max(13.5,y[0])
    h=[x[i+1]-x[i] for i in range(len(x)-1)]
    delta=[(y[i+1]-y[i])/h[i] for i in range(len(h))]
    slopes=[delta[0]]
    for i in range(1,len(x)-1):
        if delta[i-1]*delta[i]<=0:slopes.append(0)
        else:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1]
            slopes.append((w1+w2)/(w1/delta[i-1]+w2/delta[i]))
    slopes.append(delta[-1])
    result=[(0,0),(4,0),(10,2),(13.5,5),(13.5,25),(y[0],26)]
    for i in range(len(h)):
        for j in range(1,9):
            t=j/8
            r=(2*t**3-3*t*t+1)*y[i]+(t**3-2*t*t+t)*h[i]*slopes[i]+(-2*t**3+3*t*t)*y[i+1]+(t**3-t*t)*h[i]*slopes[i+1]
            result.append((max(0,min(diameter/2,r)),26+(height-26)*(x[i]+h[i]*t)))
    return result

def radius_at(points,z):
    if z<0 or z>points[-1][1]:return None
    for (r0,z0),(r1,z1) in zip(points,points[1:]):
        if z0<=z<=z1 and z1>z0:return r0+(r1-r0)*(z-z0)/(z1-z0)
    return 0

def inscribed_radius(row,wall):
    pts=[(x*(1-wall/math.hypot(x,y)),y*(1-wall/math.hypot(x,y))) for x,y,z in row]
    minimum=float("inf")
    for a,b in zip(pts,pts[1:]+pts[:1]):
        dx=b[0]-a[0];dy=b[1]-a[1];length2=dx*dx+dy*dy
        t=max(0,min(1,-(a[0]*dx+a[1]*dy)/length2)) if length2 else 0
        minimum=min(minimum,math.hypot(a[0]+t*dx,a[1]+t*dy))
    return minimum

def clearance(p,grid):
    points=outline(p);wall=p["wall"] if p["exportMode"]=="hollow" else p["lineWidth"]
    radii=[inscribed_radius(row,wall) for row in grid]
    def shade_r(z):
        index=max(0,min(len(radii)-1,z/p["height"]*(len(radii)-1)))
        low=int(index);high=min(len(radii)-1,low+1)
        return radii[low]+(radii[high]-radii[low])*(index-low)
    z0=p["bulbZ"];z1=z0+p["bulbHeight"]
    low=max(0,z0);high=min(p["height"],z1)
    gap=float("inf");envelope=float("inf");closest=None
    if high>=low:
        samples=max(2,math.ceil((high-low)/.5))
        for j in range(samples+1):
            z=low+(high-low)*j/samples;local=z-z0
            if p["bulbOrientation"]=="pendant":local=p["bulbHeight"]-local
            r=radius_at(points,local)
            if r is None:continue
            value=shade_r(z)-r
            if value<gap:gap=value;closest=z
            envelope=min(envelope,shade_r(z)-p["bulbDiameter"]/2)
    if closest is None:state="outside"
    elif gap<0:state="collision"
    elif envelope>=p["bulbClearance"]:state="clear"
    else:state="check"
    return dict(profile=points,state=state,
        gap=None if closest is None else round(gap,2),envelopeGap=None if closest is None else round(envelope,2),
        closestZ=None if closest is None else round(closest,2),
        topOpeningGap=round(radii[-1]-p["bulbDiameter"]/2,2),
        bottomOpeningGap=round(radii[0]-p["bulbDiameter"]/2,2),
        above=round(max(0,z1-p["height"]),1),below=round(max(0,-z0),1))

def make_bulb(p):
    import cadquery as cq
    points=outline(p)
    # A revolved proxy with the same profile as the on-screen guide; no electrical internals or exact thread.
    wire=[(r,z) for r,z in points]
    solid=cq.Workplane("XZ").polyline(wire).close().revolve(360,(0,0),(0,1)).val()
    if p["bulbOrientation"]=="pendant":
        solid=solid.rotate((0,0,0),(1,0,0),180).translate((0,0,p["bulbHeight"]))
    solid=solid.translate((0,0,p["bulbZ"]))
    if not solid.isValid():raise ValueError("Could not construct the bulb reference.")
    return solid
