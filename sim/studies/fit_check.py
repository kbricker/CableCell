"""Fit check — does the rotary layout close, before we model anything?

Three questions, all answerable from `layout.py` alone with no physics:

    1. Do seven angular stops fit inside the working arc at R0, given that the
       press is far wider than any other station?
    2. What Z travel does the machine actually need, and which stock ballscrew
       stage covers it?
    3. Where does R0 have to be for the arm to reach the press anvil at all?

This is deliberately arithmetic rather than simulation. If the layout does not
close here, there is no point building a scene.

Run:  python -m sim.studies.fit_check
"""

from __future__ import annotations

import sys

from sim import layout as L


def _rule(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def check_angular_fit(radius: float) -> tuple[bool, float, float]:
    """Can the press plus six normal stations fit inside the working arc?"""
    press = L.press_angular_width(radius)
    station = L.station_angular_width(radius)
    needed = press + 6.0 * station
    return needed <= L.SWEEP_ARC, needed, float(L.SWEEP_ARC) - needed


def sweep_radius_table() -> None:
    _rule("1. Angular fit vs bolt circle radius")
    print(
        f"{'R0 (mm)':>9} {'press':>9} {'station':>9} {'needed':>9} "
        f"{'spare':>9}  verdict"
    )
    for r in (125.0, 150.0, 175.0, 200.0, 225.0, 250.0, 300.0):
        ok, needed, spare = check_angular_fit(r)
        print(
            f"{r:>9.0f} {L.press_angular_width(r):>8.1f}° "
            f"{L.station_angular_width(r):>8.1f}° {needed:>8.1f}° "
            f"{spare:>8.1f}°  {'FITS' if ok else 'DOES NOT FIT'}"
        )

    print()
    print(
        f"Working arc is {float(L.SWEEP_ARC):.0f}° (not a full turn, so the trailing "
        "ribbon never wraps the pivot)."
    )
    print(
        f"Press occupies {L.PRESS_WIDTH:.0f} mm of width against a normal station's "
        f"{L.STATION_WIDTH:.0f} mm — that asymmetry is what drives R0."
    )


def z_budget() -> None:
    _rule("2. Z travel budget")
    lo = min(L.STATION_Z.values())
    hi = max(L.STATION_Z.values())
    print(f"Station engagement heights span   {lo:.0f} .. {hi:.0f} mm above deck")
    print(f"Rotation-safe height Z_clear      {L.z_clear():.0f} mm")
    print(f"Commissioning margin              {float(L.Z_STAGE_MARGIN):.0f} mm")
    print(f"Travel required                   {L.z_travel_required():.0f} mm")
    print(f"Smallest stock stage that covers  {L.z_stage_choice():.0f} mm")
    print()
    print(
        "Shortest defensible stroke is the goal: stiffness falls off with stroke, "
        "and this stage carries the entire rotating assembly at the bottom of a "
        "long lever, so its compliance is magnified at the comb."
    )
    print()
    print(
        f"Deck sits {float(L.DECK_ABOVE_BENCH):.0f} mm above the bench — chosen to pull the "
        "six short stations up near the press's fixed crimp height. At bench "
        "level the Z stage would have to span that whole difference instead."
    )


def press_reach() -> None:
    _rule("3. Press placement and reach")
    print(f"Press body            {L.PRESS_WIDTH:.0f} x {L.PRESS_DEPTH:.0f} x {L.PRESS_HEIGHT:.0f} mm, {L.PRESS_MASS_KG:.0f} kg")
    print(f"Ram axis from front   {float(L.PRESS_RAM_FROM_FRONT):.0f} mm")
    print(f"Pivot to press centre {L.press_centre_distance():.0f} mm")
    print(f"Arm radial stroke     {float(L.ARM_STROKE):.0f} mm")
    print()
    print(
        "The press must face the dial so the arm can enter its throat. Reach is "
        "only confirmed once the ram-axis-from-front distance is measured — it is "
        "a placeholder today."
    )


def main() -> int:
    print("CableCell layout fit check")
    print("=" * 60)

    sweep_radius_table()
    z_budget()
    press_reach()

    _rule("4. Verdict at the current R0")
    ok, needed, spare = check_angular_fit(float(L.ARM_R0))
    print(f"R0 = {float(L.ARM_R0):.0f} mm  ->  needs {needed:.1f}° of {float(L.SWEEP_ARC):.0f}°, {spare:.1f}° spare")
    if not ok:
        print()
        print("LAYOUT DOES NOT CLOSE. Increase R0, narrow the stations, or drop a stop.")

    _rule("5. Provenance")
    print(L.report())

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
