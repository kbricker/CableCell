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

# 1/2" nominal plywood, which is what Kyle is actually cutting — NOT the 10 mm
# aluminium tooling plate cell-design.md originally assumed. Defined here rather
# than down with the stock sizes because the engagement plane is derived from
# it, and deck_cut_sheet.py reads it so the shop drawing cannot drift.
DECK_THICKNESS = _d(12.0, COMMITTED, '1/2" ply, Kyle supplies and cuts', "DECK_THICKNESS")

# Every station bolts to the same printed base, so its thickness is part of the
# stack between the deck and the ribbon.
STATION_MOUNT_T = _d(10.0, COMMITTED, "station_mount base", "STATION_MOUNT_T")

# How far each station part's RIBBON PASSAGE sits above that part's own base.
# Read straight off the CAD in cad/build_parts.py, which imports these back so
# the printed part and this table cannot disagree.
# Only parts that sit ON the engagement plane belong here. The feeder (drive
# rollers, encoder wheel, spool, dancer) deliberately does NOT — see
# PRESENTATION_GAP below.
STATION_PART_PASSAGE: dict[str, Dim] = {
    "feed_head": _d(34.0, COMMITTED, "cut line, build_parts", "PASS_feedhead"),
    "strip_die": _d(34.0, COMMITTED, "strip line, build_parts", "PASS_stripdie"),
    "splitting_wedge": _d(18.0, COMMITTED, "channel floor, build_parts", "PASS_wedge"),
    "spreader_plate": _d(4.0, COMMITTED, "mid-plate, build_parts", "PASS_spreader"),
}

# Tube exit to the cut line. Long enough that the blade and the tube are
# separate features that can each be made properly; short enough that the
# unsupported ribbon between them cannot buckle when the rollers push it out.
#
# This is now a MOULDED-IN dimension rather than an assembly tolerance, because
# the tube bore and the blade guideway are features of one part (feed_head).
# That matters more than it looks: the cut line is the datum every measured
# length is taken from, so any play between tube and blade would land directly
# on the machine's headline spec.
PRESENTATION_GAP = _d(8.0, COMMITTED, "docs/stations.md 1", "PRESENTATION_GAP")

# ---------------------------------------------------------------------------
# Body clamp — the part that must not slip
# ---------------------------------------------------------------------------
# S3 pulls insulation off three conductors at once by RETRACTING THE ARM 4 mm.
# There is no dedicated pull-off actuator, which is a saving, but it means the
# clamp holding the ribbon body takes the whole ~50 N.
#
# If the ribbon creeps in the clamp during pull-off, strip length is wrong AND
# the measured cable length is wrong, because the ribbon has moved relative to
# the datum the encoder established. A slipping clamp corrupts the machine's
# headline spec SILENTLY - nothing downstream notices. That makes it the single
# most safety-critical printed part in Phase 1.
#
# Sprung closed, air OPENS it. That is the opposite of the obvious arrangement
# and it is deliberate: a single-acting cylinder is simpler and cheaper than a
# double-acting one, and losing air pressure then fails to GRIPPING rather than
# dropping a part mid-cycle.
CLAMP_FORCE_N = _d(80.0, ESTIMATED, "1.6x the 50 N pull-off", "CLAMP_FORCE_N")
CLAMP_JAW_LENGTH = _d(16.0, ESTIMATED, "grip area vs comb clearance", "CLAMP_JAW_LENGTH")
CLAMP_SERRATION_PITCH = _d(1.2, ESTIMATED, "bite without cutting PVC", "CLAMP_SERRATION_PITCH")
CLAMP_OPEN_GAP = _d(3.0, ESTIMATED, "ribbon entry clearance", "CLAMP_OPEN_GAP")

# ---------------------------------------------------------------------------
# S3 strip die
# ---------------------------------------------------------------------------
# Three V-blade pairs at COMB_PITCH, one stroke, so all three conductors get
# the same strip length BY CONSTRUCTION rather than by three separate settings.
#
# Depth is the whole game and it is set by a swappable SHIM, not by an
# adjustment screw. A screw can be knocked; a shim is a discrete part you can
# hold up and identify. Too shallow and the slug will not part; too deep and
# the blade nicks strands, which does not fail here - it fails a pull test two
# stations later, after the crimp, which is the expensive kind of failure.
STRIP_BLADE_ANGLE = _d(60.0, ESTIMATED, "included angle, V blade", "STRIP_BLADE_ANGLE")
STRIP_SHIM_T = _d(1.10, ESTIMATED, "= OD - 2x0.15 wall left", "STRIP_SHIM_T")
STRIP_SLUG_DROP = _d(30.0, ESTIMATED, "chute clears mechanism", "STRIP_SLUG_DROP")


def tallest_passage() -> float:
    """The part that forces the engagement plane. Currently the guillotine."""
    return max(float(v) for v in STATION_PART_PASSAGE.values())


# THE ENGAGEMENT PLANE, and why there is only one of it.
#
# Kyle 2026-07-27, asked whether to derive this per station: "yes ... we want to
# make the travel needed as minimal as possible." Those two goals pull against
# each other — deriving a height per station from that station's tallest part
# gives every stop a DIFFERENT height, and the spread between them is Z travel
# the machine then has to have.
#
# So it is derived, but derived ONCE, from the tallest part anywhere on the
# dial. Every station meets the ribbon on the same plane; the difference between
# a part's own passage height and this plane is taken up by a printed standoff
# under that part, which costs grams. Z travel is then needed only to lift clear
# during rotation, not to chase stations up and down.
#
# That is the minimum travel this architecture can have, and it is the right
# trade: standoffs are free and stiffness falls off with stroke.
STATION_TOOLING_HEIGHT = _d(
    float(DECK_THICKNESS) + float(STATION_MOUNT_T) + tallest_passage(),
    COMMITTED,
    "derived: deck + mount + tallest part passage",
    "STATION_TOOLING_HEIGHT",
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

# Per-station engagement heights above Datum A. These are still CONFIG — each
# is touched off at commissioning, which is the whole point of having a Z axis —
# but they are now all the SAME derived plane rather than seven guesses.
#
# S6 drop and reject used to sit 20 mm high, to clear a bin rim. That was 20 mm
# of Z travel bought to solve a problem the chute can solve for free: put the
# chute MOUTH on the engagement plane and let the cable fall through it to a bin
# under the deck. The arm never lifts to drop. See docs/decisions.md.
STATION_Z: dict[str, Dim] = {
    name: _d(
        float(STATION_TOOLING_HEIGHT),
        COMMITTED,
        "single derived engagement plane",
        f"Z_{name}",
    )
    for name in STATIONS
}

# Clearance height for rotation. Must sit above the tallest station tooling
# intrusion. With a Z axis, rotation clearance is VERTICAL (lift, rotate,
# descend) rather than radial — which is what decouples station tooling design
# from the arm's sweep path.
Z_CLEAR_MARGIN = _d(15.0, ESTIMATED, "handling clearance", "Z_CLEAR_MARGIN")

# ---------------------------------------------------------------------------
# Z stage sits UNDER the deck, not on it
# ---------------------------------------------------------------------------
# The platform was originally mounted on top of the deck. That forced the guide
# posts to stand ~80 mm proud of the deck — because they have to keep guiding
# the platform at the top of its travel — and the arm swept straight through
# them. Kyle found it in the viewer in about ten seconds: "how can the arm just
# travel trough them?"
#
# The deck already has a 7" centre clearance hole cut for the platform to pass
# THROUGH; the scene simply was not using it. Dropping the platform below the
# deck puts the whole guide system underneath, and the arm sweeps over the lot.
#
# Second benefit, and the reason this is a better design rather than just a
# fix: it gives the spindle room to be TALL, so the two 6810s can sit further
# apart. Bearing spacing is the lever arm that turns the cantilever moment into
# a couple — the entire reason paired bearings replaced a slew ring. 50 -> 75 mm
# is a 1.5x cut in bearing load for free.
Z_PLATFORM_BASE = _d(100.0, COMMITTED, "under the deck, clears the arm", "Z_PLATFORM_BASE")
Z_PLATFORM_T = _d(10.0, COMMITTED, "z_platform plate thickness", "Z_PLATFORM_T")


def z_post_top() -> float:
    """Height the guide posts must reach, mm above bench.

    They have to still be guiding the platform's bearings when it is at the top
    of its travel — that requirement is what pushed them into the arm before.
    """
    return (
        float(Z_PLATFORM_BASE) + z_stage_choice() + float(LM8UU_LEN) + 10.0
    )


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

MAIN_BEARING_BORE = _d(50.0, COMMITTED, "6810 spindle bore", "MAIN_BEARING_BORE")

# THE ARM IS THREE THINGS, NOT ONE. It was drawn as a single 230 x 60 x 25 mm
# box — the largest object in the machine and the last greybox in it, which is
# exactly why Kyle spotted it on sight: "the arm seems huge, its a big white
# piece, i'm not sure whats really going on at all with that."
#
#   rotor_plate   printed, joins the spindle flange to the beam
#   beam          BOUGHT 2020 aluminium extrusion
#   MGN12 rail    BOUGHT, on the beam's top face; the radial carriage rides it
#
# Drawn as one solid, two bought parts and one printed part read as a mystery
# slab, and the BOM could not see them at all.
#
# The 60 x 25 section was also a guess, and a wildly conservative one — see
# arm_tip_deflection(). 2020 extrusion is 12x inside the tolerance that
# actually matters, at roughly a ninth of the cross-section.
ARM_WIDTH = _d(20.0, COMMITTED, "2020 extrusion", "ARM_WIDTH")
ARM_THICKNESS = _d(20.0, COMMITTED, "2020 extrusion", "ARM_THICKNESS")
ARM_SECOND_MOMENT = _d(8000.0, ESTIMATED, "2020 extrusion Ix ~0.8 cm4", "ARM_SECOND_MOMENT")
ARM_TIP_LOAD_N = _d(5.0, ESTIMATED, "carriage+comb+camera+wrist ~0.5 kg", "ARM_TIP_LOAD_N")
ALU_E_MPA = _d(69000.0, COMMITTED, "aluminium 6063", "ALU_E_MPA")


def arm_tip_deflection() -> float:
    """Static tip droop of the beam under its own end load, mm.

    Cantilever: d = F L^3 / (3 E I).

    Worth stating what this is and is not. It is NOT a strength check — nothing
    here is close to yielding. It is not even really an accuracy check, because
    a CONSTANT droop is an offset the station Z table absorbs at commissioning.
    It is a sanity bound: if this number were anywhere near the +/-0.3 mm strip
    tolerance, the beam would be the thing to fix. At 24 um against 300 um it
    plainly is not, which is what licenses dropping from a 60 x 25 slab to
    stock 2020 extrusion.
    """
    return (
        float(ARM_TIP_LOAD_N) * float(ARM_R0) ** 3
        / (3.0 * float(ALU_E_MPA) * float(ARM_SECOND_MOMENT))
    )


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
# CONFIRMED FROM THE VENDOR SPEC 2026-07-27, not derived and not deferred.
# The listing states: 22 AWG, 60 cores x 0.08 mm, "Outer Diameter of Cable:
# 1.4mm", tinned copper + PVC, 50 ft weighing ~250 g.
#
# cell-design.md gave ribbon pitch as ~2.5 mm. That was the CONNECTOR cavity
# pitch borrowed by mistake. Flat JR/Futaba servo wire is three PVC-insulated
# conductors co-extruded tangent to each other, so pitch = conductor OD = 1.40 mm
# and overall width = 3 x 1.40 = 4.20 mm.
#
# THE IMPORTANT ONE: this cable is designed to be SEPARATED BY HAND. That is what
# flat servo wire is for - you zip the three conductors apart to terminate them.
# The web between conductors is therefore deliberately thin and weak, which
# changes S2 from a precision depth-controlled slitting die into something much
# closer to a splitting wedge. See docs/stations.md 2.
RIBBON_CONDUCTOR_OD = _d(1.40, COMMITTED, "vendor spec 2026-07-27", "RIBBON_CONDUCTOR_OD")
RIBBON_PITCH = _d(1.40, COMMITTED, "= OD, tangent co-extrusion", "RIBBON_PITCH")
RIBBON_WIDTH = _d(4.20, COMMITTED, "3 x OD", "RIBBON_WIDTH")
RIBBON_THICKNESS = _d(1.40, COMMITTED, "= conductor OD", "RIBBON_THICKNESS")
RIBBON_STRANDS = _d(60.0, COMMITTED, "vendor spec", "RIBBON_STRANDS")
RIBBON_STRAND_DIA = _d(0.08, COMMITTED, "vendor spec", "RIBBON_STRAND_DIA")
RIBBON_HAND_SEPARABLE = True  # the web is designed to zip apart
RIBBON_LENGTH_STOCK = _d(15240.0, COMMITTED, "50 ft spool", "RIBBON_LENGTH_STOCK")
RIBBON_MASS_PER_M = _d(16.4, COMMITTED, "250 g / 50 ft", "RIBBON_MASS_PER_M")


# ---------------------------------------------------------------------------
# 4d. S2 splitting wedge (Kyle 2026-07-27 — "we can run with that assumption")
# ---------------------------------------------------------------------------
# S2 is a FIXED PRINTED WEDGE, not a slitting die. The ribbon is designed to be
# zipped apart by hand, so we are not cutting insulation — we start a tear in a
# deliberately weak web and let geometry propagate it.
#
# Division of labour, and the reason this is two parts and not one:
#   the WEDGE starts both tears over a short ramp;
#   the SPREADER PLATE propagates them and fans the tails to comb pitch.
# Splitting them means the tear-start geometry (the uncertain part) can be
# reprinted without touching the fan geometry (the settled part).
#
# Three tangent conductors have TWO webs, at +/- RIBBON_PITCH/2 from centreline,
# so the wedge has two tips 1.40 mm apart. Each tip is centred on its web line
# and grows OUTWARD only — the inner faces stay clear of the centre conductor,
# which must not be displaced.
#
# Split length is NOT set here. It is set by how far the arm advances, which
# makes it a commanded number rather than a tooling dimension. That is the whole
# point of the wedge route.
#
# None of the four values below is measured. They are print-resolution and
# geometry reasoning, and they are cheap to iterate: leading-edge radius and
# included angle are the only two variables, and a reprint is hours not dollars.
# Fallback if the tear wanders is the $32 pneumatic die, still purchasable then.

WEDGE_WEB_OFFSET = _d(
    float(RIBBON_PITCH) / 2.0, COMMITTED, "= RIBBON_PITCH/2, tangent webs", "WEDGE_WEB_OFFSET"
)
WEDGE_TIP_RADIUS = _d(
    0.25, ESTIMATED, "0.4 mm nozzle, single-perimeter tip", "WEDGE_TIP_RADIUS"
)
WEDGE_RAMP_LENGTH = _d(10.0, ESTIMATED, "tear-start ramp, unvalidated", "WEDGE_RAMP_LENGTH")
WEDGE_OPEN_GAP = _d(
    3.0, ESTIMATED, "hand-off separation to spreader", "WEDGE_OPEN_GAP"
)


def wedge_ramp_angle() -> float:
    """Half-angle of one wedge face, degrees. Reported, not commanded.

    Shallow is safer — a steep face tries to shear the conductor sideways
    instead of propagating the tear along the web.
    """
    rise = float(WEDGE_OPEN_GAP) - float(WEDGE_TIP_RADIUS)
    return math.degrees(math.atan2(rise, float(WEDGE_RAMP_LENGTH)))

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
# PAIRED-BEARING SPINDLE, not a slew ring (2026-07-26).
#
# A slew ring resists moment in ONE plane, buying its lever arm from its own
# diameter — which is why they get big and expensive fast. Two deep-groove
# bearings spaced vertically resist the same moment as a COUPLE, and the lever
# arm is the spacing, which costs us nothing: the platform is already thick.
#
# The arm applies roughly 12 N*m (50 N insertion reaction at R0 = 200 mm, plus
# ~2 kg of self-weight at ~100 mm). At SPINDLE_SPACING that becomes:
#     12 N*m / 0.050 m = 240 N radial per bearing
# A 6810 carries ~6200 N static. Twenty-five times margin.
#
# Knock-on: 65 mm bearing OD instead of a 160 mm ring lets the Z guide posts
# come back in, which shrinks the whole centre section.
#
# PBC slew ring catalogue kept as the fallback if the spindle shows too much
# runout in practice (fetched 2026-07-26; bore -> OD, cheapest):
#     20->80 $93.69   30->100 $127.23   50->150 $164.19   60->160 $199.35
#    100->185 $289.65 150->250 $509.94  200->300 $692.46
PBC_SLEW_RINGS = {
    20: (80.0, 93.69),
    30: (100.0, 127.23),
    50: (150.0, 164.19),
    60: (160.0, 199.35),
    100: (185.0, 289.65),
    150: (250.0, 509.94),
    200: (300.0, 692.46),
}

# 6810 thin-section deep groove: 50 mm bore, 65 mm OD, 7 mm wide.
SPINDLE_BEARING_BORE = _d(50.0, COMMITTED, "6810 standard", "SPINDLE_BEARING_BORE")
SPINDLE_BEARING_OD = _d(65.0, COMMITTED, "6810 standard", "SPINDLE_BEARING_OD")
SPINDLE_BEARING_W = _d(7.0, COMMITTED, "6810 standard", "SPINDLE_BEARING_W")
SPINDLE_BEARING_STATIC_N = _d(6200.0, COMMITTED, "NSK 6810 datasheet", "SPINDLE_BEARING_STATIC_N")

# Centre-to-centre. Bigger spacing = lower bearing load, taller spindle.
SPINDLE_SPACING = _d(75.0, ESTIMATED, "load vs height", "SPINDLE_SPACING")
SPINDLE_HOUSING_WALL = _d(6.0, ESTIMATED, "printed wall", "SPINDLE_HOUSING_WALL")
SPINDLE_HOUSING_OD = _d(
    float(SPINDLE_BEARING_OD) + 2.0 * float(SPINDLE_HOUSING_WALL),
    ESTIMATED, "bearing OD + walls", "SPINDLE_HOUSING_OD",
)

# Kept for the parts that still reference a single bearing dimension.
MAIN_BEARING_OD = _d(float(SPINDLE_HOUSING_OD), ESTIMATED, "= spindle housing", "MAIN_BEARING_OD")

# Radial room between the bearing OD and the guide posts.
Z_POST_CLEARANCE = _d(14.0, ESTIMATED, "assembly access", "Z_POST_CLEARANCE")

# DERIVED, never hand-set. Two clashes came from typing a number here that was
# not checked against the bearing it had to surround.
Z_POST_CIRCLE_R = _d(
    float(MAIN_BEARING_OD) / 2.0 + float(Z_POST_CLEARANCE) + 8.0 / 2.0,
    ESTIMATED,
    "derived from bearing OD",
    "Z_POST_CIRCLE_R",
)
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
# DECK_THICKNESS is defined up in section 2 — the engagement plane derives from
# it, so it has to exist before that calculation runs.
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
