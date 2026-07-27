"""Drive the arm through a station cycle — live, or as rendered frames.

    uv run python -m sim.run_cycle              # interactive viewer, loops
    uv run python -m sim.run_cycle --sheet      # contact sheet of key poses
    uv run python -m sim.run_cycle --frames 90  # numbered frames for a GIF

The motion is the real sequence the machine will run, minus the tooling: lift to
a rotation-safe height, index to the next station, descend to that station's
engagement Z, extend into it, dwell while the station does its work, retract,
lift, repeat.

That lift-rotate-descend pattern is the whole point of the base-mounted Z axis.
Without it, clearance during rotation has to come from radial retraction alone,
which forces every station's tooling to sit outside the bolt circle.
"""

from __future__ import annotations

import argparse
import math
import pathlib

import mujoco
import numpy as np

from sim import build_scene
from sim import layout as L

MM = 0.001

# Actuator order in the model.
ACTS = ("Z_act", "T_act", "R_act", "S_act", "W_act")


def _z_ctrl(z_above_deck_mm: float) -> float:
    """Z actuator value that puts the comb at a given height above the deck."""
    lowest = min(float(v) for v in L.STATION_Z.values())
    return max(0.0, (z_above_deck_mm - lowest)) * MM


def waypoints() -> list[tuple[str, dict[str, float], float]]:
    """(label, actuator targets, seconds) — one full sweep of the stations."""
    clear = _z_ctrl(L.z_clear())
    stroke = float(L.ARM_STROKE) * MM
    wp: list[tuple[str, dict[str, float], float]] = []

    for station in L.STATIONS:
        theta = math.radians(float(L.STATION_ANGLES[station]))
        z_here = _z_ctrl(float(L.STATION_Z[station]))
        short = station.replace("_", " ").lower()

        wp.append((f"lift clear of {short}", {"Z_act": clear, "R_act": 0.0}, 0.5))
        wp.append((f"index to {short}", {"T_act": theta}, 1.4))
        wp.append((f"descend into {short}", {"Z_act": z_here}, 0.5))
        wp.append((f"extend into {short}", {"R_act": stroke}, 0.7))

        if station in ("S2_SLIT", "S3_STRIP", "S5_INSERT"):
            # Cross-slide selects conductor 1/2/3 at these stations.
            for i, y in enumerate((-1.0, 0.0, 1.0)):
                wp.append(
                    (f"{short}: conductor {i + 1}",
                     {"S_act": y * float(L.CROSS_SLIDE_STROKE) / 2.0 * MM}, 0.4)
                )
        else:
            wp.append((f"{short}: dwell", {}, 0.5))

        wp.append((f"retract from {short}", {"R_act": 0.0, "S_act": 0.0}, 0.6))

        if station == "S1_FEED":
            # The wrist flip happens once per cable, after the cut.
            wp.append(("wrist flip 180", {"W_act": math.pi}, 0.9))
            wp.append(("wrist back", {"W_act": 0.0}, 0.9))

    wp.append(("return to S1", {"Z_act": clear, "T_act": 0.0}, 1.6))
    return wp


def _act_ids(model: mujoco.MjModel) -> dict[str, int]:
    return {
        name: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
        for name in ACTS
    }


def _smooth(t: float) -> float:
    """Ease in/out so moves look like a machine rather than a teleport."""
    return t * t * (3.0 - 2.0 * t)


def play(model, data, on_frame=None, realtime: bool = True) -> None:
    """Run one pass of the cycle, calling on_frame(label, progress) per step."""
    ids = _act_ids(model)
    dt = model.opt.timestep
    current = {name: float(data.ctrl[i]) for name, i in ids.items()}

    for label, targets, seconds in waypoints():
        start = dict(current)
        steps = max(1, int(seconds / dt))
        for s in range(steps):
            f = _smooth((s + 1) / steps)
            for name, target in targets.items():
                data.ctrl[ids[name]] = start[name] + (target - start[name]) * f
            mujoco.mj_step(model, data)
            if on_frame is not None:
                on_frame(label, (s + 1) / steps)
        current.update(targets)


def contact_sheet(cols: int = 3, rows: int = 3) -> pathlib.Path:
    """Tile key poses into one image — the cycle at a glance."""
    model = mujoco.MjModel.from_xml_path(str(build_scene.MJCF_PATH))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    wps = waypoints()
    want = cols * rows
    picks = [wps[round(i * (len(wps) - 1) / (want - 1))] for i in range(want)]

    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    # Tighter than the overview — the arm is the subject here, not the bench.
    cam.azimuth, cam.elevation, cam.distance = 38.0, -27.0, 0.70
    cam.lookat[:] = (0.0, 0.0, 0.215)

    cell_w, cell_h = 640, 400
    sheet = np.zeros((cell_h * rows, cell_w * cols, 3), dtype=np.uint8)

    ids = _act_ids(model)
    with mujoco.Renderer(model, height=cell_h, width=cell_w) as renderer:
        for idx, (label, targets, _sec) in enumerate(picks):
            # Jump straight to this waypoint's pose.
            for name, target in targets.items():
                data.ctrl[ids[name]] = target
            for _ in range(400):
                mujoco.mj_step(model, data)
            renderer.update_scene(data, camera=cam)
            frame = renderer.render()
            r, c = divmod(idx, cols)
            sheet[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w] = frame
            print(f"  {idx + 1}/{want}  {label}")

    out = pathlib.Path(__file__).parent / "studies" / "renders" / "cycle_sheet.png"
    build_scene._write_png(out, sheet)
    return out


def frames(count: int) -> pathlib.Path:
    """Numbered frames across the cycle, for assembling into a GIF."""
    model = mujoco.MjModel.from_xml_path(str(build_scene.MJCF_PATH))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    out = pathlib.Path(__file__).parent / "studies" / "renders" / "cycle"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()

    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    az, el, dist, lookat = build_scene.VIEWS["overview"]
    cam.azimuth, cam.elevation, cam.distance = az, el, dist
    cam.lookat[:] = lookat

    total_steps = sum(max(1, int(s / model.opt.timestep)) for _, _, s in waypoints())
    every = max(1, total_steps // count)
    state = {"i": 0, "n": 0}

    with mujoco.Renderer(model, height=720, width=1152) as renderer:
        def on_frame(label: str, _p: float) -> None:
            if state["i"] % every == 0 and state["n"] < count:
                renderer.update_scene(data, camera=cam)
                build_scene._write_png(out / f"f{state['n']:04d}.png", renderer.render())
                state["n"] += 1
            state["i"] += 1

        play(model, data, on_frame=on_frame)

    print(f"{state['n']} frames -> {out}")
    return out


def viewer() -> None:
    import mujoco.viewer

    path = build_scene.write()
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)

    print(f"CableCell cycle — R0 {float(L.ARM_R0):.0f} mm, "
          f"{len(L.STATIONS)} stops, Z stroke {L.z_stage_choice():.0f} mm")
    print("Looping. Ctrl-C or close the window to stop.\n")

    with mujoco.viewer.launch_passive(model, data) as v:
        last = {"label": ""}

        def on_frame(label: str, _p: float) -> None:
            if label != last["label"]:
                print(f"  {label}")
                last["label"] = label
            v.sync()

        while v.is_running():
            play(model, data, on_frame=on_frame)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", action="store_true", help="contact sheet of key poses")
    parser.add_argument("--frames", type=int, default=0, help="write N frames for a GIF")
    args = parser.parse_args()

    if args.sheet:
        print("rendering contact sheet ...")
        print(f"wrote {contact_sheet()}")
    elif args.frames:
        frames(args.frames)
    else:
        viewer()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
