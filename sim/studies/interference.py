"""What actually overlaps, according to MuJoCo rather than according to me.

Kyle, looking at the viewer: "the arm still collides with the stations then
there are a lot of 'boxes' on the arm that seem to just pass through the arm
structure ... this still seems like a fantasy render."

He is right, and the reason is worth stating plainly. Every part's own geometry
is real — built from layout.py, the same numbers that produce the printable
STL. Where the parts sit RELATIVE TO EACH OTHER on the arm is not: the carriage,
cross-slide, wrist, camera and clamp were placed with hand-typed offsets like
pos="-0.030 0 -0.014" and none of them was ever checked. They interpenetrate
because nothing made them not.

The deeper mistake was mine: the display scene disables contacts everywhere
(contype="0" conaffinity="0") so it renders fast, and I responded by writing
hand-rolled radius arithmetic to check clearance — one study per thing I
happened to think of. That is how the arm came to sweep through the Z posts
with three checks reporting clear.

MuJoCo already has a collision engine that knows about every geom, not just the
ones a study author remembered. This flips the flags on and asks it.

    uv run python -m sim.studies.interference

Poses swept: every station stop x both Z extremes x R retracted/extended x the
cross-slide ends x both wrist positions.
"""

from __future__ import annotations

import collections
import itertools
import math
import sys

import mujoco

from sim import build_scene as B
from sim import layout as L

# The ribbon is soft, hangs under gravity and is SUPPOSED to touch things.
# Reporting it here would bury the structural findings under noise.
IGNORE_PREFIX = ("rib_", "stock_")


def geom_name(model, gid: int) -> str:
    return mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid) or f"geom{gid}"


def poses() -> list[dict[str, float]]:
    """Every pose the machine is actually commanded into."""
    stroke = L.z_stage_choice() * 0.001
    r_max = float(L.ARM_STROKE) * 0.001
    s_half = float(L.CROSS_SLIDE_STROKE) / 2.0 * 0.001

    out = []
    for name in L.STATIONS:
        t = math.radians(float(L.STATION_ANGLES[name]))
        for z, r, s, w in itertools.product(
            (0.0, stroke), (0.0, r_max), (-s_half, 0.0, s_half), (0.0, math.pi)
        ):
            out.append({"label": name, "T": t, "Z": z, "R": r, "S": s, "W": w})
    return out


def main() -> int:
    path = B.write_collide()
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)

    adr = {}
    for j in ("Z", "T", "R", "S", "W"):
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, j)
        adr[j] = model.jnt_qposadr[jid]

    worst: dict[tuple[str, str], float] = collections.defaultdict(float)
    where: dict[tuple[str, str], str] = {}

    all_poses = poses()
    for p in all_poses:
        mujoco.mj_resetData(model, data)
        for j in ("Z", "T", "R", "S", "W"):
            data.qpos[adr[j]] = p[j]
        mujoco.mj_forward(model, data)

        for c in range(data.ncon):
            con = data.contact[c]
            a, b = geom_name(model, con.geom1), geom_name(model, con.geom2)
            if a.startswith(IGNORE_PREFIX) or b.startswith(IGNORE_PREFIX):
                continue
            depth = -con.dist  # negative dist = penetration
            if depth <= 0.0002:  # 0.2 mm, below meshing noise
                continue
            key = tuple(sorted((a, b)))
            if depth > worst[key]:
                worst[key] = depth
                where[key] = f"{p['label']} Z={p['Z'] * 1000:.0f} R={p['R'] * 1000:.0f}"

    print("Interference — MuJoCo's answer, not mine")
    print("=" * 74)
    print(f"{len(all_poses)} poses swept: {len(L.STATIONS)} stops x 2 Z x 2 R x 3 S x 2 W")
    print(f"ribbon geoms excluded ({', '.join(IGNORE_PREFIX)}) — soft, and meant to touch")
    print()

    if not worst:
        print("Nothing overlaps.")
        return 0

    print(f"{'part':<26}{'part':<26}{'worst':>8}  at")
    print("-" * 74)
    for (a, b), depth in sorted(worst.items(), key=lambda kv: -kv[1]):
        print(f"{a:<26}{b:<26}{depth * 1000:>7.1f}  {where[(a, b)]}")

    print()
    print(f"{len(worst)} interfering pair(s).")
    print()
    print("Overlap between parts that BOLT TOGETHER is expected — a bolted joint")
    print("is two solids sharing a face. What matters here is anything that")
    print("MOVES relative to what it hits.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
