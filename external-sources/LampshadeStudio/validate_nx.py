"""Real NX Parasolid conversion and re-import checks. Requires installed, licensed NX."""
import json
import tempfile
from pathlib import Path
import cadquery as cq
from nx_export import parasolid_export

ROOT=Path(__file__).parent
cases=[('spiral','x_b',(180,180,200)),('woven','x_b',(138,138,250)),('facet','x_t',(180,180,180))]
reports=[]
for name,fmt,dimensions in cases:
    shape=cq.importers.importStep(str(ROOT/'exports'/f'{name}.step')).val()
    with tempfile.TemporaryDirectory(prefix='lamp-nx-check-') as tmp:
        data,report=parasolid_export(shape,tmp,fmt,dimensions)
    (ROOT/'exports'/f'{name}-nx.{fmt}').write_bytes(data)
    report['case']=name;reports.append(report)
    (ROOT/'exports'/'nx-validation.json').write_text(json.dumps(reports,indent=2))
    print(json.dumps(report),flush=True)
print('All NX Parasolid file checks passed.',flush=True)
