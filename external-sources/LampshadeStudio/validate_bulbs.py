"""Known clearance cases and STEP round trips for the dimensioned bulb guides."""
import json
from pathlib import Path
import cadquery as cq
from geometry import validate,rings,fit_grid,exact_bounds,make_solid,PRESETS
from bulb import BULBS,make_bulb,clearance

out=Path(__file__).parent/'exports'
results=[]
for name,definition in BULBS.items():
    for orientation in ('upright','pendant'):
        p=validate(dict(bulbType=name,bulbDiameter=definition['diameter'],bulbHeight=definition['height'],bulbZ=15,bulbOrientation=orientation))
        shape=make_bulb(p);path=out/f'bulb-{name}-{orientation}.step'
        cq.exporters.export(shape,str(path));back=cq.importers.importStep(str(path)).val()
        assert back.isValid() and len(back.Solids())==1
        x0,y0,z0,x1,y1,z1=exact_bounds(back)
        assert abs(x1-x0-p['bulbDiameter'])<.01 and abs(y1-y0-p['bulbDiameter'])<.01
        assert abs(z1-z0-p['bulbHeight'])<.01 and abs(z0-15)<.01
        results.append(dict(type=name,orientation=orientation,dimensions=[x1-x0,y1-y0,z1-z0],valid=True))

cylinder=dict(texture='smooth',bottom=100,top=100,bulge=0,wave=0,boxWidth=100,boxDepth=100,height=200,twist=0,wall=.8,exportMode='hollow')
p=validate(cylinder);report=clearance(p,fit_grid(rings(p,True),p))
assert report['state']=='clear',report
assert abs(report['gap']-17.2)<.02,report
assert abs(report['envelopeGap']-17.2)<.02,report
print('100 mm cylinder: expected radial gap 17.2 mm, measured',report['gap'],flush=True)

p=validate({**cylinder,'boxWidth':60,'boxDepth':60});report=clearance(p,fit_grid(rings(p,True),p))
assert report['state']=='collision' and report['gap']<-2.7,report
print('60 mm cylinder correctly reports bulb collision:',report['gap'],flush=True)

p=validate({**cylinder,'boxDepth':60});report=clearance(p,fit_grid(rings(p,True),p))
assert report['state']=='collision',report
print('Oval with insufficient depth correctly reports collision.',flush=True)

p=validate({**cylinder,'bulbZ':250});report=clearance(p,fit_grid(rings(p,True),p))
assert report['state']=='outside' and report['gap'] is None
p=validate({**cylinder,'bulbClearance':20});report=clearance(p,fit_grid(rings(p,True),p))
assert report['state']=='check'
print('Outside-height and larger target-gap cases pass.',flush=True)

mixed=validate({**PRESETS['silk'],'section':'square','roundness':3,'profile':'capsule','texture':'woven','ribs':24,'sway':6,'weaveRows':12,'boxWidth':175,'boxDepth':145})
shape=make_solid(mixed);path=out/'mixed-square-woven.step';cq.exporters.export(shape,str(path))
back=cq.importers.importStep(str(path)).val();b=exact_bounds(back)
assert back.isValid() and len(back.Solids())==1
assert abs(b[3]-b[0]-175)<.01 and abs(b[4]-b[1]-145)<.01
assert back.intersect(cq.Solid.makeCylinder(1,mixed['height']+2,cq.Vector(0,0,-1))).Volume()<1e-6
print('Mixed profile / texture / section STEP passes round-trip and envelope checks.',flush=True)
(out/'bulb-validation.json').write_text(json.dumps(results,indent=2))
