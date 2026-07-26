# Datum scheme

**Status:** draft, revised 2026-07-26 for the base-mounted Z axis.

The first version of this document reported that the entire layout was blocked on
one unknown measurement. **The Z axis unblocks it** — see "What the Z axis
changed" below. This is now a working scheme with a small number of open
parameters rather than a stalled one.

---

## What this is

A **datum** is a reference that other dimensions are measured *from*. Choosing
them up front is what stops tolerances stacking and stops two stations being
designed to incompatible geometry.

---

## The three datums

### A — Deck plane

Top surface of the 10 mm tooling plate. **All heights (Z) are measured from
here.** Positive up.

Chosen because it is the one surface every station physically touches, and
because hole position in a tooling plate is repeatable in a way that shimming
never is.

### B — Pivot axis

The arm's rotation centerline, normal to Datum A. **All radii (R) and angles (θ)
are measured from here.** θ = 0 is assigned to S1 (feed/cut); positive θ is
counter-clockwise viewed from above.

The pivot axis is **carried by the Z stage** — it translates vertically but never
tilts. Datum B is therefore a line in plan view, fixed in X/Y, floating in Z.

### C — Station engagement heights (Z₁…Z₇)

*Formerly a single "work line" plane. Superseded by the Z axis.*

Each station has its **own** engagement height above Datum A — the Z the arm
moves to in order to present the ribbon to that station's tooling. Seven values,
held in configuration, established once by touching off at each station during
commissioning.

| | |
|---|---|
| Z₁…Z₇ | Per-station engagement heights (config, calibrated) |
| Z\_clear | Rotation-safe height — above the tallest station tooling intrusion |
| Z\_travel | Total stage stroke — must cover max(Zᵢ) − min(Zᵢ) plus clearance headroom |

**Z\_clear is the one that matters structurally.** With a Z axis, clearance during
rotation is achieved vertically (lift, rotate, descend) rather than radially
(retract to R\_safe). That decouples station tooling design from the arm's
rotation path — a station may now intrude inside the bolt circle, provided its
tooling stays below Z\_clear.

---

## The Z axis

**Configuration:** base → Z stage → rotary axis → arm. The Z stage carries the
entire rotating assembly (Kyle, 2026-07-26).

**Class:** commodity ballscrew linear stage — SFU1605 screw, SBR16 or MGN rails,
NEMA 17/23, ~0.03 mm positioning accuracy, 100–400 mm strokes, $62–200. Widely
available; not a custom build.

### 🔴 The coaxial conflict (found in the rough-in, 2026-07-26)

**A single commodity ballscrew module cannot carry this axis.** You cannot run a
rotary axis through the middle of a linear rail — and the rotary axis has to be at
the pivot, which is exactly where the rail wants to be. Visible immediately in
`sim/studies/renders/roughin_plan.png`: the Z column and the rotor compete for the
same space. This is the first thing the rough-in caught that prose had missed.

Three ways out:

| | Approach | Trade |
|---|---|---|
| **a** | Rotor cantilevered off one commodity module's carriage face | Cheapest, simplest to build. Hangs the whole assembly on a moment arm |
| **b** | Z platform on 3–4 vertical guide posts, driven by **one off-axis ballscrew** | Rotary axis sits at the platform centre, unobstructed. Stiffness from the post triangle rather than a cantilever. Still commodity parts, ~$150–250 |
| **c** | Move Z onto the arm rather than the base | No coaxial conflict at all, but adds moving mass at the end of the arm, fights the wrist for space, and gives up the station-tooling decoupling base-Z bought |

**OPEN, and deliberately gated on a measurement** — see below.

### The deflection budget is about variance, not strength

Corrected 2026-07-26 after Kyle pointed out how light the product is.

**The payload is negligible.** A 1.2 m length of 22 AWG 3-conductor ribbon at
1.4 mm OD is roughly **15–20 g**. The rotating assembly is on the order of
**2 kg**. The cable is about **1% of the moving mass** — not a factor in any load
calculation.

So the budget is not set by payload. It is set by:

1. **Self-weight** of the assembly cantilevered ~200 mm out — the dominant static
   load, and essentially *constant*.
2. **Arriving inside the insertion funnel's capture window.** Pencilled at
   ±0.3 mm, which at 200 mm reach is an angular budget of roughly **1.5 mrad
   (0.086°) across the entire stack** — Z carriage, rotary bearing, arm, radial
   slide, cross-slide. Z is one of five contributors.

This is a **precision** problem, not a strength problem, and that distinction
changes the architecture choice:

> **Repeatable sag is calibration, not error.** If the arm always droops the same
> 0.4 mm at a given θ/R/Z, it folds into the station Z table and the angular
> positions and costs nothing. With a ~20 g payload that never varies, that is
> exactly the regime we are in.

What defeats a cantilever is **non-repeatability** — backlash on direction
reversal, stick-slip in the bearings, thermal drift, play in the cross-slide and
wrist. Those do not calibrate out. Static droop does.

**So option (a) is far more viable than first assessed.** The architecture
decision waits on one number: **the funnel's real capture window**, which is the
headline output of de-risk B (plan 657.3) and needs nothing but printed parts and
housings.

- Funnel forgiving (±0.5 mm or better) → take the cantilever, option (a).
- Funnel tight (±0.15 mm) → the platform-on-posts earns its cost, option (b).

Cheaper to measure with $20 of PLA than to insure against with $150 of ballscrew.
**This makes 657.3 a prerequisite for the Z architecture, not just an experiment.**

### Other design constraints

- **Prefer the shortest Z travel that does the job.** Stiffness falls off with
  stroke, and travel is the parameter most likely to be over-specified "just in
  case." Currently 55 mm required → 100 mm stock stroke.
- Specify dual guidance, not a printer-class single-rod T8.

**Back-drive is a safety decision.** A trapezoidal leadscrew self-locks — cut
power and it holds. A ballscrew is efficient enough to **back-drive** under load,
so on a vertical axis carrying ~10 kg an E-stop could drop the arm. Resolve
deliberately: self-locking leadscrew (slower, less stiff, cheaper), or ballscrew
plus motor brake, or ballscrew plus counterbalance. **Open — see below.**

**Z couples to the ribbon path.** The ribbon runs from S1's fixed guide tube to
the comb; changing Z changes the free length between them. Irrelevant for
clearance moves on flexible servo ribbon, but the payout/measure step is
length-critical. Therefore: **the payout reference position includes a Z, and
payout only ever occurs at that Z.** One recipe constant; a silent length error
if omitted.

**Cable management.** The drag chain / service loop must now accommodate Z travel
in addition to the ±135° sweep.

**Homing order.** Z homes to its up position *before* θ is permitted to rotate,
or the arm can sweep into station tooling on power-up.

---

## The two derived numbers

### R₀ — bolt circle radius

Pivot axis to the station work point. Constrained from below by *angular fit* —
seven stops must share a 270° working arc, and the press is 210 mm wide against
a normal station's ~80 mm. Constrained from above by bench footprint and by arm
deflection under insertion load.

**Computed 2026-07-26 by `sim/studies/fit_check.py`:**

| R₀ | Press | Station | Needed | Spare | |
|---|---|---|---|---|---|
| 125 mm | 114.3° | 37.3° | 338.2° | −68.2° | ✗ |
| **150 mm** | 88.9° | 30.9° | **274.4°** | **−4.4°** | ✗ |
| 175 mm | 73.7° | 26.4° | 232.3° | +37.7° | ✓ |
| **200 mm** | 63.3° | 23.1° | **201.8°** | **+68.2°** | ✓ |
| 250 mm | 49.7° | 18.4° | 160.2° | +109.8° | ✓ |

🔴 **The ~300 mm bolt circle in `cell-design.md` does not close.** At R₀ = 150 mm
the seven stops need 274.4° of a 270° arc — short by 4.4°. That figure predates
understanding the press as a standalone 210 mm-wide machine, and it was never
checked against seven stops.

**Working value: R₀ = 200 mm** (400 mm bolt circle). Minimum viable is ~175 mm;
200 mm buys 68° of spare arc to absorb the station widths firming up, and keeps
the deck at a sane ~280 mm radius.

Still to confirm: that the arm can physically reach the anvil once
`PRESS_RAM_FROM_FRONT` is measured. Angular fit and radial reach are separate
constraints, and only the first is settled.

### θ₁…θ₇ — station angles

Seven stops, not six — S6 drop and the reject position are separate angles:

| Stop | Station | θ | Z |
|---|---|---|---|
| 1 | S1 feed / measure / cut | 0° (assigned) | Z₁ |
| 2 | S2 slit + fan | TBD | Z₂ |
| 3 | S3 strip | TBD | Z₃ |
| 4 | S4 crimp (press) | TBD | Z₄ |
| 5 | S5 insert | TBD | Z₅ |
| 6 | S6 drop — collect | TBD | Z₆ |
| 7 | S6 drop — reject | TBD | Z₇ |

Spacing is **not** uniform. Constraints: the arm sweeps a ~270° working arc (not
a full turn, so the trailing ribbon never wraps the pivot — no slip ring, no
rotary air union); the press occupies far more angular width than any other
station; and the press anchors θ₄ because it is placed first (see below).

---

## Press envelope (researched 2026-07-26)

Class: **1.5 T / 15 kN taped-terminal crimping press for mini applicators**, the
machine class BOM line 11 belongs to.

| Spec | Value | Source |
|---|---|---|
| Footprint | **210 × 210 mm** | vendor spec |
| Height | **580 mm** | vendor spec |
| Weight | **35 kg** | vendor spec |
| Stroke | **30 mm** (40 mm variants exist) | vendor spec |
| Motor | 0.55 kW | vendor spec |
| Supply | **AC 110/220 V, 50/60 Hz** | vendor spec |
| Applicators accepted | JST, Molex, TE mini applicators | vendor spec |
| Shut height | **not stated** | — |
| Throat depth | **not stated** | — |
| Base plate height above bench | **not stated** | — |

**Correction to an earlier estimate.** This document previously described the
press as "~300 × 250 × 500 mm and 30–50 kg." The mass was right; the footprint
was not. The real machine is a **narrow tall column press** — 210 mm square and
580 mm high. Footprint is roughly 40% smaller than assumed, which makes it
considerably more compatible with a ~300 mm bolt circle than feared. The
obstruction to design around is the **column**, not a wide base.

**110 V variants exist.** The voltage worry recorded on 2026-07-25 (step-up
transformers, 50 Hz motors running 20% fast on 60 Hz mains) is softened
substantially — this class is built in a 110 V/60 Hz configuration. Specify it at
purchase rather than solving it afterwards.

### Still needed, and where each comes from

| Number | Needed for | How we get it |
|---|---|---|
| Shut height (which standard) | Applicator compatibility, Z₄ | **Ask the seller** — question 5 on the 657.2 message |
| Throat depth (ram axis to column) | R₀, and whether the arm can reach the anvil | Ask seller, or measure on arrival |
| Base plate height above bench | Press mounting, deck relationship | Measure on arrival |
| Wire height above applicator base | **Z₄** | Measure on arrival — checklist item on 657.5 |

**Working assumption until measured:** the wire/anvil line sits low in the
applicator body, well under the 165 mm overall height of the OTP unit. Treat Z₄
as a **free parameter in `layout.py`** rather than a committed value. This is
exactly the case the Z axis was added to absorb — a wrong guess costs a config
edit, not a re-machined deck. Do not let a placeholder here harden into a
number anyone believes.

---

## Layout ordering: the press is the datum, not the dial

**Decided 2026-07-26 (Kyle).** A 1.5 T bench press is ~300 × 250 × 500 mm and
30–50 kg with a fixed vertical ram. It is not a bolt-on module in a sector; the
dial gets built around it.

Ordering:

1. Place the press. Its anvil position fixes **θ₄** and one point on the bolt
   circle; its crimp height fixes **Z₄**.
2. Place the pivot at R₀ from that point → fixes Datum B in X/Y.
3. Hang the other six stops off the resulting circle.
4. Calibrate Z₁…Z₃, Z₅…Z₇ at commissioning.

Note the Z axis makes step 1 much cheaper than it was: the press sets Z₄ only,
not a global height that all six other stations must be shimmed to match.

---

## Applicator shut-height fork (researched 2026-07-26)

Applicators mount to presses at a standardized **shut height** — base plate to
ram face at bottom dead centre. Two incompatible standards exist:

| Standard | Shut height | Who |
|---|---|---|
| Western industry standard | **135.78 mm** ±0.02 (5.345″) | Molex Mini-Mac, TE, Mecal EVS |
| Chinese OTP clone | **119.7 mm** | Kingsing, crimpapplicator.com, the eBay-class units |

A 16 mm mismatch — an applicator built to one will not run in a press built for
the other. Same class of trap as the AM-10: two things that both say "standard"
and mean different things.

**Sourcing consequence:** the applicator decision *leads* and the press follows.
Shut height is a fifth question on the seller message for BOM line 10, and the
answer constrains which press we buy.

**Layout consequence — now minor.** Pre-Z this was the root blocker of the whole
scheme. With Z it determines Z₄ and press mounting height only.

---

## Current values

| Symbol | Meaning | Value | Confidence |
|---|---|---|---|
| Z₁…Z₇ | Per-station engagement heights | config, calibrated | resolved by design |
| Z\_clear | Rotation-safe height | ~95 mm above deck | derived; moves with station tooling |
| Z\_travel | Z stage stroke | **55 mm needed → 100 mm stock stage** | computed 2026-07-26 |
| R₀ | Bolt circle radius | **200 mm** (min viable 175) | computed 2026-07-26 |
| Deck height above bench | Chosen to minimise Z travel | ~170 mm | derived from placeholder crimp height |
| θ₁ | S1 angle | 0° | assigned by definition |
| θ₂…θ₇ | Remaining station angles | unknown | arc now known to fit; spacing not assigned |

**The Z travel result is worth reading twice.** Only **55 mm** of stroke is
required, covered by the smallest useful stock ballscrew stage (100 mm). That is
a direct consequence of raising the deck ~170 mm above the bench to pull the six
short stations up near the press's fixed crimp height — at bench level the stage
would have had to span the whole difference. Short stroke means a stiff stage,
which lands straight in the comb deflection budget.

**Known independently, safe to model now:** comb 3 channels at 8 mm pitch ·
cross-slide stroke 20 mm · split 25 mm · strip 2.75 mm · insert depth 6 mm ·
pullback 1.5 mm · nest index 2.5 mm · cavity pitch 2.5 mm · main bearing
80–100 mm bore · MGN12 radial / MGN9 cross · 3030 frame · 10 mm deck · cable
length envelope 90–1000 mm · wrist 180°, two positions.

---

## Open questions

1. **Z travel spec.** What is max(Zᵢ) − min(Zᵢ) in practice, plus clearance
   headroom? Drives stage cost *and* stiffness. Wants the smallest defensible
   number. Blocked on press crimp height and station tooling heights.
2. **Ballscrew + brake, or self-locking leadscrew?** Decides whether an E-stop
   drops the arm.
3. ~~Is ~300 mm enough bolt circle?~~ **ANSWERED 2026-07-26: no.** R₀ = 200 mm
   (400 mm circle). See the fit table above.
4. **Where does the payout trough live?** It must control a dangling 1 m cable —
   larger than the entire dial. Probably off-deck, below or beside.
5. ~~Does 270° of arc fit seven stops?~~ **ANSWERED 2026-07-26: yes, at
   R₀ ≥ 175 mm**, not at 150 mm. 201.8° needed of 270° at the working R₀.
7. **Can the arm physically reach the anvil?** Angular fit is settled; radial
   reach is not. Blocked on measuring the press's ram-axis-from-front distance.
8. **Station angular spacing.** The arc fits, but θ₂…θ₇ are still an even spread
   rather than an assignment that respects the press's real angular footprint.
6. **Arm deflection budget.** Total compliance from Z carriage → rotary bearing →
   arm → radial slide → comb, under insertion load, versus the funnel capture
   window. Needs a number for the funnel first.
