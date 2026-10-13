"""Flat inter-spoke leaf panels made from circular arcs, planes and round holes."""
import math


def specification(p):
    radius=p['hubRadius']+p['webReach'];half=math.pi/p['count']
    ear=p['webHole']+2*p['saddleWall']
    ear_y=p['width']/2+p['clearance']+p['saddleWall']+ear/2
    a=radius*math.cos(half)+ear_y*math.sin(half)
    b=radius*math.sin(half)-ear_y*math.cos(half)
    pad=p['webHole']/2+2
    if b<pad+p['webRib']+2:raise ValueError('Web tabs are too close. Increase hub radius or web reach, or use fewer lights.')
    if radius+p['saddleLength']/2>p['hubRadius']-p['engagement']+p['length']:
        raise ValueError('Reduce web reach to keep its collar on the T5.')
    inner=max(p['hubRadius']+12+p['webRib'],a+max(6,b*.3))
    outer=inner+min(40,max(12,b*.4))
    arcs=[]
    for middle in (inner,outer):
        sag=middle-a;cx=a+(sag*sag-b*b)/(2*sag)
        r=middle-cx
        arcs.append(dict(cx=cx,radius=r,angle=math.atan2(b,a-cx),middle=middle))
    eye=None
    if p['hangerFrom']=='web':
        hole=p['cordDiameter']+.8 if p['hanging']=='paracord' else p['webbingWidth']+1
        eye=dict(x=arcs[0 if p['webStyle']=='arc' else 1]['middle'],hole=hole,pad=hole/2+3)
    return dict(radius=radius,earY=ear_y,a=a,b=b,pad=pad,arcs=arcs,eye=eye,
                z=p['height']+p['clearance']+p['saddleWall'])


def make_panel(p,spec):
    import cadquery as cq
    w,t=p['webRib'],p['webThickness'];body=None
    for arc in spec['arcs'][:1 if p['webStyle']=='arc' else 2]:
        cx,r,theta=arc['cx'],arc['radius'],arc['angle'];co,si=math.cos(theta),math.sin(theta)
        ro,ri=r+w/2,r-w/2
        if ri<=0:raise ValueError('Reduce web rib width.')
        strip=(cq.Workplane('XY').moveTo(cx+ro*co,-ro*si)
               .threePointArc((cx+ro,0),(cx+ro*co,ro*si)).lineTo(cx+ri*co,ri*si)
               .threePointArc((cx+ri,0),(cx+ri*co,-ri*si)).close().extrude(t))
        body=strip if body is None else body.union(strip)
    if p['webStyle']=='petal':
        lo,hi=[arc['middle'] for arc in spec['arcs']]
        body=body.union(cq.Workplane('XY').box(hi-lo+w,w,t,centered=(True,True,False)).translate(((hi+lo)/2,0,0)))
    for sign in (-1,1):
        x,y=spec['a'],sign*spec['b']
        body=body.union(cq.Workplane('XY').center(x,y).circle(spec['pad']).extrude(t))
        body=body.cut(cq.Workplane('XY').center(x,y).circle(p['webHole']/2).extrude(t))
    if spec['eye']:
        eye=spec['eye'];body=body.union(cq.Workplane('XY').center(eye['x'],0).circle(eye['pad']).extrude(t))
        if p['hanging']=='paracord':cut=cq.Workplane('XY').center(eye['x'],0).circle(eye['hole']/2).extrude(t)
        else:cut=cq.Workplane('XY').box(p['webbingWidth']+1,p['webbingThickness']+1,t+2,centered=(True,True,False)).translate((eye['x'],0,-1))
        body=body.cut(cut)
    result=body.val()
    if not result.isValid() or len(result.Solids())!=1:raise ValueError('The web panel could not be joined into one part.')
    return result
