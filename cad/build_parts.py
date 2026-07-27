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

import math
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
    # SPOOL_AXLE_HEIGHT is the height of the AXLE, so the upright has to stand
    # proud of it. It was previously the upright height with the bore 18 mm
    # below, which put the real axle 18 mm under where the scene placed the
    # spool — the two disagreed silently until the meshes went into the scene.
    h = float(L.SPOOL_AXLE_HEIGHT) + 20.0
    axle_z = float(L.SPOOL_AXLE_HEIGHT)
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

    # Axle bore, through the upright at the committed axle height.
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


def feed_head():
    """S1's whole on-deck presence: guide the ribbon, present it, cut it square.

    Replaces guide_tube_mount + guillotine_holder, which were two parts bolted
    in line doing one job. Kyle 2026-07-27: "we should do the simplest thing
    possible, the smallest thing possible."

    Merging them is not just tidier, it is more accurate. The cut line is the
    datum every measured length is taken from, so any play between the tube
    exit and the blade lands straight on the machine's headline spec. As one
    part, PRESENTATION_GAP is moulded in and cannot shift.

    It is also what let the feeder come off the dial entirely. The drive
    rollers, encoder wheel, spool and dancer connect to this part through PTFE
    tube, and tube routes anywhere — so they no longer have to sit in a
    196 mm radial line on an 80 mm deck.

    Part frame: x = 0 is THE CUT LINE. +x is outboard, ribbon travels -x.
    """
    cut_z = float(L.STATION_PART_PASSAGE["feed_head"])
    gap = float(L.PRESENTATION_GAP)
    rib_w = float(L.RIBBON_WIDTH)
    rib_t = float(L.RIBBON_THICKNESS)

    x_in, x_out = -12.0, 58.0
    body_y, body_z = 34.0, cut_z + 20.0
    body = Part.makeBox(x_out - x_in, body_y, body_z, V(x_in, -body_y / 2, 0))

    # PTFE tube, press fit, running from the outboard face to the presentation
    # gap. 4 mm OD tube in a 4.1 mm bore.
    body = body.cut(
        Part.makeCylinder(2.05, x_out - gap + 4.0, V(gap, 0, cut_z), V(1, 0, 0))
    )
    # Ribbon passage across the gap, and on through the anvil past the blade.
    body = body.cut(
        Part.makeBox(gap + 14.0, rib_w + 1.0, rib_t + 0.6,
                     V(x_in - 2.0, -(rib_w + 1.0) / 2, cut_z - (rib_t + 0.6) / 2))
    )
    # Blade guideway. The close fit between this slot and the ribbon passage is
    # what makes the blade SHEAR rather than crush — and a crushed end will not
    # enter the comb channels, which stops the NEXT cycle rather than this one.
    body = body.cut(
        Part.makeBox(0.9, body_y + 4.0, body_z, V(-0.45, -body_y / 2 - 2, cut_z))
    )
    # Blade clamp pocket and its screw.
    body = body.cut(Part.makeBox(9.0, 20.0, 16.0, V(-4.5, -10.0, body_z - 16.0)))
    body = body.cut(
        Part.makeCylinder(1.7, body_y + 4.0, V(0.0, -body_y / 2 - 2, body_z - 8.0),
                          V(0, 1, 0))
    )
    # SDA20 cylinder mount on top, straddling the blade.
    for sy in (-1, 1):
        for sx in (-1, 1):
            body = body.cut(
                _z_cyl(2.2, 14.0, body_z - 13.0, sx * 13.0, sy * 13.0)
            )
    # Deck mounting on station_mount's 40 mm square pattern.
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(_z_cyl(2.6, 14.0, -1.0, 23.0 + sx * 20.0, sy * 20.0))
    return body


# guide_tube_mount and guillotine_holder were merged into feed_head above. Two
# parts bolted in line doing one job, with an assembly tolerance sitting on the
# datum that every measured length is taken from.


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


def splitting_wedge():
    """S2's splitter — starts both tears; the spreader plate finishes them.

    Kyle 2026-07-27: "I'm 100% certain we can print wedges that can split the
    ribbon cable." This part exists because the ribbon is DESIGNED to zip apart
    by hand, so S2 is not cutting insulation — it is starting a tear in a
    deliberately weak web and letting geometry propagate it.

    Three tangent conductors have TWO webs, at +/- RIBBON_PITCH/2. So there are
    two tips, 1.40 mm apart, each centred on its web line.

    The asymmetry is the whole design. Each fin grows OUTWARD only: its inner
    face pulls back barely at all, holding the centre conductor on the
    centreline, while its outer face sweeps out to WEDGE_OPEN_GAP and drives
    the outer conductor away. A symmetric fin would shove the centre conductor
    sideways and the three tails would arrive at the comb off-pitch.

    No cylinder, no depth adjustment, no anvil. Split length is set by how far
    the arm advances, which makes it a commanded number rather than a tooling
    dimension — see the wedge decision on plan #672.
    """
    web = float(L.WEDGE_WEB_OFFSET)
    tip_r = float(L.WEDGE_TIP_RADIUS)
    ramp = float(L.WEDGE_RAMP_LENGTH)
    gap = float(L.WEDGE_OPEN_GAP)
    od = float(L.RIBBON_CONDUCTOR_OD)

    ch_h = float(L.RIBBON_THICKNESS) + 0.4
    entry_half = (float(L.RIBBON_WIDTH) + 0.6) / 2.0
    exit_half = web + gap + od + 0.3

    base_x, base_y, base_t = 50.0, 50.0, 8.0
    blk_y, blk_z = 30.0, 24.0
    # Passage height comes from layout.py, which the scene also reads — so the
    # printed channel and the engagement plane cannot drift apart.
    ch_z = float(L.STATION_PART_PASSAGE["splitting_wedge"])

    part = Part.makeBox(base_x, base_y, base_t, V(-base_x / 2, -base_y / 2, 0))
    part = part.fuse(
        Part.makeBox(base_x, blk_y, blk_z, V(-base_x / 2, -blk_y / 2, base_t))
    )

    def _sect(x: float, y0: float, y1: float) -> Part.Wire:
        """Rectangle in the YZ plane at station x, spanning y0..y1."""
        pts = [
            V(x, y0, ch_z),
            V(x, y1, ch_z),
            V(x, y1, ch_z + ch_h),
            V(x, y0, ch_z + ch_h),
            V(x, y0, ch_z),
        ]
        return Part.Wire(Part.makePolygon(pts))

    # Ribbon channel: widens as the conductors are driven apart, so nothing
    # binds on the side walls while it is being split.
    x_in, x_out = -base_x / 2 - 1.0, base_x / 2 + 1.0
    part = part.cut(
        Part.makeLoft(
            [_sect(x_in, -entry_half, entry_half), _sect(x_out, -exit_half, exit_half)],
            True,
        )
    )

    # The two fins. Built after the channel is cut, because they live in it.
    x_tip = -base_x / 2 + 4.0          # short plain lead-in first
    x_open = x_tip + ramp
    for sign in (1.0, -1.0):
        sections = [
            _sect(x_tip, sign * (web - tip_r), sign * (web + tip_r)),
            _sect(x_open, sign * (od / 2.0 + 0.15), sign * (web + gap)),
            _sect(base_x / 2, sign * (od / 2.0 + 0.15), sign * (web + gap)),
        ]
        part = part.fuse(Part.makeLoft(sections, True))

    # Mounts on station_mount's 40 mm square pattern, like every other station.
    for sx in (-1, 1):
        for sy in (-1, 1):
            part = part.cut(_z_cyl(2.2, base_t + 2.0, -1.0, sx * 20.0, sy * 20.0))
    return part


def z_platform():
    """The Z platform — rides three guide posts, driven by one off-axis screw,
    and houses the paired-bearing spindle at its centre.

    Two things are resolved here. The off-axis screw leaves the rotary axis
    clear, which a single coaxial rail cannot do. And the spindle is TWO 6810s
    spaced 50 mm apart rather than one slew ring: the moment becomes a couple,
    the lever arm is the spacing rather than a bought diameter, and the centre
    section shrinks from 248 mm to 165 mm as a result.
    """
    import math

    pc = float(L.Z_POST_CIRCLE_R)
    plate_r = pc + 26.0
    plate_t = 10.0
    lm_r = float(L.LM8UU_OD) / 2.0
    bore_r = float(L.SPINDLE_BEARING_OD) / 2.0
    housing_r = float(L.SPINDLE_HOUSING_OD) / 2.0
    spacing = float(L.SPINDLE_SPACING)
    bw = float(L.SPINDLE_BEARING_W)

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

    # Spindle housing: a tower carrying two bearing seats, spacing apart.
    tower_h = spacing + bw + 6.0
    plate = plate.fuse(_z_cyl(housing_r, tower_h))

    # Through bore, relieved between the seats so only the seats touch.
    plate = plate.cut(_z_cyl(bore_r - 3.0, tower_h + 2.0, -1.0))
    plate = plate.cut(_z_cyl(bore_r + 0.02, bw + 0.2, -0.1))            # lower seat
    plate = plate.cut(_z_cyl(bore_r + 0.02, bw + 0.2, spacing - bw / 2.0))  # upper seat
    plate = plate.cut(_z_cyl(bore_r - 1.0, spacing - bw, bw))            # relief

    return plate


def spindle_shaft():
    """The rotating member — a tube through both 6810 inner races.

    Carries the rotor plate on top. Printed for Phase 1; a length of 50 mm
    aluminium tube is the upgrade if the printed seats show runout, and the
    bearing seats are the only surfaces that matter for that.
    """
    bore = float(L.SPINDLE_BEARING_BORE) / 2.0
    spacing = float(L.SPINDLE_SPACING)
    bw = float(L.SPINDLE_BEARING_W)
    total = spacing + bw + 22.0

    shaft = _z_cyl(bore - 0.02, total)
    # Waisted between the races — only the seats need to be on size.
    shaft = shaft.cut(
        _z_cyl(bore + 2.0, spacing - bw - 1.0, bw + 0.5).cut(_z_cyl(bore - 2.5, spacing, bw))
    )
    # Flange at the top for the rotor plate.
    shaft = shaft.fuse(_z_cyl(bore + 12.0, 8.0, total - 8.0))
    for i in range(6):
        a = 2.0 * math.pi * i / 6.0
        shaft = shaft.cut(
            _z_cyl(1.7, 12.0, total - 10.0, (bore + 6.0) * math.cos(a), (bore + 6.0) * math.sin(a))
        )
    # Hollow through, so cabling can pass the rotation axis if ever needed.
    shaft = shaft.cut(_z_cyl(bore - 9.0, total + 2.0, -1.0))
    return shaft


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

    # Hub axis is RADIAL (+X), matching the sim's W joint. It was built on Y
    # originally, which would have flipped the comb about the wrong axis — the
    # cable is turned end-for-end about the arm's long axis, not side to side.
    # The scene caught the mismatch; fixing it here rather than rotating the
    # mesh at placement keeps the part and the model telling the same story.
    part = Part.makeCylinder(hub_r, hub_w, V(-hub_w / 2, 0, 0), V(1, 0, 0))
    part = part.cut(Part.makeCylinder(2.6, hub_w + 4.0, V(-hub_w / 2 - 2, 0, 0), V(1, 0, 0)))

    # Comb mounting pad, on the outboard face of the hub so the comb projects
    # radially outward toward the station.
    pad = Part.makeBox(26.0, 32.0, 6.0, V(hub_w / 2, -16.0, -3.0))
    part = part.fuse(pad)
    for y in (-11.0, 11.0):
        part = part.cut(
            Part.makeCylinder(1.7, 12.0, V(hub_w / 2 + 8.0, y, -6.0), V(0, 0, 1))
        )

    # Hard-stop lugs — the two positions are mechanical, not commanded.
    for sign in (1.0, -1.0):
        part = part.fuse(
            Part.makeBox(6.0, 8.0, 10.0, V(-hub_w / 2 - 3.0, sign * hub_r - 4.0, -5.0))
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


def drive_roller_block():
    """S1's feed drive: knurled driven roller against a sprung idler.

    Pays ribbon out AND pulls it back. Deliberately does NOT measure — the
    encoder wheel does that, because a driven roller slips against the ribbon
    under any tension change and cable length is the machine's headline spec.

    The idler rides in a slot with a spring behind it, so preload is set by
    spring choice rather than by how hard a screw is done up.
    """
    import math

    body_x, body_y, body_z = 56.0, 30.0, 46.0
    body = Part.makeBox(body_x, body_y, body_z, V(-body_x / 2, -body_y / 2, 0))

    # NEMA 17 face on the back, driving the knurled roller directly.
    body = body.cut(
        Part.makeCylinder(float(L.NEMA17_BOSS_DIA) / 2.0 + 0.3, 20.0,
                          V(-body_x / 2 - 5, 0, 30.0), V(1, 0, 0))
    )
    for sy in (-1, 1):
        for sz in (-1, 1):
            body = body.cut(
                Part.makeCylinder(
                    1.7, 20.0,
                    V(-body_x / 2 - 5,
                      sy * float(L.NEMA17_BOLT) / 2.0,
                      30.0 + sz * float(L.NEMA17_BOLT) / 2.0),
                    V(1, 0, 0),
                )
            )

    # Idler shaft slot — vertical travel so the spring sets preload.
    slot_z = 30.0 - float(L.RIBBON_THICKNESS) - 12.0
    body = body.cut(
        Part.makeCylinder(2.6, body_y + 4.0, V(0, -body_y / 2 - 2, slot_z), V(0, 1, 0))
    )
    body = body.cut(Part.makeBox(5.2, body_y + 4.0, 9.0,
                                 V(-2.6, -body_y / 2 - 2, slot_z)))

    # Ribbon slot straight through, on the nip line.
    nip_z = 30.0 - float(L.RIBBON_THICKNESS) / 2.0
    body = body.cut(
        Part.makeBox(body_x + 4.0, float(L.RIBBON_WIDTH) + 2.0, 4.0,
                     V(-body_x / 2 - 2, -(float(L.RIBBON_WIDTH) + 2.0) / 2, nip_z - 2.0))
    )

    # Spring pocket above the idler slot.
    body = body.cut(_z_cyl(4.0, 14.0, slot_z + 6.0))

    # Deck mounting.
    for x in (-20.0, 20.0):
        for y in (-10.0, 10.0):
            body = body.cut(_z_cyl(2.6, 12.0, -1.0, x, y))
    return body


def _v_groove(y_c: float, depth: float, half_w: float, x0: float, length: float,
              z_top: float):
    """A V-section groove cutter running along +x. Built as a lofted face and
    extruded, because Shape.rotate() mutates in place and returns None."""
    pts = [
        V(x0, y_c - half_w, z_top),
        V(x0, y_c + half_w, z_top),
        V(x0, y_c, z_top - depth),
        V(x0, y_c - half_w, z_top),
    ]
    face = Part.Face(Part.Wire(Part.makePolygon(pts)))
    return face.extrude(V(length, 0, 0))


def rotor_plate():
    """Joins the spindle shaft's flange to the arm beam.

    The only PRINTED part of the arm — the beam is stock 2020 extrusion and the
    rail is a bought MGN12. Splitting them out is what made that visible; drawn
    as one slab, the BOM could not see two bought parts at all.

    It is also the part that sets where the beam sits relative to the pivot, so
    it carries the whole moment from a 200 mm cantilever into the spindle. Hence
    the ribs: a flat disc here would be the softest link in a chain whose
    stiffness we just spent effort justifying.
    """
    import math

    bore = float(L.SPINDLE_BEARING_BORE) / 2.0
    flange_r = bore + 12.0
    plate_t = 8.0
    beam_w = float(L.ARM_WIDTH)
    beam_h = float(L.ARM_THICKNESS)

    plate = _z_cyl(flange_r + 6.0, plate_t)

    # Bolt circle matching spindle_shaft's flange.
    for i in range(6):
        a = 2.0 * math.pi * i / 6.0
        plate = plate.cut(
            _z_cyl(1.7, plate_t + 2.0, -1.0,
                   (bore + 6.0) * math.cos(a), (bore + 6.0) * math.sin(a))
        )
    plate = plate.cut(_z_cyl(bore - 9.0, plate_t + 2.0, -1.0))

    # Saddle the beam sits in, running out along +x.
    saddle_l = flange_r + 30.0
    plate = plate.fuse(
        Part.makeBox(saddle_l, beam_w + 12.0, plate_t + beam_h * 0.6,
                     V(0, -(beam_w + 12.0) / 2, 0))
    )
    plate = plate.cut(
        Part.makeBox(saddle_l + 2.0, beam_w + 0.4, beam_h,
                     V(-1.0, -(beam_w + 0.4) / 2, plate_t))
    )
    # Beam clamping bolts, through the saddle cheeks.
    for x in (flange_r * 0.6, saddle_l - 12.0):
        plate = plate.cut(
            Part.makeCylinder(2.6, beam_w + 20.0,
                              V(x, -(beam_w + 12.0) / 2 - 4, plate_t + beam_h * 0.3),
                              V(0, 1, 0))
        )
    # Ribs from the flange out to the saddle.
    for sign in (1.0, -1.0):
        tri = Part.makePolygon([
            V(0, sign * (beam_w / 2 + 5.0), plate_t),
            V(flange_r + 4.0, sign * (beam_w / 2 + 5.0), plate_t),
            V(0, sign * (beam_w / 2 + 5.0), plate_t + beam_h * 0.55),
            V(0, sign * (beam_w / 2 + 5.0), plate_t),
        ])
        face = Part.Face(Part.Wire(tri))
        plate = plate.fuse(face.extrude(V(0, sign * 4.0, 0)))
    return plate


def cross_slide_carrier():
    """Rides the MGN9 rail on top of the radial carriage; carries the wrist.

    The S axis. 20 mm of stroke in 8 mm steps, which selects conductor 1, 2 or
    3 at comb pitch — that is its entire job, and it is why the stroke is
    exactly 2 x COMB_PITCH rather than a round number.

    It takes almost no load. The 50 N pull-off runs along R, not S, so this can
    be a small screw and a light rail. Sizing it for the pull-off would have
    been the obvious mistake.
    """
    stroke = float(L.CROSS_SLIDE_STROKE)
    w, d, t = 44.0, float(L.MGN9_CARRIAGE_W) + 14.0, 8.0
    body = Part.makeBox(w, d, t, V(-w / 2, -d / 2, 0))

    # MGN9C mounting underneath.
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(
                _z_cyl(1.7, t + 2.0, -1.0,
                       sx * float(L.MGN9_BOLT_X) / 2.0,
                       sy * float(L.MGN9_BOLT_Y) / 2.0)
            )

    # Upright carrying the wrist hub bore. Hub axis is RADIAL (+x), matching
    # wrist_mount and the W joint.
    up_t, up_h = 9.0, 30.0
    up = Part.makeBox(up_t, d, up_h, V(-w / 2 + 2.0, -d / 2, t))
    body = body.fuse(up)
    hub_z = t + up_h - 13.0
    body = body.cut(
        Part.makeCylinder(3.1, up_t + 8.0, V(-w / 2, 0, hub_z), V(1, 0, 0))
    )

    # Leadscrew nut boss, offset clear of the rail. Stroke is stamped into the
    # part as a witness slot so a mis-cut carrier is visible, not silent.
    boss_y = d / 2.0 - 6.0
    body = body.fuse(Part.makeBox(18.0, 12.0, 14.0, V(-9.0, boss_y - 12.0, t)))
    body = body.cut(
        Part.makeCylinder(2.1, 40.0, V(-20.0, boss_y - 6.0, t + 7.0), V(1, 0, 0))
    )
    body = body.cut(
        Part.makeBox(stroke, 2.0, 1.0, V(-stroke / 2, -d / 2 + 1.0, t - 1.0))
    )
    return body


def body_clamp():
    """Holds the ribbon body while S3 rips insulation off three conductors.

    THE part that must not slip. The arm pulls off by retracting 4 mm, so this
    clamp takes the whole ~50 N. If the ribbon creeps here, strip length is
    wrong and the MEASURED CABLE LENGTH is wrong too, because the ribbon has
    moved relative to the datum the encoder established — and nothing
    downstream notices. It corrupts the headline spec silently.

    Sprung closed, air opens it. A single-acting cylinder is simpler and
    cheaper than a double-acting one, and losing air pressure fails to
    GRIPPING rather than dropping a part mid-cycle.

    Serrations run ACROSS the ribbon, so their ridges bite perpendicular to the
    pull. Pitch is fine enough to grip PVC without shearing into it.
    """
    jaw_l = float(L.CLAMP_JAW_LENGTH)
    rib_w = float(L.RIBBON_WIDTH)
    rib_t = float(L.RIBBON_THICKNESS)
    pitch = float(L.CLAMP_SERRATION_PITCH)
    open_gap = float(L.CLAMP_OPEN_GAP)

    body_x, body_y, body_z = jaw_l + 16.0, 30.0, 34.0
    body = Part.makeBox(body_x, body_y, body_z, V(-body_x / 2, -body_y / 2, 0))

    grip_z = 14.0
    # Ribbon channel through the fixed lower jaw.
    body = body.cut(
        Part.makeBox(body_x + 4.0, rib_w + 0.6, rib_t + 0.3,
                     V(-body_x / 2 - 2, -(rib_w + 0.6) / 2, grip_z))
    )
    # Serration ridges on the fixed jaw floor: cut narrow slots across the
    # ribbon, leaving ridges between them.
    n = int(jaw_l / pitch)
    for i in range(n):
        x = -jaw_l / 2.0 + i * pitch
        body = body.cut(
            Part.makeBox(pitch * 0.45, rib_w + 2.0, 0.35,
                         V(x, -(rib_w + 2.0) / 2, grip_z - 0.35))
        )
    # Moving jaw slideway, open above the ribbon.
    body = body.cut(
        Part.makeBox(jaw_l + 1.0, rib_w + 4.0, open_gap + 10.0,
                     V(-(jaw_l + 1.0) / 2, -(rib_w + 4.0) / 2, grip_z + rib_t + 0.3))
    )
    # Spring pocket above the moving jaw — closes the clamp with no air.
    body = body.cut(_z_cyl(4.5, 12.0, body_z - 12.0))
    # Single-acting cylinder mount on top.
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(_z_cyl(2.2, 12.0, body_z - 11.0, sx * 10.0, sy * 10.0))
    # Mounts to the wrist pad, alongside the comb.
    for y in (-11.0, 11.0):
        body = body.cut(_z_cyl(1.7, grip_z, -1.0, -body_x / 2 + 6.0, y))
    return body


def strip_die():
    """S3. Three V-blade pairs at comb pitch, one stroke, one shim.

    All three conductors get the same strip length BY CONSTRUCTION rather than
    from three separate settings — that is the reason for a gang die rather
    than a single blade indexed three times.

    Depth is set by a SWAPPABLE SHIM, not an adjustment screw. A screw can be
    knocked out of true and nobody sees it; a shim is a discrete part you can
    hold up and identify. Too shallow and the slug will not part; too deep and
    the blade nicks strands — which does not fail here, it fails a pull test
    two stations later after the crimp, which is the expensive kind.

    No pull-off actuator: the arm retracting 4 mm does that. Hence body_clamp.
    """
    pitch = float(L.COMB_PITCH)
    n = int(L.COMB_CHANNELS)
    od = float(L.RIBBON_CONDUCTOR_OD)
    shim_t = float(L.STRIP_SHIM_T)
    drop = float(L.STRIP_SLUG_DROP)

    span = pitch * (n + 1)
    body_x, body_z = 40.0, 52.0
    body = Part.makeBox(body_x, span, body_z, V(-body_x / 2, -span / 2, 0))

    cut_z = 34.0
    half_w = od / 2.0 + 0.6

    for i in range(n):
        y = (i - (n - 1) / 2.0) * pitch
        # Conductor passage straight through.
        body = body.cut(
            Part.makeCylinder(od / 2.0 + 0.25, body_x + 4.0,
                              V(-body_x / 2 - 2, y, cut_z), V(1, 0, 0))
        )
        # The V blade itself, scoring from above at the strip line.
        body = body.cut(
            _v_groove(y, half_w - shim_t / 2.0, half_w, -0.6, 1.2,
                      cut_z + od / 2.0 + 0.25)
        )
        # Slug chute: the three insulation slugs drop away rather than into the
        # mechanism, which is what stops the second cycle jamming on the first
        # cycle's waste.
        body = body.cut(
            Part.makeCylinder(od / 2.0 + 1.5, drop, V(-6.0, y, cut_z - drop), V(0, 0, 1))
        )

    # Shim slot, entered from the side so the shim swaps without stripping the
    # die off the deck.
    body = body.cut(
        Part.makeBox(body_x + 4.0, span + 4.0, shim_t,
                     V(-body_x / 2 - 2, -(span + 4.0) / 2, cut_z + od / 2.0 + 2.0))
    )
    # SDA20 cylinder mount on top.
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(_z_cyl(2.2, 14.0, body_z - 13.0, sx * 13.0, sy * 13.0))
    # Station mount pattern.
    for sx in (-1, 1):
        for sy in (-1, 1):
            body = body.cut(_z_cyl(2.6, 14.0, -1.0, sx * 14.0, sy * 20.0))
    return body


def station_mount():
    """Generic station base — bolts a station to the deck on the bolt circle.

    Every station sits on the same interface, which is what makes stations
    bolt-on modules and makes "other connectors later" a matter of swapping a
    sector rather than rebuilding the dial. Slotted radially so a station can
    be trimmed in and out during commissioning without redrilling the deck.
    """
    w, d, t = 76.0, 60.0, 10.0
    base = Part.makeBox(w, d, t, V(-w / 2, -d / 2, 0))

    # Radial adjustment slots.
    for y in (-20.0, 20.0):
        base = base.cut(_z_cyl(2.7, t + 2.0, -1.0, -14.0, y))
        base = base.cut(_z_cyl(2.7, t + 2.0, -1.0, 14.0, y))
        base = base.cut(Part.makeBox(28.0, 5.4, t + 2.0, V(-14.0, y - 2.7, -1.0)))

    # Station bolt pattern on top, 40 mm square.
    for sx in (-1, 1):
        for sy in (-1, 1):
            base = base.cut(_z_cyl(2.2, t + 2.0, -1.0, sx * 20.0, sy * 20.0))

    # Tag plate ledge, angled toward the pivot so the arm camera reads it square.
    ledge = Part.makeBox(6.0, 34.0, 30.0, V(-w / 2, -17.0, t))
    base = base.fuse(ledge)
    base = base.cut(
        Part.makeBox(2.0, float(L.STATION_TAG_SIZE) + 1.0, float(L.STATION_TAG_SIZE) + 1.0,
                     V(-w / 2 - 0.5, -(float(L.STATION_TAG_SIZE) + 1.0) / 2, t + 2.0))
    )
    return base


PARTS = {
    "spool": spool,
    "spool_hanger": spool_hanger,
    "dancer_arm": dancer_arm,
    "comb": comb,
    "feed_head": feed_head,
    "measuring_wheel": measuring_wheel,
    "splitting_wedge": splitting_wedge,
    "spreader_plate": spreader_plate,
    "z_platform": z_platform,
    "spindle_shaft": spindle_shaft,
    "rotor_plate": rotor_plate,
    "radial_carriage": radial_carriage,
    "cross_slide_carrier": cross_slide_carrier,
    "body_clamp": body_clamp,
    "strip_die": strip_die,
    "wrist_mount": wrist_mount,
    "camera_mount": camera_mount,
    "drive_roller_block": drive_roller_block,
    "station_mount": station_mount,
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
