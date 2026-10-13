# Lampshade Studio

A standalone, local design tool inspired by your three lampshade references. It is separate from TacticalWatch.

Double-click **Start Lampshade Studio.cmd** or the **Lampshade Studio** desktop shortcut. The app opens at http://127.0.0.1:8766. After the initial setup, it works offline; the 3D viewer and CAD engine are local.

## Workflow

1. Set the final **width (X), depth (Y), and height (Z)** in millimetres. These are the complete outside bounding-box dimensions, including texture peaks. Uncheck the width/depth link to create an oval envelope. Sizing applies to generated shades only.
2. Browse the **11-form library**, then change the twist, texture, profile and cross-section. Selecting a style or resetting it preserves your envelope and export choice. Dimensions marked `mm*` describe the source profile before fitting; they control proportions, not final rim diameters.
3. Choose the export geometry:
   - **Hollow shade:** a closed, watertight CAD material body with annular rims and an open central passage at both ends. Add mounting and fitting interfaces in your CAD program. The wall setting is a radial offset, not a constant surface-normal thickness; corrugations and facets can have thinner normal walls. The final envelope correction can also slightly change the nominal radial thickness.
   - **Solid envelope:** the filled outside volume for a spiral-vase slicer. The preview illustrates the eventual open sleeve. The exported CAD body intentionally has solid caps.
4. Choose **STL**, **STEP**, **BREP**, or **NX · Parasolid** beside the export button. STL is a binary print mesh generated directly from the procedural shade; it avoids the expensive CAD-to-mesh conversion in a slicer. STEP and OpenCascade BREP preserve CAD surfaces: the actual exported file is re-imported and checked for one valid solid and outside dimensions within **0.01 mm**. Parasolid uses the local NX converter and is verified inside NX before downloading. CAD export can take longer for complex combinations.
5. **Save design** stores a small `.json` file containing the generator parameters. **Open design** restores it. Use this file to regenerate variants. There is no automatic saving.

STEP is an interoperable boundary-representation format. It does **not** include a native CAD feature tree or editable generator dimensions. You can add parametric sketches, cuts, bosses, and fitting features to the imported body in your CAD application; changing the original generator controls requires reopening the saved design here and exporting again. Downstream references may need repairing after replacement geometry is imported.

The model is centred on X/Y, with the bottom at Z=0 and the printing axis along Z. The three envelope dimensions are fit independently; this can intentionally change proportions. Smooth textures use spline surfaces; the Facet texture uses planar triangular CAD faces. The spline geometry interpolates the procedural shape, and the live display is a tessellated preview. Preview color and lighting are illustrative.

## Printing

For an open vase-mode sleeve, export **STL → Solid envelope**, enable spiral vase mode, use one perimeter, zero infill, zero top layers and zero bottom layers. Set extrusion width and layer height in the slicer and inspect the toolpath. A hollow body is primarily for CAD work; it is not the recommended vase-slicer input.

STL offers **Lite**, **Balanced** and **Fine** detail. Lite reduces triangles and file size, with more visible faceting; Balanced is the default; Fine follows small texture details more closely. Triangle count and download size appear after export. These are sampling-density choices, not certified surface-deviation tolerances. Triangular-facet designs retain their deliberate faces at every quality. The STL is fit to the requested bounding box and checked for closed, consistently oriented seams, nondegenerate triangles and positive volume. Its coordinates are in **millimetres**; STL itself has no unit metadata, so import as mm.

The direct STL approximates the same procedural design as the spline CAD body. It is not a tessellation of that BREP, so minor differences between their surfaces can occur. Both retain the requested overall dimensions. The bulb guide is excluded from shade exports and remains a separate STEP reference.

**BREP** means the OpenCascade `.brep` format, useful in compatible CAD applications such as FreeCAD. It retains the same surfaces and solid topology as STEP, and is not a lightweight slicer mesh. Neither CAD format includes the generator's parameter history. Export format and STL quality are included in saved design files.

## Siemens NX / Parasolid

NX uses the [Parasolid geometry kernel and XT exchange format](https://www.siemens.com/en-us/products/plm-components/parasolid/data-access-translation/). The tool offers:

- **NX · Parasolid (.x_b):** compact binary CAD geometry, the recommended export for NX on this computer.
- **NX · Parasolid (.x_t):** text Parasolid with the same CAD body.

Both use the installed **NX 2412** translator in an independent background session, leaving any interactive NX session alone. The conversion imports the checked STEP into NX, preserves the existing NURBS surfaces, excludes curves/PMI/assembly overhead, and writes only the solid. NX general geometry optimization, B-surface smoothing and geometry simplification are disabled: the general optimizer can spend minutes refitting a dense woven surface, while direct Parasolid conversion avoids that work and retains the relief. The actual Parasolid file is then imported into a fresh NX part and checked for one solid, no face/edge consistency faults, dimensions and placement within 0.01 mm, and unchanged face/edge counts. Runtime checks deliberately use NX solid integrity and envelope checks; they do not compute full mass/inertia properties or certify a source-to-output surface deviation.

These are full CAD surfaces, not mesh triangles. Choose **Hollow shade** to add mounting and fitting features. Import the `.x_b` or `.x_t` with NX's Parasolid importer, then save your working model as `.prt`. Parasolid does not include the original generator's parameter history; save the design JSON for that.

The converter needs an installed, licensed NX with background journaling and the STEP translator available. It detects `UGII_BASE_DIR` or an installation under `Program Files/Siemens`; `LAMPSHADE_NX_DIR` can specify a different install root. The output targets that installation's current Parasolid version. Export choices are disabled if NX is absent, and license/startup failures produce an error rather than a mislabeled STEP file. A conversion timeout stops only its own batch process tree.

Run `.venv/Scripts/python.exe validate_nx.py` for actual NX conversion/read-back checks of a thin spiral, dense woven sleeve, and faceted shade. Reports are written to `exports/nx-validation.json`; the most recent app export is recorded in `exports/last-nx-validation.json`.

Some combinations of short height, deep texture or high twist have steep overhangs. The tool checks CAD validity and size, not printer-specific manufacturability. A successful export is not a validated print. Added mounting geometry can also change vase-mode compatibility. The finished design has not been physically printed or heat-tested. Use LED lighting and choose material, ventilation and clearances for your actual assembly.

## Validation performed

The files in `exports/` cover all eleven hollow presets, a 220 × 140 × 240 mm oval Wave, and the solid Spiral export. Each was re-imported using OpenCascade and checked for a single valid solid and envelope dimensions within 0.01 mm. Hollow examples were also checked for an open centre throughout their height. Results are in `exports/validation.json`.

The browser workflow was checked for dimension changes, width/depth linking, style changes preserving envelope dimensions, invalid-input export blocking, loading a saved design, and STEP export. STEP has not yet been imported into your particular CAD application.

`validate_formats.py` checks the actual binary STL files with an independent VTK reader: all eleven forms in both solid and hollow modes, plus Lite/Fine woven exports, an oval mixed design and the legacy socket recess. Checks include bounds, closed manifold edges, connected material and the expected one or two horizontal slice contours. Three BREP round trips cover woven, faceted and oval geometry. All **29 cases passed**; details are in `exports/format-validation.json`. These are file and geometry checks, not a timed import test in your slicer.

## Local installation and maintenance

- Python 3.12 and CadQuery 2.6.1; installed into the isolated `.venv` directory.
- Three.js 0.180.0 is bundled under `public/vendor/` with its MIT license.
- The service binds only to `127.0.0.1:8766` and serves only the public app directory. Nothing is hosted publicly.
- `Start-LampshadeStudio.ps1 -NoBrowser` starts or reuses the local service without opening a window.
- `Stop-LampshadeStudio.ps1` stops the app's recorded service process.
- Logs are `server.log` and `server-error.log`.
- To rerun the CAD integration checks: `.venv/Scripts/python.exe validate_exports.py`.
- Moving to a different computer: install Python 3.12, copy this folder without `.venv`, then run the launcher to install `requirements.txt`. Internet is needed for that initial installation.

## References

- [Spiral Lamp E27 by Felix3DPrint](https://makerworld.com/en/models/2005410-spiral-lamp-e27): fine spiral-rib visual reference. Its supplied print description uses supports; it is not a vase-mode model.
- [Lampshade by Makustom](https://makerworld.com/en/models/873685-lampshade): broad twisted waves with fine ribs and a vase-mode shade.
- [Lampshade – Triangle displaced by JANBERRY DESIGN](https://makerworld.com/en/models/1532766-lampshade-triangle-displaced): triangular relief and vase-mode reference.
- [Prusa: layers, perimeters and spiral vase mode](https://help.prusa3d.com/article/layers-and-perimeters_1748): solid input geometry and slicer settings.
- [CadQuery documentation](https://cadquery.readthedocs.io/en/stable/): CAD construction and STEP import/export.

These are newly generated procedural designs inspired by the references. No source mesh from those models is included.

## Creative library and mixing controls

The library now contains **11 starting forms**: Spiral, Wave, Facet, Silk folds, Lantern, Orbit, Woven capsule, Twisted square, Bloom, Dune and Hourglass. The library previews are rendered from the actual procedural geometry. Keep **Keep my current bounding box** enabled to preserve your size when choosing a form; turn it off to adopt that form's suggested dimensions.

Mix a continuous, capsule, stacked or orbiting silhouette with a round or soft-square cross-section. Choose ribs, woven relief, smooth walls or triangular facets independently. Flow controls change fold sway and broad waves. **Try a variation** adjusts the current family while retaining the envelope and bulb settings; **Undo** restores the parameters before the last preset or variation. Your source design is also preserved at `backups/before-creative-library/your-design.json`.

Woven effects are continuous embossed/debossed diamond relief, not holes, loose strands or a true woven structure. They preserve a connected horizontal contour for vase-mode exploration. The source photos' perforated appearance is not reproduced as perforations. Detailed textures can take about 15–40 seconds to export and produce larger STEP files. Very dense combined settings are rejected with a message to reduce detail.

## E27 bulb reference and clearance

The guide offers two dimensioned examples, not a universal E27 bulb shape:

- **Edison ST64:** 64 mm diameter × 140 mm overall height, based on [Philips Filament Bulb Clear 60W ST64 E27](https://www.lighting.philips.co.uk/consumer/p/led-filament-bulb-clear-60w-st64-e27/8719514323919).
- **A60:** 60 mm diameter × 106 mm overall height, based on the A60 E27 model in the [Philips Premium Vintage Filament leaflet](https://www.assets.lighting.philips.com/is/content/PhilipsLighting/comf6981535-pss-global).

E27 specifies the screw fitting, not the bulb's glass diameter or total height. Edit both dimensions for your actual bulb. The 27 mm cap diameter is nominal; its 26 mm length and the intermediate glass outline are schematic. The guide is not an exact thread, socket, electrical part or manufacturer CAD model.

**Bulb bottom Z** locates the lowest point of the whole bulb relative to the shade's bottom at Z=0. Orientation can be upright or pendant. Click **Bulb** in the viewport to show/hide it; **X-ray shade** makes the shade transparent. Bulb settings are retained when switching forms and are stored in saved designs. Version 1 design files remain supported.

The fit report compares the bulb with the inner surface of the generated shade (or an estimated 0.6 mm printed wall for the solid vase envelope). It reports:

- An approximate **horizontal radial gap** to the illustrative bulb profile.
- A more conservative gap to a full-height cylinder with the bulb's maximum diameter. A green result means this full-width envelope meets your chosen radial gap throughout the overlapping height.
- Top and bottom opening gaps to that same bulb diameter. These are opening checks, not simulations of an insertion path or socket assembly.
- Any height extending above or below the shade. No overlapping height is reported separately.

Clearance uses the preview's sampled inner contours and interpolation in Z. It is an estimate, not an exact minimum 3D surface distance or thermal safety certification. Confirm the actual bulb, socket, material and temperature requirements. The nominal default 5 mm target is an adjustable geometric margin, not a recommended heat clearance.

**Export bulb reference STEP** downloads the same dimensioned, positioned proxy separately for CAD. The shade STEP always contains only the shade, so its specified bounding box is not affected.

The added validation includes all 11 preset hollow STEP bodies, the previous oval and solid cases, a mixed square/capsule/woven design, four bulb STEP orientation cases, known positive/negative radial-clearance cases, a tight oval, excessive target gap and a bulb outside the shade's height. See `exports/validation.json`, `exports/bulb-validation.json`, and `validate_bulbs.py`.



## Grow-light chandelier (5 October 2026)

Open `chandelier.html` or choose **Grow-light chandelier** in the shade editor. Hosted at https://projects.mungoon.net/lampshade/chandelier.html. It supports 3–32 Barrina T5 lights. The user's B099PLYWCM listing supplies the default 305 × 20 × 20 mm envelope (1 ft, yellow, white cover). T5 bodies are editable rectangular references, not manufacturer CAD. Physical lights are never scaled to fit a print bed.

The default Sunburst follows the user's Drawing.pdf: blue T5 spokes are joined by red curved bridges with integral retaining clips, repeated once per gap, with yellow paracord meeting at a printed junction and a single upper cord. The centre hub is off by default and remains optional. Optional flat, curved webs bolt between shared collars farther along each light. Choose petal or single arc, a central hub hanger or hanging from the web eyelets, and **Keep the centre hub** on/off. The integral clip bridge is one shared part definition. In the alternative bolted construction, one master web panel, root collar and web collar are reused around the assembly. Printed carrier arms remain an alternative. Halo, parallel, descending spiral and vertical lantern are suspension studies that need a rigid spreader to resist inward pull.

Paracord guides meet at a ceiling point. Webbing can instead be represented by individual flat printed straps with end holes; end connections/routing need refinement in CAD. Printed supports are concept geometry and have no verified load rating. Supplied metal retaining clips and selected fasteners are needed: an open-front printed collar alone cannot retain a suspended light. Clip dimensions, clearances, edge radii, housing bending/roll resistance, flexible material and joints require physical checks before suspension. Ceiling and paracord guides are excluded from CAD.

**Assembly navigator / BOM:** expandable light units contain their T5 reference and collars (and carrier arm, when enabled), with hub, web and suspension groups. Selecting an occurrence highlights that component; selecting a BOM row highlights every copy. Quantities come from the same occurrence inventory used for CAD. Geometry-based part numbers stay stable through JSON round trips and distinguish changed dimensions. CSV gives part number, description, category, quantity, unit, CAD inclusion and notes. It includes required clips, fixing sets, cord spans, ceiling connection and wiring separately, with unmeasured sizes/lengths marked as needing confirmation. Cord lengths are straight geometric spans, not cutting lengths with knot allowances. Structure JSON includes the tree, occurrences and BOM; normal design JSON retains settings.

**Exports:** STEP retains nested groups and repeated part references. BREP and STL contain the selected solids. Full assembly, printed parts, all collars and individual hub/arm/collar/web/strap exports are available. The web exports flat. Single-part STL exports are centred and bed-aligned; individual dimensions are checked against the default **230 × 230 × 230 mm** volume. Oversized single-part STL exports are rejected; STEP remains available for dividing parts in CAD. Allow additional room for a brim. Printed supports require ordinary solid printing, not vase mode.

All chandelier faces use planes and cylinders, including the curved webs. STEP/BREP are reimported to check solid validity/count and placements. Repeated shapes share geometry in STEP instead of duplicating complex faces. Windows supports genuine Parasolid `.x_b` and `.x_t` through installed NX 2412, importing both the source STEP and the resulting Parasolid and checking every body's bounds and topology. Parasolid contains named solid bodies; use STEP for the assembly hierarchy. The Linux NAS supports STEP, BREP and STL, and honestly disables NX formats; it remains independent of this PC.

NAS chandelier settings share the Lampshade document in its `chandelier` field. Both editors preserve unrelated fields and use conditional saves to reject stale writes. Code publication does not change saved designs. The original shade/NX pathway is preserved.

Validation: `test_chandelier.py` checks transformations, legacy layouts, CAD joint holes, both hub options, default inter-part intersections, component/BOM/tree quantities, common STEP geometry, flat closed STLs, print-volume rejection and part-number stability. `test_chandelier_store.mjs` checks independent saves, field preservation, weak ETags and stale-write rejection. Default hub and open-centre STEP and Parasolid examples, CSV BOMs and structure JSON are in `exports/chandelier-t5-webs-*`.


### Drawing-based integral clip bridges (5 October 2026)

The drawing's red connector is one continuous curved ribbon with two integral clips. Identical instances are patterned around the T5s. The two clips are staggered by clip length + 4 mm along a shared light so neighbours do not overlap; each has an adjustable retaining lip beneath the housing edges. The central band has a real cord hole (or webbing slot). A separate optional printed cord junction has one hole per branch plus a central hole for a single upper hanger. It is a CAD component and a BOM row, unlike the remaining ceiling guide.

The default 3-light arrangement uses 3 copies of one bridge, 1 printed junction and 3 T5 reference components. The bridge fits a 95.5 × 219.4 × 26.6 mm envelope; the junction is 36.8 × 36.8 × 4 mm. Single bridge STL is oriented broad face on the bed, clip openings up. This is prototype snap-clip geometry; the actual housing, print/material flex, retention and sustained load have not been tested. No separate collar/clip bolt sets are added to the BOM for integral bridge clips; those remain required for the older root/separate collars when enabled.

The separate light-position table and positions CSV were removed. BOM CSV retains only part/quantity/category/unit/CAD-inclusion/notes fields. `Use your drawing layout` switches existing designs to the new construction; older JSON/NAS settings retain their bolted construction through migration. Red printed and blue T5 component colours are also written to STEP.

Validation adds integral-clip topology, real hanger holes and retaining lips, no solid overlap in hub/open-centre patterns, BOM/STEP instance matching, shared geometry, and flat closed STL exports. Additional 4, 6, 8 and 12 light layouts were checked for inter-part intersections. Examples: `exports/chandelier-drawing-3.step`, `.x_b`, `-bom.csv`; `chandelier-clip-bridge.stl` and `chandelier-cord-junction.stl`.
