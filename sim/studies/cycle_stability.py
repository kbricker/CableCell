"""Does the cycle actually run, or does the solver blow up?

Kyle 2026-07-27: *"now the animation is tripping at the wire station only
running in a fast loop"*

It looked like a timeline bug and it was a physics one. The solve diverged
0.15 s into the cycle; MuJoCo auto-resets on divergence, so `data.time` went
back to zero, the timeline restarted at S1, and it did that several times a
second. The loop was the reset.

Cause: `write_collide()` was a blanket string replace that turned contacts on
for the RIBBON as well as the machine. An 18-link chain of capsules whose
neighbours overlap by construction promptly fought itself.

The lesson is the one this project keeps relearning in different clothes — a
check that says "clear" is not the same as a machine that RUNS. `interference`
answers "does anything overlap in this pose". Nothing answered "does the thing
survive being simulated". This does.

    uv run python -m sim.studies.cycle_stability

Cheap enough to run every time, and it fails loudly, which is the point.
"""

from __future__ import annotations

import sys

import mujoco
import numpy as np

from sim import build_scene, run_cycle

# Past this the solve is meaningless even if it has not gone non-finite yet.
QACC_LIMIT = 1e8
CYCLES = 2.0


def main() -> int:
    model = mujoco.MjModel.from_xml_path(str(build_scene.write_collide()))
    data = mujoco.MjData(model)
    segs, total = run_cycle.timeline(model)
    ids = run_cycle._act_ids(model)

    steps = int(CYCLES * total / model.opt.timestep)
    print("Cycle stability — does it survive being simulated?")
    print("=" * 74)
    print(f"{CYCLES:.0f} full cycles, {total:.1f} s each, {steps} steps at "
          f"{model.opt.timestep * 1000:.0f} ms")
    print(f"{model.nbody} bodies, {model.neq} equalities, {model.nv} dof")
    print()

    worst = 0.0
    label = ""
    for _ in range(steps):
        t = data.time % total
        for t0, t1, lab, ctrl, _eqs in segs:
            if t0 <= t < t1:
                f = run_cycle._smooth((t - t0) / (t1 - t0))
                for name, (a, b) in ctrl.items():
                    data.ctrl[ids[name]] = a + (b - a) * f
                label = lab
                break
        mujoco.mj_step(model, data)

        peak = float(np.abs(data.qacc).max()) if np.isfinite(data.qacc).all() else float("inf")
        worst = max(worst, peak) if np.isfinite(peak) else peak
        if not np.isfinite(peak) or peak > QACC_LIMIT:
            print(f"DIVERGED at t={data.time:.3f} s during '{label}'")
            print(f"peak |qacc| = {peak:.3g}")
            print()
            print("The viewer will show this as the cycle restarting over and")
            print("over at the first station — MuJoCo resets on divergence, and")
            print("a timeline driven by data.time restarts with it.")
            return 1

    print(f"Ran {CYCLES:.0f} cycles clean. Peak |qacc| {worst:.3g}, "
          f"limit {QACC_LIMIT:.0g}.")
    print()
    print("Contact classes, which is what makes this survivable:")
    print("  machine  1/1   collides with machine and deck")
    print("  ribbon   2/4   collides with the deck only — not itself, not tooling")
    print("  deck     5/3   collides with both")
    return 0


if __name__ == "__main__":
    sys.exit(main())
