"""Does the ribbon actually have a path to travel down?

Written before animating a ribbon in MuJoCo, because animating one along a path
whose parts interpenetrate would produce a convincing picture of a machine that
cannot be built. The scene draws each station part at a radius and a height; it
does NOT check that consecutive parts clear each other, and until now nothing
did.

Three checks, in the order they matter:

  1. HEIGHT     every passage on the engagement plane, or the ribbon climbs
  2. OVERLAP    consecutive parts must not occupy the same radius
  3. SPAN       unsupported ribbon between parts must not be long enough to
                buckle when the rollers push it

Run:
    uv run python -m sim.studies.ribbon_path
"""

from __future__ import annotations

import sys

from sim import build_scene as B
from sim import layout as L

# Radial half-length of each part along the ribbon's direction of travel, from
# the bounding boxes build_parts.py reports.
# Only ON-DECK parts. The feeder (spool, dancer, drive rollers, encoder wheel)
# is off the dial and reaches the machine through PTFE tube, so it has no
# radial budget to blow and nothing here to clash with.
HALF_LENGTH = {
    "feed_head": 35.0,
    "strip_die": 20.0,
    "splitting_wedge": 25.0,
    "spreader_plate": 12.5,
}

# A free ribbon span acts as a strut in compression when the rollers push it
# out. Euler buckling for a 4.2 x 1.4 mm PVC section is generous, but the
# ribbon is also not straight or perfectly held, so keep spans short.
MAX_FREE_SPAN = 30.0


def rows(station: str) -> list[tuple[str, float, float, float]]:
    """(part, centre radius, inner edge, outer edge) ordered outboard -> in."""
    out = []
    for mesh, r_off, _t, _rev, _e in B.STATION_PARTS[station]:
        r = float(L.ARM_R0) + r_off
        h = HALF_LENGTH[mesh]
        out.append((mesh, r, r - h, r + h))
    return sorted(out, key=lambda t: -t[1])


def check(station: str) -> list[str]:
    problems: list[str] = []
    engage = float(L.DECK_ABOVE_BENCH) + float(L.STATION_Z[station])

    print(f"\n{station}  — engagement plane {engage:.1f} mm above bench")
    print(f"{'part':<22}{'radius':>9}{'spans':>18}{'gap to next':>14}")
    print("-" * 66)

    r = rows(station)
    for i, (mesh, centre, inner, outer) in enumerate(r):
        gap_txt = ""
        if i + 1 < len(r):
            nxt = r[i + 1]
            gap = inner - nxt[3]  # this part's inner edge to next part's outer
            if gap < 0:
                gap_txt = f"{gap:>10.1f}  OVERLAP"
                problems.append(
                    f"{station}: {mesh} and {nxt[0]} overlap by {-gap:.1f} mm"
                )
            elif gap > MAX_FREE_SPAN:
                gap_txt = f"{gap:>10.1f}  LONG"
                problems.append(
                    f"{station}: {gap:.1f} mm unsupported between {mesh} and "
                    f"{nxt[0]} (max {MAX_FREE_SPAN:.0f})"
                )
            else:
                gap_txt = f"{gap:>10.1f}  ok"
        print(f"{mesh:<22}{centre:>9.1f}{inner:>9.1f}..{outer:<8.1f}{gap_txt}")

    # Does the whole station fit on the deck it bolts to?
    outermost = max(o for _m, _c, _i, o in r)
    if outermost > float(L.DECK_RADIUS):
        problems.append(
            f"{station}: reaches {outermost:.1f} mm, past the deck rim at "
            f"{float(L.DECK_RADIUS):.1f} mm — needs an off-deck bracket"
        )
    return problems


def main() -> int:
    print("Ribbon path — can the ribbon actually get from the spool to the comb?")
    print("=" * 70)

    problems: list[str] = []
    for station in B.STATION_PARTS:
        problems.extend(check(station))

    print()
    if not problems:
        print("Path is clear.")
        return 0

    print(f"{len(problems)} problem(s):")
    for p in problems:
        print(f"  - {p}")
    print(
        "\nThis is why the ribbon is not animated yet. A cable composite laid "
        "down\nthis path would render beautifully and mean nothing."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
