"""Drive the arm through a station cycle — live, or as rendered frames.

    uv run python -m sim.run_cycle              # interactive viewer, loops
    uv run python -m sim.run_cycle --sheet      # contact sheet of key poses
    uv run python -m sim.run_cycle --gif        # animated GIF of the cycle

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
from sim import imaging
from sim import layout as L
from sim import ribbon as RIB

MM = 0.001

# Indexing rate. Slow enough that a limp cable trails rather than whips, which
# is the whole reason the cycle is watched with contacts on.
INDEX_DEG_PER_S = 45.0

# Actuators the model actually has. Z drops out when the axis is deferred —
# asking for an actuator that is not there is how a deferral turns into a crash
# three files away.
ACTS = tuple(
    a for a in ("Z_act", "T_act", "R_act", "S_act", "W_act")
    if a != "Z_act" or L.Z_STAGE_ENABLED
)


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
    ids = _act_ids(model)
    tiles: list[tuple[str, np.ndarray]] = []

    with mujoco.Renderer(model, height=cell_h, width=cell_w) as renderer:
        for idx, (caption, targets, _sec) in enumerate(picks):
            # Jump straight to this waypoint's pose.
            for name, target in targets.items():
                data.ctrl[ids[name]] = target
            for _ in range(400):
                mujoco.mj_step(model, data)
            renderer.update_scene(data, camera=cam)
            tiles.append((caption, renderer.render()))
            print(f"  {idx + 1}/{want}  {caption}")

    out = pathlib.Path(__file__).parent / "studies" / "renders" / "cycle_sheet.png"
    return imaging.contact_sheet(tiles, cols, out)


def gif(count: int = 84, fps: int = 16, scale: float = 0.46) -> pathlib.Path:
    """Render the cycle and write it out as an animated GIF."""
    model = mujoco.MjModel.from_xml_path(str(build_scene.MJCF_PATH))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.azimuth, cam.elevation, cam.distance = 38.0, -27.0, 0.70
    cam.lookat[:] = (0.0, 0.0, 0.215)

    total_steps = sum(max(1, int(s / model.opt.timestep)) for _, _, s in waypoints())
    every = max(1, total_steps // count)
    collected: list[np.ndarray] = []
    state = {"i": 0}

    with mujoco.Renderer(model, height=720, width=1152) as renderer:
        def on_frame(caption: str, _p: float) -> None:
            if state["i"] % every == 0 and len(collected) < count:
                renderer.update_scene(data, camera=cam)
                collected.append(imaging.label(renderer.render(), caption, size=26))
            state["i"] += 1

        play(model, data, on_frame=on_frame)

    out = pathlib.Path(__file__).parent / "studies" / "renders" / "cycle.gif"
    path = imaging.save_gif(collected, out, fps=fps, scale=scale)
    size_mb = path.stat().st_size / 1_048_576
    print(f"{len(collected)} frames -> {path}  ({size_mb:.1f} MB)")
    return path


def timeline(model):
    """The whole cycle as a function of TIME, not as a loop that steps physics.

    Rewritten for two reasons, both from Kyle 2026-07-27.

    "the pause in the UI is greyed out, that should work" — it was greyed out
    because the old viewer was PASSIVE: our code owned the stepping, so the
    viewer's own pause, step and speed controls had nothing to control. Making
    the cycle a pure function of data.time hands stepping back to the managed
    viewer, and every one of those buttons starts working for free. Pausing now
    genuinely freezes the cycle, because data.time stops advancing.

    "the animation still does some wild /spastic rotation and flipping at the
    station zero and no cable moves at all" — both were real. The flip ran in
    0.9 s with no settle either side, which with contacts on whips the ribbon.
    And the cycle never touched the ribbon's equalities at all, so the material
    just sat there while the machine mimed around it.

    Returns (segments, total_seconds). A segment is
        (t0, t1, label, {actuator: (from, to)}, [(equality_id, active), ...])
    """
    ids = _act_ids(model)

    def eq(name: str) -> int:
        i = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_EQUALITY, name)
        if i < 0:
            raise KeyError(f"no equality {name!r} — the scene and the cycle disagree")
        return i

    cuts = [eq(f"cut_{i}") for i in range(RIB.CONDUCTORS)]
    grips = [eq(f"grip_{i}") for i in range(RIB.CONDUCTORS)]
    split_n = RIB.split_segments()
    webs = [
        eq(f"web_{i}_{k}")
        for i in range(RIB.CONDUCTORS - 1)
        for k in range(RIB.TAIL_SEGMENTS - split_n, RIB.TAIL_SEGMENTS)
    ]

    stroke = float(L.ARM_STROKE) * MM
    s_half = float(L.CROSS_SLIDE_STROKE) / 2.0 * MM

    # (label, targets, seconds, equality changes)
    #
    # THE ORDER COMES FROM KYLE, 2026-07-27: "at this station, the head needs to
    # grab a small end of the wire coming out of the feeder, pull it in to the
    # lengeth we want to make, then cut it. not sure what all the other activity
    # is about."
    #
    # What was there: grab, cut, flip 180, flip back, THEN go and split and
    # strip. Six seconds of wrist at a station that has no reason to flip, and
    # the cut happening before the length was ever paid out.
    #
    # The flip is gone from the prototype entirely. It exists to present END B
    # to the same stations after end A is finished — and the prototype does one
    # end, because doing two needs the payout-trough geometry that is still open
    # on 706. A wrist that flips for no reason is worse than no wrist.
    #
    # Cutting FIRST also sidesteps the thing 706 is about: process-then-cut
    # leaves the piece attached to the feed head while the arm carries it around
    # the dial, trailing a 200 mm chord across the deck. Cut-then-carry does not.
    steps: list[tuple[str, dict, float, list]] = []

    def at(name: str) -> float:
        return math.radians(float(L.STATION_ANGLES[name]))

    # HOW LONG AN INDEX TAKES, from how far it actually turns.
    #
    # Kyle: "the arm movment is not smooth, especially from, 3 to bin and back
    # to zero." Both are the long moves, and every index was running on a flat
    # 1.4-1.8 s regardless. Short hops crawled, long ones were flung.
    def index_time(frm: float, to: float) -> float:
        deg = abs(math.degrees(to - frm))
        return max(0.7, deg / INDEX_DEG_PER_S)

    # --- S1: grab the protruding end, pay out a length, cut it free ---------
    steps.append(("S1 feed: reach for the wire end", {"R_act": stroke}, 0.9, []))
    steps.append(("S1 feed: clamp closes on it", {}, 0.6, [(g, 1) for g in grips]))
    steps.append((
        f"S1 feed: pay out {float(L.CABLE_LENGTH_NOMINAL):.0f} mm (rollers, encoder measures)",
        {}, 2.0, []))
    steps.append(("S1 feed: GUILLOTINE", {}, 0.5, [(c, 0) for c in cuts]))
    steps.append(("S1 feed: withdraw with the piece", {"R_act": 0.0}, 0.9, []))

    # --- S2: split ---------------------------------------------------------
    steps.append(("S2 slit: index", {"T_act": at("S2_SLIT")},
                  index_time(at("S1_FEED"), at("S2_SLIT")), []))
    steps.append(("S2 slit: present tail to the wedge", {"R_act": stroke}, 0.9, []))
    steps.append(("S2 slit: WEDGE SPLITS the webs", {}, 0.6, [(w, 0) for w in webs]))
    steps.append(("S2 slit: spreader fans them", {"S_act": s_half}, 0.7, []))
    steps.append(("S2 slit: centre", {"S_act": 0.0}, 0.6, []))
    steps.append(("S2 slit: withdraw", {"R_act": 0.0}, 0.8, []))

    # --- S3: strip ---------------------------------------------------------
    steps.append(("S3 strip: index", {"T_act": at("S3_STRIP")},
                  index_time(at("S2_SLIT"), at("S3_STRIP")), []))
    steps.append(("S3 strip: engage the die", {"R_act": stroke}, 0.9, []))
    for i, y in enumerate((-1.0, 0.0, 1.0)):
        steps.append((f"S3 strip: conductor {i + 1}", {"S_act": y * s_half}, 0.6, []))
    steps.append(("S3 strip: PULL OFF the slugs", {"R_act": stroke * 0.6}, 0.6, []))
    steps.append(("S3 strip: withdraw", {"R_act": 0.0, "S_act": 0.0}, 0.8, []))

    # --- S4: drop ----------------------------------------------------------
    steps.append(("S4 drop: index", {"T_act": at("S6_DROP")},
                  index_time(at("S3_STRIP"), at("S6_DROP")), []))
    steps.append(("S4 drop: clamp OPENS", {}, 0.5, [(g, 0) for g in grips]))
    steps.append(("S4 drop: cable falls to the bin", {}, 1.6, []))

    # --- home ---------------------------------------------------------------
    # A real rotation back, not a jump. Kyle: "the animation still just does a
    # skip straight from the end to the beginning, the arm should rotate back
    # normally and land in the start position to complete the loop." It DID
    # rotate back — and then the first segment of the next lap spent another
    # 4.4 s driving T to a value it was already at, which read as a dead pause
    # and then a jump when the ribbon respawned.
    steps.append(("home: rotate back to S1", {"T_act": at("S1_FEED")},
                  index_time(at("S6_DROP"), at("S1_FEED")), []))
    steps.append((
        "home: new stock at the feed head",
        {}, 1.0,
        [(c, 1) for c in cuts] + [(w, 1) for w in webs] + [(g, 0) for g in grips],
    ))

    # Absolute ctrl values, resolved forward so each segment knows both ends.
    cur = {name: 0.0 for name in ACTS}
    if "Z_act" in cur:
        cur["Z_act"] = 0.0
    segs = []
    t = 0.0
    for label, targets, secs, eqs in steps:
        frm = dict(cur)
        to = dict(cur)
        to.update(targets)
        segs.append((t, t + secs, label, {k: (frm[k], to[k]) for k in ACTS}, eqs))
        cur = to
        t += secs
    return segs, t


def viewer() -> None:
    """Managed viewer, so pause / step / speed all work."""
    import mujoco.viewer

    build_scene.write()
    model = mujoco.MjModel.from_xml_path(str(build_scene.write_collide()))
    data = mujoco.MjData(model)

    segs, total = timeline(model)
    ids = _act_ids(model)
    mujoco.mj_forward(model, data)
    home_qpos = data.qpos.copy()
    state = {"label": "", "lap": -1}

    def control(m, d) -> None:
        t = d.time % total
        lap = int(d.time // total)
        if lap != state["lap"]:
            # NEW CABLE. Equalities back on, and the RIBBON back at the feed
            # head — without this the old piece stays wherever it fell and the
            # next lap runs with no stock, which is half of what read as a
            # "skip straight from the end to the beginning".
            #
            # Restoring the whole qpos is safe precisely here: the previous
            # segment drove the arm home, so every machine joint is already at
            # its start value and only the ribbon actually moves.
            d.eq_active[:] = m.eq_active0
            d.qpos[:] = home_qpos
            d.qvel[:] = 0.0
            state["lap"] = lap
        for t0, t1, label, ctrl, eqs in segs:
            if t0 <= t < t1:
                f = _smooth((t - t0) / (t1 - t0))
                for name, (a, b) in ctrl.items():
                    d.ctrl[ids[name]] = a + (b - a) * f
                if label != state["label"]:
                    for e, active in eqs:
                        d.eq_active[e] = active
                    print(f"  {label}")
                    state["label"] = label
                return

    print(f"CableCell cycle — R0 {float(L.ARM_R0):.0f} mm, "
          f"{len(L.STATIONS)} stops, {total:.0f} s per cable")
    print("Looping. Pause / step / speed all work — the cycle is a function of")
    print("simulation time, so the viewer owns the clock.\n")

    mujoco.set_mjcb_control(control)
    try:
        mujoco.viewer.launch(model, data)
    finally:
        mujoco.set_mjcb_control(None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", action="store_true", help="contact sheet of key poses")
    parser.add_argument("--gif", action="store_true", help="write an animated GIF")
    args = parser.parse_args()

    if args.sheet:
        print("rendering contact sheet ...")
        print(f"wrote {contact_sheet()}")
    elif args.gif:
        gif()
    else:
        viewer()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
