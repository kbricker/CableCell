# cad/

Printed and machined parts as real CAD solids.

```
"%LOCALAPPDATA%/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/build_parts.py
```

Regenerates everything in `parts/`. Each part exports three ways:

| Extension | For |
|---|---|
| `.FCStd` | open and edit in FreeCAD |
| `.step` | B-rep — other CAD, and TechDraw drawings |
| `.stl` | slicer, and mesh swap-in for the MuJoCo scene |

**Dimensions come from `sim/layout.py`**, the same single source the simulation
uses, so the printable parts and the sim cannot drift. Change a number there and
re-run both.

---

## Current parts

| Part | Size (mm) | Volume | What it is |
|---|---|---|---|
| `spool` | 110 × 110 × 31 | 116.6 cm³ | S1 ribbon spool. The wire ships as a loose roll, so this is ours to define |
| `spool_hanger` | 70 × 44 × 150 | 81.0 cm³ | Carries the spool axle, mounts to 3030 on 30 mm centres |
| `dancer_arm` | 82 × 12 × 20 | 6.2 cm³ | Passive tension; its flag is the spool-empty detect |
| `comb` | 26 × 32 × 12 | 9.3 cm³ | The gripper — a 3-channel **guide**, not a clamp |
| `guide_tube_mount` | 34 × 24 × 29 | 14.4 cm³ | Holds the PTFE tube that sets S1's presentation point |

---

## Print notes

**Material.** PETG over PLA for anything that sees sustained load or warmth —
the hanger and the comb especially. PLA is fine for the dancer arm and the spool.

**The comb is the part to be careful with.** Its channels are nominally
1.8 mm for a 1.4 mm conductor: only 0.2 mm clearance per side, and **FDM will
eat most of that.** Expect a 1.8 mm modelled slot to come out nearer 1.6 mm.
Print a short test coupon and check a conductor slides freely before committing
to a full comb — the channels must *guide*, never grip, or the whole
one-conductor-at-a-time premise fails.

**Orientation:**

| Part | Orientation | Why |
|---|---|---|
| `spool` | flange flat on the bed | Bore prints as a true vertical circle; no supports except the ribbon anchor slot |
| `spool_hanger` | on its back, upright flat on the bed | Axle bore axis vertical = round. Gussets and base need light support |
| `dancer_arm` | flat, as modelled | Trivial, no supports |
| `comb` | channels facing up | Channels are open-topped so they self-support; the lead-in funnels are the only overhang |
| `guide_tube_mount` | on its side, tube bore vertical | A horizontal 4 mm bore will sag; vertical prints round |

**Tolerance reality.** Everything with a bore is modelled at nominal +0.15 mm
(the 8 mm axle bores are 8.3 mm) because printed holes come out undersize. The
comb channels are *not* similarly padded — they are a functional fit and want
measuring, not guessing.

---

## Two FreeCAD scripting traps, recorded so nobody re-finds them

1. **`Shape.translate()` mutates in place and returns `None`.** Chaining it —
   `face.extrude(v).translate(v2)` — silently yields `None`, and fusing that
   kills `freecadcmd` outright with no traceback. Build geometry at its final
   position instead, or use `translated()`.
2. **`freecadcmd` sets `__name__` to the module basename, not `"__main__"`.**
   A conventional `if __name__ == "__main__":` guard never fires, so the script
   imports cleanly and does absolutely nothing. `build_parts.py` accepts both.

Also worth knowing: routing an STL through a `Mesh::Feature` document object and
`Mesh.export()` crashes the process. Write the mesh directly —
`Mesh.Mesh(shape.tessellate(dev)).write(path)`.

`freecadcmd` swallows stdout and can die without a traceback, so
`build_parts.py` writes `cad/build.log` step by step. If a run produces nothing,
read that first.
