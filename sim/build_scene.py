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

from sim import layout as L

MM = 0.001  # layout is in millimetres; MuJoCo works in metres

ASSETS = pathlib.Path(__file__).parent / "assets"
MJCF_PATH = ASSETS / "cell.generated.xml"

# Where the comb sits above the rotor base, so that Z qpos=0 puts it at the
# lowest station engagement height.
COMB_ABOVE_ROTOR = float(min(L.STATION_Z.values()))

# Station display bodies are centred outboard of their work point, so the inner
# face of the tooling lands on the bolt circle.
STATION_BODY_DEPTH = 70.0
STATION_BODY_HEIGHT = float(L.STATION_TOOLING_HEIGHT)


def _polar(radius: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return radius * math.cos(a), radius * math.sin(a)


def _fmt(*vals: float) -> str:
    return " ".join(f"{v:.6g}" for v in vals)


def _station_bodies() -> str:
    """Static station blocks on the deck, one per angular stop."""
    deck_top = float(L.DECK_ABOVE_BENCH) + float(L.DECK_THICKNESS)
    out: list[str] = []
    for name in L.STATIONS:
        if name == "S4_CRIMP":
            continue  # the press stands in for S4
        theta = float(L.STATION_ANGLES[name])
        r = float(L.ARM_R0) + STATION_BODY_DEPTH / 2.0
        x, y = _polar(r, theta)
        z = deck_top + STATION_BODY_HEIGHT / 2.0
        mat = "reject_mat" if name == "S6_REJECT" else "station_mat"
        out.append(
            f'    <geom name="{name.lower()}" type="box" '
            f'pos="{_fmt(x * MM, y * MM, z * MM)}" '
            f'size="{_fmt(STATION_BODY_DEPTH / 2 * MM, float(L.STATION_WIDTH) / 2 * MM, STATION_BODY_HEIGHT / 2 * MM)}" '
            f'euler="0 0 {math.radians(theta):.6g}" material="{mat}" '
            f'contype="0" conaffinity="0"/>'
        )
        # AprilTag facing the pivot — what the arm camera registers against.
        tx, ty = _polar(float(L.ARM_R0) - 3.0, theta)
        tz = deck_top + STATION_BODY_HEIGHT * 0.78
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

    return f"""    <!-- S4 CRIMP: the press. Placed first; everything else is derived from it. -->
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


Z_POST_RADIUS = 46.0  # posts sit on this circle around the pivot


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

    # Spool axis is tangential, so ribbon pays off radially toward the pivot.
    axis_euler = f"{math.pi / 2:.6g} 0 {math.radians(theta):.6g}"
    half_w = float(L.SPOOL_INNER_WIDTH) / 2.0
    fl = float(L.SPOOL_FLANGE_T)

    parts: list[str] = []
    parts.append(
        f'    <geom name="spool_hub" type="cylinder" pos="{_fmt(x * MM, y * MM, z * MM)}" '
        f'size="{_fmt(float(L.SPOOL_HUB_R) * MM, half_w * MM)}" euler="{axis_euler}" '
        f'material="spool_mat" contype="0" conaffinity="0"/>'
    )
    # Wound ribbon, shown at full stock.
    parts.append(
        f'    <geom name="spool_ribbon" type="cylinder" pos="{_fmt(x * MM, y * MM, z * MM)}" '
        f'size="{_fmt((float(L.SPOOL_FLANGE_R) - 4.0) * MM, (half_w - 1.0) * MM)}" '
        f'euler="{axis_euler}" material="ribbon_mat" contype="0" conaffinity="0"/>'
    )
    for sign, tag in ((1.0, "a"), (-1.0, "b")):
        ox, oy = _polar(r, theta)
        # offset along the spool axis (tangential direction)
        ax, ay = -math.sin(math.radians(theta)), math.cos(math.radians(theta))
        px = ox + ax * sign * (half_w + fl / 2.0)
        py = oy + ay * sign * (half_w + fl / 2.0)
        parts.append(
            f'    <geom name="spool_flange_{tag}" type="cylinder" '
            f'pos="{_fmt(px * MM, py * MM, z * MM)}" '
            f'size="{_fmt(float(L.SPOOL_FLANGE_R) * MM, fl / 2 * MM)}" euler="{axis_euler}" '
            f'material="spool_mat" contype="0" conaffinity="0"/>'
        )
    # Hanger upright carrying the 8 mm axle.
    hx, hy = _polar(r + 20.0, theta)
    parts.append(
        f'    <geom name="spool_hanger" type="box" '
        f'pos="{_fmt(hx * MM, hy * MM, (deck_top + float(L.SPOOL_AXLE_HEIGHT) / 2) * MM)}" '
        f'size="{_fmt(0.008, 0.030, float(L.SPOOL_AXLE_HEIGHT) / 2 * MM)}" '
        f'euler="0 0 {math.radians(theta):.6g}" material="hanger_mat" '
        f'contype="0" conaffinity="0"/>'
    )
    # Dancer arm — passive tension, and its flag is the spool-empty detect.
    dx, dy = _polar(r - 40.0, theta)
    parts.append(
        f'    <geom name="dancer_arm" type="capsule" '
        f'fromto="{_fmt(dx * MM, dy * MM, (deck_top + 40) * MM)} '
        f'{_fmt((dx - float(L.DANCER_ARM_LENGTH) * 0.7) * MM, dy * MM, (deck_top + 95) * MM)}" '
        f'size="0.005" material="hanger_mat" contype="0" conaffinity="0"/>'
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
  <compiler angle="radian" autolimits="true"/>
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
      <geom name="z_platform" type="cylinder" pos="0 0 0"
        size="{Z_POST_RADIUS * 1.45 * MM:.6g} 0.008"
        material="zstage_mat" contype="0" conaffinity="0"/>

      <body name="rotor" pos="0 0 0.018">
        <joint name="T" type="hinge" axis="0 0 1"
          range="{-math.radians(float(L.SWEEP_ARC)) / 2:.6g} {math.radians(float(L.SWEEP_ARC)) / 2:.6g}"
          damping="12"/>
        <geom name="main_bearing" type="cylinder" pos="0 0 0.012"
          size="{float(L.MAIN_BEARING_BORE) / 2 * MM:.6g} 0.012"
          material="rotor_mat" contype="0" conaffinity="0"/>

        <body name="arm" pos="0 0 {COMB_ABOVE_ROTOR * MM:.6g}">
          <geom name="arm_beam" type="box"
            pos="{arm_len / 2 * MM:.6g} 0 0"
            size="{arm_len / 2 * MM:.6g} {float(L.ARM_WIDTH) / 2 * MM:.6g} {float(L.ARM_THICKNESS) / 2 * MM:.6g}"
            material="arm_mat" contype="0" conaffinity="0"/>

          <body name="radial" pos="{r_retracted * MM:.6g} 0 0">
            <joint name="R" type="slide" axis="1 0 0"
              range="0 {float(L.ARM_STROKE) * MM:.6g}" damping="20"/>
            <geom name="radial_carriage" type="box" pos="0 0 0.014"
              size="0.020 0.028 0.010" material="arm_mat"
              contype="0" conaffinity="0"/>
            <!-- Arm camera. Rides the RADIAL carriage, deliberately NOT the
                 wrist — the wrist flips 180 degrees and the camera must not.
                 Looks radially outward and down at the station work point;
                 registers against each station's AprilTag. -->
            <geom name="arm_camera" type="box"
              pos="{-float(L.CAMERA_BACK_OFFSET) * MM:.6g} 0 {float(L.CAMERA_UP_OFFSET) * MM:.6g}"
              size="{_fmt(float(L.CAMERA_DEPTH) / 2 * MM, float(L.CAMERA_BOARD) / 2 * MM, float(L.CAMERA_BOARD) / 2 * MM)}"
              euler="0 {math.radians(float(L.CAMERA_TILT)):.6g} 0"
              material="camera_mat" contype="0" conaffinity="0"/>
            <camera name="arm_cam"
              pos="{-float(L.CAMERA_BACK_OFFSET) * MM:.6g} 0 {float(L.CAMERA_UP_OFFSET) * MM:.6g}"
              euler="0 {math.radians(90.0 + float(L.CAMERA_TILT)):.6g} {-math.pi / 2:.6g}"
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
                <!-- Comb: 3 channels at 8 mm pitch, guiding not clamping. -->
                <geom name="comb_body" type="box" pos="0.006 0 0"
                  size="0.010 {(float(L.COMB_PITCH) * 1.6) * MM:.6g} 0.006"
                  material="comb_mat" contype="0" conaffinity="0"/>
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
      ctrlrange="{-math.radians(float(L.SWEEP_ARC)) / 2:.6g} {math.radians(float(L.SWEEP_ARC)) / 2:.6g}"/>
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
    "arm_detail": (0.0, -18.0, 0.42, (0.16, 0.0, 0.24)),
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
            _write_png(path, pixels)
            written.append(path)
    return written


def _write_png(path: pathlib.Path, pixels) -> None:
    """Minimal PNG writer so we do not add an image dependency."""
    import struct
    import zlib

    height, width, _ = pixels.shape
    raw = bytearray()
    for row in range(height):
        raw.append(0)  # filter type 0
        raw.extend(pixels[row].tobytes())

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + chunk(b"IEND", b"")
    )


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

    if args.render:
        for p in render():
            print(f"rendered {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
