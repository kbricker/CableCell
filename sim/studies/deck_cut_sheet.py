"""Deck cut sheet — imperial, because Kyle cuts the wood.

The machine is metric everywhere else and stays that way; only this one part is
made on a woodworking bench, so only this one part gets stated in inches. Both
units are given side by side so a slip is visible rather than silent.

    uv run python -m sim.studies.deck_cut_sheet          # print the spec
    uv run python -m sim.studies.deck_cut_sheet --draw   # dimensioned template

Everything derives from sim/layout.py — change R0 and the sheet follows.
"""

from __future__ import annotations

import argparse
import math
import pathlib

import numpy as np
from PIL import Image, ImageDraw

from sim import imaging
from sim import layout as L

MM_PER_IN = 25.4


def frac(inches: float, denom: int = 16) -> str:
    """Decimal inches as a shop-readable fraction, e.g. 15-3/4."""
    whole = int(inches)
    num = round((inches - whole) * denom)
    if num == 0:
        return f'{whole}"'
    if num == denom:
        return f'{whole + 1}"'
    g = math.gcd(num, denom)
    if whole == 0:
        return f'{num // g}/{denom // g}"'  # 1/2", not 0-1/2"
    return f'{whole}-{num // g}/{denom // g}"'


def spec() -> dict:
    deck_d_mm = float(L.DECK_RADIUS) * 2.0
    bolt_d_mm = float(L.ARM_R0) * 2.0
    # Central clearance: the Z platform passes through, plus the off-axis motor.
    z_reach_mm = float(L.Z_POST_CIRCLE_R) + float(L.NEMA17_SQUARE) / 2.0
    centre_d_mm = math.ceil((z_reach_mm * 2.0 + 20.0) / MM_PER_IN * 2) / 2 * MM_PER_IN
    return {
        "deck_d": (deck_d_mm, deck_d_mm / MM_PER_IN),
        "thickness": (float(L.DECK_THICKNESS), float(L.DECK_THICKNESS) / MM_PER_IN),
        "bolt_d": (bolt_d_mm, bolt_d_mm / MM_PER_IN),
        "centre_d": (centre_d_mm, centre_d_mm / MM_PER_IN),
        "deck_above_bench": (float(L.DECK_ABOVE_BENCH), float(L.DECK_ABOVE_BENCH) / MM_PER_IN),
        "station_hole_x": (28.0, 28.0 / MM_PER_IN),
        "station_hole_y": (40.0, 40.0 / MM_PER_IN),
    }


def report() -> str:
    s = spec()
    out = ["CableCell deck - cut sheet", "=" * 62, ""]
    out.append('Material: 1/2" plywood or MDF (12 mm nominal). Void-free ply if you')
    out.append("have it - the station bolts land near the top face.")
    out.append("")
    out.append(f"{'feature':<34}{'inches':>14}{'mm':>13}")
    out.append("-" * 62)
    for label, key in (
        ("Outside diameter", "deck_d"),
        ("Thickness", "thickness"),
        ("Centre clearance hole", "centre_d"),
        ("Station bolt circle diameter", "bolt_d"),
        ("Mounts above bench top", "deck_above_bench"),
    ):
        mm, inch = s[key]
        out.append(f"{label:<34}{frac(inch):>14}{mm:>10.1f} mm")

    out.append("")
    out.append("STATION POSITIONS - 7 stops on the bolt circle")
    out.append("Angles from S1, positive counter-clockwise viewed from above.")
    out.append("")
    out.append(f"{'stop':<14}{'angle':>9}{'chord from S1':>18}")
    out.append("-" * 62)
    r_in = s["bolt_d"][1] / 2.0
    for name in L.STATIONS:
        a = float(L.STATION_ANGLES[name])
        chord = 2.0 * r_in * math.sin(math.radians(a) / 2.0)
        out.append(f"{name.replace('_', ' ').lower():<14}{a:>8.1f} deg{frac(chord):>15}")

    out.append("")
    out.append("Chord = straight-line distance from the S1 hole across the face.")
    out.append("Easier to lay out with a tape than to protract an angle.")
    out.append("")
    out.append("PER-STATION HOLES - 4 per stop")
    hx, hy = s["station_hole_x"], s["station_hole_y"]
    out.append(f"  Rectangle {frac(hx[1])} radial x {frac(hy[1])} tangential")
    out.append(f"  ({hx[0]:.0f} x {hy[0]:.0f} mm), centred on the bolt circle at each angle.")
    out.append('  Drill 1/4" (6.5 mm) clearance for M5 hardware.')
    out.append("  The printed station mounts are slotted radially, so a little")
    out.append("  drift is absorbed at assembly.")
    out.append("")
    out.append("PRESS SCALLOP")
    out.append(f"  The press body crosses the disc at the S4 stop "
               f"({float(L.STATION_ANGLES['S4_CRIMP']):.1f} deg).")
    out.append(f"  Cut a scallop {frac(float(L.PRESS_WIDTH) / MM_PER_IN)} wide, inward from the")
    out.append(f"  rim to roughly {frac((float(L.DECK_RADIUS) - 130.0) / MM_PER_IN)} from centre.")
    out.append("  Cut it OVERSIZE and fit to the real press when it arrives - the")
    out.append("  ram-axis depth is still unmeasured.")
    out.append("")
    out.append("TOLERANCE")
    out.append('  Bolt-circle diameter within +/- 1/16" is fine. The station mounts are')
    out.append("  slotted, and every station's height is calibrated in software at")
    out.append("  commissioning - the wood is not holding the precision.")
    return "\n".join(out)


def draw() -> pathlib.Path:
    """Dimensioned plan-view template."""
    s = spec()
    px, margin = 1400, 110
    deck_d_in = s["deck_d"][1]
    scale = (px - 2 * margin) / deck_d_in
    cx = cy = px // 2

    img = Image.new("RGB", (px, px), (252, 251, 248))
    d = ImageDraw.Draw(img)
    f_big, f, f_sm = imaging._font(30), imaging._font(21), imaging._font(17)

    def circle(r_in, **kw):
        r = r_in * scale
        d.ellipse([cx - r, cy - r, cx + r, cy + r], **kw)

    circle(deck_d_in / 2, outline=(30, 30, 30), width=4)
    circle(s["centre_d"][1] / 2, outline=(30, 30, 30), width=3)
    circle(s["bolt_d"][1] / 2, outline=(190, 60, 50), width=2)

    r_bolt = s["bolt_d"][1] / 2
    hx_in, hy_in = s["station_hole_x"][1], s["station_hole_y"][1]
    for name in L.STATIONS:
        a = math.radians(float(L.STATION_ANGLES[name]))
        x = cx + r_bolt * scale * math.cos(a)
        y = cy - r_bolt * scale * math.sin(a)
        for sx in (-0.5, 0.5):
            for sy in (-0.5, 0.5):
                ox = sx * hx_in * scale * math.cos(a) - sy * hy_in * scale * math.sin(a)
                oy = -(sx * hx_in * scale * math.sin(a) + sy * hy_in * scale * math.cos(a))
                d.ellipse([x + ox - 5, y + oy - 5, x + ox + 5, y + oy + 5], fill=(190, 60, 50))
        d.line([cx, cy, x, y], fill=(218, 200, 196), width=1)
        lx = cx + (r_bolt + 0.9) * scale * math.cos(a)
        ly = cy - (r_bolt + 0.9) * scale * math.sin(a)
        d.text((lx - 28, ly - 11), name.replace("_", " ").replace("S6 ", "").upper(),
               font=f_sm, fill=(40, 40, 40))

    d.text((margin - 45, 28), 'CableCell deck  -  1/2" plywood', font=f_big, fill=(20, 20, 20))
    d.text((margin - 45, 70),
           f'OD {frac(deck_d_in)}     bolt circle {frac(s["bolt_d"][1])}     '
           f'centre hole {frac(s["centre_d"][1])}',
           font=f, fill=(70, 70, 70))
    d.text((margin - 45, px - 78),
           f'Angles from S1, counter-clockwise from above. 4 holes per stop, '
           f'{frac(hx_in)} x {frac(hy_in)}, 1/4" clearance.',
           font=f_sm, fill=(70, 70, 70))
    d.text((margin - 45, px - 52),
           "NOT TO SCALE - lay out from the dimensions, do not measure this sheet.",
           font=f_sm, fill=(175, 60, 50))

    return imaging.save_png(pathlib.Path(__file__).parent / "renders" / "deck_cut_sheet.png",
                            np.asarray(img))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draw", action="store_true", help="also write the template image")
    args = ap.parse_args()
    text = report()
    print(text)
    doc = pathlib.Path(__file__).parent.parent.parent / "docs" / "deck-cut-sheet.md"
    doc.write_text(
        "# Deck cut sheet\n\n*Generated by `sim/studies/deck_cut_sheet.py` — do not "
        "edit by hand. Re-run it if R₀ or the station layout changes.*\n\n```\n"
        + text + "\n```\n",
        encoding="utf-8",
    )
    print(f"\nwrote {doc}")
    if args.draw:
        print(f"wrote {draw()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
