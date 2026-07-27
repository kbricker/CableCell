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

MM = 0.001  # layout is in millimetres; MuJoCo works in metres

ASSETS = pathlib.Path(__file__).parent / "assets"
MJCF_PATH = ASSETS / "cell.generated.xml"

# Fixed stack heights between the Z carriage and the arm.
Z_CARRIAGE_T = 18.0   # platform half-thickness + rotor seat
ROTOR_SEAT_T = 18.0

# Where the comb sits above the rotor base, so that Z qpos=0 puts it at the
# LOWEST station engagement height measured from the DECK (Datum A).
#
# This was previously just min(STATION_Z), which silently ignored the carriage
# and rotor stack underneath — putting the comb 28 mm above where every station
# expects to meet the ribbon. Derive it instead.
_DECK_TOP = float(L.DECK_ABOVE_BENCH) + float(L.DECK_THICKNESS)
_ROTOR_BASE = _DECK_TOP + ROTOR_SEAT_T
COMB_ABOVE_ROTOR = (
    float(L.DECK_ABOVE_BENCH) + min(float(v) for v in L.STATION_Z.values()) - _ROTOR_BASE
)

# Station display bodies are centred outboard of their work point, so the inner
# face of the tooling lands on the bolt circle.
STATION_BODY_DEPTH = 70.0
STATION_BODY_HEIGHT = float(L.STATION_TOOLING_HEIGHT)


def _polar(radius: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return radius * math.cos(a), radius * math.sin(a)


def _fmt(*vals: float) -> str:
    return " ".join(f"{v:.6g}" for v in vals)


# Every printed part that build_parts.py produces, available as a mesh.
MESHES = (
    "comb", "spool", "spool_hanger", "dancer_arm", "guide_tube_mount",
    "measuring_wheel", "splitting_wedge", "spreader_plate", "z_platform",
    "spindle_shaft", "radial_carriage", "wrist_mount", "camera_mount",
    "drive_roller_block", "guillotine_holder", "station_mount",
)


def _mesh_assets() -> str:
    """Real CAD geometry from cad/build_parts.py.

    Same layout.py dimensions drive both the printed part and the sim, so they
    cannot disagree. STL is in millimetres; MuJoCo is in metres.
    """
    return "\n".join(
        f'    <mesh name="{n}_mesh" file="{n}.stl" scale="0.001 0.001 0.001"/>'
        for n in MESHES
    )


# Where the station mount sits. Its tag ledge is at part x = -38, and the tag
# must land just inboard of the bolt circle, so the mount centre goes 35 mm
# outboard of R0.
STATION_MOUNT_R = float(L.ARM_R0) + 35.0
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
    "S1_FEED": (
        ("drive_roller_block", 78.0, 0.0, True, None),
        ("measuring_wheel", 56.0, 0.0, False, "1.5708 0 {t}"),
        ("guide_tube_mount", 30.0, 0.0, True, None),
        ("guillotine_holder", 8.0, 0.0, True, None),
    ),
    "S2_SLIT": (
        ("splitting_wedge", 30.0, 0.0, True, None),
        ("spreader_plate", 2.0, 0.0, True, None),
    ),
}

# Stops with no modelled tooling yet. These stay grey ON PURPOSE and say why —
# a detailed guess is worse than an obvious blank.
UNMODELLED = {
    "S3_STRIP": "V-blade die geometry undecided",
    "S5_INSERT": "out of Phase 1 scope",
    "S6_DROP": "chute not designed",
    "S6_REJECT": "chute not designed",
}


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
            mat = "reject_mat" if name == "S6_REJECT" else "unknown_mat"
            out.append(
                f'    <!-- {name}: greybox - {UNMODELLED[name]} -->\n'
                f'    <geom name="{name.lower()}" type="box" '
                f'pos="{_fmt(x * MM, y * MM, z * MM)}" '
                f'size="{_fmt(STATION_BODY_DEPTH / 2 * MM, float(L.STATION_WIDTH) / 2 * MM, STATION_BODY_HEIGHT / 2 * MM)}" '
                f'euler="0 0 {rot:.6g}" material="{mat}" '
                f'contype="0" conaffinity="0"/>'
            )
        # AprilTag facing the pivot — what the arm camera registers against.
        tx, ty = _polar(float(L.ARM_R0) - 3.0, theta)
        tz = float(L.DECK_ABOVE_BENCH) + float(L.STATION_Z[name]) + 10.0
        out.append(
            f'    <geom name="{name.lower()}_tag" type="box" '
            f'pos="{_fmt(tx * MM, ty * MM, tz * MM)}" '
            f'size="{_fmt(0.0015, float(L.STATION_TAG_SIZE) / 2 * MM, float(L.STATION_TAG_SIZE) / 2 * MM)}" '
            f'euler="0 0 {math.radians(theta):.6g}" material="tag_mat" '
            f'contype="0" conaffinity="0"/>'
        )
        # A short marker at the actual work point on the bolt circle.
        wx, wy = _polar(float(L.ARM_R0), theta)
        out.append(
            f'    <site name="{name.lower()}_wp" '
            f'pos="{_fmt(wx * MM, wy * MM, (deck_top + COMB_ABOVE_ROTOR) * MM)}" '
            f'size="0.004" rgba="1 0.85 0.2 1"/>'
        )
    return "\n".join(out)


def _press_body() -> str:
    """The press — placed first, because it is the layout datum."""
    theta = float(L.STATION_ANGLES["S4_CRIMP"])
    d = L.press_centre_distance()
    cx, cy = _polar(d, theta)
    rot = math.radians(theta)

    # Column occupies the rear portion of the footprint; the throat is open
    # toward the dial so the arm can enter it.
    col_depth = float(L.PRESS_DEPTH) * 0.45
    col_offset = float(L.PRESS_DEPTH) / 2.0 - col_depth / 2.0  # toward the rear
    ox, oy = _polar(d + col_offset, theta)

    plate_z = float(L.PRESS_BASEPLATE_ABOVE_BENCH)
    crimp_z = float(L.CRIMP_POINT_ABOVE_BENCH)

    # Applicator sits on the base plate, under the ram, its long axis radial.
    ax, ay = _polar(float(L.ARM_R0) + float(L.APPLICATOR_LENGTH) / 2.0 - 40.0, theta)

    return f"""    <!-- S4 CRIMP: the press. Placed first; everything else is derived from it.

         THIS ONE STAYS A BOX ON PURPOSE (Kyle 2026-07-27, "sure press is still
         a box"). We have footprint, height and weight from the vendor and
         nothing else - ram-axis depth and base-plate height are unmeasured.
         Drawing a detailed press would be INVENTING detail, and
         detailed-but-wrong is worse than obviously-blank. Greybox where we are
         ignorant is honest; greybox where the part is already designed is just
         undone work. Every other station here is real geometry. -->
    <geom name="press_base" type="box"
      pos="{_fmt(cx * MM, cy * MM, 0.030)}"
      size="{_fmt(float(L.PRESS_DEPTH) / 2 * MM, float(L.PRESS_WIDTH) / 2 * MM, 0.030)}"
      euler="0 0 {rot:.6g}" material="press_mat" contype="0" conaffinity="0"/>
    <geom name="press_column" type="box"
      pos="{_fmt(ox * MM, oy * MM, float(L.PRESS_HEIGHT) / 2 * MM)}"
      size="{_fmt(col_depth / 2 * MM, float(L.PRESS_WIDTH) / 2 * MM, float(L.PRESS_HEIGHT) / 2 * MM)}"
      euler="0 0 {rot:.6g}" material="press_mat" contype="0" conaffinity="0"/>
    <geom name="press_baseplate" type="box"
      pos="{_fmt(cx * MM, cy * MM, plate_z * MM)}"
      size="{_fmt(float(L.PRESS_DEPTH) / 2 * MM, float(L.PRESS_WIDTH) / 2 * MM, 0.008)}"
      euler="0 0 {rot:.6g}" material="press_plate_mat" contype="0" conaffinity="0"/>
    <geom name="applicator" type="box"
      pos="{_fmt(ax * MM, ay * MM, (plate_z + float(L.APPLICATOR_HEIGHT) / 2) * MM)}"
      size="{_fmt(float(L.APPLICATOR_LENGTH) / 2 * MM, float(L.APPLICATOR_WIDTH) / 2 * MM, float(L.APPLICATOR_HEIGHT) / 2 * MM)}"
      euler="0 0 {rot:.6g}" material="applicator_mat" contype="0" conaffinity="0"/>
    <site name="crimp_point" pos="{_fmt(*[v * MM for v in _polar(float(L.ARM_R0), theta)], crimp_z * MM)}"
      size="0.006" rgba="1 0.25 0.2 1"/>"""


# Posts sit on this circle around the pivot. From layout.py — nothing in this
# file may hard-code a dimension.
Z_POST_RADIUS = float(L.Z_POST_CIRCLE_R)


def _z_posts(deck_top: float, z_stroke: float) -> str:
    """Three guide posts plus one off-axis leadscrew.

    A single coaxial rail cannot work — the rotary axis needs the space the
    rail wants. Moving the screw off-axis and guiding on posts leaves the
    platform centre clear.
    """
    top = deck_top + z_stroke + 30.0
    parts: list[str] = []
    for i, angle in enumerate((90.0, 210.0, 330.0)):
        px, py = _polar(Z_POST_RADIUS, angle)
        parts.append(
            f'    <geom name="z_post_{i}" type="cylinder" '
            f'pos="{_fmt(px * MM, py * MM, (deck_top + (top - deck_top) / 2) * MM)}" '
            f'size="0.004 {(top - deck_top) / 2 * MM:.6g}" '
            f'material="zstage_mat" contype="0" conaffinity="0"/>'
        )
    sx, sy = _polar(Z_POST_RADIUS, 270.0)
    parts.append(
        f'    <geom name="z_leadscrew" type="cylinder" '
        f'pos="{_fmt(sx * MM, sy * MM, (deck_top + (top - deck_top) / 2) * MM)}" '
        f'size="0.005 {(top - deck_top) / 2 * MM:.6g}" '
        f'material="screw_mat" contype="0" conaffinity="0"/>'
    )
    parts.append(
        f'    <geom name="z_motor" type="box" '
        f'pos="{_fmt(sx * MM, sy * MM, (deck_top - 22) * MM)}" '
        f'size="0.021 0.021 0.020" material="motor_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    return "\n".join(parts)


def _spool_and_hanger() -> str:
    """S1's printed spool + hanger, off-deck outboard of station 1.

    The ribbon ships as a loose roll, so the spool is our design: 8 mm bore to
    match the Z-stage rod stock, sized to take a whole 50 ft roll.
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
    dx, dy = _polar(r - 46.0, theta)
    parts.append(
        f'    <geom name="dancer_arm" type="mesh" mesh="dancer_arm_mesh" '
        f'pos="{_fmt(dx * MM, dy * MM, (deck_top + 70.0) * MM)}" '
        f'euler="0 0 {rot + math.pi:.6g}" material="hanger_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    return "\n".join(parts)


def build_mjcf() -> str:
    deck_z = float(L.DECK_ABOVE_BENCH)
    deck_top = deck_z + float(L.DECK_THICKNESS)
    z_stroke = L.z_stage_choice()
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
    <material name="unknown_mat" rgba="0.52 0.52 0.54 0.55"/>
    <material name="zstage_mat" rgba="0.35 0.55 0.42 1"/>
    <material name="rotor_mat" rgba="0.50 0.50 0.55 1"/>
    <material name="arm_mat" rgba="0.72 0.74 0.78 1"/>
    <material name="comb_mat" rgba="0.90 0.85 0.30 1"/>
    <material name="spool_mat" rgba="0.85 0.86 0.88 1"/>
    <material name="ribbon_mat" rgba="0.20 0.20 0.22 1"/>
    <material name="hanger_mat" rgba="0.45 0.48 0.52 1"/>
    <material name="camera_mat" rgba="0.15 0.15 0.17 1"/>
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
    <geom name="deck" type="cylinder"
      pos="0 0 {(deck_z + float(L.DECK_THICKNESS) / 2) * MM:.6g}"
      size="{float(L.DECK_RADIUS) * MM:.6g} {float(L.DECK_THICKNESS) / 2 * MM:.6g}"
      material="deck_mat" contype="0" conaffinity="0"/>
    <geom name="frame_ring" type="cylinder"
      pos="0 0 {deck_z / 2 * MM:.6g}"
      size="{(float(L.DECK_RADIUS) - 40) * MM:.6g} {deck_z / 2 * MM:.6g}"
      material="frame_mat" rgba="0.42 0.45 0.50 0.25" contype="0" conaffinity="0"/>

{_station_bodies()}

    <!-- S1's spool + hanger + dancer, off-deck outboard of station 1. -->
{_spool_and_hanger()}

    <!-- Z stage: platform on three guide posts, driven by ONE OFF-AXIS
         leadscrew. The off-axis screw is the whole trick — it leaves the
         rotary axis at the platform centre unobstructed, which a single
         coaxial rail cannot do. T8 trapezoidal, so it self-locks and an
         E-stop will not drop the arm. -->
{_z_posts(deck_top, z_stroke)}

    <!-- ============ the moving assembly ============ -->
    <body name="z_carriage" pos="0 0 {deck_top * MM:.6g}">
      <joint name="Z" type="slide" axis="0 0 1" range="0 {z_stroke * MM:.6g}"
        damping="40"/>
      <geom name="z_platform" type="mesh" mesh="z_platform_mesh" pos="0 0 0"
        material="zstage_mat" contype="0" conaffinity="0"/>

      <body name="rotor" pos="0 0 0.018">
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

        <body name="arm" pos="0 0 {COMB_ABOVE_ROTOR * MM:.6g}">
          <geom name="arm_beam" type="box"
            pos="{arm_len / 2 * MM:.6g} 0 0"
            size="{arm_len / 2 * MM:.6g} {float(L.ARM_WIDTH) / 2 * MM:.6g} {float(L.ARM_THICKNESS) / 2 * MM:.6g}"
            material="arm_mat" contype="0" conaffinity="0"/>

          <body name="radial" pos="{r_retracted * MM:.6g} 0 0">
            <joint name="R" type="slide" axis="1 0 0"
              range="0 {float(L.ARM_STROKE) * MM:.6g}" damping="20"/>
            <geom name="radial_carriage" type="mesh" mesh="radial_carriage_mesh"
              pos="0 0 0.004" material="arm_mat"
              contype="0" conaffinity="0"/>
            <!-- Arm camera. Rides the RADIAL carriage, deliberately NOT the
                 wrist — the wrist flips 180 degrees and the camera must not.
                 Looks radially outward and down at the station work point;
                 registers against each station's AprilTag. -->
            <geom name="arm_camera" type="mesh" mesh="camera_mount_mesh"
              pos="{-float(L.CAMERA_BACK_OFFSET) * MM:.6g} 0 {float(L.CAMERA_UP_OFFSET) * MM:.6g}"
              euler="0 {math.radians(float(L.CAMERA_TILT)):.6g} 0"
              material="camera_mat" contype="0" conaffinity="0"/>
            <camera name="arm_cam"
              pos="{-float(L.CAMERA_BACK_OFFSET) * MM:.6g} 0 {float(L.CAMERA_UP_OFFSET) * MM:.6g}"
              euler="0 {math.radians(float(L.CAMERA_TILT) - 90.0):.6g} 0"
              fovy="48"/>

            <body name="cross" pos="0 0 0">
              <joint name="S" type="slide" axis="0 1 0"
                range="{-float(L.CROSS_SLIDE_STROKE) / 2 * MM:.6g} {float(L.CROSS_SLIDE_STROKE) / 2 * MM:.6g}"
                damping="8"/>
              <geom name="cross_carriage" type="box" pos="0 0 0"
                size="0.012 0.016 0.007" material="arm_mat"
                contype="0" conaffinity="0"/>

              <body name="wrist" pos="0 0 0">
                <joint name="W" type="hinge" axis="1 0 0" range="0 {math.pi:.6g}"
                  damping="6"/>
                <!-- Wrist hub. Two positions only, set by mechanical hard
                     stops; the motor just has to reach them. Hub axis is
                     radial, so the cable turns end-for-end. -->
                <geom name="wrist_hub" type="mesh" mesh="wrist_mount_mesh"
                  pos="-0.014 0 -0.009" material="arm_mat"
                  contype="0" conaffinity="0"/>
                <!-- Comb: 3 channels at 8 mm pitch, guiding not clamping. -->
                <geom name="comb_body" type="mesh" mesh="comb_mesh"
                  pos="-0.004 0 -0.006" material="comb_mat"
                  contype="0" conaffinity="0"/>
                <site name="comb_tip" pos="{float(L.TAIL_PROJECTION) * MM:.6g} 0 0"
                  size="0.003" rgba="0.2 1 0.4 1"/>
              </body>
            </body>
          </body>
        </body>
      </body>
    </body>
  </worldbody>

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
    ASSETS.mkdir(parents=True, exist_ok=True)
    MJCF_PATH.write_text(build_mjcf(), encoding="utf-8")
    return MJCF_PATH


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
    print(f"  press at    theta {float(L.STATION_ANGLES['S4_CRIMP']):.0f} deg, "
          f"{L.press_centre_distance():.0f} mm from pivot")

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
