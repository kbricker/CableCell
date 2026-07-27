# Dependencies

Every dependency in this project is here because someone asked for it explicitly
and it was justified in writing first. This file is that record.

**The rule:** nothing enters a package manifest without an explicit yes from
Kyle, preceded by a written proposal covering what it does, what drives the
need, what the alternatives were, and what it costs — transitive fan-out,
licence, platform coupling, footprint, maintenance status. Dev-only, build-only
and test-only dependencies get no exemption. Neither does "it's a tiny helper."

The default answer is **write it ourselves**. Small hand-rolled utilities cost
less than accumulated framework debt.

---

## Runtime — `pyproject.toml`

### `mujoco>=3.10`

| | |
|---|---|
| **What** | Physics simulation and rendering. |
| **Why** | The layout rough-in: reach, collision and cycle-closure studies. Kyle proposed it directly (2026-07-26) — TendWright already uses it, so the skills transfer. |
| **Licence** | Apache-2.0 |
| **Alternatives** | PyBullet was rejected on TendWright for being stale. Nothing else gives free contact simulation plus a usable viewer. |

### `numpy>=2.0`

| | |
|---|---|
| **What** | Array maths. |
| **Why** | MuJoCo's Python bindings hand back and take numpy arrays; it is effectively part of using MuJoCo at all. |
| **Licence** | BSD-3-Clause |

### `pillow>=12.3.0`

| | |
|---|---|
| **What** | Reads and writes image files, including saving a frame sequence as an animated GIF. |
| **Why** | Assembling `sim/run_cycle.py --frames` output into a single animated GIF of the arm cycle, for the README and for sharing progress. Plan 657.6. |
| **Authorised** | Kyle, 2026-07-26 |
| **Transitive fan-out** | **Zero.** Verified before install (`uv pip install --dry-run pillow` → 1 package) and again after, against the `uv.lock` diff. |
| **Licence** | MIT-CMU (HPND). Permissive; compatible with this repo's MIT + CC BY 4.0. |
| **Platform coupling** | None problematic. Compiled C extensions, but prebuilt wheels ship for Windows/macOS/Linux on all current Pythons — no source build. |
| **Footprint** | 6.9 MiB wheel. |
| **Maintenance** | Very active, near-monthly releases, among the most-downloaded packages on PyPI. |

**Alternatives considered, and why they lost:**

1. **Write a GIF89a encoder ourselves** — ~120–150 lines with LZW compression, and there was precedent: `sim/imaging.py`'s PNG writer started life hand-rolled. The killer was LZW. It is fiddly, and a subtly wrong encoder produces files that open in some viewers and not others — a miserable class of bug to chase for a convenience feature.
2. **An existing dependency** — no coverage. numpy cannot encode images; mujoco renders to arrays only.
3. **Skip the feature** — genuinely defensible, and it was offered as the honest second choice. The live viewer and the contact sheet already answer "show me the arm moving."
4. **ffmpeg → MP4** — better quality and smaller files, but a system binary rather than a Python dep, and MP4 does not inline in a GitHub README the way a GIF does.

**Net code impact:** roughly neutral. Pillow replaced the hand-written PNG
writer, and it enables text labels rendered into the contact sheet — previously
impossible, so reading order had to be explained in prose alongside the image.

---

## Tooling — not in any manifest

Installed on the machine, not depended on by the package. Listed so a fresh
setup knows what to install.

### FreeCAD 1.1.2

Parametric CAD. Generates every printed part in `cad/parts/` as a B-rep solid
and exports FCStd + STEP + STL. Also the route to dimensioned fabrication
drawings via TechDraw. Approved by Kyle 2026-07-26; installed per-user via
winget. Headless binary:

```
%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecadcmd.exe
```

Chosen over Onshape Free (all free-tier documents are public) and Fusion
Personal (licence churn). FreeCAD 1.0 fixed the topological naming problem that
made earlier versions unusable.

### poppler-utils

PDF rendering, so vendor datasheets can be read locally. This project consumes a
lot of them and two applicator drawings were unreadable without it. Approved by
Kyle 2026-07-26; installed via winget (`oschwartz10612.Poppler`).

### uv

Python environment and dependency management. Same tooling as TendWright.

---

## Not dependencies

Worth stating, because they look like they might be:

- **Blender** — used for renders and mockups, never imported by anything here.
- **The MuJoCo viewer** — ships with `mujoco`, not separate.
- **AprilTag detection** — `opencv-python` and `pupil-apriltags` are on
  **TendWright's** manifest, not this one. If CableCell grows its own vision
  code, that is a **new dependency conversation for this project**, not
  something inherited by proximity.
