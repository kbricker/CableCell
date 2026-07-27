"""How every part of this machine gets MADE — cut, printed, or bought.

Kyle 2026-07-27, looking at the viewer: *"the bar and all framing attached to
it, its mostly all white. I want to see the geometry for the metal part(s) of
this that will be cut from the stock in the bom, and then I want to understand
if all these other housing/framing things are printed parts?"*

Both halves of that were fair, and the first one had a real answer: there was
no frame geometry. The frame was ONE translucent cylinder — a structure implied
rather than drawn. Nothing to cut, no lengths, no joints. It is eight kinds of
3030 member now, and this study is what turns them into a saw list.

The second half is the reason this file exists rather than a comment somewhere.
The scene colours parts by FUNCTION — station tooling blue, arm parts white,
clamp orange, comb yellow — which says nothing about how any of them is made.
A part is one of four things and you cannot tell by looking:

    CUT FROM STOCK   aluminium extrusion, ground rod, leadscrew, linear rail.
                     Bought by the metre, cut to a number that comes from
                     layout.py.
    PRINTED          every housing, bracket, mount and die body. FDM, our
                     design, no lead time, free to iterate.
    CUT FROM SHEET   the deck. One part, made on a woodworking bench, which is
                     why its drawing is in inches.
    BOUGHT AS-IS     bearings, blocks, motors, the press. See bom/.

    uv run python -m sim.studies.cut_list
"""

from __future__ import annotations

import pathlib
import struct
import sys

from sim import layout as L

MESH_DIR = pathlib.Path(__file__).parent.parent.parent / "cad" / "parts"

# Rough FDM figures for turning volume into something orderable. PLA at ~1.24
# g/cm3, and a typical 4-wall / 20 % infill part is nearer 45 % of solid.
PLA_DENSITY = 1.24
INFILL_FRACTION = 0.45
SPOOL_G = 1000.0


def mesh_volume_cm3(name: str) -> float:
    """Solid volume of an STL, by the signed-tetrahedron sum.

    Reads the same STL the sim renders and the slicer would open, so this
    cannot drift from what actually gets printed.
    """
    raw = (MESH_DIR / f"{name}.stl").read_bytes()
    n = struct.unpack("<I", raw[80:84])[0]
    total = 0.0
    for i in range(n):
        base = 84 + i * 50 + 12
        v = struct.unpack_from("<9f", raw, base)
        ax, ay, az, bx, by, bz, cx, cy, cz = v
        total += (
            ax * (by * cz - bz * cy)
            - ay * (bx * cz - bz * cx)
            + az * (bx * cy - by * cx)
        ) / 6.0
    return abs(total) / 1000.0  # mm3 -> cm3


def printed_parts() -> tuple[list[str], list[str]]:
    """(current parts, orphans left on disk).

    The authority is build_scene.MESHES, which mirrors build_parts.PARTS — NOT
    whatever STLs happen to be in the folder. Globbing the folder found 22 parts
    when the machine has 20: guide_tube_mount and guillotine_holder were merged
    into feed_head and deleted from the builder, but their exported files stayed
    behind and quietly kept appearing in counts and totals.

    Orphans are reported rather than ignored. A file that no code produces is a
    trap for whoever opens the folder next.
    """
    from sim import build_scene

    live = sorted(build_scene.MESHES)
    on_disk = {p.stem for p in MESH_DIR.glob("*.stl")}
    return live, sorted(on_disk - set(live))


def main() -> int:
    print("How CableCell gets made")
    print("=" * 78)
    print()

    # ---- cut from stock ---------------------------------------------------
    print("CUT FROM STOCK — metal, bought by the bar, cut to a derived length")
    print("-" * 78)
    print(f"{'stock':<18}{'part':<22}{'qty':>4}{'length':>10}   why")
    last = ""
    for stock, what, qty, length, why in L.cut_stock():
        label = stock if stock != last else ""
        last = stock
        print(f"{label:<18}{what:<22}{qty:>4}{length:>9.1f}   {why}")
    print()
    print(f"{'stock':<18}{'total mm':>10}{'bars':>7}   at stock length")
    for stock, (total, bars) in sorted(L.stock_totals().items()):
        print(f"{stock:<18}{total:>10.0f}{bars:>7}   {L.STOCK_BAR.get(stock, 1000.0):.0f} mm")
    print()
    print("Bar counts assume no offcut reuse across profiles, which is the")
    print("honest way to buy: a 1 mm shortfall costs a whole bar and a week.")
    print()

    # ---- printed ----------------------------------------------------------
    names, orphans = printed_parts()
    print(f"PRINTED — {len(names)} parts, all of them ours, all FDM")
    print("-" * 78)
    print(f"{'part':<24}{'solid cm3':>11}{'~filament g':>13}   ")
    total_g = 0.0
    for n in names:
        v = mesh_volume_cm3(n)
        g = v * INFILL_FRACTION * PLA_DENSITY
        total_g += g
        print(f"{n:<24}{v:>11.1f}{g:>13.1f}")
    print("-" * 78)
    print(f"{'':<24}{'':>11}{total_g:>13.1f}   ~{total_g / SPOOL_G:.1f} spools")
    print()
    if orphans:
        print("ORPHANED EXPORTS — files on disk that no builder produces:")
        for o in orphans:
            print(f"  {o}.stl / .step / .FCStd")
        print("  Delete them. They were counted in this table until it stopped")
        print("  globbing the folder and started reading build_scene.MESHES.")
        print()
    print(f"Filament figure is solid volume x {INFILL_FRACTION:.0%} (4 walls, 20% infill)")
    print(f"x {PLA_DENSITY} g/cm3. Good to maybe +/-25%; it sizes an order, not a budget.")
    print()

    # ---- cut from sheet ---------------------------------------------------
    print("CUT FROM SHEET — one part, and it is the only one made on a saw")
    print("-" * 78)
    print(f"deck   {float(L.DECK_RADIUS) * 2:.0f} mm disc x {float(L.DECK_THICKNESS):.0f} mm ply")
    print("       Full drawing, in inches, from studies/deck_cut_sheet.py")
    print()

    # ---- bought -----------------------------------------------------------
    print("BOUGHT AS-IS — not listed here on purpose")
    print("-" * 78)
    print("Bearings, MGN blocks, LM8UU, NEMA 17s, T8 nuts, the press and the")
    print("applicator live in bom/ with vendor links and prices. Repeating them")
    print("here would make a second source for a number someone has to order")
    print("against, which is how the Z post height came to be wrong in three")
    print("places at once.")
    print()

    print("WHICH IS WHICH, IN THE VIEWER")
    print("-" * 78)
    print("The scene colours by FUNCTION, not by how a part is made — station")
    print("tooling blue, arm parts white, clamp orange, comb yellow. Every one")
    print("of those is printed. The metal is the grey: the frame members, the")
    print("arm beam, the rails, the Z posts and the leadscrew.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
