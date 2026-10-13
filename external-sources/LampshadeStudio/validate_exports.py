"""Integration checks against re-imported STEP geometry, not just file headers."""
from pathlib import Path
import json, time
import cadquery as cq
from geometry import PRESETS, validate, make_solid, exact_bounds

out=Path(__file__).parent/'exports'
out.mkdir(exist_ok=True)
cases={name:{**p,'exportMode':'hollow'} for name,p in PRESETS.items()}
cases['oval-wave']={**PRESETS['wave'],'boxWidth':220,'boxDepth':140,'height':240,'exportMode':'hollow'}
cases['vase-spiral']={**PRESETS['spiral'],'exportMode':'solid'}
results=[]
for name,raw in cases.items():
    started=time.time();p=validate(raw)
    shape=make_solid(p)
    path=out/f'{name}.step'
    cq.exporters.export(shape,str(path))
    imported=cq.importers.importStep(str(path)).val()
    assert imported.isValid() and len(imported.Solids())==1,name
    x0,y0,z0,x1,y1,z1=exact_bounds(imported)
    dims=[x1-x0,y1-y0,z1-z0]
    target=[p['boxWidth'],p['boxDepth'],p['height']]
    assert max(abs(a-b) for a,b in zip(dims,target))<0.01,(name,dims)
    if p['exportMode']=='hollow':
        # Both ends and the entire centre axis must be open.
        probe=cq.Solid.makeCylinder(1,p['height']+2,cq.Vector(0,0,-1))
        assert imported.intersect(probe).Volume()<1e-6,name
        assert imported.Volume()<p['boxWidth']*p['boxDepth']*p['height']*.12,name
    else:
        assert imported.isInside((0,0,p['height']/2)),name
    result=dict(name=name,valid=True,solids=len(imported.Solids()),faces=len(imported.Faces()),
                dimensions=dims,volume=imported.Volume(),bytes=path.stat().st_size,seconds=round(time.time()-started,2))
    results.append(result);print(json.dumps(result),flush=True)
    (out/f'{name}.json').write_text(json.dumps(dict(app='lampshade-studio',version=1,parameters=p),indent=2))

for bad in ({'boxWidth':0},{'boxWidth':float('nan')},{'ribs':12.5},{'wall':-1},{'style':'unknown'}):
    try:validate(bad)
    except ValueError:pass
    else:raise AssertionError(f'Invalid input accepted: {bad}')
(out/'validation.json').write_text(json.dumps(results,indent=2))
print('All STEP round-trip, size, open-centre and input validation checks passed.',flush=True)
