"""Does the arm camera actually frame each station's AprilTag?

The arm-mounted camera has two jobs: verify a station is ready / an operation
happened, and register against that station's tag so actual pose can be compared
to commanded. Neither works if the tag is out of frame, too far, or viewed at a
grazing angle.

This study drives the arm to each stop and answers, per station:

    in frame?      is the tag inside the camera's FOV at all
    range          camera to tag, mm
    off-axis       how far from the optical centre, degrees
    obliquity      viewing angle onto the tag face, degrees

Obliquity is the one people forget. AprilTag pose degrades sharply past ~60°
off-normal because the tag's projected area collapses and corner localisation
gets noisy. A tag you can *see* is not necessarily a tag you can *measure*.

Run:  uv run python -m sim.studies.camera_check
      uv run python -m sim.studies.camera_check --render
"""

from __future__ import annotations

import argparse
import math
import pathlib
import sys

import mujoco
import numpy as np

from sim import build_scene
from sim import layout as L

# Practical limits, not hard physics.
MAX_OBLIQUITY_DEG = 60.0   # past this, tag pose estimation degrades badly
MIN_RANGE_MM = 60.0        # closer than this and a 3.6 mm lens will not focus
MAX_RANGE_MM = 400.0       # further and a 25 mm tag is too few pixels


def _station_qpos(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> None:
    """Pose the arm at a station: rotate to theta, lift to Z, extend R."""
    theta = math.radians(float(L.STATION_ANGLES[name]))
    z_mm = float(L.STATION_Z[name]) - min(float(v) for v in L.STATION_Z.values())

    for joint, value in (("T", theta), ("Z", z_mm * 0.001), ("R", float(L.ARM_STROKE) * 0.001)):
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint)
        adr = model.jnt_qposadr[jid]
        lo, hi = model.jnt_range[jid]
        data.qpos[adr] = min(max(value, lo), hi)
    mujoco.mj_forward(model, data)


def _tag_geom_name(station: str) -> str:
    return f"{station.lower()}_tag"


def check() -> list[dict]:
    model = mujoco.MjModel.from_xml_path(str(build_scene.MJCF_PATH))
    data = mujoco.MjData(model)

    cam_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "arm_cam")
    if cam_id < 0:
        raise SystemExit("arm_cam not found in the scene")

    fovy = float(model.cam_fovy[cam_id])
    half_v = math.radians(fovy) / 2.0
    aspect = 1600.0 / 1000.0
    half_h = math.atan(math.tan(half_v) * aspect)

    rows: list[dict] = []
    for station in L.STATIONS:
        if station == "S4_CRIMP":
            continue  # the press stands in for S4; no tag plate yet

        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, _tag_geom_name(station))
        if gid < 0:
            continue

        _station_qpos(model, data, station)

        cam_pos = np.array(data.cam_xpos[cam_id])
        cam_mat = np.array(data.cam_xmat[cam_id]).reshape(3, 3)
        tag_pos = np.array(data.geom_xpos[gid])
        tag_mat = np.array(data.geom_xmat[gid]).reshape(3, 3)

        # Into camera frame. MuJoCo cameras look down their own -z.
        v = tag_pos - cam_pos
        local = cam_mat.T @ v
        depth = -local[2]

        if depth <= 0:
            rows.append({"station": station, "in_frame": False, "reason": "behind camera"})
            continue

        ang_h = math.atan2(local[0], depth)
        ang_v = math.atan2(local[1], depth)
        in_frame = abs(ang_h) <= half_h and abs(ang_v) <= half_v

        # The tag plate is a thin box; its local x is the face normal.
        normal = tag_mat[:, 0]
        to_cam = cam_pos - tag_pos
        to_cam /= np.linalg.norm(to_cam)
        obliquity = math.degrees(math.acos(min(1.0, abs(float(normal @ to_cam)))))

        rows.append(
            {
                "station": station,
                "in_frame": in_frame,
                "range_mm": float(np.linalg.norm(v)) * 1000.0,
                "off_axis_deg": math.degrees(math.hypot(ang_h, ang_v)),
                "obliquity_deg": obliquity,
                "half_h_deg": math.degrees(half_h),
                "half_v_deg": math.degrees(half_v),
            }
        )
    return rows


def render_views() -> list[pathlib.Path]:
    """Render what the arm camera sees at each stop."""
    model = mujoco.MjModel.from_xml_path(str(build_scene.MJCF_PATH))
    data = mujoco.MjData(model)
    out = pathlib.Path(__file__).parent / "renders" / "arm_cam"
    out.mkdir(parents=True, exist_ok=True)

    written: list[pathlib.Path] = []
    with mujoco.Renderer(model, height=600, width=960) as renderer:
        for station in L.STATIONS:
            if station == "S4_CRIMP":
                continue
            _station_qpos(model, data, station)
            renderer.update_scene(data, camera="arm_cam")
            path = out / f"{station.lower()}.png"
            build_scene._write_png(path, renderer.render())
            written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="also render each view")
    args = parser.parse_args()

    rows = check()
    if not rows:
        print("no tagged stations found")
        return 1

    first = next(r for r in rows if "half_h_deg" in r)
    print("Arm camera — station tag framing")
    print("=" * 74)
    print(f"FOV half-angles: {first['half_h_deg']:.1f}° horizontal, "
          f"{first['half_v_deg']:.1f}° vertical\n")
    print(f"{'station':<12} {'in frame':>9} {'range mm':>10} {'off-axis':>10} "
          f"{'obliquity':>11}  verdict")
    print("-" * 74)

    problems = 0
    for r in rows:
        if not r.get("in_frame"):
            print(f"{r['station']:<12} {'NO':>9}  {r.get('reason', 'outside FOV')}")
            problems += 1
            continue

        issues = []
        if r["obliquity_deg"] > MAX_OBLIQUITY_DEG:
            issues.append("too oblique")
        if r["range_mm"] < MIN_RANGE_MM:
            issues.append("too close")
        if r["range_mm"] > MAX_RANGE_MM:
            issues.append("too far")
        verdict = ", ".join(issues) if issues else "ok"
        if issues:
            problems += 1

        print(f"{r['station']:<12} {'yes':>9} {r['range_mm']:>10.0f} "
              f"{r['off_axis_deg']:>9.1f}° {r['obliquity_deg']:>10.1f}°  {verdict}")

    print()
    print(f"limits: obliquity < {MAX_OBLIQUITY_DEG:.0f}°, "
          f"range {MIN_RANGE_MM:.0f}–{MAX_RANGE_MM:.0f} mm")
    if problems:
        print(f"\n{problems} station(s) need the camera mount reworked — "
              "adjust CAMERA_BACK_OFFSET / CAMERA_UP_OFFSET / CAMERA_TILT.")

    if args.render:
        for p in render_views():
            print(f"rendered {p}")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
