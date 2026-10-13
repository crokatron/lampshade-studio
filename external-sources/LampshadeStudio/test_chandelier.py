import json, math, tempfile, unittest
from pathlib import Path
import cadquery as cq
import chandelier as ch
from geometry import exact_bounds
from chandelier_assembly import inventory, build, bom_csv
LEGACY={**ch.DEFAULT,"hubRadius":110.,"webReach":30.,"webThickness":2.4,"keepHub":True,"webConstruction":"bolted","cordCollector":False}
SLINGS={**LEGACY,"support":"slings","webEnabled":False,"hangerFrom":"hub"}
CARRIERS={**LEGACY,"spokeType":"printed","hubRadius":60.,"radius":210.,"webEnabled":False,"hangerFrom":"hub"}


class ChandelierTests(unittest.TestCase):
    def test_integral_clip_pattern_matches_bom_and_step(self):
        for keep,expected in [(False,7),(True,14)]:
            model=ch.preview({**ch.DEFAULT,'keepHub':keep})
            catalog=inventory(model);_,bodies,names=build(model)
            self.assertTrue(all(c['fits'] for c in model['printChecks']))
            self.assertEqual(catalog['summary']['modeledComponents'],expected)
            self.assertEqual(len(model['web']['collars']),0)
            self.assertEqual(len(model['anchors']),4)
            self.assertEqual(len([r for r in catalog['bom'] if r['kind']=='web']),1)
            self.assertEqual(next(r['quantity'] for r in catalog['bom'] if r['kind']=='web'),3)
            self.assertNotIn('HW-WEB-FIX',[r['partNumber'] for r in catalog['bom']])
            if not keep:self.assertNotIn('HW-T5-CLIP',[r['partNumber'] for r in catalog['bom']])
            for i,body in enumerate(bodies):
                self.assertTrue(body.isValid());self.assertEqual(len(body.Solids()),1)
                self.assertLessEqual({face.geomType() for face in body.Faces()},{'PLANE','CYLINDER'})
                for other in bodies[:i]:self.assertLess(body.intersect(other).Volume(),.001)
            with tempfile.TemporaryDirectory() as folder:
                data,_=ch.export(model['parameters'],'step',folder)
                self.assertEqual(len(cq.importers.importStep(str(Path(folder)/'chandelier.step')).val().Solids()),expected)
                self.assertEqual(data.count(b'MANIFOLD_SOLID_BREP('),5 if keep else 3)
                self.assertIn(b'Repeated_clip_bridges',data)
                self.assertIn(b'JUNCTION-',data)
            self.assertNotIn('centre_x',bom_csv(model).decode('utf-8-sig'))

    def test_integral_clip_holes_retention_and_bed_orientation(self):
        from chandelier_bridge import make_bridge,make_collector
        import vtk
        model=ch.layout(ch.DEFAULT);p=model['parameters'];spec=model['web'];part=make_bridge(p,spec)
        eye=spec['eye'];self.assertFalse(part.isInside(cq.Vector(eye['x'],eye['y'],spec['top']-p['webThickness']/2)))
        # Lip at the opening projects beneath the housing but does not enter it.
        clip=spec['clips'][0];a=math.radians(clip['angle'])
        x=clip['radius'];y=p['width']/2-p['bridgeLip']/2
        self.assertTrue(part.isInside(cq.Vector(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),-.8)))
        self.assertFalse(make_collector(p).isInside(cq.Vector(0,0,2)))
        with tempfile.TemporaryDirectory() as folder:
            for scope in ['web','collector']:
                ch.export({**p,'scope':scope},'stl',folder)
                reader=vtk.vtkSTLReader();reader.SetFileName(str(Path(folder)/'chandelier.stl'));reader.Update()
                self.assertAlmostEqual(reader.GetOutput().GetBounds()[4],0,places=5)
                edges=vtk.vtkFeatureEdges();edges.SetInputData(reader.GetOutput());edges.BoundaryEdgesOn();edges.NonManifoldEdgesOn();edges.FeatureEdgesOff();edges.ManifoldEdgesOff();edges.Update()
                self.assertEqual(edges.GetOutput().GetNumberOfCells(),0)
            with self.assertRaisesRegex(ValueError,'print volume'):ch.export({**p,'scope':'web','printSize':150},'stl',folder)
        six=ch.preview({**p,'count':6,'hubRadius':110})
        self.assertEqual(inventory(six)['summary']['modeledComponents'],13)

    def test_part_numbers_survive_json_number_roundtrip(self):
        original=inventory(ch.layout(LEGACY))['parts']
        browser={k:int(v) if isinstance(v,float) and v.is_integer() else v for k,v in LEGACY.items()}
        self.assertEqual(set(original),set(inventory(ch.layout(browser))['parts']))

    def test_web_assembly_bom_quantities_and_shared_step_geometry(self):
        import csv,io
        for keep,expected,unique in [(True,16,5),(False,9,3)]:
            p={**LEGACY,'keepHub':keep};m=ch.preview(p);catalog=inventory(m)
            self.assertEqual(catalog['summary']['modeledComponents'],expected)
            self.assertEqual(catalog['summary']['uniqueParts'],unique)
            self.assertTrue(all(r['fits'] for r in m['printChecks']))
            self.assertEqual(len(m['anchors']),3)
            quantities={r['kind']:r['quantity'] for r in catalog['bom'] if r['modeled']}
            self.assertEqual(quantities['light'],3);self.assertEqual(quantities['web'],3);self.assertEqual(quantities['web-collar'],3)
            self.assertEqual(quantities.get('collar',0),6 if keep else 0)
            self.assertEqual(sum(c['quantity'] for g in catalog['tree']['children'] for c in g['children'] if c['modeled']),expected)
            rows=list(csv.DictReader(io.StringIO(bom_csv(m).decode('utf-8-sig'))))
            self.assertEqual(sum(int(r['Quantity']) for r in rows if r['Included in CAD']=='Yes'),expected)
            _,bodies,names=build(m)
            self.assertEqual(len(bodies),expected)
            for i,body in enumerate(bodies):
                self.assertTrue(body.isValid())
                self.assertLessEqual({f.geomType() for f in body.Faces()},{'PLANE','CYLINDER'})
                for other in bodies[:i]:self.assertLess(body.intersect(other).Volume(),.001)
            with tempfile.TemporaryDirectory() as folder:
                data,_=ch.export(p,'step',folder)
                self.assertEqual(data.count(b'MANIFOLD_SOLID_BREP('),unique)
                self.assertEqual(len(cq.importers.importStep(str(Path(folder)/'chandelier.step')).val().Solids()),expected)
                self.assertIn(b'Inter_spoke_webs',data)

    def test_web_holes_flat_export_and_print_volume_limit(self):
        from chandelier_web import make_panel
        m=ch.layout(LEGACY);w=m['web'];p=m['parameters'];panel=make_panel(p,w)
        for x,y in [(w['a'],w['b']),(w['a'],-w['b']),(w['eye']['x'],0)]:
            self.assertFalse(panel.isInside(cq.Vector(x,y,p['webThickness']/2)))
        with tempfile.TemporaryDirectory() as folder:
            for scope in ['web','web-collar','hub','single']:
                ch.export({**p,'scope':scope},'stl',folder)
                import vtk
                reader=vtk.vtkSTLReader();reader.SetFileName(str(Path(folder)/'chandelier.stl'));reader.Update()
                edges=vtk.vtkFeatureEdges();edges.SetInputData(reader.GetOutput());edges.BoundaryEdgesOn();edges.NonManifoldEdgesOn();edges.FeatureEdgesOff();edges.ManifoldEdgesOff();edges.Update()
                self.assertEqual(edges.GetOutput().GetNumberOfCells(),0)
                self.assertAlmostEqual(reader.GetOutput().GetBounds()[4],0,places=5)
            oversized={**p,'scope':'web','webReach':100}
            with self.assertRaisesRegex(ValueError,'print volume'):ch.export(oversized,'stl',folder)
            ch.export(oversized,'step',folder)
        direct=ch.layout({**p,'webEnabled':False,'hangerFrom':'hub'})
        self.assertEqual(len(direct['anchors']),1)
        self.assertEqual(direct['hub']['fixingRadii'],[58,97])
        self.assertIsNone(ch.hub_parts(direct)[1])

    def test_printed_hub_assembly_and_matching_joints(self):
        m=ch.layout(CARRIERS)
        self.assertEqual(len(m['anchors']),1)
        self.assertEqual(m['anchors'][0]['bottom'][:2],[0,0])
        self.assertEqual(m['anchors'][0]['top'][:2],[0,0])
        hub,arm=ch.hub_parts(m);p=m['parameters'];h=m['hub']
        self.assertTrue(hub.isValid());self.assertTrue(arm.isValid())
        for radius in h['fixingRadii']:
            self.assertFalse(hub.isInside(cq.Vector(radius,0,p['hubThickness']/2)))
            self.assertFalse(arm.isInside(cq.Vector(radius,0,p['armThickness']/2)))
        for radius in (p['radius']-p['length']*.32,p['radius']+p['length']*.32):
            self.assertFalse(arm.isInside(cq.Vector(radius,0,p['armThickness']/2)))
        with tempfile.TemporaryDirectory() as d:
            for material,expected in [('paracord',13),('webbing',14)]:
                data,_=ch.export({**CARRIERS,'hanging':material},'step',d)
                shape=cq.importers.importStep(str(Path(d)/'chandelier.step')).val()
                self.assertEqual(len(shape.Solids()),expected)
                self.assertLessEqual({f.geomType() for f in shape.Faces()},{'PLANE','CYLINDER'})
                self.assertIn(b'Centre_hub',data);self.assertIn(b'ARM-',data)
            for scope in ('hub','arm'):
                ch.export({**CARRIERS,'scope':scope},'brep',d)
                self.assertEqual(len(cq.Shape.importBrep(str(Path(d)/'chandelier.brep')).Solids()),1)
        for changes in ({'tiers':2,'count':6},{'tilt':20},{'count':32},{'radius':120}):
            with self.assertRaises(ValueError):ch.layout({**CARRIERS,**changes})

    def test_layout_counts_dimensions_and_orientation(self):
        for style in ch.LAYOUTS:
            for count in (3,7,24,32):
                p={**SLINGS,'layout':style,'count':count,'radius':1600,'spacing':100,'tilt':25}
                m=ch.layout(p)
                self.assertEqual(len(m['bars']),count)
                self.assertEqual(len(m['mounts']),2*count)
                self.assertEqual(len(m['anchors']),4*count)
                self.assertAlmostEqual(m['bounds']['min'][2],0)
                for bar in m['bars']:
                    u,v,w=bar['axes']
                    self.assertAlmostEqual(ch.dot(u,u),1)
                    self.assertAlmostEqual(ch.dot(u,v),0)
                    self.assertAlmostEqual(ch.dot(ch.cross(u,v),w),1)
                    corners=ch.corners(bar,m['size'])
                    self.assertAlmostEqual(math.dist(corners[0],corners[4]),305)

    def test_layers_keep_all_bars(self):
        m=ch.layout({**SLINGS,'count':10,'tiers':3,'tierGap':70})
        self.assertEqual([sum(b['tier']==i for b in m['bars']) for i in (1,2,3)],[4,3,3])
        self.assertEqual([b['id'] for b in m['bars']],list(range(1,11)))

    def test_validation_and_collisions(self):
        for changes in ({'count':2},{'count':3.2},{'count':True},{'radius':float('nan')},{'layout':'bad'},
                        {'count':3,'tiers':2},{'hanging':'chain'},{'printedWebbing':'yes'},
                        {'hanging':'webbing','webbingWidth':40,'saddleLength':26}):
            with self.assertRaises(ValueError):ch.layout({**SLINGS,**changes})
        self.assertTrue(ch.layout({**SLINGS,'layout':'parallel','spacing':10})['clashes'])
        m=ch.layout({**SLINGS,'layout':'parallel','spacing':40})
        self.assertFalse(m['clashes']);self.assertTrue(m['mountClashes'])
        self.assertFalse(ch.layout(LEGACY)['mountClashes'])

    def test_step_assembly_names_and_solid_counts(self):
        with tempfile.TemporaryDirectory() as d:
            for material,printed,count in [('paracord',True,9),('webbing',False,9),('webbing',True,21)]:
                p={**SLINGS,'hanging':material,'printedWebbing':printed}
                data,m=ch.export(p,'step',d)
                shape=cq.importers.importStep(str(Path(d)/'chandelier.step')).val()
                self.assertTrue(shape.isValid());self.assertEqual(len(shape.Solids()),count)
                self.assertLessEqual({face.geomType() for face in shape.Faces()},{'PLANE','CYLINDER'})
                self.assertIn(b'Light_unit_01',data)
                self.assertIn(b'CLIP-',data)
                if material=='webbing' and printed:self.assertIn(b'STRAP-',data)
                expected=[p['length'],p['width'],p['height']]
                bars=[s for s in shape.Solids() if abs(s.Volume()-math.prod(expected))<.001]
                self.assertEqual(len(bars),3)

    def test_brep_single_saddle_holes_and_strap(self):
        with tempfile.TemporaryDirectory() as d:
            for material in ('paracord','webbing'):
                p={**SLINGS,'hanging':material,'scope':'single'}
                data,m=ch.export(p,'brep',d);s=cq.Shape.importBrep(str(Path(d)/'chandelier.brep'))
                self.assertEqual(len(s.Solids()),1);self.assertTrue(s.isValid())
                # Centre clip fixing remains a real through-hole.
                z=p['height']/2+p['clearance']+p['saddleWall']/2
                self.assertFalse(s.isInside(cq.Vector(0,0,z)))
                self.assertFalse(s.isInside(cq.Vector(0,m['saddle']['earY'],z)))
                self.assertTrue(s.isInside(cq.Vector(p['saddleLength']/2-1,0,z)))
            p={**SLINGS,'hanging':'webbing','scope':'strap'}
            data,m=ch.export(p,'step',d);s=cq.importers.importStep(str(Path(d)/'chandelier.step')).val()
            span=max(a['length'] for a in m['anchors']);bb=exact_bounds(s)
            self.assertAlmostEqual(bb[4]-bb[1],span+2*p['strapEnd'],places=4)
            self.assertAlmostEqual(bb[3]-bb[0],p['webbingWidth'],places=4)
            self.assertFalse(s.isInside(cq.Vector(0,span/2,0)))

    def test_single_stl_is_closed(self):
        import vtk
        with tempfile.TemporaryDirectory() as d:
            ch.export({**SLINGS,'scope':'single'},'stl',d)
            reader=vtk.vtkSTLReader();reader.SetFileName(str(Path(d)/'chandelier.stl'));reader.Update()
            edges=vtk.vtkFeatureEdges();edges.SetInputData(reader.GetOutput());edges.BoundaryEdgesOn();edges.NonManifoldEdgesOn();edges.FeatureEdgesOff();edges.ManifoldEdgesOff();edges.Update()
            self.assertEqual(edges.GetOutput().GetNumberOfCells(),0)


if __name__=='__main__':unittest.main()
