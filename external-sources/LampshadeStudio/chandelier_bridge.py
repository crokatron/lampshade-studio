"""A repeatable curved ribbon with two integral T5 clips, using analytic faces."""
import math


def specification(p):
    half=math.pi/p['count'];radius=p['hubRadius']+p['webReach']
    length=p['bridgeClipLength'];step=(length+4)/2
    # Each repeated bridge has an inner clip at its first end and an outer
    # clip at its second. Adjacent copies share a bar without overlapping.
    clips=[dict(radius=radius-step,angle=-math.degrees(half)),dict(radius=radius+step,angle=math.degrees(half))]
    if radius-step-length/2 < p['hubRadius']+1:
        raise ValueError('Increase clip distance beyond the hub edge to separate neighbouring clip pairs and the optional hub.')
    if radius+step+length/2 > p['hubRadius']-p['engagement']+p['length']:
        raise ValueError('Reduce clip distance to keep both clip pairs on the T5 lights.')
    offset=p['width']/2+p['clearance']+p['saddleWall']-2
    co,si=math.cos(half),math.sin(half)
    first=[(radius-step)*co+offset*si,-(radius-step)*si+offset*co]
    last=[(radius+step)*co+offset*si,(radius+step)*si-offset*co]
    center=[(x+y)/2 for x,y in zip(first,last)]
    dy=last[1]-first[1];dx=last[0]-first[0];span=math.hypot(dx,dy);b=span/2
    if dy<length+4:raise ValueError('The printed bridges are too close. Increase the spoke spacing or use fewer lights.')
    normal=[dy/span,-dx/span];angle=math.degrees(math.atan2(normal[1],normal[0]))
    sag=max(12,p['hubRadius']+14-math.hypot(*center))
    outer=sag+p['bridgeBandWidth']
    if outer>=b*.95:raise ValueError('The curved band is too wide for this spoke spacing. Reduce band width or increase the clip radius with Auto space.')
    arcs=[]
    for middle in (sag,outer):
        cx=(middle*middle-b*b)/(2*middle);r=middle-cx
        arcs.append(dict(cx=cx,radius=r,angle=math.atan2(b,-cx),middle=middle))
    eye_local=(sag+outer)/2
    eye=dict(x=center[0]+normal[0]*eye_local,y=center[1]+normal[1]*eye_local,
             localX=eye_local,hole=p['cordDiameter']+.8)
    return dict(integrated=True,radius=radius,clips=clips,center=center,angle=angle,b=b,arcs=arcs,
                eye=eye if p['hangerFrom']=='web' else None,z=0,
                top=p['height']+p['clearance']+p['saddleWall'])


def make_bridge(p,spec):
    import cadquery as cq
    top=spec['top'];t=p['webThickness'];rib=2.
    def end(arc,side,outer):
        r=arc['radius']+(rib/2 if outer else -rib/2)
        return (arc['cx']+r*math.cos(arc['angle']),side*r*math.sin(arc['angle']))
    inner,outer=spec['arcs']
    # Filled curved band, tapering into the clips at each end.
    outline=(cq.Workplane('XY').moveTo(*end(outer,-1,True))
             .threePointArc((outer['middle']+rib/2,0),end(outer,1,True))
             .lineTo(*end(inner,1,False))
             .threePointArc((inner['middle']-rib/2,0),end(inner,-1,False)).close())
    body=outline.extrude(t).translate((0,0,top-t))
    if spec['eye']:
        if p['hanging']=='paracord':cut=cq.Workplane('XY').center(spec['eye']['localX'],0).circle(spec['eye']['hole']/2).extrude(top+1)
        else:cut=cq.Workplane('XY').box(p['webbingThickness']+1,p['webbingWidth']+1,top+1,centered=(True,True,False)).translate((spec['eye']['localX'],0,0))
        body=body.cut(cut)
    body=body.rotate((0,0,0),(0,0,1),spec['angle']).translate((*spec['center'],0))
    L,W,H,c,wall=p['bridgeClipLength'],p['width'],p['height'],p['clearance'],p['saddleWall']
    lip=p['bridgeLip'];lip_t=1.6
    clip=cq.Workplane('XY').box(L,W+2*c+2*wall,wall,centered=(True,True,False)).translate((0,0,H+c))
    for sign in (-1,1):
        clip=clip.union(cq.Workplane('XY').box(L,wall,top+lip_t,centered=(True,True,False)).translate((0,sign*(W/2+c+wall/2),-lip_t)))
        width=wall+c+lip
        clip=clip.union(cq.Workplane('XY').box(L,width,lip_t,centered=(True,True,False)).translate((0,sign*(W/2-lip+width/2),-lip_t)))
    for item in spec['clips']:
        a=math.radians(item['angle'])
        placed=clip.rotate((0,0,0),(0,0,1),item['angle']).translate((item['radius']*math.cos(a),item['radius']*math.sin(a),0))
        body=body.union(placed)
    result=body.val()
    if not result.isValid() or len(result.Solids())!=1:raise ValueError('The curved bridge and its clips could not join into one printed part.')
    return result


def collector_spec(p):
    hole=p['cordDiameter']+.8
    pitch=max(12.,(hole+4)/(2*math.sin(math.pi/p['count'])))
    return dict(pitch=pitch,radius=pitch+hole/2+4,thickness=4.,hole=hole)


def make_collector(p):
    import cadquery as cq
    spec=collector_spec(p)
    body=cq.Workplane('XY').circle(spec['radius']).extrude(spec['thickness'])
    body=body.cut(cq.Workplane('XY').circle(spec['hole']/2).extrude(spec['thickness']))
    for i in range(p['count']):
        a=math.radians(p['rotation']+180/p['count'])+2*math.pi*i/p['count']
        body=body.cut(cq.Workplane('XY').center(spec['pitch']*math.cos(a),spec['pitch']*math.sin(a)).circle(spec['hole']/2).extrude(spec['thickness']))
    return body.val()
