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
VIEW = (34.0, -34.0, 0.26)  # azimuth, elevation, distance
# The camera FOLLOWS THE MATERIAL, not the machine. A 1.4 mm ribbon is
# ~3 px at any framing that shows the whole cell, so a fixed wide view
# renders a cycle in which the thing being made is invisible.
#
# TWO SHEETS, WITH DIFFERENT JOBS. Chasing one framing that showed both the
# machine and a 1.4 mm strand was the mistake: 300 mm made the ribbon a few
# pixels, 120 mm filled the frame with the station tooling that was standing in
# front of it, and a steeper angle put the camera under the deck.
#
#   ribbon_cycle.png         this free view — context, where the arm is
#   ribbon_cycle_armcam.png  the ARM'S OWN CAMERA — the material, close
#
# The arm cam is the better sheet and it costs nothing, because the machine has
# to be able to see its own work anyway. If the ribbon is not legible there, the
# machine cannot verify its own steps, so that sheet is an acceptance test and
# not just a picture.
#
# What made either of them work was colour, not framing: each conductor carries
# its real black/red/white material now. Three joined conductors and three split
# ones look identical in a single grey, so the SPLIT stage was unreadable no
# matter how close the camera got.
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
    # THE COLLIDE SCENE, not the display one. This ran against the display
    # scene, where every geom carries contype="0" — so the cut workpiece fell
    # straight THROUGH the deck and the last three stages framed the underside
    # of a piece of plywood. A cycle rendered with contacts off is a cycle in
    # which the material can be anywhere.
    #
    # It is also the point of the whole exercise: the ribbon is the one thing in
    # this scene that is supposed to touch everything.
    build_scene.write()
    model = mujoco.MjModel.from_xml_path(str(build_scene.write_collide()))
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

    # A SECOND PANEL FROM THE ARM'S OWN CAMERA. This used to say the arm camera
    # was unusable because the body clamp filled its field of view — true when
    # written, and no longer: the camera has been re-sited and camera_check now
    # casts rays to prove the tag AND the tail are unobstructed at every stop.
    # The operator's view of a cycle is the one the machine will actually judge
    # itself by, so it belongs in the contact sheet.

    def aim() -> None:
        cam.lookat[:] = data.xpos[track]

    def settle(n: int, renderer, keep_every: int = 0) -> None:
        for step in range(n):
            mujoco.mj_step(model, data)
            if keep_every and step % keep_every == 0:
                aim(); renderer.update_scene(data, camera=cam)
                frames.append(renderer.render().copy())

    shots: list[np.ndarray] = []
    arm_shots: list[np.ndarray] = []
    every = 12 if make_gif else 0

    def snap(renderer) -> None:
        """Both views of the same instant: the material, and what the machine
        will actually be looking at when it judges this step."""
        aim()
        renderer.update_scene(data, camera=cam)
        shots.append(renderer.render().copy())
        renderer.update_scene(data, camera="arm_cam")
        arm_shots.append(renderer.render().copy())

    with mujoco.Renderer(model, height=720, width=1120) as rnd:
        # 1. fed — everything joined, nothing gripped
        data.ctrl[r_act] = float(L.ARM_STROKE) * 0.001
        settle(240, rnd, every)
        snap(rnd)

        # 2. gripped
        for g in grips:
            data.eq_active[g] = 1
        settle(160, rnd, every)
        snap(rnd)

        # 3. CUT
        for c in cuts:
            data.eq_active[c] = 0
        settle(200, rnd, every)
        snap(rnd)

        # 4. carried — lift, index, descend
        data.ctrl[z_act] = 0.020
        data.ctrl[r_act] = 0.0
        settle(220, rnd, every)
        data.ctrl[theta] = s2
        settle(320, rnd, every)
        snap(rnd)

        # 5. presented
        data.ctrl[z_act] = 0.0
        data.ctrl[r_act] = float(L.ARM_STROKE) * 0.001
        settle(280, rnd, every)
        snap(rnd)

        # 6. SPLIT
        for w in webs:
            data.eq_active[w] = 0
        settle(320, rnd, every)
        snap(rnd)

    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    tiles = [(f"{n} — {d}", shot) for shot, (n, d) in zip(shots, labels)]
    written.append(imaging.contact_sheet(tiles, 2, OUT / "ribbon_cycle.png"))
    if arm_shots:
        arm_tiles = [(f"arm cam — {n}", shot) for shot, (n, _d) in zip(arm_shots, labels)]
        written.append(imaging.contact_sheet(arm_tiles, 2, OUT / "ribbon_cycle_armcam.png"))
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
