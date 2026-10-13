# Lampshade Studio — visual user manual

[Project overview](../README.md) · [Offline interactive demo](../demo.html)

Start with the numbered picture guide. Each number identifies the exact highlighted control. Work through one step at a time; the longer reference is below it.

### Actual tool · controls at a glance

Actual application screenshot. Numbered boxes point to the controls described below. 

![Lampshade Studio — numbered controls](images/guide-1.jpg)

1. **Set final size.** The envelope includes texture peaks. Width and depth can be linked or separated.
2. **Choose a starting form.** Pick a form, then tune texture and twist while keeping the envelope.
3. **Choose the right output.** STL for slicing; STEP/BREP for CAD. Save design JSON separately.

### Try the working offline example

Screenshot of this project’s interactive demo. Side-by-side services are explicitly simulated.

![Lampshade Studio — numbered controls](images/guide-2.jpg)

1. **Change the envelope.** Move the width slider and compare the illustrated shade.
2. **Choose the purpose.** Compare a print-mesh preview with a hollow CAD concept.
3. **Inspect the example output.** The dummy engine reports inputs; it does not certify a solid.

## Detailed task reference

### Design a shade to a fixed size

1. Set Width, Depth and Height first; these describe the final outside dimensions including texture peaks. Unlink width/depth for an oval.
2. Browse forms and select a starting style. Changing the style preserves the envelope rather than silently changing the final size.
3. Adjust texture, twist and profile. Values marked mm* are source-profile proportions before fitting, not necessarily final rim diameters.
4. Orbit the model, compare Front and Top and inspect the box and bulb guides. A radial fit check is not a heat rating or a complete holder-fit check.

### Export for spiral-vase printing

1. Choose Solid envelope and STL. Select Lite, Balanced or Fine mesh detail according to the intended print and file size.
2. Import into the slicer as millimetres. For an open sleeve, use the intended spiral-vase setup and inspect zero top/bottom layers, perimeter and toolpath.
3. Inspect overhangs and the complete sliced preview. The preview shows a sleeve but the exported solid envelope intentionally has caps for the slicer to interpret.
4. Save the JSON separately so you can regenerate another size. STL does not contain the procedural design controls.

### Export a CAD body

1. Choose Hollow shade when you want a material body to add mounting details to in CAD. The wall control is radial, not uniform surface-normal thickness.
2. Export STEP or BREP and wait for the server’s geometry checks. Complex surface combinations may take longer than STL.
3. Import the result into CAD, inspect bounds and openings, then add your fittings. The imported body has surfaces, not the original generator feature history.
4. Parasolid options require the local NX translator and licence; disabled NAS options are expected when NX is absent.

## Keep your work

JSON preserves the generator parameters. Mesh and CAD exports are separate deliverables. The hosted edition saves a shared NAS draft; the local edition uses explicit Save design. Keep model exports and their matching design version together.

## If something looks wrong

- Empty preview: the local design engine or viewer dependencies are unavailable; a static HTML server alone is insufficient.
- Unexpected wall thickness: radial offset and envelope fitting differ from constant normal wall thickness.
- NX export disabled: verify the required local licensed translator.
- Heavy file: try lower STL detail or a less complex surface.

## What this manual does not promise

CAD validity and dimensions do not certify a physical print, mounting system or thermal safety. No new physical print or heat test was performed. Third-party reference designs and libraries retain their own rights.

Screenshots show the actual application where captured. The offline demo is a deliberately smaller simulation and identifies its dummy services. It never controls devices, sends notifications, uploads files or launches printing.
