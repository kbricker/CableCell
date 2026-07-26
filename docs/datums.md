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

### Design constraints

**Stiffness is the dominant cost.** The stage carries the rotary bearing, arm,
radial slide, cross-slide, wrist, comb and drag chain — est. 5–15 kg — and sits
at the *bottom of a long lever*. A small angular deflection at the Z carriage
becomes a large displacement at the comb, which must stay inside the insertion
funnel's capture window (`cell-design.md` §8 item 5). Two implications:

- Specify a dual-rail module, not a printer-class single-rod T8.
- **Prefer the shortest Z travel that does the job.** Stiffness falls off with
  stroke, and travel is the parameter most likely to be over-specified "just in
  case."

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

Pivot axis to the station work point. Constrained from below by the press: the
arm must reach the applicator's anvil, which sits some distance inside the press
frame, so R₀ ≥ (pivot-to-press-face) + (press throat depth). Constrained from
above by bench footprint and by arm deflection under insertion load.

Working figure in `cell-design.md` is a ~300 mm bolt circle (R₀ ≈ 150 mm).
**Treat that as a placeholder** — written before the press was understood as a
30–50 kg standalone machine.

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
| Z\_clear | Rotation-safe height | unknown | derived from station tooling heights |
| Z\_travel | Z stage stroke | **unknown — spec me** | wanted: shortest that works |
| R₀ | Bolt circle radius | ~150 mm | placeholder — predates press-as-datum |
| θ₁ | S1 angle | 0° | assigned by definition |
| θ₂…θ₇ | Remaining station angles | unknown | blocked on R₀ + press angular width |

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
3. **Is ~300 mm enough bolt circle** once a press of that footprint and a payout
   trough for a 1 m cable are both in the picture?
4. **Where does the payout trough live?** It must control a dangling 1 m cable —
   larger than the entire dial. Probably off-deck, below or beside.
5. **Does 270° of arc fit seven stops** given the press's angular width?
6. **Arm deflection budget.** Total compliance from Z carriage → rotary bearing →
   arm → radial slide → comb, under insertion load, versus the funnel capture
   window. Needs a number for the funnel first.
