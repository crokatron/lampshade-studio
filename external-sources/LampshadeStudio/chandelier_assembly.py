"""One component inventory for the navigator, quantified BOM and CAD assembly.

Part numbers identify geometry within and across configurations. Occurrences
reuse the same canonical shape; placement never creates a new part definition.
"""
import csv
import hashlib
import io
import json
import math
from collections import Counter


def inventory(model):
    p=model['parameters'];parts={};occurrences=[];groups={}
    def part(code,name,kind,keys=(),extra=None,notes=''):
        signature={k:p[k] for k in keys}
        if extra:signature.update(extra)
        def canonical(value):
            if isinstance(value,dict):return {k:canonical(v) for k,v in value.items()}
            if isinstance(value,list):return [canonical(v) for v in value]
            if isinstance(value,(float,int)) and not isinstance(value,bool):
                value=round(value,9)
                return int(value) if value==int(value) else value
            return value
        signature=canonical(signature)
        suffix=hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()[:8].upper()
        number=f'{code}-{suffix}'
        parts[number]=dict(partNumber=number,name=name,kind=kind,category='Purchased' if kind=='light' else 'Printed',
                           unit='each',modeled=True,notes=notes,specification=signature)
        return number
    def occurrence(number,label,group,pose=None):
        groups.setdefault(group,[])
        item=dict(id=f'C{len(occurrences)+1:03}',partNumber=number,name=label,group=group,pose=pose or {})
        occurrences.append(item);groups[group].append(item)
    collar_keys=('width','height','clearance','saddleLength','saddleWall','clipHole')
    light=part('T5','Barrina T5 light reference','light',('length','width','height'),notes='Rectangular listing-size proxy; verify the actual light and its clip fit.')
    root=None
    if model['mounts']:
        extra={'earOpening':p['cordDiameter']+.8 if p['hanging']=='paracord' else [p['webbingWidth']+1,p['webbingThickness']+1]} if p['support']=='slings' else {'earOpening':None}
        root=part('CLIP','Root retaining collar' if p['support']=='hub' else 'Suspension saddle','collar',collar_keys,extra)
    wc=None
    if model['web'] and p['webConstruction']=='bolted':
        wc=part('WEBCLIP','Web retaining collar','web-collar',(*collar_keys,'webHole'))
    for bar in model['bars']:
        group=f"Light_unit_{bar['id']:02}"
        occurrence(light,f"T5 light {bar['id']:02}",group,bar)
        for mount in model['mounts']:
            if mount['bar']==bar['id']:occurrence(root,f"Root collar {mount['number']}",group,mount)
        if wc:
            collar=next(m for m in model['web']['collars'] if m['bar']==bar['id'])
            occurrence(wc,'Web collar',group,collar)
    if model['hub'] and model['hub']['included']:
        h=model['hub']
        hub=part('HUB','Printed centre hub','hub',('hubRadius','hubThickness'),
                 dict(fixingRadii=h['fixingRadii'],hole=p['clipHole'] if p['spokeType']=='t5' else p['hubFixing'],
                      angles=[b['yaw'] for b in model['bars']],hanger=[p['hanging'],p['hangerHole'],p['webbingWidth'],p['webbingThickness']]))
        occurrence(hub,'Centre hub','Centre_hub',dict(translation=[0,0,h['bottom']]))
        if p['spokeType']=='printed':
            arm=part('ARM','Carrier spoke','arm',('armWidth','armThickness','hubFixing','clipHole'),
                     dict(root=h['armRoot'],end=h['armEnd'],holes=h['fixingRadii']+[p['radius']-p['length']*.32,p['radius']+p['length']*.32]))
            for b in model['bars']:occurrence(arm,f"Carrier {b['id']:02}",f"Light_unit_{b['id']:02}",dict(angle=b['yaw'],translation=[0,0,h['armBottom']]))
    if model['web']:
        if p['webConstruction']=='integrated':
            web=part('BRIDGE','Curved bridge with integral T5 clips','web',('width','height','clearance','saddleWall','webThickness','bridgeClipLength','bridgeBandWidth','bridgeLip','hanging','webbingWidth','webbingThickness'),
                     dict(clips=model['web']['clips'],center=model['web']['center'],arcs=model['web']['arcs'],eye=model['web']['eye']),
                     'One printed part: two staggered clips and a curved ribbon. Print broad face down, clip openings up. Test clip fit and retention on your actual T5 before suspension.')
        else:
            web=part('WEB','Curved web panel','web',('webRib','webThickness','webHole','webStyle'),
                     dict(a=model['web']['a'],b=model['web']['b'],arcs=model['web']['arcs'],eye=model['web']['eye'],hanging=p['hanging'],webbingThickness=p['webbingThickness']))
        for i,panel in enumerate(model['web']['panels']):
            occurrence(web,f"{'Clip bridge' if p['webConstruction']=='integrated' else 'Web panel'} {i+1:02}",'Repeated_clip_bridges' if p['webConstruction']=='integrated' else 'Inter_spoke_webs',dict(angle=panel['angle'],translation=[0,0,model['web']['z']]))
    if model.get('collector'):
        junction=part('JUNCTION','Printed paracord junction','collector',('count','cordDiameter','rotation'),notes='One hole for each bridge cord plus the central hanger. Knot/termination details and loads require physical validation.')
        occurrence(junction,'Cord junction','Suspension',dict(translation=[0,0,model['collector']['z']]))
    if p['hanging']=='webbing' and p['printedWebbing']:
        for i,anchor in enumerate(model['anchors']):
            span=round(anchor['length'],6)
            strap=part('STRAP','Printed suspension strap','strap',('webbingWidth','webbingThickness','strapHole','strapEnd'),dict(span=span),
                       'Straight span with end holes; finish end attachment in CAD. Flexible material and load testing required.')
            occurrence(strap,f'Suspension strap {i+1:02}','Suspension',dict(anchor=anchor))
    quantities=Counter(o['partNumber'] for o in occurrences)
    bom=[{**v,'quantity':quantities[k]} for k,v in parts.items() if quantities[k]]
    hardware=[]
    def required(number,name,qty,notes,unit='each'):
        if qty:hardware.append(dict(partNumber=number,name=name,quantity=qty,unit=unit,category='Hardware',modeled=False,notes=notes,kind='hardware',specification={}))
    collars=len(model['mounts'])+(len(model['web']['collars']) if model['web'] else 0)
    required('HW-T5-CLIP','Supplied T5 metal retaining clip',collars,'One per printed collar; verify the actual clip profile and retention. Not modeled.')
    required('HW-CLIP-FIX','Clip fixing set',collars,f"Nominal {p['clipHole']:g} mm clearance hole. Thread, length, nut and washer selection require measured clip/stack dimensions. Not modeled.")
    if model['web'] and p['webConstruction']=='bolted':required('HW-WEB-FIX','Web-to-collar fixing set',2*p['count'],f"One per panel end, {p['webHole']:g} mm clearance. Select thread and length for {p['webThickness']+p['saddleWall']:g} mm nominal printed stack plus washers/clip hardware. Not modeled.")
    if model['hub'] and model['hub']['included'] and p['spokeType']=='printed':required('HW-ARM-FIX','Carrier-to-hub fixing set',2*p['count'],f"{p['hubFixing']:g} mm clearance; {p['hubThickness']+p['armThickness']:g} mm printed stack. Thread/length TBD. Not modeled.")
    if p['hanging']=='paracord' or not p['printedWebbing']:
        spans=Counter(round(a['length'],3) for a in model['anchors'])
        for length,qty in sorted(spans.items()):
            material='Paracord' if p['hanging']=='paracord' else 'Webbing'
            required(f"HW-{material.upper()}-{length:g}",f'{material} span · {length:g} mm',qty,
                     f"Straight geometric length only; add knot/loop/fastening allowance before cutting. {'Diameter '+str(p['cordDiameter']) if material=='Paracord' else 'Width '+str(p['webbingWidth'])} mm. Preview guide, not CAD solid.")
    required('HW-CEILING','Ceiling suspension connection',1,'Select for the complete fixture and ceiling substrate; connection details and rating TBD. Not modeled.')
    required('HW-WIRING','Power and interconnection harness',1,'Route and measure for this arrangement using compatible T5 leads. Cable quantities/lengths TBD; not modeled.','set')
    bom+=hardware
    tree=dict(id='assembly',name='Grow-light chandelier',children=[])
    for group,items in groups.items():
        tree['children'].append(dict(id=group,name=group.replace('_',' '),children=[dict(id=o['id'],name=o['name'],partNumber=o['partNumber'],quantity=1,modeled=True) for o in items]))
    tree['children'].append(dict(id='hardware',name='Required hardware · not modeled',children=[dict(id=r['partNumber'],name=r['name'],partNumber=r['partNumber'],quantity=r['quantity'],modeled=False) for r in hardware]))
    return dict(parts=parts,occurrences=occurrences,bom=bom,tree=tree,
                summary=dict(modeledComponents=len(occurrences),uniqueParts=len(quantities),printedQuantity=sum(r['quantity'] for r in bom if r['category']=='Printed')))


def bom_csv(model):
    output=io.StringIO(newline='');writer=csv.writer(output)
    writer.writerow(['Part number','Description','Category','Quantity','Unit','Included in CAD','Notes'])
    for r in inventory(model)['bom']:
        writer.writerow([r['partNumber'],r['name'],r['category'],r['quantity'],r['unit'],'Yes' if r['modeled'] else 'No',r['notes']])
    return output.getvalue().encode('utf-8-sig')


def location(pose):
    import cadquery as cq
    if 'axes' in pose:return cq.Plane(origin=tuple(pose['center']),xDir=tuple(pose['axes'][0]),normal=tuple(pose['axes'][2])).location
    if 'anchor' in pose:
        a=pose['anchor'];direction=cq.Vector(*a['top']).sub(cq.Vector(*a['bottom'])).normalized()
        x=cq.Vector(1,0,0).cross(direction)
        if x.Length<1e-6:x=cq.Vector(0,1,0).cross(direction)
        x=x.normalized();normal=x.cross(direction)
        center=cq.Vector(*a['top']).add(cq.Vector(*a['bottom'])).multiply(.5)
        return cq.Plane(origin=center,xDir=x,normal=normal).location
    return cq.Location(tuple(pose.get('translation',[0,0,0])),(0,0,1),pose.get('angle',0))


def build(model,scope='assembly'):
    import cadquery as cq
    from chandelier import saddle,hub_parts,strap
    from chandelier_web import make_panel
    p=model['parameters'];data=inventory(model);shapes={};hub_pair=None
    selected_kind={'single':'collar','hub':'hub','arm':'arm','web':'web','web-collar':'web-collar','strap':'strap','collector':'collector'}.get(scope)
    selected=[]
    for o in data['occurrences']:
        kind=data['parts'][o['partNumber']]['kind']
        if selected_kind and kind!=selected_kind:continue
        if scope=='parts' and kind=='light':continue
        if scope=='saddles' and kind not in ('collar','web-collar'):continue
        selected.append(o)
    if selected_kind:
        if not selected:raise ValueError('This component is not included in the current assembly.')
        if scope=='strap':selected=[max(selected,key=lambda o:data['parts'][o['partNumber']]['specification']['span'])]
        else:selected=selected[:1]
        selected=[{**selected[0],'pose':{}}]
    assembly=cq.Assembly(name='Grow_light_chandelier');groups={};bodies=[];names=[]
    for o in selected:
        number=o['partNumber'];part=data['parts'][number];kind=part['kind']
        if number not in shapes:
            if kind=='light':shape=cq.Workplane('XY').box(*model['size']).val()
            elif kind=='collar':shape=saddle(p)
            elif kind=='web-collar':shape=saddle({**p,'support':'slings','hanging':'paracord','cordDiameter':p['webHole']-.8})
            elif kind=='web':
                if p['webConstruction']=='integrated':
                    from chandelier_bridge import make_bridge
                    shape=make_bridge(p,model['web'])
                else:shape=make_panel(p,model['web'])
            elif kind=='collector':
                from chandelier_bridge import make_collector
                shape=make_collector(p)
            elif kind=='strap':shape=strap(p,part['specification']['span'])
            else:
                if hub_pair is None:hub_pair=hub_parts(model)
                shape=hub_pair[0 if kind=='hub' else 1]
            shapes[number]=shape
        loc=location(o['pose']);shape=shapes[number];name=number+'__'+o['id']
        if o['group'] not in groups:groups[o['group']]=cq.Assembly(name=o['group'])
        groups[o['group']].add(shape,loc=loc,name=name,color=cq.Color(.05,.46,.85) if kind=='light' else cq.Color(.8,.12,.15))
        bodies.append(shape.located(loc));names.append(name)
    for group in groups.values():assembly.add(group)
    if not bodies:raise ValueError('No components are included in this export.')
    return assembly,bodies,names
