"""Generate CableCell's printed parts as real CAD solids.

Run under FreeCAD's headless Python, NOT the uv venv:

    "%LOCALAPPDATA%/Programs/FreeCAD 1.1/bin/freecadcmd.exe" cad/build_parts.py

Every part is a B-rep solid built from the dimensions in `sim/layout.py` — the
same single source the MuJoCo scene uses, so the sim and the printable parts
cannot drift. Each part exports three ways:

    cad/parts/<name>.FCStd   open and edit in FreeCAD
    cad/parts/<name>.step    B-rep, for other CAD and for TechDraw
    cad/parts/<name>.stl     tessellated, for the slicer and for MuJoCo

Why B-rep here and primitives in the sim: MuJoCo answers reach and collision and
tessellates everything anyway. These are the parts that get *made*, so they are
modelled exactly and tolerance appears only at STL export, where we control it.

Print notes are in `cad/README.md`.
"""

from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import FreeCAD  # noqa: E402
import Import  # noqa: E402
import Mesh  # noqa: E402
import Part  # noqa: E402

from sim import layout as L  # noqa: E402

OUT = REPO / "cad" / "parts"
V = FreeCAD.Vector

# STL tessellation tolerance. 0.02 mm is well inside FDM resolution and keeps
# curved surfaces from faceting visibly.
STL_DEVIATION = 0.02


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _z_cyl(r: float, h: float, z: float = 0.0, x: float = 0.0, y: float = 0.0):
    return Part.makeCylinder(r, h, V(x, y, z))


def _ring_holes(shape, count: int, radius: float, hole_r: float, z: float, h: float):
    """Punch `count` holes evenly around a bolt circle — flange lightening."""
    import math

    for i in range(count):
        a = 2.0 * math.pi * i / count
        shape = shape.cut(
            _z_cyl(hole_r, h, z, radius * math.cos(a), radius * math.sin(a))
        )
    return shape


# ---------------------------------------------------------------------------
# parts
# ---------------------------------------------------------------------------


def spool():
    """S1 ribbon spool.

    The wire ships as a loose roll, so this is ours to define. Bore is 8 mm to
    match the hardened rod already on the BOM for the Z stage — one less part
    to source. Capacity is checked against the stock roll in layout.py.
    """
    hub_r = float(L.SPOOL_HUB_R)
    fl_r = float(L.SPOOL_FLANGE_R)
    w = float(L.SPOOL_INNER_WIDTH)
    ft = float(L.SPOOL_FLANGE_T)
    bore = float(L.SPOOL_BORE) / 2.0

    total = w + 2 * ft
    body = _z_cyl(hub_r, total)
    body = body.fuse(_z_cyl(fl_r, ft, 0.0))
    body = body.fuse(_z_cyl(fl_r, ft, w + ft))

    # Lightening holes in both flanges — a solid 110 mm disc is wasted plastic.
    mid = (hub_r + fl_r) / 2.0
    body = _ring_holes(body, 6, mid, 9.0, -1.0, ft + 2.0)
    body = _ring_holes(body, 6, mid, 9.0, w + ft - 1.0, ft + 2.0)

    # Ribbon anchor: a radial slot through the hub wall to tuck the tail into,
    # so the first wrap does not slip when the dancer pulls.
    slot = Part.makeBox(hub_r + 2.0, 5.0, 3.0, V(0, -2.5, ft + w / 2.0 - 1.5))
    body = body.cut(slot)

    body = body.cut(_z_cyl(bore, total + 2.0, -1.0))
    return body


def spool_hanger():
    """Bracket carrying the spool axle, off-deck outboard of S1.

    Mounts to 3030 extrusion on 30 mm centres. Gusseted, because a 150 mm
    upright in PLA will flex under dancer tension otherwise.
    """
    h = float(L.SPOOL_AXLE_HEIGHT)
    base_l, base_w, base_t = 70.0, 44.0, 6.0
    up_t, up_w = 8.0, 44.0

    base = Part.makeBox(base_l, base_w, base_t, V(-base_l / 2, -base_w / 2, 0))
    upright = Part.makeBox(up_t, up_w, h, V(-up_t / 2, -up_w / 2, 0))
    part = base.fuse(upright)

    # Triangular gusset both sides of the upright. Built directly at the right
    # Y so we never call Shape.translate(), which mutates in place and returns
    # None — fusing that result silently kills FreeCAD.
    gusset_t = 5.0
    for sign in (1.0, -1.0):
        tri = Part.makePolygon(
            [
                V(sign * up_t / 2, -gusset_t / 2, base_t),
                V(sign * (base_l / 2 - 6), -gusset_t / 2, base_t),
                V(sign * up_t / 2, -gusset_t / 2, h * 0.55),
                V(sign * up_t / 2, -gusset_t / 2, base_t),
            ]
        )
        face = Part.Face(Part.Wire(tri))
        part = part.fuse(face.extrude(V(0, gusset_t, 0)))

    # Axle bore, through the upright near the top.
    axle_z = h - 18.0
    bore = Part.makeCylinder(
        float(L.SPOOL_BORE) / 2.0 + 0.15, up_t + 20.0, V(-up_t / 2 - 10, 0, axle_z), V(1, 0, 0)
    )
    part = part.cut(bore)

    # Boss around the bore for bearing length.
    boss = Part.makeCylinder(11.0, up_t + 10.0, V(-up_t / 2 - 5, 0, axle_z), V(1, 0, 0))
    part = part.fuse(boss)
    part = part.cut(
        Part.makeCylinder(
            float(L.SPOOL_BORE) / 2.0 + 0.15, up_t + 24.0, V(-up_t / 2 - 12, 0, axle_z), V(1, 0, 0)
        )
    )

    # M5 slots for extrusion T-nuts, 30 mm centres.
    for x in (-15.0, 15.0):
        part = part.cut(_z_cyl(2.7, base_t + 2.0, -1.0, x, 14.0))
        part = part.cut(_z_cyl(2.7, base_t + 2.0, -1.0, x, -14.0))
    return part


def dancer_arm():
    """Passive tension arm. Its flag doubles as the spool-empty detect.

    Pivots at one end, carries an idler roller at the other; a spring pulls it
    toward the take-up direction so the ribbon stays at constant light tension
    regardless of how the roll pays off.
    """
    ln = float(L.DANCER_ARM_LENGTH)
    w, t = 12.0, 6.0

    arm = Part.makeBox(ln, w, t, V(0, -w / 2, 0))
    arm = arm.fuse(_z_cyl(w / 2, t))
    arm = arm.fuse(_z_cyl(w / 2, t, 0.0, ln, 0.0))

    # Pivot bore and roller-shaft bore.
    arm = arm.cut(_z_cyl(2.6, t + 2.0, -1.0))
    arm = arm.cut(_z_cyl(2.1, t + 2.0, -1.0, ln, 0.0))

    # Spring anchor post.
    arm = arm.fuse(_z_cyl(2.5, t + 5.0, 0.0, ln * 0.45, 0.0))

    # Optical flag — breaks the slot sensor beam when the roll runs out.
    flag = Part.makeBox(18.0, 2.5, 14.0, V(ln * 0.2, -1.25, t))
    return arm.fuse(flag)


def comb():
    """The gripper — a 3-channel guide, NOT a clamp.

    Channels guide; the ribbon body is clamped behind, so each conductor slides
    freely in its own channel. That is what lets a pusher advance one conductor
    at a time at the insert station.

    Channel pitch is COMB_PITCH (8 mm), deliberately decoupled from the 2.5 mm
    connector pitch — the extra spacing is what removes pin-to-pin collision
    risk at the applicator throat.
    """
    pitch = float(L.COMB_PITCH)
    n = int(L.COMB_CHANNELS)
    ch_w = float(L.RIBBON_CONDUCTOR_OD) + 0.4  # clearance to slide, not grip
    ch_d = float(L.RIBBON_CONDUCTOR_OD) + 0.6

    body_x, body_y, body_z = 26.0, pitch * (n + 1), 12.0
    body = Part.makeBox(body_x, body_y, body_z, V(0, -body_y / 2, 0))

    for i in range(n):
        y = (i - (n - 1) / 2.0) * pitch
        slot = Part.makeBox(
            body_x + 2.0, ch_w, ch_d, V(-1.0, y - ch_w / 2.0, body_z - ch_d)
        )
        body = body.cut(slot)
        # Lead-in funnel at the outboard face so a fanned tail self-finds.
        cone = Part.makeCone(
            ch_w / 2.0, 3.2, 6.0, V(body_x - 6.0, y, body_z - ch_d / 2.0), V(1, 0, 0)
        )
        body = body.cut(cone)

    # Mounting to the cross-slide carrier.
    for y in (-body_y / 2 + 5.0, body_y / 2 - 5.0):
        body = body.cut(_z_cyl(1.7, body_z + 2.0, -1.0, 6.0, y))
    return body


def guide_tube_mount():
    """Holds the PTFE guide tube that sets S1's presentation point.

    The presentation point has to be repeatable regardless of what the roll is
    doing — this is the part that makes it so.
    """
    base = Part.makeBox(34.0, 24.0, 8.0, V(-17, -12, 0))
    boss = Part.makeCylinder(9.0, 26.0, V(-17, 0, 20.0), V(1, 0, 0))
    part = base.fuse(boss)
    part = part.fuse(Part.makeBox(10.0, 24.0, 22.0, V(-5, -12, 0)))
    # 4 mm OD PTFE tube, press fit.
    part = part.cut(
        Part.makeCylinder(2.05, 40.0, V(-20, 0, 20.0), V(1, 0, 0))
    )
    for x in (-12.0, 12.0):
        part = part.cut(_z_cyl(1.7, 10.0, -1.0, x, 0.0))
    return part


PARTS = {
    "spool": spool,
    "spool_hanger": spool_hanger,
    "dancer_arm": dancer_arm,
    "comb": comb,
    "guide_tube_mount": guide_tube_mount,
}


LOG = REPO / "cad" / "build.log"


def note(msg: str) -> None:
    """Append to the build log, flushed immediately.

    freecadcmd swallows stdout and can die without a traceback, so the only
    reliable record of how far a run got is a file written step by step.
    """
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")
        fh.flush()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    report: list[str] = []
    for name, fn in PARTS.items():
        note(f"--- {name}")
        shape = fn()
        if shape is None or not shape.isValid():
            note(f"  !! {name} produced an invalid shape, skipping")
            continue
        doc = FreeCAD.newDocument(name)
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        doc.recompute()

        doc.saveAs(str(OUT / f"{name}.FCStd"))
        note("  FCStd")
        Import.export([obj], str(OUT / f"{name}.step"))
        note("  STEP")

        # Write the mesh directly. Routing it through a Mesh::Feature document
        # object and Mesh.export() crashes freecadcmd outright — no traceback,
        # just a dead process.
        Mesh.Mesh(shape.tessellate(STL_DEVIATION)).write(str(OUT / f"{name}.stl"))
        note("  STL")

        bb = shape.BoundBox
        report.append(
            f"{name:18s} {bb.XLength:6.1f} x {bb.YLength:6.1f} x {bb.ZLength:6.1f} mm"
            f"   {shape.Volume / 1000.0:7.1f} cm3"
        )
        FreeCAD.closeDocument(doc.Name)

    report.append(f"\n{len(PARTS)} parts -> {OUT}")
    text = "\n".join(report)
    print(text, flush=True)
    # freecadcmd's console swallows stdout on exit; the log is the reliable copy.
    (REPO / "cad" / "build.log").write_text(text, encoding="utf-8")
    return 0


# freecadcmd execs a script file with __name__ set to the module BASENAME, not
# "__main__" — so the conventional guard never fires and the script silently
# does nothing. Accept both.
if __name__ in ("__main__", "build_parts"):
    main()
