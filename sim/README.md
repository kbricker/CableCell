# sim/

MuJoCo CSG rough-in. Answers **reach, collision and cycle-closure** — not
precision. MuJoCo tessellates everything; manufacturing truth lives in FreeCAD.

| File | What it does |
|---|---|
| `layout.py` | **The single source of every dimension.** Nothing else may hard-code one. Millimetres and degrees; each value carries a provenance status (COMMITTED / ESTIMATED / PLACEHOLDER) |
| `build_scene.py` | Generates `assets/cell.generated.xml` from `layout.py`; `--render` also writes PNG views |
| `run_cell.py` | Interactive viewer — regenerates the scene first, so edit-a-dimension-and-rerun is the whole loop |
| `studies/fit_check.py` | Arithmetic-only layout check: angular fit, Z budget, press reach |
| `studies/renders/` | Rendered views, committed so the layout can be reviewed without running anything |

## Run

```
uv sync
uv run python -m sim.layout                  # provenance: what is real, what is not
uv run python -m sim.studies.fit_check       # does the layout close?
uv run python -m sim.build_scene --render    # write MJCF + PNGs
uv run python -m sim.run_cell                # interactive viewer
```

## Frame convention

- world `z = 0` is the **bench top**
- world `x = y = 0` is the **pivot axis** (Datum B)
- the deck (Datum A) sits at `layout.DECK_ABOVE_BENCH`
- conversion mm → m happens once, in `build_scene.py`, never in `layout.py`

## Axes

Five joints model the arm: `Z` (assembly lift), `T` (theta, rotate), `R` (extend),
`S` (comb cross-slide), `W` (wrist flip). Ribbon feed (`F`) and nest index (`H`)
are station-local and not part of the arm kinematics.

`assets/cell.generated.xml` is generated — do not edit it. Change `layout.py`.
