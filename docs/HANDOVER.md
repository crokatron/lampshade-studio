# Lampshade Studio: maintainer handover

[One-screen summary](START-HERE.md) · [User manual](USER-MANUAL.md) · [Feature overview](../README.md) · [Recorded validation](../VALIDATION.md)

## Purpose and behaviour to preserve

Create procedural lampshades by setting a final envelope and varying form, texture and twist. Preview the shade and bulb fit, then export a print mesh or CAD body. The included grow-light chandelier workspace extends the same project into an assembly; it is separate from a finished, validated lighting product.

- **Envelope:** Final outside width, depth and height in mm; unlink width/depth for an oval. (Design and export.)
- **Form library:** Eleven forms with ribs/folds, woven relief, smooth and triangular-facet texture choices. (Design and export.)
- **Profile controls:** Silhouette, cross-section, belly/waist and twist vary proportions inside the envelope. (Design and export.)
- **Bulb reference:** Dimensioned E27 bulb guides, orientation and radial clearance preview. (Design and export.)
- **Geometry modes:** Hollow material body for CAD, or filled outer envelope for vase slicing. (Design and export.)
- **Export formats:** STL, STEP and OpenCascade BREP; Parasolid requires a compatible licensed local NX installation. (Design and export.)
- **Design persistence:** Save/Open JSON, hosted NAS drafts and separate chandelier design controls. (Design and export.)

The [demo](../demo.html) is a smaller, labelled simulation with fictional data. It explains cause and effect without the real service; it is not evidence of a working production installation. Numbered screenshots in the user manual distinguish actual-app captures from demo captures.

## Files and sources of truth

| Actual package path | Maintainer role |
| --- | --- |
| [external-sources/LampshadeStudio/README.md](../external-sources/LampshadeStudio/README.md) | Local setup, geometric contracts and historical validation |
| [external-sources/LampshadeStudio/geometry.py](../external-sources/LampshadeStudio/geometry.py) | Procedural geometry |
| [external-sources/LampshadeStudio/public](../external-sources/LampshadeStudio/public) | Editor and preview |
| [external-sources/LampshadeStudio/nx_export.py](../external-sources/LampshadeStudio/nx_export.py) | Optional licensed NX export integration |
| [demo-source](../demo-source) | Editable demo HTML/CSS/runtime and embedded screenshot tour |
| [SOURCE-MANIFEST.json](../SOURCE-MANIFEST.json) | Original copied-source paths and SHA-256 checkpoint values |

The original working source is under C:/Users/lamon/Desktop/AI TOOLS/NAS for NAS modules; adjacent CAD/watch source locations are recorded by the full backup’s reviewed source manifest. This package contains only the explicitly copied source, not an automatic mirror. The main private nas-projects backup retains the broader shared host context.

## Setup, run and tests

Run commands from this repository root unless a `cd` is shown. Use a disposable checkout and fictional data for first setup. Dependencies, SDKs, signing material and personal data are not bundled. The following are continuation instructions grounded in the retained source, **not commands executed or newly certified by this handover**.

```powershell
cd external-sources/LampshadeStudio
.\Start-LampshadeStudio.ps1 -NoBrowser
```

http://127.0.0.1:8766 after the documented local environment is installed.

Selected project check:

```powershell
cd external-sources/LampshadeStudio
.venv/Scripts/python.exe validate_exports.py
```

For the documentation demo alone, serve this repository on loopback with `python -m http.server 8765 --bind 127.0.0.1` and open `/demo.html`. Choose a free port if another preview is running. JavaScript syntax can be checked with `node --check demo-source/runtime.js`. `python demo-source/rebuild.py` rewrites demo.html, so run it only in a disposable checkout or an authorised demo-editing session. A local server cannot provide missing HA/CAD/NAS functions. Inspect browser tests for installed dependencies, fixture requirements and network targets before running them with the approved browser tooling.

## Data, configuration and backup boundaries

Local Save design is explicit JSON export; hosted drafts live separately on the NAS. Python 3.12/CadQuery 2.6.1 and runtime assets must be installed; caches are not included. NX conversion requires a licensed local installation; LAMPSHADE_NX_DIR/UGII_BASE_DIR are path settings, not portable bundled licences.

JSON preserves the generator parameters. Mesh and CAD exports are separate deliverables. The hosted edition saves a shared NAS draft; the local edition uses explicit Save design. Keep model exports and their matching design version together.

Git preserves reviewed source and documentation. It does not copy browser storage, application databases, uploaded models/photos, accepted device settings, SDKs or credentials. Maintain independent recovery copies of the data identified above, including matching configuration and asset versions. Never add real secrets to examples, issues or logs. Private source copies on GitHub are not proof of a complete NAS/offsite data backup.

## Current verification and Git state

Before these documentation edits on 14 October 2026, this package was clean on branch `main` at `129e0eaf7802bbc2cfc10b888280a308670516b3` and its private upload was verified. All 37 manifest-listed source entries matched their stored checksums before editing. The upload follow-up has completed all 17 repositories and is paused; it does not run this tool or back up its live data.

These handover pages and README links accompany the private source package. Preserve them when continuing; stage only reviewed changes. Recheck current `git status --short --branch` and `git diff` before starting. No project-specific background schedule was inspected or changed in this documentation pass. Any service schedules in older notes are historical claims to verify in the actual deployment.

Earlier package checks and limits are recorded in [VALIDATION.md](../VALIDATION.md). This handover adds documentation/link/whitespace/secret and source-preservation checks only. No current NAS release, real hardware state, fresh installation, complete data restoration or offsite-backup freshness was verified here.

## Recovery approach

1. Preserve the current installation/data before changing it. Identify the exact code commit and data snapshot required; do not assume this package matches the running service.
2. Recover source into a new folder. Verify the source manifest and restore the project-specific configuration/assets described above separately. Recreate dependencies from the retained project files and guides.
3. Restore user data into an isolated instance or clean test browser. Check a representative editable record, associated files and save/reload behaviour, then compare to the original. Do not test recovery by overwriting production.
4. Record what actually restored and what remains missing. A demo opening or a passing syntax check is not a production recovery drill. Real deployment/device actions need the existing authorised workflow.

## Known limits and next work

CAD validity and dimensions do not certify a physical print, mounting system or thermal safety. No new physical print or heat test was performed. Third-party reference designs and libraries retain their own rights.

**Priority:** Reimport candidate exports and measure bounds/solids, then review real slicer paths, mounting and heat conditions. Radial wall offset is not constant normal thickness. Successful CAD validation is not a physical-print or thermal certification.

Common symptoms to check for this tool:

- Empty preview: the local design engine or viewer dependencies are unavailable; a static HTML server alone is insufficient.
- Unexpected wall thickness: radial offset and envelope fitting differ from constant normal wall thickness.
- NX export disabled: verify the required local licensed translator.
- Heavy file: try lower STL detail or a less complex surface.

Keep [the release checklist](../RELEASE-CHECKLIST.md) and [third-party notes](../THIRD-PARTY.md) with the package. Original contributions use MIT; bundled/upstream code and assets keep their own licences. Public publication is a separate decision; preparing documentation is not permission to publish.
