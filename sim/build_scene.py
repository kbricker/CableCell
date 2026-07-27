"""Generate the CableCell MuJoCo scene from `layout.py`.

This is the CSG rough-in: every element is a primitive box or cylinder, sized
and placed entirely from the dimensions in `layout.py`. Real vendor meshes get
swapped in per component later, keeping these primitives as the collision geoms
(MuJoCo convexifies collision meshes anyway, so visual-mesh + primitive-collision
is the right pattern).

What this scene is for: reach, collision and cycle-closure. It is NOT for
precision — MuJoCo tessellates everything, and manufacturing truth lives in
FreeCAD.

Frame convention:
    world z = 0 is the BENCH TOP
    world x = y = 0 is the pivot axis (Datum B)
    the deck (Datum A) sits at layout.DECK_ABOVE_BENCH

Six axes are modelled as joints: Z (assembly lift), T (theta, arm rotate),
R (arm extend), S (comb cross-slide), W (wrist flip). The ribbon feed (F) and
nest index (H) are station-local and not part of the arm kinematics.

Run:
    uv run python -m sim.build_scene            # write the MJCF
    uv run python -m sim.build_scene --render   # write it and render PNGs
"""

from __future__ import annotations

import argparse
import math
import pathlib

from sim import imaging
from sim import layout as L
from sim import ribbon as RIB

MM = 0.001  # layout is in millimetres; MuJoCo works in metres

ASSETS = pathlib.Path(__file__).parent / "assets"
MESH_DIR = pathlib.Path(__file__).parent.parent / "cad" / "parts"
MJCF_PATH = ASSETS / "cell.generated.xml"

# Fixed stack heights between the Z carriage and the arm.
Z_CARRIAGE_T = 18.0   # platform half-thickness + rotor seat
ROTOR_SEAT_T = 18.0

# Where the rotating assembly stands. COMB_ABOVE_ROTOR used to live here and
# was deleted with this pass: the arm's heights are all derived in layout.py
# section 4d now, and a second copy here is exactly how clearance_check came to
# grade a machine that no longer existed.
_DECK_TOP = float(L.DECK_ABOVE_BENCH) + float(L.DECK_THICKNESS)
# The platform rides BELOW the deck, through its 7" centre hole, so the rotor
# base is measured from the platform rather than from the deck.
_PLATFORM_BASE = float(L.Z_PLATFORM_BASE)
_ROTOR_BASE = _PLATFORM_BASE + float(L.Z_PLATFORM_T) + ROTOR_SEAT_T
# THE ARM'S DATUM. Bench-absolute height of the beam's bottom face, and the
# helper that converts any layout height (which are all measured from the deck's
# UNDERSIDE) into this body's local frame.
#
# There is exactly one conversion in the scene and this is it. Every arm offset
# below goes through _REL(); none of them is typed.
_ARM_BEAM_BOTTOM = float(L.DECK_ABOVE_BENCH) + L.arm_beam_bottom()
_BEAM_TIP = L.arm_beam_tip()
_BEAM_LEN_MM = int(round(_BEAM_TIP - (float(L.SPINDLE_HOUSING_OD) / 2.0 + 6.0)))
# The R leadscrew sits where radial_carriage's nut boss puts it: outboard of the
# beam tangentially, level with the beam's centre vertically. Both derived from
# the same numbers the part is built from, so the screw and its nut cannot end
# up in different places.
_R_SCREW_Y = -float(L.ARM_BEAM_Y) - (float(L.MGN12_CARRIAGE_W) + 12.0) / 2.0 - 8.0
_R_SCREW_Z = float(L.ARM_THICKNESS) / 2.0


def _REL(h_above_deck_underside: float) -> float:
    """A layout height, expressed in the arm body's local frame."""
    return float(L.DECK_ABOVE_BENCH) + h_above_deck_underside - _ARM_BEAM_BOTTOM


# Station display bodies are centred outboard of their work point, so the inner
# face of the tooling lands on the bolt circle.
# Beam starts outboard of the spindle housing rather than at the pivot —
# the old slab ran straight through the rotating assembly.
_BEAM_X0 = float(L.SPINDLE_HOUSING_OD) / 2.0 + 6.0

STATION_BODY_DEPTH = 70.0
STATION_BODY_HEIGHT = float(L.STATION_TOOLING_HEIGHT)


def _polar(radius: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return radius * math.cos(a), radius * math.sin(a)


def _fmt(*vals: float) -> str:
    return " ".join(f"{v:.6g}" for v in vals)


# Every printed part that build_parts.py produces, available as a mesh.
MESHES = (
    "comb", "spool", "spool_hanger", "dancer_arm", "feed_head",
    "measuring_wheel", "splitting_wedge", "spreader_plate", "z_platform",
    "spindle_shaft", "radial_carriage", "wrist_mount", "camera_mount",
    "drive_roller_block", "station_mount", "cross_slide_carrier",
    "body_clamp", "strip_die", "rotor_plate", "drop_chute",
)


# BOUGHT stock, modelled as real T-slot profile rather than drawn as a slab.
# Separate from MESHES on purpose: these are not printed, and cut_list must not
# count them as filament.
BOUGHT_MESHES = tuple(sorted(L.extrusion_meshes()))


def _mesh_assets() -> str:
    """Real CAD geometry from cad/build_parts.py.

    Same layout.py dimensions drive both the printed part and the sim, so they
    cannot disagree. STL is in millimetres; MuJoCo is in metres.
    """
    return "\n".join(
        f'    <mesh name="{n}_mesh" file="{n}.stl" scale="0.001 0.001 0.001"/>'
        for n in MESHES + BOUGHT_MESHES
    )


# Where the station mount sits. The tag pocket is in its top face at the inboard
# end (part x = -38 + 3), and the mount centre goes 35 mm outboard of R0 so the
# plate straddles the bolt circle.
STATION_MOUNT_R = float(L.STATION_MOUNT_R)
STATION_MOUNT_T = float(L.STATION_MOUNT_T)

# Which real parts stand at each stop, as
#   (mesh, radial offset from R0, tangential offset, height of the part's
#    RIBBON PASSAGE above its own base, flow-reversed, extra euler)
# Radial offsets are negative INBOARD. "flow-reversed" rotates the part 180
# degrees about z, because ribbon travels from outboard IN toward the pivot
# while every part is modelled with its flow along its own +x.
# Radial order matters and follows the documented ribbon path (docs/stations.md
# 1): spool -> dancer -> drive rollers -> encoder wheel -> PTFE tube ->
# presentation point, with the guillotine cutting AT the presentation point.
# The first cut of this table had the guillotine outboard of the guide tube,
# which would have cut the ribbon before it was ever guided.
# Passage heights are NOT repeated here — they come from
# layout.STATION_PART_PASSAGE, which build_parts.py also reads.
STATION_PARTS: dict[str, tuple] = {
    # S1's entire on-deck presence is now ONE part. The feeder that used to
    # need 196 mm of radial run lives off the dial and connects through PTFE
    # tube, which routes anywhere.
    "S1_FEED": (
        ("feed_head", 10.0, 0.0, False, None),
    ),
    # S2's order was BACKWARDS. At S1 the ribbon is fed from outboard inward,
    # so upstream parts sit further out. At S2 the arm has already got the
    # ribbon and pushes its free tail OUTWARD into the tooling — so the wedge
    # (which the tail meets first) is inboard and the spreader is outboard,
    # the opposite arrangement. Copying S1's ordering put the fan before the
    # splitter.
    "S2_SLIT": (
        ("splitting_wedge", 25.0, 0.0, False, None),
        ("spreader_plate", 67.0, 0.0, False, None),
    ),
    # S3 takes three conductors already fanned to comb pitch and scores all
    # three in one stroke. The arm does the pull-off by retracting.
    "S3_STRIP": (
        ("strip_die", 22.0, 0.0, False, None),
    ),
}

# Stops with no modelled tooling yet. These stay grey ON PURPOSE and say why —
# a detailed guess is worse than an obvious blank.
# Nothing is greyboxed any more. S4_CRIMP and S5_INSERT were the last two and
# they are stashed (see layout.STATIONS) rather than drawn as blocks the arm has
# to dodge. Every stop that exists now has real geometry.
UNMODELLED: dict[str, str] = {}

# The two stops that are a hole in the deck rather than a piece of tooling.
# Same printed collar at both; SEPARATE bins, because good work and rejects
# sharing a bin would silently defeat the point of having a reject angle.
CHUTE_STOPS = {
    "S6_DROP": ("collect", "collect_bin_mat"),
}


def _mesh_x_range(name: str) -> tuple[float, float]:
    """Radial extent of a printed part, read from its own STL, in mm."""
    import struct

    raw = (MESH_DIR / f"{name}.stl").read_bytes()
    n = struct.unpack("<I", raw[80:84])[0]
    lo, hi = 1e9, -1e9
    for i in range(n):
        base = 84 + i * 50 + 12
        for v in range(3):
            x = struct.unpack_from("<f", raw, base + v * 12)[0]
            lo, hi = min(lo, x), max(hi, x)
    return lo, hi


def check_station_inner_radius() -> list[str]:
    """L.STATION_INNER_R is a summary of THIS table. Prove it still is.

    The value lives in layout.py because that is where the arm reads it from;
    the placements it summarises live here. That is duplicated knowledge, and
    duplicated knowledge drifts — clearance_check.py once carried its own copy
    of the Z-post formula and went on reporting "clear" about a machine that had
    already been changed. So the copy has to prove itself on every build.
    """
    bad: list[str] = []
    innermost, owner = 1e9, "?"
    for parts in STATION_PARTS.values():
        for mesh, r_off, _t, reversed_, _e in parts:
            x_lo, x_hi = _mesh_x_range(mesh)
            # A reversed part faces inward, so its OUTBOARD extent becomes the
            # inboard one.
            inner = float(L.ARM_R0) + r_off + (-x_hi if reversed_ else x_lo)
            if inner < innermost:
                innermost, owner = inner, mesh
    if innermost < float(L.STATION_INNER_R) - 0.01:
        bad.append(
            f"{owner} reaches inboard to R={innermost:.1f}, inside "
            f"L.STATION_INNER_R={float(L.STATION_INNER_R):.1f} — the arm is "
            f"cleared against the layout value, so fix the layout value"
        )
    return bad


def _ribbon_bodies() -> str:
    """The ribbon, generated at S1's presentation point."""
    engage = float(L.DECK_ABOVE_BENCH) + float(L.STATION_Z["S1_FEED"])
    # THE CUT LINE IS THE WORK POINT. It was R0+10, which put the whole ribbon
    # 10 mm outboard of where the arm actually presents it — small, and enough
    # that the grip and the comb never lined up.
    cut_x = float(L.ARM_R0)
    return RIB.bodies(engage, cut_x, float(L.STATION_ANGLES["S1_FEED"]))


def _frame_members() -> str:
    """The frame as EIGHTEEN CUT MEMBERS, not one translucent cylinder.

    It was a single grey cylinder at the deck's radius — a structure implied
    rather than drawn, with no members, no lengths and no joints. Kyle: "I want
    to see the geometry for the metal part(s) of this that will be cut from the
    stock in the bom." There was nothing there to cut.

    Every length here comes from layout.frame_members(), which cut_list.py also
    reads, so the frame you see and the frame you saw are the same frame.
    """
    e = float(L.EXTRUSION)
    half = float(L.FRAME_SPAN) / 2.0 - e / 2.0     # centreline of a leg
    rail = L.frame_rail_len()
    leg = L.frame_leg_len()
    cross_y = float(L.FRAME_CROSS_Y)
    deck_under = float(L.DECK_ABOVE_BENCH)

    out: list[str] = []

    def bar(name: str, pos: tuple[float, float, float], length: float,
            axis: str) -> None:
        """A real 3030 bar. Built along its own +x, so a vertical leg turns
        about y and a y-running rail turns about z."""
        euler = {"x": "0 0 0", "y": f"0 0 {math.pi / 2:.6g}",
                 "z": f"0 {math.pi / 2:.6g} 0"}[axis]
        out.append(
            f'    <geom name="{name}" type="mesh" '
            f'mesh="ext3030_{int(round(length))}_mesh" '
            f'pos="{_fmt(pos[0] * MM, pos[1] * MM, pos[2] * MM)}" '
            f'euler="{euler}" material="extrusion_mat" contype="0" conaffinity="0"/>'
        )

    # Legs, bench top to the deck's underside minus the top rail.
    for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        bar(f"frame_leg_{i}", (sx * half, sy * half, e + leg / 2.0), leg, "z")

    # Bottom perimeter, on the bench. Two run in x, two in y.
    for i, sy in enumerate((-1, 1)):
        bar(f"frame_bot_x_{i}", (0.0, sy * half, e / 2.0), rail, "x")
        bar(f"frame_bot_y_{i}", (sy * half, 0.0, e / 2.0), rail, "y")

    # Top perimeter, directly under the deck.
    top_z = deck_under - e / 2.0
    for i, sy in enumerate((-1, 1)):
        bar(f"frame_top_x_{i}", (0.0, sy * half, top_z), rail, "x")
        bar(f"frame_top_y_{i}", (sy * half, 0.0, top_z), rail, "y")

    # Cross rails, top and bottom, straddling the Z platform.
    for i, sy in enumerate((-1, 1)):
        bar(f"frame_cross_top_{i}", (0.0, sy * cross_y, top_z), rail, "x")
        bar(f"frame_cross_bot_{i}", (0.0, sy * cross_y, e / 2.0), rail, "x")

    return "\n".join(out)


def _chute_body(name: str, theta: float, rot: float, deck_top: float) -> str:
    """S6: the collar, its bin, and the tag — no station mount.

    S6 gets no station_mount, deliberately. The mount spans radius 162..238 and
    the drop hole is 123..192; a mount here would roof over the hole it exists
    to leave open. The AprilTag moves onto the collar's own top face, which is
    at the same height and in the same place the camera already looks.
    """
    kind, mat = CHUTE_STOPS[name]
    r_mid = (float(L.DROP_HOLE_R_IN) + float(L.DROP_HOLE_R_OUT)) / 2.0
    cx, cy = _polar(r_mid, theta)

    ln = float(L.DROP_HOLE_R_OUT) - float(L.DROP_HOLE_R_IN)
    w = float(L.DROP_HOLE_W)
    bin_depth = float(L.BIN_DEPTH)
    bin_top = float(L.DECK_ABOVE_BENCH)
    bin_z = bin_top - bin_depth / 2.0

    tag = float(L.STATION_TAG_SIZE)
    tx, ty = _polar(float(L.DROP_HOLE_R_OUT) - tag / 2.0 - 2.0, theta)

    return "\n".join([
        f'    <!-- {name}: collar over a deck hole, bin under. The cable hangs',
        f'         from R={L.clamp_grip_radius():.0f} and the deck is what is under it — a',
        f'         funnel out at the bolt circle would have missed by 68 mm. -->',
        f'    <geom name="{name.lower()}_chute" type="mesh" mesh="drop_chute_mesh" '
        f'pos="{_fmt(cx * MM, cy * MM, deck_top * MM)}" '
        f'euler="0 0 {rot:.6g}" material="chute_mat" contype="0" conaffinity="0"/>',
        f'    <geom name="{name.lower()}_bin" type="box" '
        f'pos="{_fmt(cx * MM, cy * MM, bin_z * MM)}" '
        f'size="{_fmt(ln / 2 * MM, w / 2 * MM, bin_depth / 2 * MM)}" '
        f'euler="0 0 {rot:.6g}" material="{mat}" contype="0" conaffinity="0"/>',
        f'    <geom name="{name.lower()}_tag" type="box" '
        f'pos="{_fmt(tx * MM, ty * MM, (deck_top + float(L.CHUTE_COLLAR_H) - 0.6) * MM)}" '
        f'size="{_fmt(tag / 2 * MM, tag / 2 * MM, 0.0006)}" '
        f'euler="0 0 {rot:.6g}" material="tag_mat" contype="0" conaffinity="0"/>',
    ])


def _station_bodies() -> str:
    """Station assemblies on the deck, one per angular stop.

    Real printed geometry where a part exists; an honest grey block where it
    does not, labelled with the reason.
    """
    deck_top = float(L.DECK_ABOVE_BENCH) + float(L.DECK_THICKNESS)
    out: list[str] = []
    for name in L.STATIONS:
        if name == "S4_CRIMP":
            continue  # the press stands in for S4
        theta = float(L.STATION_ANGLES[name])
        rot = math.radians(theta)
        engage_z = float(L.DECK_ABOVE_BENCH) + float(L.STATION_Z[name])

        if name in CHUTE_STOPS:
            out.append(_chute_body(name, theta, rot, deck_top))
            continue

        # Every station sits on the same printed mount — that shared interface
        # is what makes stations bolt-on modules.
        mx, my = _polar(STATION_MOUNT_R, theta)
        out.append(
            f'    <geom name="{name.lower()}_mount" type="mesh" mesh="station_mount_mesh" '
            f'pos="{_fmt(mx * MM, my * MM, deck_top * MM)}" '
            f'euler="0 0 {rot:.6g}" material="mount_mat" contype="0" conaffinity="0"/>'
        )

        for mesh, r_off, t_off, reversed_, euler_tpl in STATION_PARTS.get(name, ()):
            passage_h = float(L.STATION_PART_PASSAGE[mesh])
            r = float(L.ARM_R0) + r_off
            px = r * math.cos(rot) - t_off * math.sin(rot)
            py = r * math.sin(rot) + t_off * math.cos(rot)
            pz = engage_z - passage_h
            if euler_tpl is not None:
                euler = euler_tpl.format(t=f"{rot:.6g}")
            else:
                euler = f"0 0 {rot + (math.pi if reversed_ else 0.0):.6g}"
            out.append(
                f'    <geom name="{name.lower()}_{mesh}" type="mesh" mesh="{mesh}_mesh" '
                f'pos="{_fmt(px * MM, py * MM, pz * MM)}" '
                f'euler="{euler}" material="printed_mat" contype="0" conaffinity="0"/>'
            )
            # Every part is placed by its RIBBON PASSAGE, which must land on the
            # station's engagement height. Its base then lands wherever it
            # lands, and the gap down to the mount is a real printed pedestal —
            # not a modelling fudge. Draw it, so the parts count is honest.
            # pedestal_heights() reports these for the BOM.
            gap = pz - (deck_top + STATION_MOUNT_T)
            if gap > 0.5:
                out.append(
                    f'    <geom name="{name.lower()}_{mesh}_pedestal" type="box" '
                    f'pos="{_fmt(px * MM, py * MM, (pz - gap / 2.0) * MM)}" '
                    f'size="{_fmt(0.020, 0.020, gap / 2.0 * MM)}" '
                    f'euler="{euler}" material="pedestal_mat" '
                    f'contype="0" conaffinity="0"/>'
                )

        if name in UNMODELLED:
            # Deliberately a box. See UNMODELLED for why this one is blank.
            r = float(L.ARM_R0) + STATION_BODY_DEPTH / 2.0
            x, y = _polar(r, theta)
            z = deck_top + STATION_MOUNT_T + STATION_BODY_HEIGHT / 2.0
            mat = "unknown_mat"
            out.append(
                f'    <!-- {name}: greybox - {UNMODELLED[name]} -->\n'
                f'    <geom name="{name.lower()}" type="box" '
                f'pos="{_fmt(x * MM, y * MM, z * MM)}" '
                f'size="{_fmt(STATION_BODY_DEPTH / 2 * MM, float(L.STATION_WIDTH) / 2 * MM, STATION_BODY_HEIGHT / 2 * MM)}" '
                f'euler="0 0 {rot:.6g}" material="{mat}" '
                f'contype="0" conaffinity="0"/>'
            )
        # AprilTag, LYING FLAT in the mount's top face — what the arm camera
        # registers against. It used to stand upright on a 30 mm ledge facing
        # the pivot, which read better to the camera and stood squarely in the
        # arm's path at every one of the seven stops. Flat costs ~24 degrees of
        # obliquity and buys back the entire radial approach.
        tag_r = L.station_tag_radius()
        t_off = float(L.STATION_TAG_OFFSET_T)
        tx = tag_r * math.cos(rot) - t_off * math.sin(rot)
        ty = tag_r * math.sin(rot) + t_off * math.cos(rot)
        tz = deck_top + STATION_MOUNT_T - 0.6
        out.append(
            f'    <geom name="{name.lower()}_tag" type="box" '
            f'pos="{_fmt(tx * MM, ty * MM, tz * MM)}" '
            f'size="{_fmt(float(L.STATION_TAG_SIZE) / 2 * MM, float(L.STATION_TAG_SIZE) / 2 * MM, 0.0006)}" '
            f'euler="0 0 {math.radians(theta):.6g}" material="tag_mat" '
            f'contype="0" conaffinity="0"/>'
        )
    return "\n".join(out)


def _press_body() -> str:
    """The press is STASHED for the prototype, so it is not drawn.

    It stays the deck-height datum in layout.py — DECK_ABOVE_BENCH is still
    derived from its crimp point, so Phase 2 bolts onto this deck rather than
    starting a new one. What it no longer does is stand in the scene as a
    greybox the arm has to dodge, or hold a third of the sweep arc for a
    station that does not exist yet.
    """
    return "    <!-- S4 press: stashed for the prototype. Still the deck-height datum. -->"


Z_POST_RADIUS = float(L.Z_POST_CIRCLE_R)

def _z_pedestal() -> str:
    """What stands in for the Z stage while the axis is deferred.

    A fixed 3030 pedestal off the frame's cross rails, holding the rotor at
    exactly the height the platform used to. Same interface, no motion — so
    turning Z_STAGE_ENABLED back on swaps the stand for the stage without
    moving anything above it.
    """
    e = float(L.EXTRUSION)
    h = float(L.Z_PEDESTAL_TOP)
    out = []
    for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        out.append(
            f'    <geom name="z_pedestal_{i}" type="box" '
            f'pos="{_fmt(sx * 55 * MM, sy * 55 * MM, h / 2 * MM)}" '
            f'size="{_fmt(e / 2 * MM, e / 2 * MM, h / 2 * MM)}" '
            f'material="extrusion_mat" contype="0" conaffinity="0"/>'
        )
    return "\n".join(out)


def _z_posts() -> str:
    """Three guide posts plus one off-axis leadscrew, ALL BELOW THE DECK.

    A single coaxial rail cannot work — the rotary axis needs the space the
    rail wants. Moving the screw off-axis and guiding on posts leaves the
    platform centre clear for the spindle.

    They live under the deck because they have to keep guiding the platform at
    the top of its travel, and standing that proud of the deck put them
    straight through the arm's sweep. See clearance_check.
    """
    base = float(L.Z_POST_BASE)      # on a plate on the bottom cross rails
    top = L.z_post_top()
    mid, half = (base + top) / 2.0, (top - base) / 2.0
    parts: list[str] = []
    for i, angle in enumerate((90.0, 210.0, 330.0)):
        px, py = _polar(Z_POST_RADIUS, angle)
        parts.append(
            f'    <geom name="z_post_{i}" type="cylinder" '
            f'pos="{_fmt(px * MM, py * MM, mid * MM)}" '
            f'size="{float(L.Z_POST_DIA) / 2 * MM:.6g} {half * MM:.6g}" '
            f'material="zstage_mat" contype="0" conaffinity="0"/>'
        )
    sx, sy = _polar(Z_POST_RADIUS, 270.0)
    parts.append(
        f'    <geom name="z_leadscrew" type="cylinder" '
        f'pos="{_fmt(sx * MM, sy * MM, mid * MM)}" '
        f'size="0.005 {half * MM:.6g}" '
        f'material="screw_mat" contype="0" conaffinity="0"/>'
    )
    parts.append(
        f'    <geom name="z_motor" type="box" '
        f'pos="{_fmt(sx * MM, sy * MM, (base - 22) * MM)}" '
        f'size="0.021 0.021 0.020" material="motor_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    return "\n".join(parts)


def _spool_and_hanger() -> str:
    """The feed module: spool, dancer, drive rollers and encoder wheel.

    Deliberately NOT a dial station. Kyle 2026-07-27: "we should do the
    simplest thing possible, the smallest thing possible."

    These four parts were originally laid out in a straight radial line on the
    deck alongside the guillotine, which needed 196 mm of run against the 80 mm
    the deck actually offers — and every consecutive pair interpenetrated. The
    fix was not a bigger deck or a folded path. It was noticing that none of
    these parts has any relationship to the dial: the ribbon reaches the
    machine through PTFE tube, and tube routes anywhere.

    So the feeder is a compact VERTICAL stack on one post outboard of S1.
    Radial footprint ~60 mm instead of 196 mm, and it is free to move anywhere
    the tube reaches if the bench layout ever wants it elsewhere.
    """
    deck_top = float(L.DECK_ABOVE_BENCH) + float(L.DECK_THICKNESS)
    theta = float(L.STATION_ANGLES["S1_FEED"])
    r = float(L.ARM_R0) + float(L.SPOOL_RADIAL_OFFSET)
    x, y = _polar(r, theta)
    z = deck_top + float(L.SPOOL_AXLE_HEIGHT)

    rot = math.radians(theta)
    # Spool axis is tangential, so ribbon pays off radially toward the pivot.
    # euler (90deg about x, then theta about z) sends the mesh's own +z along
    # this unit vector:
    axis_euler = f"{math.pi / 2:.6g} 0 {rot:.6g}"
    ax, ay = math.sin(rot), -math.cos(rot)
    # The spool mesh is modelled from z=0 up, so shift it back half its width
    # to sit centred on the axle.
    total_w = float(L.SPOOL_INNER_WIDTH) + 2.0 * float(L.SPOOL_FLANGE_T)
    sx = x - ax * total_w / 2.0
    sy = y - ay * total_w / 2.0

    parts: list[str] = []
    parts.append(
        f'    <geom name="spool" type="mesh" mesh="spool_mesh" '
        f'pos="{_fmt(sx * MM, sy * MM, z * MM)}" euler="{axis_euler}" '
        f'material="spool_mat" contype="0" conaffinity="0"/>'
    )
    # Wound ribbon, shown at full stock — a cylinder, because it is stock on a
    # reel, not a part we make.
    parts.append(
        f'    <geom name="spool_ribbon" type="cylinder" pos="{_fmt(x * MM, y * MM, z * MM)}" '
        f'size="{_fmt((float(L.SPOOL_FLANGE_R) - 4.0) * MM, (float(L.SPOOL_INNER_WIDTH) / 2 - 1.0) * MM)}" '
        f'euler="{axis_euler}" material="ribbon_mat" contype="0" conaffinity="0"/>'
    )
    # Hanger. Its axle bore runs along the part's own +x, so turning it a
    # further 90 degrees puts the axle tangential, parallel to the spool.
    #
    # It does NOT bolt to the deck. At SPOOL_RADIAL_OFFSET = 90 the spool sits
    # outboard of DECK_RADIUS, which is deliberate — but the first version of
    # this scene left the hanger floating in mid-air at deck height, because
    # nothing was holding it up. The part's own base has T-nut slots on 30 mm
    # centres, so what it actually wants is a 3030 extrusion post off the
    # bench. Drawing that post is what made the omission visible.
    hx, hy = _polar(r + 34.0, theta)
    parts.append(
        f'    <geom name="spool_post" type="box" '
        f'pos="{_fmt(hx * MM, hy * MM, deck_top / 2 * MM)}" '
        f'size="0.015 0.015 {deck_top / 2 * MM:.6g}" material="frame_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    parts.append(
        f'    <geom name="spool_hanger" type="mesh" mesh="spool_hanger_mesh" '
        f'pos="{_fmt(hx * MM, hy * MM, deck_top * MM)}" '
        f'euler="0 0 {rot + math.pi / 2:.6g}" material="hanger_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    # Dancer arm — passive tension, and its flag is the spool-empty detect.
    # Hangs below the spool on the same post.
    parts.append(
        f'    <geom name="dancer_arm" type="mesh" mesh="dancer_arm_mesh" '
        f'pos="{_fmt(hx * MM, hy * MM, (deck_top + 96.0) * MM)}" '
        f'euler="0 0 {rot + math.pi:.6g}" material="hanger_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    # Drive rollers and the encoder wheel, stacked low on the same post. Their
    # height is now arbitrary — the tube carries the ribbon to the feed head,
    # so nothing here has to sit on the engagement plane. That is exactly what
    # buys back the radial run.
    parts.append(
        f'    <geom name="drive_roller_block" type="mesh" mesh="drive_roller_block_mesh" '
        f'pos="{_fmt(hx * MM, hy * MM, (deck_top + 6.0) * MM)}" '
        f'euler="0 0 {rot + math.pi:.6g}" material="printed_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    wx, wy = _polar(r + 4.0, theta)
    parts.append(
        f'    <geom name="measuring_wheel" type="mesh" mesh="measuring_wheel_mesh" '
        f'pos="{_fmt(wx * MM, wy * MM, (deck_top + 46.0) * MM)}" '
        f'euler="1.5708 0 {rot:.6g}" material="printed_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    return "\n".join(parts)


def build_mjcf() -> str:
    deck_z = float(L.DECK_ABOVE_BENCH)
    deck_top = deck_z + float(L.DECK_THICKNESS)
    z_stroke = L.z_stroke_active()
    r_retracted = float(L.ARM_R0) - float(L.ARM_STROKE)
    arm_len = float(L.ARM_R0) + 30.0

    return f"""<mujoco model="cablecell_roughin">
  <!--
    GENERATED FILE - do not edit. Produced by sim/build_scene.py from sim/layout.py.
    Every dimension here traces to a named value in layout.py; 17 of 45 of those
    are placeholders. Run `uv run python -m sim.layout` for provenance.

    z = 0 is the bench top. x = y = 0 is the pivot axis.
    Deck at {deck_z:.0f} mm, bolt circle R0 = {float(L.ARM_R0):.0f} mm, Z stroke {z_stroke:.0f} mm.
  -->
  <compiler angle="radian" autolimits="true" meshdir="../../cad/parts"/>
  <option integrator="implicitfast" timestep="0.002"/>

  <visual>
    <headlight ambient="0.45 0.45 0.45" diffuse="0.55 0.55 0.55"/>
    <global azimuth="130" elevation="-22" offwidth="1600" offheight="1000"/>
    <scale forcewidth="0.02" contactwidth="0.04" contactheight="0.02"/>
  </visual>

  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.30 0.38 0.48" rgb2="0.06 0.08 0.11"
      width="32" height="512"/>
    <texture name="bench_tex" type="2d" builtin="checker" rgb1="0.24 0.22 0.20"
      rgb2="0.30 0.28 0.25" width="300" height="300"/>
    <material name="bench_mat" texture="bench_tex" texrepeat="8 8" reflectance="0.03"/>
    <material name="frame_mat" rgba="0.42 0.45 0.50 1"/>
    <material name="deck_mat" rgba="0.62 0.65 0.70 1"/>
    <material name="press_mat" rgba="0.30 0.33 0.38 1"/>
    <material name="press_plate_mat" rgba="0.55 0.58 0.62 1"/>
    <material name="applicator_mat" rgba="0.80 0.55 0.15 1"/>
    <material name="station_mat" rgba="0.25 0.42 0.60 1"/>
    <material name="reject_mat" rgba="0.60 0.30 0.30 1"/>
    <!-- Printed parts read as printed; anything still grey is grey BECAUSE we
         do not know its shape, not because the modelling is unfinished. -->
    <material name="printed_mat" rgba="0.24 0.52 0.72 1"/>
    <material name="mount_mat" rgba="0.34 0.38 0.44 1"/>
    <material name="pedestal_mat" rgba="0.18 0.40 0.56 1"/>
    <material name="clamp_mat" rgba="0.78 0.38 0.20 1"/>
    <material name="extrusion_mat" rgba="0.58 0.61 0.66 1"/>
    <material name="rail_mat" rgba="0.80 0.82 0.86 1"/>
    <material name="unknown_mat" rgba="0.52 0.52 0.54 0.55"/>
    <material name="zstage_mat" rgba="0.35 0.55 0.42 1"/>
    <material name="rotor_mat" rgba="0.50 0.50 0.55 1"/>
    <material name="arm_mat" rgba="0.72 0.74 0.78 1"/>
    <material name="comb_mat" rgba="0.90 0.85 0.30 1"/>
    <material name="spool_mat" rgba="0.85 0.86 0.88 1"/>
    <material name="ribbon_mat" rgba="0.85 0.95 0.15 1"/>
    <material name="hanger_mat" rgba="0.45 0.48 0.52 1"/>
    <material name="camera_mat" rgba="0.15 0.15 0.17 1"/>
    <!-- ONE MATERIAL PER CONDUCTOR, in the cable's real colours. The ribbon was
         a single grey "ribbon_mat", which made a 1.4 mm strand invisible AND
         made the split unreadable — three joined conductors and three separated
         ones look identical when they are all the same colour. Black/red/white
         is also what the camera has to tell apart at S5, so the sim and the
         acceptance test now agree about what they are looking at. -->
    <material name="cond_mat_0" rgba="0.10 0.10 0.12 1"/>
    <material name="cond_mat_1" rgba="0.85 0.15 0.12 1"/>
    <material name="cond_mat_2" rgba="0.95 0.95 0.95 1"/>
    <material name="chute_mat" rgba="0.45 0.50 0.58 1"/>
    <material name="collect_bin_mat" rgba="0.20 0.55 0.35 1"/>
    <material name="tag_mat" rgba="0.97 0.97 0.97 1"/>
    <material name="screw_mat" rgba="0.72 0.68 0.45 1"/>
    <material name="motor_mat" rgba="0.20 0.22 0.26 1"/>

    <!-- Real CAD geometry from cad/build_parts.py. Same layout.py dimensions
         drive both, so the printed part and the sim cannot disagree. STL is in
         millimetres; MuJoCo is in metres. -->
{_mesh_assets()}
  </asset>

  <worldbody>
    <light pos="0.4 -0.5 1.6" dir="-0.2 0.25 -1" diffuse="0.6 0.6 0.6"/>
    <light pos="-0.5 0.4 1.2" dir="0.3 -0.25 -1" diffuse="0.35 0.35 0.35"/>

    <geom name="bench" type="plane" size="1.2 1.2 0.05" material="bench_mat"/>

{_press_body()}

    <!-- Frame and deck. Deck raised deliberately to collapse Z travel. -->
    <body name="deck_body">
    <geom name="deck" type="cylinder"
      pos="0 0 {(deck_z + float(L.DECK_THICKNESS) / 2) * MM:.6g}"
      size="{float(L.DECK_RADIUS) * MM:.6g} {float(L.DECK_THICKNESS) / 2 * MM:.6g}"
      material="deck_mat" contype="0" conaffinity="0"/>
    </body>
    <body name="frame_body">
{_frame_members()}
    </body>

{_station_bodies()}

    <!-- S1's spool + hanger + dancer, off-deck outboard of station 1. -->
{_spool_and_hanger()}

    <!-- Z stage: platform on three guide posts, driven by ONE OFF-AXIS
         leadscrew. The off-axis screw is the whole trick — it leaves the
         rotary axis at the platform centre unobstructed, which a single
         coaxial rail cannot do. T8 trapezoidal, so it self-locks and an
         E-stop will not drop the arm. -->
    <body name="post_body">
{_z_posts() if L.Z_STAGE_ENABLED else _z_pedestal()}
    </body>

{_ribbon_bodies()}

    <!-- ============ the moving assembly ============ -->
    <body name="z_carriage" pos="0 0 {_PLATFORM_BASE * MM:.6g}">
      <joint name="Z" type="slide" axis="0 0 1" range="0 {z_stroke * MM:.6g}"
        damping="40"/>
      {'<geom name="z_platform" type="mesh" mesh="z_platform_mesh" pos="0 0 0" material="zstage_mat" contype="0" conaffinity="0"/>' if L.Z_STAGE_ENABLED else '<!-- Z platform: deferred with the axis. The rotor sits on a fixed pedestal. -->'}

      <geom name="t_motor" type="box"
        pos="{(float(L.SPINDLE_HOUSING_OD) / 2 + 46.0) * MM:.6g} 0 {(float(L.Z_PLATFORM_T) + 22.0) * MM:.6g}"
        size="{float(L.NEMA17_SQUARE) / 2 * MM:.6g} {float(L.NEMA17_SQUARE) / 2 * MM:.6g} 0.021"
        material="motor_mat" contype="0" conaffinity="0"/>

      <body name="rotor" pos="0 0 {(float(L.Z_PLATFORM_T) + ROTOR_SEAT_T) * MM:.6g}">
        <!-- theta = 0 is S1 by definition and the arm sweeps counter-clockwise
             from there, so the range is 0..SWEEP_ARC. It was previously
             +/-SWEEP_ARC/2, which put four of the seven stops outside the
             joint's own limits. -->
        <joint name="T" type="hinge" axis="0 0 1"
          range="0 {math.radians(float(L.SWEEP_ARC)):.6g}"
          damping="12"/>
        <!-- The rotating member: a tube through both 6810 inner races, which
             replaced the slew ring. Moment becomes a couple and the lever arm
             is SPINDLE_SPACING rather than a bought diameter. -->
        <geom name="spindle" type="mesh" mesh="spindle_shaft_mesh" pos="0 0 -0.018"
          material="rotor_mat" contype="0" conaffinity="0"/>
        <!-- THE T DRIVE: a toothed pulley on the spindle, belt-driven from a
             NEMA 17 on the platform below. Belt rather than a direct-drive
             gearbox because the arc is 270 degrees, not continuous — no slip
             ring, no rotary union, and the reduction comes free with the
             pulley ratio. -->
        <geom name="t_pulley" type="cylinder" pos="0 0 0.004"
          size="{(float(L.SPINDLE_HOUSING_OD) / 2 + 8.0) * MM:.6g} 0.008"
          material="rotor_mat" contype="0" conaffinity="0"/>

        <body name="arm" pos="0 0 {(_ARM_BEAM_BOTTOM - _ROTOR_BASE) * MM:.6g}">
          <!-- EVERY OFFSET BELOW IS DERIVED. They used to be hand-typed
               (pos="-0.030 0 -0.014" and friends), which is how the arm came to
               have 115 interfering pairs: nothing added them up because the
               stack was not written down anywhere. It is now layout.py section
               4d, and layout.py refuses to import if it does not close.

               This body's origin is the BEAM'S BOTTOM FACE, {float(L.ARM_BEAM_CLEARANCE):.0f} mm of air
               above the station mount plates.

               Three parts, not one: printed rotor_plate, BOUGHT 2020 extrusion,
               BOUGHT MGN12 rail. Tip droop {L.arm_tip_deflection() * 1000:.0f} um against a
               300 um strip tolerance. -->
          <geom name="rotor_plate" type="mesh" mesh="rotor_plate_mesh"
            pos="0 0 0" material="arm_mat" contype="0" conaffinity="0"/>
          <geom name="arm_beam" type="mesh" mesh="ext2020_{_BEAM_LEN_MM}_mesh"
            pos="{(_BEAM_X0 + _BEAM_TIP) / 2 * MM:.6g} {-float(L.ARM_BEAM_Y) * MM:.6g} {float(L.ARM_THICKNESS) / 2 * MM:.6g}"
            material="extrusion_mat" contype="0" conaffinity="0"/>
          <!-- The beam stops at R={_BEAM_TIP:.0f}. It used to run to R0+30={float(L.ARM_R0) + 30:.0f} —
               a 20 mm bar driven through all seven stations at exactly the
               height of their tooling. -->
          <geom name="mgn12_rail" type="box"
            pos="{(_BEAM_X0 + _BEAM_TIP) / 2 * MM:.6g} {-float(L.ARM_BEAM_Y) * MM:.6g} {(float(L.ARM_THICKNESS) + float(L.MGN12_RAIL_H) / 2) * MM:.6g}"
            size="{(_BEAM_TIP - _BEAM_X0) / 2 * MM:.6g} 0.006 {float(L.MGN12_RAIL_H) / 2 * MM:.6g}"
            material="rail_mat" contype="0" conaffinity="0"/>

          <!-- ============ THE R DRIVE ============
               Kyle 2026-07-27: "I think we have a plan for a specific part
               right, some sort of linear gear and motor to run up and down the
               arm? I dont see that at all."

               He was right — there was nothing there. Z was the only axis with
               a screw and a motor drawn; R, S and the rotation all moved by
               magic. The parts were in the cut list and in the printed carriers
               (radial_carriage has had a T8 nut boss all along) and simply were
               not in the scene.

               T8 trapezoidal, driven by a NEMA 17 at the inboard end, running
               alongside the beam rather than through it. Trapezoidal because it
               self-locks: the arm carries a 50 N pull-off at S3 and must not
               back-drive when the motor is unpowered. -->
          <geom name="r_leadscrew" type="cylinder"
            pos="{(_BEAM_X0 + _BEAM_TIP) / 2 * MM:.6g} {_R_SCREW_Y * MM:.6g} {_R_SCREW_Z * MM:.6g}"
            euler="0 {math.pi / 2:.6g} 0"
            size="0.004 {(_BEAM_TIP - _BEAM_X0) / 2 * MM:.6g}"
            material="screw_mat" contype="0" conaffinity="0"/>
          <!-- The motor sits ABOVE the beam near the pivot and drives the
               screw through a short belt, rather than sitting on the screw's
               axis at its inboard end. Inline was the obvious build and
               z_needed.py rejected it: on the screw's axis the motor sweeps a
               116 mm circle at deck height and clipped the drop chute's collar
               by 8.7 mm between stops. Up here it sweeps 61 mm and clears
               everything on the deck. -->
          <geom name="r_belt" type="box"
            pos="{(_BEAM_X0 / 2) * MM:.6g} {_R_SCREW_Y * MM:.6g} {(_R_SCREW_Z + 16.0) * MM:.6g}"
            size="{(_BEAM_X0 / 2) * MM:.6g} 0.003 0.018"
            material="rail_mat" contype="0" conaffinity="0"/>
          <geom name="r_motor" type="box"
            pos="0 {_R_SCREW_Y * MM:.6g} {(_R_SCREW_Z + 44.0) * MM:.6g}"
            size="{float(L.NEMA17_SQUARE) / 2 * MM:.6g} {float(L.NEMA17_SQUARE) / 2 * MM:.6g} {float(L.NEMA17_SQUARE) / 2 * MM:.6g}"
            material="motor_mat" contype="0" conaffinity="0"/>

          <body name="radial" pos="{L.arm_r_retracted() * MM:.6g} 0 0">
            <joint name="R" type="slide" axis="1 0 0"
              range="0 {float(L.ARM_STROKE) * MM:.6g}" damping="20"/>
            <!-- The bought MGN12 block, drawn because it is 5 mm of the stack
                 and was previously invisible. -->
            <geom name="mgn12_block" type="box"
              pos="0 {-float(L.ARM_BEAM_Y) * MM:.6g} {(float(L.ARM_THICKNESS) + float(L.MGN12_BLOCK_H) / 2) * MM:.6g}"
              size="0.021 {float(L.MGN12_CARRIAGE_W) / 2 * MM:.6g} {float(L.MGN12_BLOCK_H) / 2 * MM:.6g}"
              material="rail_mat" contype="0" conaffinity="0"/>
            <geom name="radial_carriage" type="mesh" mesh="radial_carriage_mesh"
              pos="0 {-float(L.ARM_BEAM_Y) * MM:.6g} {_REL(L.arm_r_block_top()) * MM:.6g}"
              material="arm_mat" contype="0" conaffinity="0"/>
            <!-- MGN9 rail. FIXED to the R carriage, so it lives here and not in
                 the cross body — the block slides along it, not the other way
                 round. -->
            <geom name="mgn9_rail" type="box"
              pos="0 {-float(L.ARM_BEAM_Y) * MM:.6g} {(_REL(L.arm_carriage_plate_top()) + float(L.MGN9_RAIL_H) / 2) * MM:.6g}"
              size="0.0045 {(float(L.CROSS_SLIDE_STROKE) / 2 + float(L.MGN9_CARRIAGE_W) / 2) * MM:.6g} {float(L.MGN9_RAIL_H) / 2 * MM:.6g}"
              material="rail_mat" contype="0" conaffinity="0"/>
            <!-- Arm camera. Rides the RADIAL carriage, deliberately NOT the
                 wrist — the wrist flips 180 degrees and the camera must not.
                 Offsets are from the WORK POINT, which is where it has to look;
                 they were from the comb, which now moves relative to it. -->
            <!-- Placed by its FOOT on the carriage plate, and unrotated: the
                 tilt is built into the part now, so the bracket stands on
                 something instead of floating at the lens position. -->
            <geom name="arm_camera" type="mesh" mesh="camera_mount_mesh"
              pos="0 0 {_REL(L.arm_carriage_plate_top()) * MM:.6g}"
              material="camera_mat" contype="0" conaffinity="0"/>
            <camera name="arm_cam"
              pos="{(L.arm_tool_reach() - float(L.CAMERA_BACK_OFFSET)) * MM:.6g} 0 {(_REL(float(L.STATION_TOOLING_HEIGHT)) + float(L.CAMERA_UP_OFFSET)) * MM:.6g}"
              euler="0 {math.radians(float(L.CAMERA_TILT) - 90.0):.6g} 0"
              fovy="48"/>

            <!-- THE S DRIVE. Rides the R carriage, so it moves with R and
                 not with S — the screw has to stay still relative to the nut it
                 turns in. Tiny: the 50 N pull-off runs along R, and S only ever
                 shifts the comb by one conductor pitch. -->
            <geom name="s_leadscrew" type="cylinder"
              pos="0 {(-float(L.ARM_BEAM_Y) - 5.0) * MM:.6g} {(_REL(L.arm_carriage_plate_top()) + float(L.MGN9_RAIL_H) + 12.0) * MM:.6g}"
              euler="{math.pi / 2:.6g} 0 0"
              size="0.002 {(float(L.CROSS_SLIDE_STROKE) / 2 + 16.0) * MM:.6g}"
              material="screw_mat" contype="0" conaffinity="0"/>
            <geom name="s_motor" type="box"
              pos="0 {(-float(L.ARM_BEAM_Y) - float(L.CROSS_SLIDE_STROKE) / 2 - 32.0) * MM:.6g} {(_REL(L.arm_carriage_plate_top()) + float(L.MGN9_RAIL_H) + 12.0) * MM:.6g}"
              size="0.014 0.014 0.014"
              material="motor_mat" contype="0" conaffinity="0"/>

            <body name="cross" pos="0 0 0">
              <joint name="S" type="slide" axis="0 1 0"
                range="{-float(L.CROSS_SLIDE_STROKE) / 2 * MM:.6g} {float(L.CROSS_SLIDE_STROKE) / 2 * MM:.6g}"
                damping="8"/>
              <!-- S axis carrier. Takes almost no load: the 50 N pull-off
                   runs along R, not S. Sizing it for the pull-off would have
                   been the obvious mistake. Its cheek hangs DOWN from the
                   inboard end to put the wrist axis on the engagement plane —
                   {L.wrist_cheek_drop_from_seat():.0f} mm, derived, not chosen. -->
              <geom name="cross_carriage" type="mesh" mesh="cross_slide_carrier_mesh"
                pos="0 {-float(L.ARM_BEAM_Y) * MM:.6g} {_REL(L.arm_s_block_top()) * MM:.6g}"
                material="arm_mat" contype="0" conaffinity="0"/>

              <body name="wrist"
                pos="{(-float(L.CROSS_PLATE_LEN) / 2 + float(L.WRIST_CHEEK_T)) * MM:.6g} 0 {_REL(float(L.STATION_TOOLING_HEIGHT)) * MM:.6g}">
                <joint name="W" type="hinge" axis="1 0 0" range="0 {math.pi:.6g}"
                  damping="6"/>
                <!-- THE WRIST AXIS IS THE ENGAGEMENT PLANE, and the comb's
                     channels and the clamp's grip face both lie ON it. The flip
                     is therefore a pure rotation: the conductors do not move.
                     With the axis anywhere else, turning the cable end-for-end
                     would also TRANSLATE it, and every second end would come
                     out the wrong length while the encoder measured perfectly.

                     hub -> clamp -> comb, cantilevered outboard off one cheek.
                     Two positions only, set by mechanical hard stops. -->
                <geom name="wrist_hub" type="mesh" mesh="wrist_mount_mesh"
                  pos="0 0 0" material="arm_mat"
                  contype="0" conaffinity="0"/>
                <!-- Sprung closed, air opens it: losing pressure fails to
                     GRIPPING rather than dropping a part mid-cycle. If the
                     ribbon creeps here the measured length is silently wrong,
                     which makes this the most critical printed part we have. -->
                <geom name="body_clamp" type="mesh" mesh="body_clamp_mesh"
                  pos="{float(L.WRIST_HUB_WIDTH) * MM:.6g} 0 0" material="clamp_mat"
                  contype="0" conaffinity="0"/>
                <!-- Comb: 3 channels at 8 mm pitch, guiding not clamping. -->
                <geom name="comb_body" type="mesh" mesh="comb_mesh"
                  pos="{(float(L.WRIST_HUB_WIDTH) + float(L.CLAMP_BODY_LEN)) * MM:.6g} 0 0"
                  material="comb_mat" contype="0" conaffinity="0"/>
                <!-- The work point: comb front face + the free tail. Past this
                     face it is ribbon, not machine — which is the whole reason
                     the arm can stop {float(L.TAIL_PROJECTION):.0f} mm short of the stations. -->
                <!-- What the camera INSPECTS. Not the work point: at S1 the
                     work point is inside the feed head's channel and cannot be
                     seen from anywhere, which is correct and not a defect. The
                     exposed tail between the comb's front face and the tooling
                     line is the thing a camera can actually verify. -->
                <site name="tail_mid"
                  pos="{(float(L.WRIST_HUB_WIDTH) + float(L.CLAMP_BODY_LEN) + float(L.COMB_LENGTH) + float(L.TAIL_PROJECTION) / 2) * MM:.6g} 0 0"
                  size="0.002" rgba="1 0.85 0.2 1"/>
                <site name="comb_tip"
                  pos="{(float(L.WRIST_HUB_WIDTH) + float(L.CLAMP_BODY_LEN) + float(L.COMB_LENGTH) + float(L.TAIL_PROJECTION)) * MM:.6g} 0 0"
                  size="0.003" rgba="0.2 1 0.4 1"/>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>
  </worldbody>

  <!-- BY-DESIGN pass-throughs. Declared, not silently tolerated: each of
       these is two solids that share space because that is the mechanism.
       The deck is drawn as a full disc because MuJoCo has no annulus
       primitive, but it really has a 7" centre hole - hence the first two. -->
  <contact>
    <exclude body1="deck_body" body2="z_carriage"/>
    <exclude body1="deck_body" body2="rotor"/>
    <exclude body1="frame_body" body2="z_carriage"/>
    <exclude body1="frame_body" body2="rotor"/>
    <exclude body1="post_body" body2="z_carriage"/>
  </contact>

  <equality>
{RIB.equalities()}
  </equality>

  <actuator>
    <position name="Z_act" joint="Z" kp="800" ctrlrange="0 {z_stroke * MM:.6g}"/>
    <position name="T_act" joint="T" kp="200"
      ctrlrange="0 {math.radians(float(L.SWEEP_ARC)):.6g}"/>
    <position name="R_act" joint="R" kp="400" ctrlrange="0 {float(L.ARM_STROKE) * MM:.6g}"/>
    <position name="S_act" joint="S" kp="200"
      ctrlrange="{-float(L.CROSS_SLIDE_STROKE) / 2 * MM:.6g} {float(L.CROSS_SLIDE_STROKE) / 2 * MM:.6g}"/>
    <position name="W_act" joint="W" kp="100" ctrlrange="0 {math.pi:.6g}"/>
  </actuator>
</mujoco>
"""


def write() -> pathlib.Path:
    failures = check_station_inner_radius()
    if failures:
        raise AssertionError(
            "station placement contradicts the layout:\n  " + "\n  ".join(failures)
        )
    ASSETS.mkdir(parents=True, exist_ok=True)
    MJCF_PATH.write_text(build_mjcf(), encoding="utf-8")
    return MJCF_PATH


MAKE_PATH = ASSETS / "cell.make.xml"

# How a part is made, by geom-name prefix. Checked in order; first match wins.
# Anything unmatched is a printed mesh, because that is what everything else in
# this machine is.
MAKE_RULES = (
    ("stock", ("frame_", "arm_beam", "mgn12_rail", "mgn9_rail", "z_post_", "z_leadscrew")),
    # NOT "spindle" — spindle_shaft is one of ours, printed. It was in this
    # list for one render and came out the colour of a bought part, which is
    # the exact confusion this palette exists to remove.
    ("bought", ("press_", "applicator", "z_motor", "mgn12_block")),
    ("sheet", ("deck",)),
    ("workpiece", ("rib_", "stock_")),
    ("marker", ("_tag", "_bin", "_pedestal")),
    ("scene", ("bench",)),
)

MAKE_MATERIALS = """
    <material name="make_stock" rgba="0.62 0.66 0.72 1"/>
    <material name="make_printed" rgba="0.90 0.42 0.20 1"/>
    <material name="make_sheet" rgba="0.76 0.62 0.42 1"/>
    <material name="make_bought" rgba="0.24 0.26 0.30 1"/>
    <material name="make_workpiece" rgba="0.95 0.85 0.15 1"/>
    <material name="make_marker" rgba="0.55 0.57 0.60 0.35"/>
    <material name="make_scene" rgba="0.30 0.32 0.36 1"/>"""


def _make_method(geom_name: str) -> str:
    for method, keys in MAKE_RULES:
        if any(k in geom_name for k in keys):
            return method
    return "printed"


def write_make() -> pathlib.Path:
    """The same scene coloured by HOW EACH PART IS MADE, not by what it does.

    Kyle 2026-07-27: "I want to understand if all these other housing/framing
    things are printed parts? the yellow part the orange part etc, those are all
    printed?"

    They are — and there was no way to tell by looking, because the display
    palette encodes FUNCTION. Station tooling is blue because it is tooling, the
    comb is yellow because it is the comb. Two parts made completely differently
    can be the same colour and two identical processes can be four colours.

    So this is a second palette over the same geometry: metal you cut, plastic
    you print, sheet you saw, parts you buy. Same scene, one question.
    """
    import re

    xml = build_mjcf()
    xml = xml.replace("</asset>", MAKE_MATERIALS + "\n  </asset>")

    def swap(m: re.Match) -> str:
        head, name, mid, _mat, tail = m.groups()
        return f'{head}{name}{mid}material="make_{_make_method(name)}"{tail}'

    xml = re.sub(
        r'(<geom name=")([^"]+)("[^>]*?)material="([^"]+)"([^>]*?/>)',
        swap, xml, flags=re.S,
    )
    ASSETS.mkdir(parents=True, exist_ok=True)
    MAKE_PATH.write_text(xml, encoding="utf-8")
    return MAKE_PATH


COLLIDE_PATH = ASSETS / "cell.collide.xml"


def write_collide() -> pathlib.Path:
    """The same scene with contacts ENABLED, for interference checking.

    Every geom in the display scene carries contype="0" conaffinity="0" so it
    renders fast and nothing ever pushes anything. That is fine for looking at
    and useless for telling the truth: bodies pass through each other in
    silence, which is how the arm came to sweep through the Z posts with three
    studies reporting clear.

    Rather than hand-rolling more radius arithmetic, flip the flags and let
    MuJoCo's own collision engine answer. It knows about every geom, not just
    the ones a study author remembered.
    """
    failures = check_station_inner_radius()
    if failures:
        raise AssertionError(
            "station placement contradicts the layout:\n  " + "\n  ".join(failures)
        )
    ASSETS.mkdir(parents=True, exist_ok=True)
    xml = build_mjcf().replace('contype="0" conaffinity="0"', 'contype="1" conaffinity="1"')
    COLLIDE_PATH.write_text(xml, encoding="utf-8")
    return COLLIDE_PATH


# Views as (azimuth, elevation, distance, lookat). Driven programmatically
# rather than as MJCF <camera xyaxes>, because hand-computing camera basis
# vectors is error-prone and gets silently-wrong renders rather than errors.
VIEWS: dict[str, tuple[float, float, float, tuple[float, float, float]]] = {
    "overview": (35.0, -24.0, 0.95, (0.0, 0.0, 0.16)),
    "plan": (90.0, -89.0, 0.80, (0.0, 0.0, 0.18)),
    "press_side": (135.0, -14.0, 0.62, (-0.12, 0.12, 0.22)),
    "arm_detail": (95.0, -14.0, 0.26, (0.185, 0.0, 0.247)),
    "s1_feed": (30.0, -18.0, 0.42, (0.245, 0.0, 0.265)),
}


def render(views: tuple[str, ...] | None = None) -> list[pathlib.Path]:
    """Offscreen render of each named view, for looking at without a viewer."""
    import mujoco

    names = tuple(VIEWS) if views is None else views

    model = mujoco.MjModel.from_xml_path(str(MJCF_PATH))
    data = mujoco.MjData(model)
    # Park the arm somewhere informative: extended toward S1, mid Z.
    data.qpos[:] = 0.0
    mujoco.mj_forward(model, data)

    out_dir = pathlib.Path(__file__).parent / "studies" / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)

    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE

    written: list[pathlib.Path] = []
    with mujoco.Renderer(model, height=1000, width=1600) as renderer:
        for name in names:
            azimuth, elevation, distance, lookat = VIEWS[name]
            cam.azimuth = azimuth
            cam.elevation = elevation
            cam.distance = distance
            cam.lookat[:] = lookat
            renderer.update_scene(data, camera=cam)
            pixels = renderer.render()
            path = out_dir / f"roughin_{name}.png"
            imaging.save_png(path, pixels)
            written.append(path)
    return written


def pedestal_heights() -> list[tuple[str, str, float]]:
    """Standoff each station part needs under it, in mm.

    These are real printed parts and they belong in the BOM. They exist because
    every station now meets the ribbon on ONE derived engagement plane, set by
    the tallest part anywhere on the dial (the guillotine). Every shorter part
    is packed up to that plane by a standoff.

    That is the deliberate trade behind minimum Z travel: the alternative —
    a height per station — would push the spread between stations into the Z
    stage, and stroke costs stiffness. Standoffs cost grams.

    The tallest part's standoff is 0 by construction. If any value here goes
    negative, a part is trying to sink through its own mount and the plane is
    wrong.
    """
    deck_top = float(L.DECK_ABOVE_BENCH) + float(L.DECK_THICKNESS)
    rows: list[tuple[str, str, float]] = []
    for name, parts in STATION_PARTS.items():
        engage_z = float(L.DECK_ABOVE_BENCH) + float(L.STATION_Z[name])
        for mesh, _r, _t, _rev, _e in parts:
            passage_h = float(L.STATION_PART_PASSAGE[mesh])
            rows.append((name, mesh, engage_z - passage_h - (deck_top + STATION_MOUNT_T)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="also render PNG views")
    args = parser.parse_args()

    path = write()
    print(f"wrote {path}")
    print(f"  deck        {float(L.DECK_ABOVE_BENCH):.0f} mm above bench")
    print(f"  bolt circle R0 = {float(L.ARM_R0):.0f} mm")
    print(f"  Z stroke    {L.z_stage_choice():.0f} mm (needs {L.z_travel_required():.0f})")
    print("  press       stashed for the prototype (still the deck datum)")

    rows = pedestal_heights()
    print("\n  station part standoffs (mm above the station mount):")
    for station, mesh, h in rows:
        flag = "  <-- NEGATIVE, part sinks into its mount" if h < 0 else ""
        print(f"    {station:<10} {mesh:<20}{h:7.1f}{flag}")
    print(f"  {len(rows)} standoffs, none costed. See pedestal_heights().")

    if args.render:
        for p in render():
            print(f"rendered {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
