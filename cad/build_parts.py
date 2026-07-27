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


def measuring_wheel():
    """S1's length-measuring wheel — the part that owns cable length accuracy.

    31.83 mm diameter is exactly 100.00 mm of circumference, so with a 600 P/R
    quadrature encoder length in mm is counts * 100 / 2400.

    Deliberately NO rubber tyre or O-ring: a compliant surface changes the
    effective circumference and its compression varies with preload, which is
    exactly the error this wheel exists to avoid. Grip comes from a light
    axial knurl in the printed surface plus spring preload.
    """
    import math

    r = float(L.MEASURING_WHEEL_DIA) / 2.0
    w = float(L.MEASURING_WHEEL_WIDTH)
    bore = float(L.MEASURING_WHEEL_BORE) / 2.0 + 0.1

    body = _z_cyl(r, w)

    # Axial knurl: shallow flutes cut around the rim for grip on PVC insulation.
    flutes = 60
    for i in range(flutes):
        a = 2.0 * math.pi * i / flutes
        cutter = Part.makeCylinder(
            0.35, w + 2.0, V(r * math.cos(a), r * math.sin(a), -1.0)
        )
        body = body.cut(cutter)

    # Relief so only the rim rides the ribbon, and a hub for the grub screw.
    body = body.cut(_z_cyl(r - 4.0, w - 4.0, 2.0))
    body = body.fuse(_z_cyl(bore + 4.0, w))
    body = body.cut(_z_cyl(bore, w + 2.0, -1.0))
    return body


def spreader_plate():
    """S2's fan — diverging slots that splay the slit tails into the comb.

    Takes three conductors from the ribbon's ~1.45 mm pitch out to the comb's
    8 mm pitch over the 25 mm split length. That is 3.275 mm of lateral travel
    on each outer conductor, or 7.5 degrees — gentle enough that the insulation
    takes no set and the finished cable does not look mangled at the breakout.

    The fiddliest printed part in Phase 1: the slot entries have to catch a
    1.45 mm-pitch tail reliably.
    """
    n = int(L.COMB_CHANNELS)
    entry_pitch = float(L.RIBBON_PITCH)
    exit_pitch = float(L.COMB_PITCH)
    run = float(L.SPLIT_LENGTH)
    slot_w = float(L.RIBBON_CONDUCTOR_OD) + 0.5
    plate_t = 8.0
    body_y = exit_pitch * (n + 1)

    plate = Part.makeBox(run, body_y, plate_t, V(0, -body_y / 2, 0))

    for i in range(n):
        y_in = (i - (n - 1) / 2.0) * entry_pitch
        y_out = (i - (n - 1) / 2.0) * exit_pitch

        def rect(x: float, y: float) -> Part.Wire:
            hw, hh = slot_w / 2.0, slot_w / 2.0
            zc = plate_t / 2.0
            pts = [
                V(x, y - hw, zc - hh),
                V(x, y + hw, zc - hh),
                V(x, y + hw, zc + hh),
                V(x, y - hw, zc + hh),
                V(x, y - hw, zc - hh),
            ]
            return Part.Wire(Part.makePolygon(pts))

        slot = Part.makeLoft([rect(-1.0, y_in), rect(run + 1.0, y_out)], True)
        plate = plate.cut(slot)

        # Flared entry so a tail that is slightly off-pitch still finds its slot.
        flare = Part.makeCone(
            slot_w * 1.15, slot_w / 2.0, 4.0, V(-1.0, y_in, plate_t / 2.0), V(1, 0, 0)
        )
        plate = plate.cut(flare)

    for y in (-body_y / 2 + 4.0, body_y / 2 - 4.0):
        plate = plate.cut(_z_cyl(1.7, plate_t + 2.0, -1.0, run / 2.0, y))
    return plate


def z_platform():
    """The Z platform — rides three guide posts, driven by one off-axis screw.

    This is the part that resolves the coaxial conflict: a rotary axis cannot
    pass through a linear rail, so the screw moves off-axis and the platform
    centre is left clear for the main bearing. Stiffness comes from the post
    triangle rather than a cantilever.
    """
    import math

    pc = float(L.Z_POST_CIRCLE_R)
    plate_r = pc + 26.0
    plate_t = 10.0
    lm_r = float(L.LM8UU_OD) / 2.0

    plate = _z_cyl(plate_r, plate_t)

    # Three LM8UU housings, one per post.
    for angle in (90.0, 210.0, 330.0):
        x, y = pc * math.cos(math.radians(angle)), pc * math.sin(math.radians(angle))
        plate = plate.fuse(_z_cyl(lm_r + 3.0, float(L.LM8UU_LEN), 0.0, x, y))
        plate = plate.cut(_z_cyl(lm_r + 0.1, float(L.LM8UU_LEN) + 2.0, -1.0, x, y))

    # Off-axis leadscrew nut boss at 270 degrees.
    sx = pc * math.cos(math.radians(270.0))
    sy = pc * math.sin(math.radians(270.0))
    plate = plate.fuse(_z_cyl(float(L.T8_NUT_FLANGE_DIA) / 2.0 + 3.0, plate_t + 8.0, 0.0, sx, sy))
    plate = plate.cut(_z_cyl(5.5, plate_t + 12.0, -1.0, sx, sy))
    for i in range(4):
        a = math.radians(45.0 + 90.0 * i)
        bx = sx + float(L.T8_NUT_BOLT_CIRCLE) / 2.0 * math.cos(a)
        by = sy + float(L.T8_NUT_BOLT_CIRCLE) / 2.0 * math.sin(a)
        plate = plate.cut(_z_cyl(1.7, plate_t + 12.0, -1.0, bx, by))

    # Central bore + bolt ring for the main rotary bearing.
    bearing_r = float(L.MAIN_BEARING_BORE) / 2.0
    plate = plate.cut(_z_cyl(bearing_r - 6.0, plate_t + 2.0, -1.0))
    for i in range(6):
        a = 2.0 * math.pi * i / 6.0
        plate = plate.cut(
            _z_cyl(2.2, plate_t + 2.0, -1.0, bearing_r * math.cos(a), bearing_r * math.sin(a))
        )
    return plate


def radial_carriage():
    """Rides the MGN12 rail; carries the cross-slide and takes the R thrust.

    R is the axis that pulls insulation slugs off three conductors at once —
    the largest force the arm ever applies, ~50 N. Hence a T8 leadscrew nut
    rather than a belt clamp.
    """
    import math

    w = float(L.MGN12_CARRIAGE_W) + 12.0
    ln, t = 52.0, 8.0
    body = Part.makeBox(ln, w, t, V(-ln / 2, -w / 2, 0))

    # MGN12H mounting pattern.
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(
                _z_cyl(1.7, t + 2.0, -1.0, sx * float(L.MGN12_BOLT_X) / 2.0,
                       sy * float(L.MGN12_BOLT_Y) / 2.0)
            )

    # T8 nut boss, standing proud so the screw clears the rail.
    boss_y = w / 2.0 + 6.0
    body = body.fuse(Part.makeBox(30.0, 16.0, 22.0, V(-15, boss_y - 16.0, 0)))
    nut_y = boss_y - 8.0
    body = body.cut(_z_cyl(5.5, 30.0, -1.0, 0.0, nut_y))
    for i in range(4):
        a = math.radians(45.0 + 90.0 * i)
        body = body.cut(
            _z_cyl(1.7, 30.0, -1.0,
                   float(L.T8_NUT_BOLT_CIRCLE) / 2.0 * math.cos(a),
                   nut_y + float(L.T8_NUT_BOLT_CIRCLE) / 2.0 * math.sin(a))
        )

    # Cross-slide rail mounting face on top.
    for x in (-float(L.MGN9_BOLT_X) / 2.0, float(L.MGN9_BOLT_X) / 2.0):
        body = body.cut(_z_cyl(1.7, t + 2.0, -1.0, x, -w / 2.0 + 6.0))
    return body


def wrist_mount():
    """Carries the comb and flips it 180 degrees between cable ends.

    Two positions only, set by mechanical hard stops — the motor just has to
    reach them. The pneumatic rotary actuator originally specified here was
    dropped at $220 against ~$20 for a stepper and belt.
    """
    hub_r, hub_w = 13.0, 14.0
    part = Part.makeCylinder(hub_r, hub_w, V(0, -hub_w / 2, 0), V(0, 1, 0))
    part = part.cut(Part.makeCylinder(2.6, hub_w + 4.0, V(0, -hub_w / 2 - 2, 0), V(0, 1, 0)))

    # Comb mounting pad.
    pad = Part.makeBox(26.0, 32.0, 6.0, V(hub_r - 4.0, -16.0, -3.0))
    part = part.fuse(pad)
    for y in (-11.0, 11.0):
        part = part.cut(
            Part.makeCylinder(1.7, 12.0, V(hub_r + 2.0, y, -6.0), V(0, 0, 1))
        )

    # Hard-stop lugs — the two positions are mechanical, not commanded.
    for sign in (1.0, -1.0):
        part = part.fuse(
            Part.makeBox(8.0, 6.0, 10.0, V(-hub_r - 2.0, sign * 4.0 - 3.0, -5.0))
        )
    return part


def camera_mount():
    """Holds the ELP board on the RADIAL carriage — deliberately not the wrist.

    The wrist flips 180 degrees between cable ends; the camera must not. Tilted
    down at the station work point so it can read that station's AprilTag.
    """
    board = float(L.CAMERA_BOARD)
    plate_t = 5.0
    face = Part.makeBox(board + 10.0, board + 10.0, plate_t, V(-(board + 10) / 2, -(board + 10) / 2, 0))

    # ELP boards use a 30 mm M2 pattern.
    for sx in (-1, 1):
        for sy in (-1, 1):
            face = face.cut(_z_cyl(1.15, plate_t + 2.0, -1.0, sx * 15.0, sy * 15.0))
    face = face.cut(_z_cyl(9.0, plate_t + 2.0, -1.0))  # lens clearance

    # Angled leg setting CAMERA_TILT, with a slot so the angle can be trimmed
    # once we see what the camera actually frames.
    leg = Part.makeBox(12.0, board + 10.0, 34.0, V(-(board + 10) / 2 - 12.0, -(board + 10) / 2, 0))
    part = face.fuse(leg)
    for z in (10.0, 24.0):
        part = part.cut(
            Part.makeCylinder(1.7, 20.0, V(-(board + 10) / 2 - 16.0, 0, z), V(1, 0, 0))
        )
    return part


PARTS = {
    "spool": spool,
    "spool_hanger": spool_hanger,
    "dancer_arm": dancer_arm,
    "comb": comb,
    "guide_tube_mount": guide_tube_mount,
    "measuring_wheel": measuring_wheel,
    "spreader_plate": spreader_plate,
    "z_platform": z_platform,
    "radial_carriage": radial_carriage,
    "wrist_mount": wrist_mount,
    "camera_mount": camera_mount,
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
