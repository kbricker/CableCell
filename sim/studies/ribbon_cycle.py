"""Watch the ribbon get fed, gripped, cut, carried and split.

Every machine operation here is a constraint being switched off. That is not a
simulation shortcut — it is the most honest description of what the tooling
does. The guillotine's whole job is to stop the workpiece being attached to the
stock; the wedge's whole job is to stop the conductors being attached to each
other.

    uv run python -m sim.studies.ribbon_cycle          # contact sheet
    uv run python -m sim.studies.ribbon_cycle --gif    # animation
"""

from __future__ import annotations

import argparse
import pathlib

import mujoco
import numpy as np

from sim import build_scene, imaging
from sim import layout as L
from sim import ribbon as RIB

OUT = pathlib.Path(__file__).parent / "renders"
VIEW = (34.0, -28.0, 0.30)  # azimuth, elevation, distance
# The camera FOLLOWS THE MATERIAL, not the machine. A 1.4 mm ribbon is
# ~3 px at any framing that shows the whole cell, so a fixed wide view
# renders a cycle in which the thing being made is invisible.
TRACK_BODY = "rib_1_3"


def eq(model, name: str) -> int:
    i = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_EQUALITY, name)
    if i < 0:
        raise KeyError(f"no equality {name!r} — the scene and the cycle disagree")
    return i


def stage_plan() -> list[tuple[str, str]]:
    """(label, what changes). Kept as data so the story is readable."""
    return [
        ("fed", "ribbon paid out through the feed head, one piece"),
        ("gripped", "body clamp closes on the ribbon body"),
        ("CUT", "guillotine: stock and workpiece stop being one thing"),
        ("carried", "arm lifts clear and indexes toward S2"),
        ("presented", "tail pushed onto the splitting wedge"),
        ("SPLIT", f"webs released over {float(L.SPLIT_LENGTH):.0f} mm — three conductors"),
    ]


def run(make_gif: bool = False) -> list[pathlib.Path]:
    build_scene.write()
    model = mujoco.MjModel.from_xml_path(str(build_scene.MJCF_PATH))
    data = mujoco.MjData(model)

    theta = model.actuator("T_act").id
    r_act = model.actuator("R_act").id
    z_act = model.actuator("Z_act").id

    cuts = [eq(model, f"cut_{i}") for i in range(RIB.CONDUCTORS)]
    grips = [eq(model, f"grip_{i}") for i in range(RIB.CONDUCTORS)]
    # Webs nearest the FREE END are the ones the wedge opens.
    split_n = RIB.split_segments()
    webs = [
        eq(model, f"web_{i}_{k}")
        for i in range(RIB.CONDUCTORS - 1)
        for k in range(RIB.TAIL_SEGMENTS - split_n, RIB.TAIL_SEGMENTS)
    ]

    s2 = np.radians(float(L.STATION_ANGLES["S2_SLIT"]))
    frames: list[np.ndarray] = []
    labels = stage_plan()

    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.azimuth, cam.elevation, cam.distance = VIEW
    track = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, TRACK_BODY)

    # NOT rendered from the arm's own camera, though that was the obvious idea:
    # the body clamp fills its entire field of view. See the occlusion finding
    # in docs/decisions.md — camera_check passes because it tests angle and
    # range, not whether anything is in the way.

    def aim() -> None:
        cam.lookat[:] = data.xpos[track]

    def settle(n: int, renderer, keep_every: int = 0) -> None:
        for step in range(n):
            mujoco.mj_step(model, data)
            if keep_every and step % keep_every == 0:
                aim(); renderer.update_scene(data, camera=cam)
                frames.append(renderer.render().copy())

    shots: list[np.ndarray] = []
    every = 12 if make_gif else 0

    with mujoco.Renderer(model, height=720, width=1120) as rnd:
        # 1. fed — everything joined, nothing gripped
        data.ctrl[r_act] = float(L.ARM_STROKE) * 0.001
        settle(240, rnd, every)
        aim(); rnd.update_scene(data, camera=cam); shots.append(rnd.render().copy())

        # 2. gripped
        for g in grips:
            data.eq_active[g] = 1
        settle(160, rnd, every)
        aim(); rnd.update_scene(data, camera=cam); shots.append(rnd.render().copy())

        # 3. CUT
        for c in cuts:
            data.eq_active[c] = 0
        settle(200, rnd, every)
        aim(); rnd.update_scene(data, camera=cam); shots.append(rnd.render().copy())

        # 4. carried — lift, index, descend
        data.ctrl[z_act] = 0.020
        data.ctrl[r_act] = 0.0
        settle(220, rnd, every)
        data.ctrl[theta] = s2
        settle(320, rnd, every)
        aim(); rnd.update_scene(data, camera=cam); shots.append(rnd.render().copy())

        # 5. presented
        data.ctrl[z_act] = 0.0
        data.ctrl[r_act] = float(L.ARM_STROKE) * 0.001
        settle(280, rnd, every)
        aim(); rnd.update_scene(data, camera=cam); shots.append(rnd.render().copy())

        # 6. SPLIT
        for w in webs:
            data.eq_active[w] = 0
        settle(320, rnd, every)
        aim(); rnd.update_scene(data, camera=cam); shots.append(rnd.render().copy())

    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    tiles = [(f"{n} — {d}", shot) for shot, (n, d) in zip(shots, labels)]
    written.append(imaging.contact_sheet(tiles, 2, OUT / "ribbon_cycle.png"))
    if make_gif and frames:
        written.append(imaging.save_gif(frames, OUT / "ribbon_cycle.gif", fps=22))
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gif", action="store_true")
    args = ap.parse_args()
    print(RIB.summary())
    print()
    for name, what in stage_plan():
        print(f"  {name:<12}{what}")
    print()
    for p in run(args.gif):
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
