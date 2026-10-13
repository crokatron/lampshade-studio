"""Read exported meshes with VTK and CAD files with OpenCascade."""
import json
import struct
import tempfile
import time
from pathlib import Path
import vtk
import cadquery as cq
from geometry import PRESETS, validate, make_solid, exact_bounds
from exports import stl_export, cad_export, export_options


def inspect_stl(path,p,count):
    data=path.read_bytes()
    assert struct.unpack('<I',data[80:84])[0]==count
    assert len(data)==84+50*count
    reader=vtk.vtkSTLReader(); reader.SetFileName(str(path)); reader.MergingOn(); reader.Update()
    poly=reader.GetOutput()
    assert poly.GetNumberOfPolys()==count
    bounds=poly.GetBounds()
    assert max(abs(a-b) for a,b in zip(bounds,(-p['boxWidth']/2,p['boxWidth']/2,-p['boxDepth']/2,p['boxDepth']/2,0,p['height'])))<.01
    edges=vtk.vtkFeatureEdges(); edges.SetInputData(poly)
    edges.BoundaryEdgesOn(); edges.NonManifoldEdgesOn(); edges.FeatureEdgesOff(); edges.ManifoldEdgesOff(); edges.Update()
    assert edges.GetOutput().GetNumberOfCells()==0,'Open or nonmanifold STL'
    regions=vtk.vtkPolyDataConnectivityFilter(); regions.SetInputData(poly); regions.SetExtractionModeToAllRegions(); regions.Update()
    assert regions.GetNumberOfExtractedRegions()==1,'Disconnected material'
    mass=vtk.vtkMassProperties(); mass.SetInputData(poly); mass.Update()
    assert mass.GetVolume()>0
    # A horizontal slicer section must have one contour for vase mode, two for a sleeve.
    plane=vtk.vtkPlane(); plane.SetOrigin(0,0,p['height']*.487); plane.SetNormal(0,0,1)
    cutter=vtk.vtkCutter(); cutter.SetInputData(poly); cutter.SetCutFunction(plane); cutter.Update()
    sections=vtk.vtkPolyDataConnectivityFilter(); sections.SetInputConnection(cutter.GetOutputPort()); sections.SetExtractionModeToAllRegions(); sections.Update()
    expected=2 if p['exportMode']=='hollow' else 1
    assert sections.GetNumberOfExtractedRegions()==expected,'Unexpected slice contour count'
    return dict(triangles=count,megabytes=round(len(data)/1e6,3),sliceContours=expected,valid=True)


def run():
    results=[]
    with tempfile.TemporaryDirectory(prefix='lampshade-formats-') as folder:
        folder=Path(folder)
        cases=[(f'{style}-{mode}','balanced',dict(p,exportMode=mode)) for style,p in PRESETS.items() for mode in ('solid','hollow')]
        cases += [(f'woven-{quality}',quality,dict(PRESETS['woven'],exportMode='solid')) for quality in ('lite','fine')]
        cases += [('oval-sway','lite',dict(PRESETS['square'],boxWidth=220,boxDepth=130,sway=8,swayCycles=.5)),
                  ('socket-legacy','balanced',dict(PRESETS['spiral'],exportMode='solid',base='socket'))]
        for name,quality,raw in cases:
            p=validate(raw); started=time.perf_counter(); data,count=stl_export(p,quality)
            path=folder/'shade.stl'; path.write_bytes(data)
            report=inspect_stl(path,p,count)
            results.append(dict(case=name,format='stl',quality=quality,seconds=round(time.perf_counter()-started,2),**report))
            print(results[-1],flush=True)
        woven=[next(x for x in results if x['case']==name)['triangles'] for name in ('woven-lite','woven-solid','woven-fine')]
        assert woven[0]<woven[1]<woven[2]
        for name,raw in [('woven-hollow',PRESETS['woven']),('facet-solid',dict(PRESETS['facet'],exportMode='solid')),('oval-hollow',dict(PRESETS['spiral'],boxWidth=220,boxDepth=140))]:
            p=validate(raw); started=time.perf_counter(); solid=make_solid(p); path=folder/'shade.brep'
            data=cad_export(solid,path,'brep',(p['boxWidth'],p['boxDepth'],p['height']))
            back=cq.Shape.importBrep(str(path))
            assert len(back.Faces())==len(solid.Faces())
            assert abs(back.Volume()-solid.Volume())/solid.Volume()<1e-6
            results.append(dict(case=name,format='brep',megabytes=round(len(data)/1e6,3),seconds=round(time.perf_counter()-started,2),valid=True))
            print(results[-1],flush=True)
        assert export_options({})==('step','balanced')
        for raw in ({'exportFormat':'obj'},{'stlQuality':'extreme'},{'exportFormat':[]},{'stlQuality':{}}):
            try:export_options(raw)
            except ValueError:pass
            else:raise AssertionError('Invalid format accepted')
    (Path(__file__).parent/'exports'/'format-validation.json').write_text(json.dumps(results,indent=2))
    print(f'Passed {len(results)} exported-file cases.',flush=True)


if __name__=='__main__':run()
