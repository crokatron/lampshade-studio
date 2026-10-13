"""Dimensioned light-bar layouts. Editable printed parts and dimensioned hardware references; no load rating."""
import math
from itertools import product
from pathlib import Path

DEFAULT = dict(layout="sunburst", count=3, length=305., width=20., height=20.,
               radius=210., spacing=90., tiers=1, tierGap=140., stagger=30.,
               spiralDrop=300., tilt=0., rotation=0., suspension=300., endSpace=25.,
               hanging="paracord", cordDiameter=4., webbingWidth=15., webbingThickness=1.5,
               clearance=1., saddleLength=26., saddleWall=4., clipHole=3.4,
               printedWebbing=True, strapHole=4., strapEnd=10., support='hub',
               hubRadius=90., hubThickness=10., armWidth=18., armThickness=8., hubFixing=4.5, hangerHole=6.5,
               spokeType='t5',engagement=65.,webEnabled=True,webReach=20.,webRib=3.,webThickness=3.,webHole=3.4,webStyle='petal',
               hangerFrom='web',keepHub=False,printSize=230.,webConstruction='integrated',bridgeClipLength=16.,
               bridgeBandWidth=24.,bridgeLip=.8,cordCollector=True,collectorRise=80.)
LAYOUTS = {
    "sunburst": "Sunburst", "halo": "Halo", "parallel": "Parallel",
    "spiral": "Descending spiral", "lantern": "Vertical lantern",
}
LIMITS = dict(count=(3,32), length=(100,1500), width=(5,150), height=(5,150),
              radius=(30,2000), spacing=(10,1000), tiers=(1,8), tierGap=(20,1000),
              stagger=(-180,180), spiralDrop=(0,2000), tilt=(-60,60),
              rotation=(-180,180), suspension=(50,2000), endSpace=(0,150),
              cordDiameter=(2,10),webbingWidth=(8,40),webbingThickness=(.5,5),
              clearance=(.3,4),saddleLength=(16,70),saddleWall=(3,10),clipHole=(2,6),strapHole=(2,8),strapEnd=(6,30),
              hubRadius=(45,400),hubThickness=(6,30),armWidth=(12,50),armThickness=(5,25),hubFixing=(3,8),hangerHole=(4,12),engagement=(35,150),
              webReach=(20,100),webRib=(2,8),webThickness=(1.2,6),webHole=(2,6),printSize=(100,1000),
              bridgeClipLength=(12,40),bridgeBandWidth=(12,45),bridgeLip=(.3,1.5),collectorRise=(30,500))


def validate(raw):
    if not isinstance(raw, dict): raise ValueError("A chandelier design is required.")
    p = {**DEFAULT, **{k:v for k,v in raw.items() if k in DEFAULT}}
    if 'support' not in raw and (p['layout']!='sunburst' or p['tiers']!=1 or p['tilt']!=0):p['support']='slings'
    if p['layout'] not in LAYOUTS: raise ValueError("Choose a chandelier layout.")
    if p['hanging'] not in ('paracord','webbing'): raise ValueError('Choose paracord or webbing.')
    if p['support'] not in ('hub','slings'):raise ValueError('Choose a printed hub or suspension study.')
    if p['spokeType'] not in ('t5','printed'):raise ValueError('Choose T5 spokes or printed carrier spokes.')
    if not isinstance(p['printedWebbing'],bool): raise ValueError('Printed webbing must be on or off.')
    if not isinstance(p['webEnabled'],bool):raise ValueError('Inter-spoke webs must be on or off.')
    if p['webStyle'] not in ('petal','arc'):raise ValueError('Choose petal or arc webs.')
    if p['webConstruction'] not in ('integrated','bolted'):raise ValueError('Choose integral clips or separate bolted collars.')
    if not isinstance(p['cordCollector'],bool):raise ValueError('Printed cord junction must be on or off.')
    if p['hangerFrom'] not in ('hub','web'):raise ValueError('Choose a central hanger or web eyelets.')
    if not isinstance(p['keepHub'],bool):raise ValueError('Keep hub must be on or off.')
    if p['hangerFrom']=='web' and not p['webEnabled']:raise ValueError('Enable inter-spoke webs to hang from them.')
    for key, (lo, hi) in LIMITS.items():
        value = p[key]
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f"{key} must be between {lo} and {hi}.")
        if key in ('count','tiers'):
            if value != int(value): raise ValueError(f"{key} must be a whole number.")
            value = int(value)
        p[key] = value
    if p['layout'] == 'spiral': p['tiers'] = 1
    if p['count'] < 3*p['tiers']: raise ValueError("Allow at least 3 bars in each tier, or reduce the tier count.")
    opening=p['cordDiameter']+.8 if p['hanging']=='paracord' else p['webbingWidth']+1
    if p['support']=='slings' and p['saddleLength'] < opening+2*p['saddleWall']:
        raise ValueError('Increase saddle length to leave a full wall around the suspension opening.')
    if p['saddleLength'] >= p['length']*.3: raise ValueError('Saddle length must be less than 30% of bar length.')
    if p['strapHole']+4>p['webbingWidth'] or p['strapHole']/2+3>p['strapEnd']:
        raise ValueError('Leave at least 2 mm beside strap holes and 3 mm at each end.')
    if p['support']=='hub':
        if p['layout']!='sunburst' or p['tiers']!=1 or p['tilt']!=0:
            raise ValueError('The rigid centre hub uses a single-level Sunburst with no bar tilt.')
        direct=p['spokeType']=='t5'
        if direct and (p['engagement']<2*p['saddleLength']+4 or p['engagement']>p['length']*.6):
            raise ValueError('Hub engagement must fit two saddles with a 4 mm gap, and remain below 60% of bar length.')
        minimum=(p['engagement']-p['saddleLength']/2+(p['width']+2*p['clearance']+2*p['saddleWall']+3)/(2*math.sin(math.pi/p['count']))) if direct else 38+(p['armWidth']+3)/(2*math.sin(math.pi/p['count']))
        if p['hubRadius']<minimum:raise ValueError(f'Increase hub radius to at least {math.ceil(minimum)} mm to separate the spoke roots.')
        if direct:p['radius']=p['hubRadius']-p['engagement']+p['length']/2
        if not direct and p['radius']-p['length']*.32-p['saddleLength']/2<p['hubRadius']+5:
            raise ValueError('Increase bar centre radius to keep the inner saddles outside the hub.')
        if p['armWidth']<p['hubFixing']+8:raise ValueError('Increase spoke width to leave 4 mm beside each fixing hole.')
    if p['webEnabled'] and (p['support']!='hub' or p['spokeType']!='t5'):
        raise ValueError('Inter-spoke webs use the T5-spoke centre hub.')
    if p['webEnabled'] and p['webConstruction']=='integrated' and p['webThickness']>p['saddleWall']:
        raise ValueError('Keep bridge thickness at or below clip wall thickness for a flat printing face.')
    return p


def add(a,b): return [x+y for x,y in zip(a,b)]
def mul(a,n): return [x*n for x in a]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]


def point(bar, xyz):
    result = bar['center'][:]
    for axis, n in zip(bar['axes'], xyz): result = add(result,mul(axis,n))
    return result


def corners(bar, size):
    return [point(bar,[s*d/2 for s,d in zip(signs,size)]) for signs in product((-1,1),repeat=3)]


def intersects(a,b,size):
    """Separating-axis test for oriented rectangular hardware envelopes."""
    axes = a['axes']+b['axes']+[cross(u,v) for u in a['axes'] for v in b['axes']]
    delta = [x-y for x,y in zip(a['center'],b['center'])]
    for axis in axes:
        if dot(axis,axis) < 1e-12: continue
        ra = sum(abs(dot(axis,u))*d/2 for u,d in zip(a['axes'],size))
        rb = sum(abs(dot(axis,u))*d/2 for u,d in zip(b['axes'],size))
        if abs(dot(axis,delta)) >= ra+rb-1e-7: return False
    return True


def layout(raw):
    p=validate(raw); bars=[]; start=0
    for tier in range(p['tiers']):
        n=p['count']//p['tiers']+(tier < p['count']%p['tiers'])
        for j in range(n):
            i=start+j
            angle=math.radians(p['rotation']+tier*p['stagger'])+2*math.pi*j/n
            if p['layout']=='parallel':
                rot=math.radians(p['rotation']+tier*p['stagger'])
                offset=(j-(n-1)/2)*p['spacing']
                x,y=-offset*math.sin(rot),offset*math.cos(rot); yaw=rot
            else:
                x,y=p['radius']*math.cos(angle),p['radius']*math.sin(angle)
                yaw=angle+(math.pi/2 if p['layout'] in ('halo','spiral') else math.pi if p['layout']=='lantern' else 0)
            z=tier*p['tierGap']
            if p['layout']=='spiral': z=(1-i/(p['count']-1))*p['spiralDrop']
            pitch=math.radians(p['tilt']+(90 if p['layout']=='lantern' else 0))
            u=[math.cos(yaw)*math.cos(pitch),math.sin(yaw)*math.cos(pitch),math.sin(pitch)]
            v=[-math.sin(yaw),math.cos(yaw),0.]; w=cross(u,v)
            bars.append(dict(id=i+1,tier=tier+1,center=[x,y,z],axes=[u,v,w],yaw=math.degrees(yaw),pitch=math.degrees(pitch)))
        start+=n
    size=[p['length'],p['width'],p['height']]
    low=min(q[2] for b in bars for q in corners(b,size))
    for b in bars: b['center'][2]-=low
    all_points=[q for b in bars for q in corners(b,size)]
    lower=[min(q[k] for q in all_points) for k in range(3)]
    upper=[max(q[k] for q in all_points) for k in range(3)]
    clashes=[]; connectors=[]
    expanded=[p['length']+2*p['endSpace'],p['width'],p['height']]
    for i,a in enumerate(bars):
        for b in bars[i+1:]:
            if intersects(a,b,size): clashes.append([a['id'],b['id']])
            elif p['endSpace'] and intersects(a,b,expanded): connectors.append([a['id'],b['id']])
    ceiling=upper[2]+p['suspension']; anchors=[]; mounts=[]
    hole=p['cordDiameter']+.8 if p['hanging']=='paracord' else p['webbingThickness']+1
    ear=hole+2*p['saddleWall'] if p['support']=='slings' else 0
    ear_y=p['width']/2+p['clearance']+p['saddleWall']+ear/2
    top_z=p['height']/2+p['clearance']+p['saddleWall']/2
    offsets=[-p['length']/2+p['saddleLength']/2,-p['length']/2+p['engagement']-p['saddleLength']/2] if p['support']=='hub' and p['spokeType']=='t5' else [-p['length']*.32,p['length']*.32]
    for b in bars:
        for index,n in enumerate(offsets):
            mounts.append(dict(bar=b['id'],number=index+1,center=point(b,[n,0,0]),axes=b['axes']))
            for side in (-1,1):
                bottom=point(b,[n,side*ear_y,top_z])
                top=[bottom[0]*.22,bottom[1]*.22,ceiling]
                anchors.append(dict(bar=b['id'],saddle=index+1,side=side,bottom=bottom,top=top,length=math.dist(bottom,top)))
    hub=None
    if p['support']=='hub':
        arm_bottom=p['height']+p['clearance']+p['saddleWall']
        hub_bottom=arm_bottom+(p['armThickness'] if p['spokeType']=='printed' else 0);hub_top=hub_bottom+p['hubThickness']
        ceiling=hub_top+p['suspension']
        hub=dict(bottom=hub_bottom,top=hub_top,armBottom=arm_bottom,armRoot=p['hubRadius']-38,
                 armEnd=p['radius']+p['length']*.32+p['saddleLength']/2,
                 fixingRadii=[p['radius']+n for n in offsets] if p['spokeType']=='t5' else [p['hubRadius']-30,p['hubRadius']-12])
        hub['included']=p['hangerFrom']!='web' or p['keepHub']
        if not hub['included']:mounts=[]
        anchors=[dict(bar=0,saddle=0,side=0,bottom=[0,0,hub_top],top=[0,0,ceiling],length=p['suspension'])]
    web=None;collector=None
    if p['webEnabled']:
        if p['webConstruction']=='integrated':from chandelier_bridge import specification
        else:from chandelier_web import specification
        web=specification(p)
        web['panels']=[];web['collars']=[]
        for b in bars:
            web['panels'].append(dict(angle=b['yaw']+180/p['count']))
            if p['webConstruction']=='bolted':web['collars'].append(dict(bar=b['id'],center=point(b,[web['radius']-p['radius'],0,0]),axes=b['axes']))
        if p['hangerFrom']=='web':
            anchors=[]
            if p['cordCollector'] and p['hanging']=='paracord':
                from chandelier_bridge import collector_spec
                collector={**collector_spec(p),'z':ceiling}
            for i,item in enumerate(web['panels']):
                a=math.radians(item['angle']);x=web['eye']['x'];y=web['eye'].get('y',0)
                bottom=[x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),web.get('top',web['z']+p['webThickness'])]
                top=[collector['pitch']*math.cos(a),collector['pitch']*math.sin(a),ceiling] if collector else [0,0,ceiling]
                anchors.append(dict(bar=0,saddle=i+1,side=0,bottom=bottom,top=top,length=math.dist(bottom,top)))
            if collector:
                bottom=[0,0,ceiling+collector['thickness']];top=[0,0,bottom[2]+p['collectorRise']]
                anchors.append(dict(bar=0,saddle=0,side=0,bottom=bottom,top=top,length=p['collectorRise']))
                ceiling=top[2]
    # Check the three solid rectangular regions of each saddle. Hole voids are
    # conservatively ignored; no claim is made about cord routing intersections.
    regions=[]
    for m in mounts:
        for local,dim in [([0,0,top_z],[p['saddleLength'],2*(p['width']/2+p['clearance']+p['saddleWall']+ear),p['saddleWall']]),
                          ([0,-(p['width']/2+p['clearance']+p['saddleWall']/2),(p['clearance']+p['saddleWall'])/2],[p['saddleLength'],p['saddleWall'],p['height']+p['clearance']+p['saddleWall']]),
                          ([0,(p['width']/2+p['clearance']+p['saddleWall']/2),(p['clearance']+p['saddleWall'])/2],[p['saddleLength'],p['saddleWall'],p['height']+p['clearance']+p['saddleWall']])]:
            regions.append(dict(center=point(m,local),axes=m['axes'],size=dim,bar=m['bar']))
    def overlap(a,b,asize,bsize):
        # Reuse SAT with different half extents through local unit scaling below.
        axes=a['axes']+b['axes']+[cross(u,v) for u in a['axes'] for v in b['axes']]
        delta=[x-y for x,y in zip(a['center'],b['center'])]
        for axis in axes:
            if dot(axis,axis)<1e-12: continue
            ra=sum(abs(dot(axis,u))*d/2 for u,d in zip(a['axes'],asize))
            rb=sum(abs(dot(axis,u))*d/2 for u,d in zip(b['axes'],bsize))
            if abs(dot(axis,delta))>=ra+rb-1e-7:return False
        return True
    mount_clashes=set()
    for i,a in enumerate(regions):
        for b in bars:
            if a['bar']!=b['id'] and overlap(a,b,a['size'],size):mount_clashes.add(tuple(sorted((a['bar'],b['id']))))
        for b in regions[i+1:]:
            if a['bar']!=b['bar'] and overlap(a,b,a['size'],b['size']):mount_clashes.add(tuple(sorted((a['bar'],b['bar']))))
    return dict(parameters=p,bars=bars,size=size,bounds=dict(min=lower,max=upper,size=[hi-lo for lo,hi in zip(lower,upper)]),
                clashes=clashes,connectorClashes=connectors,ceiling=ceiling,anchors=anchors,mounts=mounts,
                mountClashes=sorted(mount_clashes),saddle=dict(ear=ear,earY=ear_y,topZ=top_z),hub=hub,web=web,collector=collector)


def preview(raw):
    model=layout(raw)
    p=model['parameters'];checks=[]
    def fit(name,size):checks.append(dict(name=name,size=size,fits=all(d<=p['printSize']+.001 for d in size)))
    if model['hub'] and model['hub']['included']:
        fit('Centre hub',[2*p['hubRadius'],2*p['hubRadius'],p['hubThickness']])
        if p['spokeType']=='printed':fit('Carrier spoke',[model['hub']['armEnd']-model['hub']['armRoot'],p['armWidth'],p['armThickness']])
    if model['mounts']:fit('Retaining collar',[p['saddleLength'],p['width']+2*p['clearance']+2*p['saddleWall']+2*model['saddle']['ear'],p['height']+p['clearance']+p['saddleWall']])
    if model['web']:
        if p['webConstruction']=='integrated':from chandelier_bridge import make_bridge as make_panel
        else:from chandelier_web import make_panel
        panel=make_panel(model['parameters'],model['web'])
        vertices,faces=panel.tessellate(.15,.15)
        model['web']['mesh']=dict(positions=[coord for v in vertices for coord in v.toTuple()],indices=[i for face in faces for i in face])
        from geometry import exact_bounds
        bounds=exact_bounds(panel);model['web']['printSize']=[bounds[i+3]-bounds[i] for i in range(3)]
        fit('Clip bridge' if p['webConstruction']=='integrated' else 'Curved web panel',model['web']['printSize'])
        if p['webConstruction']=='bolted':fit('Web clip collar',[p['saddleLength'],p['width']+2*p['clearance']+6*p['saddleWall']+2*p['webHole'],p['height']+p['clearance']+p['saddleWall']])
    if model['collector']:
        from chandelier_bridge import make_collector
        c=model['collector'];vertices,faces=make_collector(p).tessellate(.15,.15)
        c['mesh']=dict(positions=[coord for v in vertices for coord in v.toTuple()],indices=[i for face in faces for i in face])
        fit('Cord junction',[2*c['radius'],2*c['radius'],c['thickness']])
    if p['hanging']=='webbing' and p['printedWebbing']:
        fit('Longest suspension strap',[p['webbingWidth'],max(a['length'] for a in model['anchors'])+2*p['strapEnd'],p['webbingThickness']])
    model['printChecks']=checks
    from chandelier_assembly import inventory
    catalog=inventory(model)
    model.update(bom=catalog['bom'],tree=catalog['tree'],assemblySummary=catalog['summary'],occurrences=catalog['occurrences'])
    return model


def solids(model):
    import cadquery as cq
    result=[]
    for bar in model['bars']:
        plane=cq.Plane(origin=tuple(bar['center']),xDir=tuple(bar['axes'][0]),normal=tuple(bar['axes'][2]))
        result.append(cq.Workplane(plane).box(*model['size']).val())
    return result


def saddle(p):
    """Open-front saddle with a centre hole for the fixture's supplied metal clip."""
    import cadquery as cq
    L,W,H,t,c=p['saddleLength'],p['width'],p['height'],p['saddleWall'],p['clearance']
    opening=p['cordDiameter']+.8 if p['hanging']=='paracord' else p['webbingThickness']+1
    ear=opening+2*t if p['support']=='slings' else 0; half=W/2+c+t
    z=H/2+c+t/2
    body=cq.Workplane('XY').box(L,2*half+2*ear,t).translate((0,0,z))
    for side in (-1,1):
        wall=cq.Workplane('XY').box(L,t,H+c+t).translate((0,side*(W/2+c+t/2),(c+t)/2))
        body=body.union(wall)
        if p['support']=='hub':continue
        cy=side*(half+ear/2)
        if p['hanging']=='paracord':
            cut=cq.Workplane('XY').center(0,cy).circle((p['cordDiameter']+.8)/2).extrude(t+2).translate((0,0,z-t/2-1))
        else:
            cut=cq.Workplane('XY').box(p['webbingWidth']+1,p['webbingThickness']+1,t+2).translate((0,cy,z))
        body=body.cut(cut)
    drill=cq.Workplane('XY').circle(p['clipHole']/2).extrude(t+2).translate((0,0,z-t/2-1))
    result=body.cut(drill).val()
    if not result.isValid() or len(result.Solids())!=1: raise ValueError('Saddle geometry is invalid.')
    return result


def strap(p,span):
    """Flat printable strap, with the two end-hole centres separated by span."""
    import cadquery as cq
    body=cq.Workplane('XY').box(p['webbingWidth'],span+2*p['strapEnd'],p['webbingThickness'])
    for sign in (-1,1):
        drill=cq.Workplane('XY').center(0,sign*span/2).circle(p['strapHole']/2).extrude(p['webbingThickness']+2).translate((0,0,-p['webbingThickness']/2-1))
        body=body.cut(drill)
    return body.val()


def hub_parts(model):
    """Bolted spoke roots below the hub; spokes seat on top of both clip saddles."""
    import cadquery as cq
    p=model['parameters'];h=model['hub']
    hub=cq.Workplane('XY').circle(p['hubRadius']).extrude(p['hubThickness'])
    if p['hanging']=='webbing':
        hub=hub.cut(cq.Workplane('XY').box(p['webbingWidth']+1,p['webbingThickness']+1,p['hubThickness']+2).translate((0,0,p['hubThickness']/2)))
    else:hub=hub.cut(cq.Workplane('XY').circle(p['hangerHole']/2).extrude(p['hubThickness']))
    arm=None
    if p['spokeType']=='printed':
        length=h['armEnd']-h['armRoot'];cx=(h['armRoot']+h['armEnd'])/2
        arm=cq.Workplane('XY').box(length,p['armWidth'],p['armThickness'],centered=(True,True,False)).translate((cx,0,0))
        for radius in h['fixingRadii']+[p['radius']-p['length']*.32,p['radius']+p['length']*.32]:
            diameter=p['hubFixing'] if radius in h['fixingRadii'] else p['clipHole']
            arm=arm.cut(cq.Workplane('XY').center(radius,0).circle(diameter/2).extrude(p['armThickness']))
    for b in model['bars']:
        yaw=math.radians(b['yaw'])
        for radius in h['fixingRadii']:
            hole=cq.Workplane('XY').center(radius*math.cos(yaw),radius*math.sin(yaw)).circle((p['clipHole'] if p['spokeType']=='t5' else p['hubFixing'])/2).extrude(p['hubThickness'])
            hub=hub.cut(hole)
    return hub.val(),arm.val() if arm is not None else None


def export(raw,fmt,folder):
    """Keep each bar a separate, named CAD solid; round-trip and check placements."""
    import cadquery as cq
    from geometry import exact_bounds
    model=layout(raw)
    if fmt not in ('step','brep','stl','x_b','x_t'): raise ValueError("Choose STEP, BREP, STL or Parasolid for the bar layout.")
    scope=raw.get('scope','assembly')
    if scope not in ('assembly','saddles','single','strap','parts','hub','arm','web','web-collar','collector'): raise ValueError('Choose an export content option.')
    if scope not in ('single','strap','hub','arm','web','web-collar') and model['clashes']: raise ValueError("Bars overlap. Increase spacing or change the layout before exporting.")
    if scope not in ('single','strap','hub','arm','web','web-collar') and model['mountClashes']: raise ValueError('Suspension saddles overlap other parts. Increase spacing, tier separation or radius.')
    if scope in ('hub','arm') and (not model['hub'] or not model['hub']['included']):raise ValueError('Choose the printed centre hub first.')
    if scope=='arm' and model['parameters']['spokeType']=='t5':raise ValueError('The T5 lights are the spokes; there is no printed arm to export.')
    if scope in ('web','web-collar') and not model['web']:raise ValueError('Enable inter-spoke webs first.')
    from chandelier_assembly import build
    assembly,bodies,names=build(model,scope)
    compound=cq.Compound.makeCompound(bodies)
    if fmt=='stl' and scope in ('single','strap','hub','arm','web','web-collar','collector'):
        if scope=='web' and model['parameters']['webConstruction']=='integrated':compound=compound.rotate((0,0,0),(1,0,0),180)
        bounds=exact_bounds(compound);size=[bounds[i+3]-bounds[i] for i in range(3)]
        if max(size)>model['parameters']['printSize']+.001:
            raise ValueError(f"This part is {' × '.join(f'{d:.1f}' for d in size)} mm. It exceeds the {model['parameters']['printSize']:g} mm print volume; resize the part or export STEP to divide it in CAD.")
        compound=compound.translate((-(bounds[0]+bounds[3])/2,-(bounds[1]+bounds[4])/2,-bounds[2]))
    path=Path(folder)/('chandelier.'+('step' if fmt in ('x_b','x_t') else fmt))
    if fmt in ('step','x_b','x_t'):
        assembly.save(str(path),'STEP')
        back=cq.importers.importStep(str(path)).val()
    elif fmt=='brep':
        if not compound.exportBrep(str(path)): raise ValueError('BREP export failed.')
        back=cq.Shape.importBrep(str(path))
    else:
        cq.exporters.export(compound,str(path),exportType='STL',tolerance=.1,angularTolerance=.2)
        return path.read_bytes(),model
    imported=back.Solids()
    if len(imported)!=len(bodies) or not back.isValid(): raise ValueError('The exported bar bodies did not validate.')
    expected=[exact_bounds(b) for b in bodies]
    actual=[exact_bounds(b) for b in imported]
    for bounds in expected:
        match=next((i for i,candidate in enumerate(actual) if max(abs(x-y) for x,y in zip(bounds,candidate))<.001),None)
        if match is None: raise ValueError('The exported component positions did not validate.')
        actual.pop(match)
    if fmt in ('x_b','x_t'):
        from nx_export import translate_step
        data,report=translate_step(path,folder,fmt,components=[dict(name=name,bounds=list(exact_bounds(body))) for name,body in zip(names,bodies)])
        return data,model
    return path.read_bytes(),model
