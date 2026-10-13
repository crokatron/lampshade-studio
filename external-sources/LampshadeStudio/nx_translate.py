"""Run only via Siemens NX run_journal, in an isolated batch session."""
import json
import math
import os
import sys
import time
import traceback
import NXOpen
import NXOpen.UF


def inspect_part(part,uf,target):
    bodies=list(part.Bodies)
    if len(bodies)!=1 or not bodies[0].IsSolidBody:
        raise ValueError(f'NX must contain exactly one solid body (found {len(bodies)} bodies).')
    body=bodies[0]
    print('Checking body consistency',flush=True)
    faults,tokens,tags=uf.Modeling.AskBodyConsistency(body.Tag)
    if faults:raise ValueError('NX found inconsistent faces or edges in the converted body.')
    print('Checking dimensions',flush=True)
    corner,directions,dimensions=uf.ModlGeneral.AskBoundingBoxExact(body.Tag,0)
    if any(not math.isfinite(a) or abs(a-b)>.01 for a,b in zip(dimensions,target)):
        raise ValueError('The NX body did not preserve the requested envelope within 0.01 mm.')
    expected=(-target[0]/2,-target[1]/2,0)
    if any(abs(a-b)>.01 for a,b in zip(corner,expected)):
        raise ValueError('The NX body did not preserve its position.')
    return body,dict(bodyCount=1,solid=True,consistencyFaults=faults,dimensions=dimensions,
                     minimumCorner=corner,faceCount=len(body.GetFaces()),edgeCount=len(body.GetEdges()))


def inspect_components(part,uf,expected):
    bodies=list(part.Bodies)
    if len(bodies)!=len(expected) or not all(b.IsSolidBody for b in bodies):
        raise ValueError('NX did not preserve every chandelier component as a solid body.')
    remaining=list(expected);details=[]
    for body in bodies:
        faults,_,_=uf.Modeling.AskBodyConsistency(body.Tag)
        if faults:raise ValueError('NX found inconsistent component geometry.')
        corner,_,dimensions=uf.ModlGeneral.AskBoundingBoxExact(body.Tag,0)
        bounds=list(corner)+[a+b for a,b in zip(corner,dimensions)]
        match=next((i for i,item in enumerate(remaining) if max(abs(a-b) for a,b in zip(bounds,item['bounds']))<.01),None)
        if match is None:raise ValueError('NX changed a component position or dimensions.')
        item=remaining.pop(match);body.SetName(item['name'])
        details.append(dict(name=item['name'],dimensions=dimensions,minimumCorner=corner,faceCount=len(body.GetFaces()),edgeCount=len(body.GetEdges()),consistencyFaults=faults))
    details.sort(key=lambda d:d['name'])
    return bodies,dict(bodyCount=len(bodies),solid=True,consistencyFaults=0,bodies=details,
                       faceCount=sum(d['faceCount'] for d in details),edgeCount=sum(d['edgeCount'] for d in details))


def main():
    config=json.load(open(sys.argv[1]))
    report={"ok":False}
    try:
        session=NXOpen.Session.GetSession()
        uf=NXOpen.UF.UFSession.GetUFSession()
        part=session.Parts.NewDisplay('lampshade_conversion',NXOpen.Part.Units.Millimeters)
        start=time.time()
        imp=session.DexManager.CreateStep242Importer()
        imp.InputFile=config['input']
        imp.OutputFile=os.path.splitext(config['output'])[0]+'.prt'
        imp.SettingsFile=os.path.join(os.environ['UGII_BASE_DIR'],'TRANSLATORS','step242','step242ug.def')
        imp.ImportTo=NXOpen.Step242Importer.ImportToOption.WorkPart
        imp.FlattenAssembly=True
        imp.ObjectTypes.Solids=True
        imp.ObjectTypes.Surfaces=False
        imp.ObjectTypes.Curves=False
        imp.ObjectTypes.PmiData=False
        # NX's general optimizer can spend minutes refitting dense relief surfaces.
        # Preserve their existing NURBS and translate directly into Parasolid instead.
        imp.Optimize=False
        imp.SimplifyGeometry=False
        imp.SmoothBSurfaces=False
        imp.ProcessHoldFlag=True
        print('Importing STEP into NX',flush=True)
        imp.Commit(); imp.Destroy()
        report['stepImportSeconds']=round(time.time()-start,4)
        if 'components' in config:
            bodies,report['beforeExport']=inspect_components(part,uf,config['components'])
        else:
            body,report['beforeExport']=inspect_part(part,uf,config['target'])
            body.SetName('Lampshade');bodies=[body]
        out=session.DexManager.CreateParasolidExporter()
        out.OutputFile=config['output']
        out.ExportFrom=NXOpen.ParasolidExporter.ExportFromOption.DisplayedPart
        out.ExportSelectionBlock.SelectionScope=NXOpen.ObjectSelector.Scope.SelectedObjects
        for body in bodies:out.ExportSelectionBlock.SelectionComp.Add(body)
        out.FlattenAssembly=True
        out.ObjectTypes.Solids=True
        out.ObjectTypes.Surfaces=False
        out.ObjectTypes.Curves=False
        out.ParasolidVersion=NXOpen.ParasolidExporter.ParasolidVersionOption.Current
        out.ProcessHoldFlag=True
        print('Writing Parasolid',flush=True)
        out.Commit();out.Destroy()
        report['bytes']=os.path.getsize(config['output'])
        second=session.Parts.NewDisplay('lampshade_readback',NXOpen.Part.Units.Millimeters)
        session.Parts.SetWork(second)
        back=session.DexManager.CreateParasolidImporter()
        back.InputFile=config['output'];back.FlattenAssembly=True;back.ProcessHoldFlag=True
        back.ObjectTypes.Solids=True;back.ObjectTypes.Surfaces=False;back.ObjectTypes.Curves=False
        print('Reading Parasolid back into NX',flush=True)
        start=time.time();back.Commit();back.Destroy()
        report['parasolidImportSeconds']=round(time.time()-start,4)
        if 'components' in config:
            returned,report['afterImport']=inspect_components(second,uf,config['components'])
            for before,after in zip(report['beforeExport']['bodies'],report['afterImport']['bodies']):
                if any(before[k]!=after[k] for k in ('name','faceCount','edgeCount')):raise ValueError('A component changed during Parasolid round-trip.')
        else:returned,report['afterImport']=inspect_part(second,uf,config['target'])
        if any(report['afterImport'][key]!=report['beforeExport'][key] for key in ('faceCount','edgeCount')):
            raise ValueError('Parasolid round-trip topology verification failed.')
        report['ok']=True
    except Exception as e:
        report['error']=str(e)
        report['traceback']=traceback.format_exc()
    with open(config['report'],'w') as f:json.dump(report,f,indent=2)


if __name__=='__main__':main()
