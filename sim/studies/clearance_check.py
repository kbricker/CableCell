"""What does the rotating assembly hit when it turns?

WHY THIS EXISTS, AND WHAT IT SAYS ABOUT THE OTHER STUDIES
---------------------------------------------------------
Kyle found the arm passing straight through the Z stage guide posts by looking
at the viewer for ten seconds. Nothing in this repo had caught it, and the word
"collision" appeared in a checklist item, a study name and a commit message
along the way.

The reason is worth writing down: every geom in the generated scene carries
contype="0" conaffinity="0". Contacts are disabled throughout for render speed,
so bodies pass through each other silently and a played cycle looks correct no
matter what it intersects. `fit_check` tests ANGULAR fit and reach. Neither
tests interference.

So this study does the one thing MuJoCo is not being asked to do here: sweep the
rotating assembly through its whole arc and every Z position, and check it
against the fixed structure by plain geometry.

    uv run python -m sim.studies.clearance_check

It is deliberately NOT a general collision checker. It knows about the specific
fixed obstacles a rotating cantilever can hit, and it says so — a check whose
name over-promises is how we got here.
"""

from __future__ import annotations

import sys

from sim import build_scene as B
from sim import layout as L


def swept_annulus() -> tuple[float, float]:
    """Radial band the arm sweeps through, mm."""
    return B._BEAM_X0, float(L.ARM_R0) + 30.0


def z_band() -> tuple[float, float]:
    """Height band the arm occupies across its whole Z travel, mm above bench."""
    deck_top = float(L.DECK_ABOVE_BENCH) + float(L.DECK_THICKNESS)
    low = deck_top + B.ROTOR_SEAT_T + B.COMB_ABOVE_ROTOR
    return low - float(L.ARM_THICKNESS) / 2.0, low + L.z_stage_choice() + float(L.ARM_THICKNESS) / 2.0


def obstacles() -> list[tuple[str, float, float, float]]:
    """(name, radius from pivot, top height, note) for fixed structure."""
    deck_top = float(L.DECK_ABOVE_BENCH) + float(L.DECK_THICKNESS)
    post_top = deck_top + L.z_stage_choice() + 30.0
    r = float(L.Z_POST_CIRCLE_R)
    return [
        ("Z guide post x3", r, post_top, "LM8UU rides these; must outlast the travel"),
        ("Z leadscrew", r, post_top, "off-axis so the spindle can use the centre"),
    ]


def main() -> int:
    r_in, r_out = swept_annulus()
    z_lo, z_hi = z_band()

    print("Clearance — the rotating assembly against fixed structure")
    print("=" * 70)
    print(f"arm sweeps radius   {r_in:.1f} .. {r_out:.1f} mm")
    print(f"arm occupies height {z_lo:.1f} .. {z_hi:.1f} mm above bench")
    print(f"over {float(L.SWEEP_ARC):.0f} degrees of arc")
    print()
    print(f"{'obstacle':<20}{'radius':>9}{'top':>9}   verdict")
    print("-" * 70)

    problems: list[str] = []
    for name, radius, top, note in obstacles():
        in_band = r_in <= radius <= r_out
        below = top > z_lo
        if in_band and below:
            verdict = f"HIT — {top - z_lo:.0f} mm into the arm"
            problems.append(f"{name}: stands {top - z_lo:.0f} mm into the arm's path")
        elif in_band:
            verdict = f"clear by {z_lo - top:.0f} mm vertically"
        else:
            verdict = "clear — outside the swept annulus"
        print(f"{name:<20}{radius:>9.1f}{top:>9.1f}   {verdict}")
        print(f"{'':<20}{note}")

    print()
    print("NOT TESTED HERE: station tooling (see ribbon_path), the press, the")
    print("spool post, anything on the arm itself. This checks the rotating")
    print("assembly against the Z stage only.")
    print()

    if not problems:
        print("Clear.")
        return 0
    print(f"{len(problems)} interference(s):")
    for p in problems:
        print(f"  - {p}")
    print()
    print("The deck already has a 7\" centre clearance hole cut for the Z platform")
    print("to pass THROUGH. Dropping the platform below the deck puts the posts")
    print("entirely under it and the arm sweeps over the lot.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
