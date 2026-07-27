"""CableCell layout — the single source of every dimension in the machine.

Nothing else in `sim/` may hard-code a dimension. If a number matters, it lives
here, and the scene builder and studies derive from it.

UNITS ARE MILLIMETRES AND DEGREES throughout, matching the docs and the BOM.
MuJoCo works in metres and radians; conversion happens once, at the scene-build
boundary (`build_scene.py`), never here.

Datums (see docs/datums.md):
    A - deck plane        z = 0, positive up
    B - pivot axis        x = y = 0, normal to A
    C - per-station Z     each station has its own engagement height Z1..Z7

Every dimension carries a provenance status, because roughly half of them are
not yet real:

    COMMITTED  - decided, or measured from a vendor spec
    ESTIMATED  - reasoned from a known class of part, good to maybe +/-20%
    PLACEHOLDER- a number chosen so the model runs; carries no information

`report()` prints what is still soft. Run it before believing any output of
this model.
"""

from __future__ import annotations

import math

COMMITTED = "committed"
ESTIMATED = "estimated"
PLACEHOLDER = "placeholder"

_REGISTRY: list[Dim] = []


class Dim(float):
    """A float that remembers where it came from.

    Subclasses float so it drops straight into arithmetic — `ARM_R0 * 2` works
    and yields a plain float. The provenance is for humans and for `report()`.
    """

    status: str
    source: str
    name: str

    def __new__(cls, value: float, status: str, source: str = "", name: str = "") -> Dim:
        self = float.__new__(cls, value)
        self.status = status
        self.source = source
        self.name = name
        _REGISTRY.append(self)
        return self


def _d(value: float, status: str, source: str = "", name: str = "") -> Dim:
    return Dim(value, status, source, name)


# ---------------------------------------------------------------------------
# 1. The press — placed FIRST, because it is the layout datum (Kyle 2026-07-26)
# ---------------------------------------------------------------------------
# Class: 1.5T/15kN taped-terminal crimping press for mini applicators.
# Footprint/height/weight/stroke are vendor-published and verified 2026-07-26.
# Everything about where the crimp point sits inside that envelope is not.

PRESS_WIDTH = _d(210.0, COMMITTED, "vendor spec 2026-07-26", "PRESS_WIDTH")
PRESS_DEPTH = _d(210.0, COMMITTED, "vendor spec 2026-07-26", "PRESS_DEPTH")
PRESS_HEIGHT = _d(580.0, COMMITTED, "vendor spec 2026-07-26", "PRESS_HEIGHT")
PRESS_MASS_KG = _d(35.0, COMMITTED, "vendor spec 2026-07-26", "PRESS_MASS_KG")
PRESS_STROKE = _d(30.0, COMMITTED, "vendor spec 2026-07-26", "PRESS_STROKE")

# How far the ram axis sits back from the press's front face. Decides whether
# the arm can physically reach the anvil, and therefore constrains R0.
# ASK THE SELLER or measure on arrival - checklist item on 657.1.
PRESS_RAM_FROM_FRONT = _d(70.0, PLACEHOLDER, "unmeasured", "PRESS_RAM_FROM_FRONT")

# Height of the applicator base plate above the bench. On a column press the
# lower part of the 580mm is motor and gearbox. Measure on arrival.
PRESS_BASEPLATE_ABOVE_BENCH = _d(
    200.0, ESTIMATED, "column-press class", "PRESS_BASEPLATE_ABOVE_BENCH"
)

# Height of the wire/anvil line above the applicator's own base surface.
# THE key unknown for Z4. Two attempts to extract it from published drawings
# failed 2026-07-26 (Molex host reset, JST PDF needs poppler). Measured when the
# donor applicator arrives - checklist item on 657.5.
APPLICATOR_WIRE_ABOVE_BASE = _d(
    30.0, PLACEHOLDER, "unmeasured", "APPLICATOR_WIRE_ABOVE_BASE"
)

# OTP clone applicator envelope, from listing copy.
APPLICATOR_LENGTH = _d(225.0, ESTIMATED, "OTP listing 2026-07-26", "APPLICATOR_LENGTH")
APPLICATOR_WIDTH = _d(80.0, ESTIMATED, "OTP listing 2026-07-26", "APPLICATOR_WIDTH")
APPLICATOR_HEIGHT = _d(165.0, ESTIMATED, "OTP listing 2026-07-26", "APPLICATOR_HEIGHT")


# ---------------------------------------------------------------------------
# 2. Deck height — chosen to MINIMISE Z travel
# ---------------------------------------------------------------------------
# Non-obvious but important. The press's crimp point is fixed high off the bench;
# every other station's tooling is short and sits on the deck. If the deck were
# at bench level, the Z stage would have to span that whole difference — and Z
# travel costs stiffness, which lands directly on the comb deflection budget.
#
# So the deck is deliberately raised on the frame to bring the other six
# stations up near the press's crimp height, collapsing the Z range.

CRIMP_POINT_ABOVE_BENCH = _d(
    float(PRESS_BASEPLATE_ABOVE_BENCH + APPLICATOR_WIRE_ABOVE_BASE),
    PLACEHOLDER,
    "derived from two unmeasured terms",
    "CRIMP_POINT_ABOVE_BENCH",
)

# Typical tooling height for the short stations (guillotine, slit die, strip
# die, nest) measured from the deck they bolt to.
STATION_TOOLING_HEIGHT = _d(
    60.0, ESTIMATED, "printed station class", "STATION_TOOLING_HEIGHT"
)

DECK_ABOVE_BENCH = _d(
    float(CRIMP_POINT_ABOVE_BENCH - STATION_TOOLING_HEIGHT),
    PLACEHOLDER,
    "derived to minimise Z travel",
    "DECK_ABOVE_BENCH",
)


# ---------------------------------------------------------------------------
# 3. Rotary layout — R0 and the seven angular stops
# ---------------------------------------------------------------------------
# theta = 0 is assigned to S1 (feed/cut). Positive theta is counter-clockwise
# viewed from above. The arm sweeps a working ARC, not a full turn, so the
# trailing ribbon never wraps the pivot: no slip ring, no rotary air union.

SWEEP_ARC = _d(270.0, COMMITTED, "cell-design.md", "SWEEP_ARC")

# Bolt circle radius. cell-design.md carries ~150mm (a 300mm circle), but that
# was written before the press was understood as a standalone machine. The
# angular-fit check in studies/fit_check.py exists to test it.
ARM_R0 = _d(200.0, ESTIMATED, "angular fit, see fit_check", "ARM_R0")

# Angular half-width each station occupies at R0, from its physical width.
STATION_WIDTH = _d(80.0, ESTIMATED, "printed station class", "STATION_WIDTH")

# Radial stroke of the arm: how far it extends from retracted to engaged.
ARM_STROKE = _d(80.0, ESTIMATED, "MGN12 slide class", "ARM_STROKE")


# Station identifiers, in cycle order.
STATIONS = ("S1_FEED", "S2_SLIT", "S3_STRIP", "S4_CRIMP", "S5_INSERT", "S6_DROP", "S6_REJECT")

# Angular positions. S1 is 0 by definition; S4 (crimp) is anchored by where the
# press physically goes; the rest are spread across the remaining arc.
# PLACEHOLDER spacing — fit_check.py tests whether they actually fit.
STATION_ANGLES: dict[str, Dim] = {
    "S1_FEED": _d(0.0, COMMITTED, "assigned by definition", "theta_S1"),
    "S2_SLIT": _d(35.0, PLACEHOLDER, "even spread", "theta_S2"),
    "S3_STRIP": _d(70.0, PLACEHOLDER, "even spread", "theta_S3"),
    "S4_CRIMP": _d(135.0, PLACEHOLDER, "press placement not fixed", "theta_S4"),
    "S5_INSERT": _d(200.0, PLACEHOLDER, "even spread", "theta_S5"),
    "S6_DROP": _d(240.0, PLACEHOLDER, "even spread", "theta_S6"),
    "S6_REJECT": _d(265.0, PLACEHOLDER, "even spread", "theta_S6r"),
}

# Per-station engagement heights above the deck (Datum C). These are CONFIG,
# calibrated by touching off at commissioning — the whole point of the Z axis.
# Values here only need to be close enough for the rough-in to be meaningful.
STATION_Z: dict[str, Dim] = {
    "S1_FEED": _d(60.0, PLACEHOLDER, "station tooling class", "Z_S1"),
    "S2_SLIT": _d(60.0, PLACEHOLDER, "station tooling class", "Z_S2"),
    "S3_STRIP": _d(60.0, PLACEHOLDER, "station tooling class", "Z_S3"),
    "S4_CRIMP": _d(60.0, PLACEHOLDER, "= crimp point by construction", "Z_S4"),
    "S5_INSERT": _d(60.0, PLACEHOLDER, "station tooling class", "Z_S5"),
    "S6_DROP": _d(80.0, PLACEHOLDER, "drop clear of bin rim", "Z_S6"),
    "S6_REJECT": _d(80.0, PLACEHOLDER, "drop clear of bin rim", "Z_S6r"),
}

# Clearance height for rotation. Must sit above the tallest station tooling
# intrusion. With a Z axis, rotation clearance is VERTICAL (lift, rotate,
# descend) rather than radial — which is what decouples station tooling design
# from the arm's sweep path.
Z_CLEAR_MARGIN = _d(15.0, ESTIMATED, "handling clearance", "Z_CLEAR_MARGIN")


# ---------------------------------------------------------------------------
# 4. The arm
# ---------------------------------------------------------------------------

COMB_CHANNELS = 3
COMB_PITCH = _d(8.0, COMMITTED, "cell-design.md 5.4", "COMB_PITCH")
CROSS_SLIDE_STROKE = _d(20.0, COMMITTED, "cell-design.md 5.2", "CROSS_SLIDE_STROKE")
TAIL_PROJECTION = _d(28.0, COMMITTED, "cell-design.md 3 step 2", "TAIL_PROJECTION")
SPLIT_LENGTH = _d(25.0, COMMITTED, "recipe SPOX-3P", "SPLIT_LENGTH")
STRIP_LENGTH = _d(2.75, COMMITTED, "recipe SPOX-3P", "STRIP_LENGTH")
CAVITY_PITCH = _d(2.5, COMMITTED, "Molex 5264 TRUE 2.5mm", "CAVITY_PITCH")
INSERT_DEPTH = _d(6.0, COMMITTED, "recipe SPOX-3P", "INSERT_DEPTH")
PULLBACK = _d(1.5, COMMITTED, "recipe SPOX-3P", "PULLBACK")

MAIN_BEARING_BORE = _d(90.0, ESTIMATED, "80-100mm range, cell-design.md", "MAIN_BEARING_BORE")
ARM_THICKNESS = _d(25.0, ESTIMATED, "stiffness guess", "ARM_THICKNESS")
ARM_WIDTH = _d(60.0, ESTIMATED, "MGN12 carriage width", "ARM_WIDTH")


# ---------------------------------------------------------------------------
# 4b. Arm-mounted camera (Kyle 2026-07-26)
# ---------------------------------------------------------------------------
# One camera rides the arm and looks at whichever station it faces. Two jobs:
#   1. Step-readiness / operation verification (did the slit happen, is the
#      ribbon gripped, are the conductors fanned).
#   2. Station registration against an AprilTag at each stop — which turns
#      droop, detent error and belt backlash from assumed-repeatable into
#      measured-and-corrected.
#
# Realistic accuracy for tag36h11 pose at this working distance with a 3.6 mm
# lens is ~+/-0.5-1 mm. Good enough for registration and presence; NOT good
# enough for insertion. Sub-mm still comes from mechanical repeatability plus
# the funnel capture window.
#
# Hardware reuses TendWright's fleet: ELP-USBFHD01M-L36, 1920x1080, and the
# cameras.py / camserve.py stack (identity by USB port path).

CAMERA_BOARD = _d(38.0, ESTIMATED, "ELP-USBFHD01M board", "CAMERA_BOARD")
CAMERA_DEPTH = _d(30.0, ESTIMATED, "board + M12 lens", "CAMERA_DEPTH")
CAMERA_MASS_G = _d(28.0, ESTIMATED, "ELP board + lens", "CAMERA_MASS_G")

# Mounted behind and above the comb, looking radially outward and down at the
# station work point. Offsets are from the comb.
# Offsets from the comb. CAMERA_TILT is degrees BELOW horizontal, positive down.
# Validated by sim/studies/camera_check.py, which checks every station tag for
# framing, range and obliquity.
CAMERA_BACK_OFFSET = _d(62.0, ESTIMATED, "camera_check validated", "CAMERA_BACK_OFFSET")
CAMERA_UP_OFFSET = _d(48.0, ESTIMATED, "camera_check validated", "CAMERA_UP_OFFSET")
CAMERA_TILT = _d(33.0, ESTIMATED, "camera_check validated", "CAMERA_TILT")

# AprilTag at each station, tag36h11. TendWright prints these at 40 mm.
STATION_TAG_SIZE = _d(25.0, ESTIMATED, "scaled from TendWright 40mm", "STATION_TAG_SIZE")


# ---------------------------------------------------------------------------
# 4c. Ribbon and spool
# ---------------------------------------------------------------------------
# CORRECTION 2026-07-26: cell-design.md gives ribbon pitch as ~2.5 mm. That is
# the CONNECTOR cavity pitch borrowed by mistake. Derived from 22 AWG / 60 cores
# x 0.08 mm / 1.4 mm OD, the real conductor pitch is ~1.4-1.5 mm. Consequence:
# the webs sit at +/-0.7 mm from centreline, so S2's slitting blades are finer
# and closer together than the doc implies. MEASURE ON ARRIVAL before cutting
# any tooling.

RIBBON_CONDUCTOR_OD = _d(1.4, ESTIMATED, "vendor spec", "RIBBON_CONDUCTOR_OD")
RIBBON_PITCH = _d(1.45, ESTIMATED, "derived, was wrongly 2.5", "RIBBON_PITCH")
RIBBON_WIDTH = _d(4.5, ESTIMATED, "3 x OD + webs", "RIBBON_WIDTH")
RIBBON_THICKNESS = _d(1.4, ESTIMATED, "= conductor OD", "RIBBON_THICKNESS")
RIBBON_LENGTH_STOCK = _d(15240.0, COMMITTED, "50 ft spool", "RIBBON_LENGTH_STOCK")
RIBBON_MASS_PER_M = _d(16.4, COMMITTED, "250 g / 50 ft", "RIBBON_MASS_PER_M")

# The wire ships as a LOOSE ROLL, not on a rigid spool — so the spool is ours
# to design. Sized in spool_capacity_m() below; printed, 8 mm bore to match the
# hardened rod stock already on the BOM for the Z stage.
SPOOL_HUB_R = _d(30.0, ESTIMATED, "printable, min bend radius", "SPOOL_HUB_R")
SPOOL_FLANGE_R = _d(55.0, ESTIMATED, "capacity + margin", "SPOOL_FLANGE_R")
SPOOL_INNER_WIDTH = _d(25.0, ESTIMATED, "5 wraps of 4.5mm ribbon", "SPOOL_INNER_WIDTH")
SPOOL_FLANGE_T = _d(3.0, ESTIMATED, "printed stiffness", "SPOOL_FLANGE_T")
SPOOL_BORE = _d(8.0, COMMITTED, "matches Z-stage rod stock", "SPOOL_BORE")

# The spool hangs outboard of S1, off-deck, on a printed bracket.
SPOOL_AXLE_HEIGHT = _d(150.0, PLACEHOLDER, "above deck", "SPOOL_AXLE_HEIGHT")
SPOOL_RADIAL_OFFSET = _d(90.0, PLACEHOLDER, "outboard of S1", "SPOOL_RADIAL_OFFSET")

# Dancer arm: passive payoff at constant light tension; its flag doubles as the
# spool-empty detect.
DANCER_ARM_LENGTH = _d(70.0, ESTIMATED, "sets tension travel", "DANCER_ARM_LENGTH")

# Measuring wheel: 31.83 mm diameter gives EXACTLY 100.00 mm circumference, so
# with a 600 P/R encoder in quadrature (2400 counts/rev) length in mm is just
# counts * 100 / 2400 = 0.0417 mm per count. Chosen, not inherited.
#
# CAVEAT: that is the nominal. Effective circumference depends on how far the
# ribbon compresses under preload, so it is a CALIBRATION CONSTANT measured at
# commissioning, not a constant to trust. The clean number is a convenience for
# sanity-checking, not a guarantee. Do NOT add a rubber tyre or O-ring for grip
# — it changes the effective circumference and its compression varies.
MEASURING_WHEEL_DIA = _d(31.83, COMMITTED, "100.00 mm circumference", "MEASURING_WHEEL_DIA")
MEASURING_WHEEL_WIDTH = _d(9.0, ESTIMATED, "wider than ribbon", "MEASURING_WHEEL_WIDTH")
MEASURING_WHEEL_BORE = _d(5.0, ESTIMATED, "encoder shaft", "MEASURING_WHEEL_BORE")
ENCODER_PPR = _d(600.0, ESTIMATED, "optical, quadrature", "ENCODER_PPR")

# Presentation gap: PTFE tube exit to comb face at the grip position. Long
# enough that the comb never hits the tube across Z and R tolerance; short
# enough that ~28 mm of unsupported tail cannot buckle when the rollers push.
PRESENTATION_GAP = _d(8.0, ESTIMATED, "buckle vs collision", "PRESENTATION_GAP")


# ---------------------------------------------------------------------------
# 5. The Z stage
# ---------------------------------------------------------------------------
# Commodity ballscrew linear module (SFU1605 + dual rails + NEMA 17/23).
# Travel wants to be the SHORTEST defensible number — stiffness falls off with
# stroke, and this stage sits at the bottom of a long lever carrying the entire
# rotating assembly, so its compliance is magnified at the comb.

Z_STAGE_MARGIN = _d(20.0, ESTIMATED, "commissioning headroom", "Z_STAGE_MARGIN")

# Guide posts on a circle around the pivot, with the leadscrew OFF-AXIS so the
# rotary axis at the platform centre stays clear. This is the arrangement a
# single coaxial rail cannot give us.
# Posts must clear the main bearing's OUTER diameter, not its bore. A 90 mm-bore
# slew ring runs ~120 mm OD, so anything inside r=60 fouls it. 78 mm gives the
# bearing 18 mm of radial room and still keeps the platform compact.
# (Caught 2026-07-26: the first value, 46 mm, put the posts inside the bearing.)
Z_POST_CIRCLE_R = _d(78.0, ESTIMATED, "clears bearing OD + margin", "Z_POST_CIRCLE_R")
MAIN_BEARING_OD = _d(120.0, ESTIMATED, "90mm-bore slew ring class", "MAIN_BEARING_OD")
Z_POST_DIA = _d(8.0, COMMITTED, "hardened rod stock", "Z_POST_DIA")


# ---------------------------------------------------------------------------
# 5b. Bought-hardware interface dimensions
# ---------------------------------------------------------------------------
# Industry-standard footprints the printed parts must mate to. These are stable
# across vendors, which is why designing against them now is safe even though
# the specific parts are not ordered.

LM8UU_OD = _d(15.0, COMMITTED, "LM8UU standard", "LM8UU_OD")
LM8UU_LEN = _d(24.0, COMMITTED, "LM8UU standard", "LM8UU_LEN")

MGN12_CARRIAGE_W = _d(27.0, COMMITTED, "MGN12H standard", "MGN12_CARRIAGE_W")
MGN12_BOLT_X = _d(20.0, COMMITTED, "MGN12H M3 pattern", "MGN12_BOLT_X")
MGN12_BOLT_Y = _d(20.0, COMMITTED, "MGN12H M3 pattern", "MGN12_BOLT_Y")

MGN9_CARRIAGE_W = _d(20.0, COMMITTED, "MGN9C standard", "MGN9_CARRIAGE_W")
MGN9_BOLT_X = _d(20.0, COMMITTED, "MGN9C M3 pattern", "MGN9_BOLT_X")
MGN9_BOLT_Y = _d(10.0, COMMITTED, "MGN9C M3 pattern", "MGN9_BOLT_Y")

NEMA17_SQUARE = _d(42.3, COMMITTED, "NEMA 17 standard", "NEMA17_SQUARE")
NEMA17_BOLT = _d(31.0, COMMITTED, "NEMA 17 M3 pattern", "NEMA17_BOLT")
NEMA17_BOSS_DIA = _d(22.0, COMMITTED, "NEMA 17 standard", "NEMA17_BOSS_DIA")

T8_NUT_FLANGE_DIA = _d(22.0, COMMITTED, "T8 POM/brass nut", "T8_NUT_FLANGE_DIA")
T8_NUT_BOLT_CIRCLE = _d(16.0, COMMITTED, "T8 nut M3 pattern", "T8_NUT_BOLT_CIRCLE")

# Standard commodity stroke options, mm.
Z_STAGE_STOCK_STROKES = (50.0, 100.0, 150.0, 200.0, 300.0, 400.0)


# ---------------------------------------------------------------------------
# 6. Frame and deck
# ---------------------------------------------------------------------------

EXTRUSION = _d(30.0, COMMITTED, "3030, cell-design.md 5.1", "EXTRUSION")
DECK_THICKNESS = _d(10.0, COMMITTED, "tooling plate, cell-design.md 5.1", "DECK_THICKNESS")
DECK_RADIUS = _d(
    float(ARM_R0 + STATION_WIDTH), ESTIMATED, "R0 + station depth", "DECK_RADIUS"
)


# ---------------------------------------------------------------------------
# Derived geometry
# ---------------------------------------------------------------------------


def assign_station_angles(radius: float | None = None) -> dict[str, float]:
    """Lay the seven stops out around the arc, respecting their real widths.

    The press is 210 mm wide against a normal station's ~80 mm, so an even
    angular spread is wrong — it either crowds the press or wastes arc. Walk
    the stops in cycle order, giving each its own half-width and sharing the
    leftover arc equally as gaps.

    S1 stays at theta = 0 by definition; the arm sweeps counter-clockwise.
    Returns degrees. Raises if the layout does not close.
    """
    r = ARM_R0 if radius is None else radius
    order = list(STATIONS)

    def half(name: str) -> float:
        width = PRESS_WIDTH if name == "S4_CRIMP" else STATION_WIDTH
        return angular_half_width(float(width), float(r))

    occupied = sum(2.0 * half(n) for n in order)
    gaps = len(order) - 1
    spare = float(SWEEP_ARC) - occupied
    if spare < 0:
        raise ValueError(
            f"layout does not close at R0={float(r):.0f} mm: "
            f"needs {occupied:.1f}° of {float(SWEEP_ARC):.0f}°"
        )
    gap = spare / (gaps + 1)  # leave a half-gap of margin at each end

    angles: dict[str, float] = {}
    cursor = 0.0
    for i, name in enumerate(order):
        if i == 0:
            angles[name] = 0.0
            cursor = half(name)
            continue
        cursor += gap + half(name)
        angles[name] = cursor
        cursor += half(name)
    return angles


def apply_derived_station_angles() -> None:
    """Replace the placeholder spread with the derived layout, in place."""
    for name, value in assign_station_angles().items():
        if name == "S1_FEED":
            continue
        STATION_ANGLES[name] = _d(
            value, ESTIMATED, "derived by assign_station_angles", f"theta_{name}"
        )


def station_xy(name: str, radius: float | None = None) -> tuple[float, float]:
    """Plan-view position of a station's work point, relative to Datum B."""
    r = ARM_R0 if radius is None else radius
    a = math.radians(STATION_ANGLES[name])
    return (r * math.cos(a), r * math.sin(a))


def angular_half_width(physical_width: float, radius: float) -> float:
    """Half-angle (degrees) an object of the given width subtends at a radius.

    Returns 180.0 when the object is too wide to fit at that radius at all,
    which is the honest answer rather than a math domain error.
    """
    ratio = (physical_width / 2.0) / radius
    if ratio >= 1.0:
        return 180.0
    return math.degrees(math.asin(ratio))


def press_angular_width(radius: float | None = None) -> float:
    """Full angle the press body occupies at the bolt circle."""
    return 2.0 * angular_half_width(PRESS_WIDTH, ARM_R0 if radius is None else radius)


def station_angular_width(radius: float | None = None) -> float:
    """Full angle a normal station occupies at the bolt circle."""
    return 2.0 * angular_half_width(STATION_WIDTH, ARM_R0 if radius is None else radius)


def z_clear() -> float:
    """Rotation-safe height: above the tallest station engagement plus margin."""
    return max(STATION_Z.values()) + Z_CLEAR_MARGIN


def z_travel_required() -> float:
    """Z stroke the machine actually needs, before choosing a stock stage."""
    lo = min(STATION_Z.values())
    return (z_clear() - lo) + Z_STAGE_MARGIN


def z_stage_choice() -> float:
    """Smallest stock ballscrew stroke that covers the requirement."""
    need = z_travel_required()
    for stroke in Z_STAGE_STOCK_STROKES:
        if stroke >= need:
            return stroke
    return Z_STAGE_STOCK_STROKES[-1]


def spool_capacity_m(packing: float = 0.80) -> float:
    """How much ribbon the printed spool holds, in metres.

    Wound flat: each wrap builds RIBBON_THICKNESS radially, and
    SPOOL_INNER_WIDTH / RIBBON_WIDTH wraps sit side by side per layer.
    """
    wraps_per_layer = math.floor(float(SPOOL_INNER_WIDTH) / float(RIBBON_WIDTH))
    layers = math.floor(
        (float(SPOOL_FLANGE_R) - float(SPOOL_HUB_R)) / float(RIBBON_THICKNESS)
    )
    total_mm = 0.0
    for i in range(layers):
        r = float(SPOOL_HUB_R) + (i + 0.5) * float(RIBBON_THICKNESS)
        total_mm += wraps_per_layer * 2.0 * math.pi * r
    return total_mm * packing / 1000.0


def spool_holds_stock() -> bool:
    """Does the spool take a whole 50 ft roll?"""
    return spool_capacity_m() >= float(RIBBON_LENGTH_STOCK) / 1000.0


def cable_mass_g(length_mm: float) -> float:
    """Mass of a finished cable — the arm's actual payload."""
    return float(RIBBON_MASS_PER_M) * length_mm / 1000.0


def press_centre_distance() -> float:
    """Pivot to press-body centre, with the press facing the dial.

    The crimp point sits on the bolt circle at R0. The press body extends
    further out by the distance from its front face to the ram axis.
    """
    return ARM_R0 + (PRESS_DEPTH / 2.0 - PRESS_RAM_FROM_FRONT)


# ---------------------------------------------------------------------------
# Provenance reporting
# ---------------------------------------------------------------------------


# Station angles start as an even placeholder spread; replace them with the
# width-aware layout as soon as the helpers above are defined. Done at import so
# every consumer — the scene builder, the studies, the CAD — sees the same
# numbers without having to remember to call it.
apply_derived_station_angles()


def report() -> str:
    """Human-readable summary of what in this model is real and what is not."""
    named = [d for d in _REGISTRY if getattr(d, "name", "")]
    by_status: dict[str, list[Dim]] = {COMMITTED: [], ESTIMATED: [], PLACEHOLDER: []}
    for d in named:
        by_status.setdefault(d.status, []).append(d)

    lines = ["CableCell layout provenance", "=" * 60, ""]
    for status in (PLACEHOLDER, ESTIMATED, COMMITTED):
        items = by_status.get(status, [])
        lines.append(f"{status.upper()} ({len(items)})")
        for d in items:
            lines.append(f"    {d.name:<32} {float(d):>9.2f}   {d.source}")
        lines.append("")

    total = len(named)
    soft = len(by_status.get(PLACEHOLDER, []))
    lines.append(
        f"{soft}/{total} dimensions are placeholders. "
        "Treat any conclusion touching them as provisional."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
