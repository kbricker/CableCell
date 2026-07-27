"""Does this machine actually need a Z axis?

Kyle 2026-07-27: *"since we have deferred on 4 and 5, im not sure this version
of the system even needs to move in the Z ??"*

Worth taking seriously rather than defending, because the original argument for
Z has quietly expired. It was:

    rotation clearance is VERTICAL (lift, rotate, descend) rather than radial,
    which is what decouples station tooling design from the arm's sweep path

That was true when the arm's structure reached out to R0+30 and swept through
every station. It does not reach any more — `arm_structure_max_r()` stops
26 mm short of the tooling line, and the only thing that crosses into a station
is TAIL_PROJECTION mm of free ribbon. If retracting R gets the tail out too,
nothing on the moving assembly is inside a station during rotation, and the Z
stage is carrying a requirement that no longer exists.

The other two jobs Z was doing are also gone or never existed:

  * per-station engagement heights — every stop is on ONE derived plane now
  * the press at S4 — stashed, and it was the only thing at a different height

So this asks the question directly: sweep T through the whole arc with Z pinned
at zero, at several R positions, and see what touches.

    uv run python -m sim.studies.z_needed

A machine that does not need an axis should not have one. Deleting Z would take
out a leadscrew, a motor, three ground rods, three LM8UUs, a platform and a
coupling — and it would shorten the whole stack.
"""

from __future__ import annotations

import collections
import math
import sys

import mujoco

from sim import build_scene as B
from sim import layout as L

IGNORE_PREFIX = ("rib_", "stock_")

# Known convex-hull artefacts, listed rather than filtered silently.
#
# MuJoCo collides meshes as convex hulls. camera_mount is a yoke — two posts
# with a deliberate gap for the wrist to pass through — so its hull fills the
# exact space the part was shaped to leave open, and reports the wrist hitting
# a bracket built to clear it. In the part's own coordinates the posts sit at
# y +/-20..32 and the clamp at +/-15: 5 mm of air.
#
# Tracked on plan 701 (primitive collision geoms). Named here so the verdict is
# not quietly resting on an exclusion.
HULL_ARTEFACTS = {
    ("arm_camera", "body_clamp"),
    ("arm_camera", "wrist_hub"),
}
SWEEP_STEPS = 180


def main() -> int:
    model = mujoco.MjModel.from_xml_path(str(B.write_collide()))
    data = mujoco.MjData(model)
    adr = {
        j: model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, j)]
        for j in ("Z", "T", "R", "S", "W")
    }

    stroke = float(L.ARM_STROKE)
    # R positions to try, most retracted first. The question is not "does it
    # clear at full retraction" but "how much retraction does it take".
    r_options = [0.0, stroke * 0.25, stroke * 0.5, stroke]

    print("Does the arm need Z to rotate?")
    print("=" * 74)
    print(f"Sweeping T through {float(L.SWEEP_ARC):.0f} deg in {SWEEP_STEPS} steps, "
          f"Z pinned at 0, both wrist positions.")
    print(f"Arm structure stops at R={L.arm_structure_max_r():.0f}; "
          f"tooling starts at R={float(L.STATION_INNER_R):.0f}; "
          f"free tail is {float(L.TAIL_PROJECTION):.0f} mm.")
    print()
    print(f"{'R (mm)':>8}  {'tail tip R':>11}  verdict")
    print("-" * 74)

    clean_at: float | None = None
    for r in r_options:
        hits: dict[tuple[str, str], float] = collections.defaultdict(float)
        artefacts: set = set()
        for step in range(SWEEP_STEPS + 1):
            theta = math.radians(float(L.SWEEP_ARC)) * step / SWEEP_STEPS
            for w in (0.0, math.pi):
                mujoco.mj_resetData(model, data)
                data.qpos[adr["Z"]] = 0.0
                data.qpos[adr["T"]] = theta
                data.qpos[adr["R"]] = r * 0.001
                data.qpos[adr["W"]] = w
                mujoco.mj_forward(model, data)
                for c in range(data.ncon):
                    con = data.contact[c]
                    a = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, con.geom1) or ""
                    b = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, con.geom2) or ""
                    if a.startswith(IGNORE_PREFIX) or b.startswith(IGNORE_PREFIX):
                        continue
                    depth = -con.dist
                    if depth <= 0.0002:
                        continue
                    key = tuple(sorted((a, b)))
                    if key in HULL_ARTEFACTS:
                        artefacts.add(key)
                        continue
                    hits[key] = max(hits[key], depth)

        tail_tip = L.arm_r_retracted() + r + L.arm_tool_reach()
        if hits:
            lines = [f"{len(hits)} pair(s)"]
            for (a, b), dep in sorted(hits.items(), key=lambda kv: -kv[1]):
                lines.append(f"{'':>23}{a} / {b}  {dep * 1000:.1f} mm")
            verdict = "\n".join(lines)
        else:
            verdict = "CLEAR through the whole arc"
            if artefacts:
                verdict += f"  ({len(artefacts)} hull artefact(s) set aside)"
            if clean_at is None:
                clean_at = r
        print(f"{r:>8.0f}  {tail_tip:>11.0f}  {verdict}")

    print()
    if clean_at is None:
        print("Z IS STILL NEEDED: no R position clears the arc on its own.")
        return 1

    print(f"Z IS NOT NEEDED FOR ROTATION at R <= {clean_at:.0f} mm.")
    print()
    print("What that means, stated carefully:")
    print("  * rotation clearance can come from R retraction alone")
    print("  * every stop is on one engagement plane, so Z has no height to chase")
    print("  * the press was the only thing at a different height, and it is stashed")
    print()
    print("What it does NOT mean:")
    print("  * the CONVEX-HULL caveat still applies - concave printed parts")
    print("    over-report, so 'clear' here is conservative, not permissive")
    print("  * Phase 2 brings the press back at its own height, and that is the")
    print("    one thing that would need Z again. Deleting the axis is cheap;")
    print("    re-adding it after the deck is cut is not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
