# CableCell

Benchtop cable-making robot cell — ribbon in, finished Molex 5264 cables out.
Full project doc: `README.md`.

**This is one of Kyle's PERSONAL projects, orchestrated by overwatch.**

## Hive

- **App:** CableCell (id 9)
- **Modules:** Design, Applicator, Stations, Motion, Sourcing
- **Plan:** #657 (Sourcing) — sourcing pass, two de-risk experiments, DIY
  ribbon-fed applicator subproject

## Phase

**Planning / design / simulation.** There is no code yet and will not be for a
while. The order is plan → research → design → simulate → source → build, and it
is deliberate: nothing gets bought until the simulated layout closes.

## Layout

| Folder | Contents |
|---|---|
| `docs/` | Design of record, prior art, decision log, sourcing index |
| `components/` | `registry.yaml` — the BOM↔sim join |
| `bom/` | Rendered buy lists |
| `cad/` | Vendor STEP originals |
| `sim/` | MuJoCo rough-in and studies |
| `hardware/` | Printed/machined parts (later) |

## Rules

- **`docs/cell-design.md` is the design of record.** When a decision changes the
  machine, update it in the same breath. The v1 docs drifted from the BOM within
  a day (pneumatic press, Pi 5, Pi Camera all overridden and left stale) — do not
  repeat that.
- **The registry is the source of truth.** Never hand-maintain a component fact
  in both `bom/` and `sim/`. Add it to `components/registry.yaml` and render.
- **Precision belongs in CAD, not the sim.** MuJoCo tessellates everything; it
  answers reach, collision and cycle questions only. Anything that gets
  fabricated or mates with a bought part is modeled B-rep in FreeCAD.
- **Nothing is ordered without Kyle.** Sourcing work produces markdown buy lists
  with real links. Clicking is Kyle's, always.
- **Verify listings live.** A price or a link older than a pass is a claim, not a
  fact — mark it as unverified rather than restating it.
- **Dependencies:** every dependency goes through the no-new-deps gate — Kyle's
  explicit yes before anything is added, and it must be actively maintained.
- **Git identity:** personal repo — commit as
  `Kyle Bricker <kyle.bricker@gmail.com>`. Remote is
  `git@github.com:kbricker/CableCell.git` over the default `github.com` SSH host
  (personal key `id_ed25519`), NOT the WonderForge `github-second.com` alias.
  Note `gh` on this machine is authenticated as `kyle-wf`, which cannot
  administer repos in the `kbricker` namespace — pushes work over SSH regardless.
- **Public repo** — never commit secrets, tokens, or machine-specific paths.
- **Dual-licensed:** MIT for software, CC BY 4.0 for docs/CAD/hardware designs.
  New files land under whichever applies; see the README license table. Do not
  add an explicit patent grant (Apache-2.0 etc.) without Kyle's decision — a
  patent grant would run *from* Kyle *to* users, and the applicator mechanism is
  a plausible future patent.
- **Units:** millimeters throughout the docs and registry. MuJoCo works in
  meters — convert at the scene-build boundary, never in the registry.

## Tooling

- **FreeCAD 1.1.2**, installed per-user (winget). Headless binary:
  `C:\Users\kyleb\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe`.
  Verified: `Part`, `Mesh`, `Import` all load — STEP in, STL out, scriptable.
  Use it for STEP→STL conversion and for TechDraw fabrication drawings.
- **MuJoCo** for the layout/motion rough-in. Not yet in a `pyproject.toml` —
  we add one when the first sim code lands, not before.
