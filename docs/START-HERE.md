# Lampshade Studio: start here

**Continuing this tool? Read [the detailed handover](HANDOVER.md).** For pictures and operation, use the [manual](USER-MANUAL.md) and [offline demo](../demo.html).

Procedural shade/chandelier geometry with final envelope dimensions, patterns and mesh/CAD exports. Hollow material and the solid envelope for vase slicing are intentionally different outputs.

**Start with:** Design a shade to a fixed size. Set Width, Depth and Height first; these describe the final outside dimensions including texture peaks. Unlink width/depth for an oval.

**Source:** this is a private source checkpoint, not a live-system mirror. Check [the source manifest](../SOURCE-MANIFEST.json) and current working files before merging.

**Keep your work safe:** JSON preserves the generator parameters. Mesh and CAD exports are separate deliverables. The hosted edition saves a shared NAS draft; the local edition uses explicit Save design. Keep model exports and their matching design version together.

**Next maintainer action:** Reimport candidate exports and measure bounds/solids, then review real slicer paths, mounting and heat conditions. Radial wall offset is not constant normal thickness. Successful CAD validation is not a physical-print or thermal certification.

**Status:** private upload verified on 14 October 2026. These guides accompany the source package. Live runtime, data backups and full recovery were not retested. Public sharing was authorised on 14 October 2026; the NAS backup remains private.
