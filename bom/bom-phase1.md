# Phase 1 BOM — motion system + ribbon prep

**Plan:** 657.6 · **Scope:** the arm (Z, θ, R, S, W) plus S1 feed/measure/cut,
S2 slit/fan, S3 strip. Crimp and insert are out of scope.

**Nothing here is ordered.** This is a buy list; clicking is Kyle's.

**Verification convention** — same as `bom-v1.md`:
- ✅ price and listing confirmed live, with date
- ⚠️ product class confirmed live, exact price not pinned
- ⓘ estimated from part class — **not** verified, treat as a planning figure

Sourcing rationale per category is in [`docs/sourcing-index.md`](../docs/sourcing-index.md).

---

## 0. Totals

| Module | Cost | Confidence |
|---|---|---|
| §1 Cell infrastructure | ~$300 | mixed |
| §2 Pneumatics | ~$390 | mixed |
| §3 Main arm | ~$250 | mostly estimated |
| §4 Station 1 — feed / measure / cut | ~$70 | estimated |
| §5 Station 2 — slit + fan | ~$35 | estimated |
| §6 Station 3 — strip | ~$35 | estimated |
| §7 Printed parts (filament) | ~$40 | estimated |
| §7b Arm camera | ~$20 | camera already owned |
| **Phase 1 total** | **~$1,140** | |

**This is above the $700–900 I quoted, and well above the "few hundred" first
estimated.** Two reasons: pneumatics are ~36% of the build once valves, flow
controls, reed switches and fittings are counted rather than just cylinders; and
the frame/deck for a 560 mm dial is not trivial. Reduction options are in §8.

Excluded because already owned or already on `bom-v1.md`: the NUC supervisor
($0), the ribbon itself ($9.30 ×2), and all printed parts (filament only).

---

## 1. Cell infrastructure

| # | Item | Vendor | Pick | Unit | Qty | Notes |
|---|---|---|---|---|---|---|
| 1.1 | Motion controller + drivers | Amazon | [BTT Octopus V1.1 + 6× TMC2209](https://www.amazon.com/BIGTREETECH-Octopus-Control-Compatible-Touchscreen/dp/B0D676J4M1) `B0D676J4M1` | ⚠️ ~$110 | 1 | 8 driver slots for 6 axes, and the spare **heater/fan MOSFET outputs drive the solenoid valves** — see §2. Board-only alternative: [`B094Y77FQN`](https://www.amazon.com/BIGTREETECH-Direct-Octopus-Control-Supports/dp/B094Y77FQN) |
| 1.2 | 24 V / 350 W PSU | Amazon | Mean Well LRS-350-24 class | ⓘ ~$35 | 1 | Steppers, valve coils, sensors |
| 1.3 | 3030 extrusion | Misumi / Amazon | frame set, ~6 m total | ⓘ ~$65 | 1 | Misumi cuts to length; Amazon sells fixed lengths |
| 1.4 | Extrusion hardware | Amazon | corner brackets, T-nuts, M5 cap screws | ⓘ ~$30 | 1 | |
| 1.5 | Deck plate, 560 mm dia | local / Amazon | 12 mm ply or acrylic for Phase 1 | ⓘ ~$25 | 1 | **Not** the 10 mm aluminium tooling plate yet — see §8 |
| 1.6 | E-stop, hard-wired | Amazon | 22 mm mushroom, latching, NC | ⓘ ~$12 | 1 | Cuts 24 V to motors and valves directly, not via software |
| 1.7 | Drag chain | Amazon | 10×20 mm, 1 m | ⓘ ~$15 | 1 | Must take the ±135° sweep **and** the Z stroke |
| 1.8 | Wiring, connectors, ferrules | Amazon | 18–22 AWG, JST-XH, heatshrink | ⓘ ~$30 | 1 | |

**Subtotal ~$322**

---

## 2. Pneumatics

The chain per actuator is **cylinder → flow controls → solenoid valve (on a
shared manifold) → MOSFET output**. The cylinder itself has no electrical
connection; the valve is what the controller talks to.

| # | Item | Vendor | Pick | Unit | Qty | Notes |
|---|---|---|---|---|---|---|
| 2.1 | Compressor | Amazon | [California Air Tools 1P1060S](https://www.amazon.com/dp/B01LYHYHEA) `B01LYHYHEA` | ✅ $149.00 *(2026-07-25)* | 1 | 56 dBA, oil-free, 1 gal, 1.20 CFM @ 90 psi |
| 2.2 | Filter + regulator | Amazon | [NANPU 1/4" NPT](https://www.amazon.com/dp/B07TPCGWPY) `B07TPCGWPY` | ✅ $15.99 *(2026-07-25)* | 1 | **Deliberately not a full FRL** — a lubricator injects oil into the air, the last thing we want near crimp tooling |
| 2.3 | Valve manifold, 6 station | Amazon | [US Solid 4V210-08 ×6 + manifold base, 24 V](https://www.amazon.com/U-S-Solid-4V210-08-Pneumatic-Solenoid/dp/B098NMSZ6Z) `B098NMSZ6Z` | ⚠️ ~$58 | 1 | 5/2, 24 VDC coils. Alt: [Baomain `B07JW4ZHV3`](https://www.amazon.com/Baomain-4V210-08-Position-Pneumatic-Solenoid/dp/B07JW4ZHV3). Anchors: 4-station $37.56, 8-station $80.30 *(US Solid, 2026-07-26)* |
| 2.4 | Cylinder — body clamp | Amazon | SDA16×10, **magnetic piston** | ⓘ ~$14 | 1 | On the arm. Clamps the unsplit ribbon behind the comb |
| 2.5 | Cylinder — guillotine | Amazon | SDA20×20, magnetic | ⓘ ~$16 | 1 | Needs the most force of the five |
| 2.6 | Cylinder — slit blades | Amazon | SDA20×20, magnetic | ⓘ ~$16 | 1 | |
| 2.7 | Cylinder — spreader | Amazon | SDA16×20, magnetic | ⓘ ~$14 | 1 | |
| 2.8 | Cylinder — strip blades | Amazon | SDA20×20, magnetic | ⓘ ~$16 | 1 | |
| 2.9 | Flow controls (meter-out) | Amazon | elbow, 6 mm tube × 1/8" BSPT | ⓘ ~$22 | 10 | **Two per cylinder, not optional.** Without them cylinders slam at full line pressure — fatal to slit-depth repeatability |
| 2.10 | Reed switches | Amazon | magnetic cylinder sensors, 2-wire | ⓘ ~$35 | 8 | Extended + retracted confirmation on the four station cylinders. Turns "fire and hope" into "fire and confirm" — required before the arm may rotate away from a die |
| 2.11 | Tubing + fittings | Amazon | 6 mm OD PU, 10 m + push-to-connect assortment | ⓘ ~$28 | 1 | |
| 2.12 | Air pressure switch | Amazon | adjustable, NO/NC | ⓘ ~$15 | 1 | Refuse to run on low air — a half-stroke die is worse than no stroke |

**Subtotal ~$398**

**Wiring note:** valve coils draw ~170–330 mA at 24 V — far past a logic pin.
Drive from the Octopus's MOSFET outputs. **Flyback protection is mandatory**:
either buy valves with DIN 43650 connectors that include surge suppression, or
fit a diode across each coil. Skipping it kills outputs.

---

## 3. Main arm

Five axes: **Z** lift, **θ** rotate, **R** extend, **S** cross-slide, **W** wrist.

| # | Item | Vendor | Pick | Unit | Qty | Notes |
|---|---|---|---|---|---|---|
| 3.1 | Steppers | Amazon / StepperOnline | NEMA 17, 42×40 mm, ~0.4 N·m | ⓘ ~$90 | 6 | Z, θ, R, S, W, F(feed). 6th slot spare on the Octopus |
| 3.2 | **Z stage** — guide rods | Amazon | 8 mm hardened rod, 200 mm | ⓘ ~$14 | 3 | See §8 — the platform-on-posts arrangement |
| 3.3 | Z stage — linear bearings | Amazon | LM8UU / SC8UU | ⓘ ~$12 | 6 | Two per post |
| 3.4 | Z stage — leadscrew | Amazon | T8, 2 mm lead, 200 mm + anti-backlash nut | ⓘ ~$16 | 1 | **Off-axis**, so the rotary axis at the platform centre stays clear. T8 trapezoidal **self-locks** — an E-stop will not drop the arm |
| 3.5 | θ — rotary bearing | PBC Linear / Amazon | slew ring or turntable bearing, ~80–100 mm | ⓘ ~$40 | 1 | Carries radial extension load and insertion reaction. [PBC SRB-P02 series](https://pbclinear.com/collections/plain-bearing-slewing-ring-bearings) is the right class; no public pricing — **quote needed** |
| 3.6 | θ — belt reduction | Amazon | GT2 20T + 100T pulleys, belt | ⓘ ~$18 | 1 | 5:1. Buys resolution and holding torque against station reaction |
| 3.7 | R — linear rail | Amazon | MGN12H, 250 mm + carriage | ⓘ ~$32 | 1 | The shared "extend into the station" motion |
| 3.8 | R — drive | Amazon | T8 leadscrew 150 mm + nut | ⓘ ~$14 | 1 | |
| 3.9 | S — cross-slide rail | Amazon | MGN9C, 100 mm + carriage | ⓘ ~$24 | 1 | 20 mm stroke, selects conductor 1/2/3 |
| 3.10 | S — drive | Amazon | T8 leadscrew 100 mm + nut | ⓘ ~$12 | 1 | |
| 3.11 | **W — wrist drive** | Amazon | NEMA 17 + GT2 belt, 2 hard stops | ⓘ ~$20 | 1 | 🔴 **Changed from the pneumatic rotary actuator — see §8** |
| 3.12 | Couplers, shaft hardware | Amazon | 5×8 flexible couplers, collars | ⓘ ~$18 | 1 | |

**Subtotal ~$250** (excludes the slew bearing if it quotes high)

---

## 4. Station 1 — feed / measure / cut

| # | Item | Vendor | Pick | Unit | Qty | Notes |
|---|---|---|---|---|---|---|
| 4.1 | Spool | printed | our design | — | 1 | **The ribbon ships as a loose roll, not on a rigid spool** — so hub diameter, flange spacing and bore are ours to choose |
| 4.2 | Hanger + dancer arm | printed | our design | — | 1 | Passive payoff at constant light tension; dancer flag doubles as spool-empty detect |
| 4.3 | Dancer spring | Amazon | extension spring assortment | ⓘ ~$8 | 1 | Also on `bom-v1.md` line 7 |
| 4.4 | **Measuring encoder** | Amazon | **600 P/R** optical rotary, quadrature | ⓘ ~$22 | 1 | **Owns cable length accuracy.** Independent of the drive — never trust drive-roller steps, ribbon slips. With the wheel below: **0.0417 mm/count**. Alt: complete meter-counter [`B0D2D4F5BX`](https://www.amazon.com/Rolling-Electronic-Digital-Measuring-Accuracy/dp/B0D2D4F5BX) |
| 4.5 | Measuring wheel | printed | **31.83 mm dia = 100.00 mm circumference** | — | 1 | Length in mm is `counts × 100 / 2400`. **No rubber tyre** — a compliant surface changes effective circumference, which is the exact error this wheel exists to avoid. Fallback if the printed knurl slips: [McMaster encoder wheels](https://www.mcmaster.com/products/encoder-wheels/) |
| 4.6 | Drive rollers | printed + Amazon | knurled shaft + polyurethane idler, spring preload | ⓘ ~$15 | 1 | |
| 4.7 | PTFE guide tube | Amazon | 2 mm ID / 4 mm OD | ⓘ ~$8 | 1 | Delivers ribbon to a repeatable presentation point |
| 4.8 | Guillotine blade + anvil | Amazon | replaceable chisel/utility blade in printed holder | ⓘ ~$10 | 1 | Blade geometry must not crush the ribbon end — a crushed end will not enter the comb channels |
| 4.9 | Spool-empty / ribbon-out sensor | Amazon | optical slot sensor | ⓘ ~$6 | 1 | Reads the dancer flag |

**Subtotal ~$79**

---

## 5. Station 2 — slit + fan

🔴 **Harder than the design doc implies.** `cell-design.md` gives ribbon pitch as
~2.5 mm; the real figure is **~1.4–1.5 mm** (derived from 22 AWG / 60 cores ×
0.08 mm / 1.4 mm OD — the 2.5 mm looks like the *connector* cavity pitch borrowed
by mistake). So the webs sit at **±0.7 mm** from centreline, not ±1.25 mm. Finer
blades, closer together, and depth control — already "the whole game" — gets
tighter. **Confirm on arrival before cutting any tooling.**

| # | Item | Vendor | Pick | Unit | Qty | Notes |
|---|---|---|---|---|---|---|
| 5.1 | Slitting blades | Amazon | scalpel/#11 blades in an adjustable holder | ⓘ ~$14 | 1 | Two blades, one per web. Thin section matters at 1.4 mm pitch |
| 5.2 | Depth adjustment | McMaster | M3 fine-pitch screws + locknuts | ⓘ ~$8 | 1 | Depth-adjustable to 0.05 mm. Too shallow and it will not zip; too deep and it nicks copper |
| 5.3 | Backing anvil | McMaster | ground steel flat, 3 mm | ⓘ ~$10 | 1 | Supports the ribbon so the blades cut rather than push |
| 5.4 | Spreader plate | printed | diverging slots, ~1.5 → 8 mm | — | 1 | Fans the slit tails into the comb channels |

**Subtotal ~$32**

---

## 6. Station 3 — strip

| # | Item | Vendor | Pick | Unit | Qty | Notes |
|---|---|---|---|---|---|---|
| 6.1 | V-blade die, 3-position | McMaster / grind | HSS or repurposed stripper blades at 8 mm comb pitch | ⓘ ~$22 | 1 | One stroke scores all three conductors — equal strip length by construction |
| 6.2 | Depth stop shims | McMaster | shim stock assortment | ⓘ ~$10 | 1 | Per-recipe. Wrong depth = nicked strands = the crimp fails a pull test later |
| 6.3 | Slug waste chute | printed | our design | — | 1 | Three insulation slugs drop away rather than into the mechanism |

**Subtotal ~$32**

*(The pull-off is done by the arm retracting 4 mm — no dedicated actuator.)*

---

## 7. Printed parts

Filament only. **Eleven are modelled** — generate with
`freecadcmd cad/build_parts.py`, which writes FCStd + STEP + STL for each from
the same `sim/layout.py` dimensions the simulation uses.

| Part | Size (mm) | Volume | Module |
|---|---|---|---|
| `spool` | 110 × 110 × 31 | 116.6 cm³ | S1 |
| `spool_hanger` | 70 × 44 × 150 | 81.0 cm³ | S1 |
| `dancer_arm` | 82 × 12 × 20 | 6.2 cm³ | S1 |
| `guide_tube_mount` | 34 × 24 × 29 | 14.4 cm³ | S1 |
| `measuring_wheel` | 31.8 × 31.8 × 9 | 5.3 cm³ | S1 |
| `spreader_plate` | 25 × 32 × 8 | 6.0 cm³ | S2 |
| `comb` | 26 × 32 × 12 | 9.3 cm³ | arm |
| `z_platform` | 208 × 208 × 24 | 295.1 cm³ | arm |
| `radial_carriage` | 52 × 45 × 22 | 21.2 cm³ | arm |
| `wrist_mount` | 50 × 32 × 26 | 12.0 cm³ | arm |
| `camera_mount` | 60 × 48 × 34 | 29.5 cm³ | arm |
| `drive_roller_block` | 56 × 30 × 46 | 67.0 cm³ | S1 |
| `guillotine_holder` | 44 × 34 × 54 | 75.1 cm³ | S1 |
| `station_mount` × 7 | 76 × 60 × 40 | 46.6 cm³ ea | all |

**~1,065 cm³ with seven station mounts ≈ 1.3 kg of filament**, call it
**$35–45** in PLA/PETG. Print notes and orientations in
[`cad/README.md`](../cad/README.md).

Still to model: slug chute, body-clamp mount, cross-slide carrier.

## 7b. Arm camera

| # | Item | Vendor | Pick | Unit | Qty | Notes |
|---|---|---|---|---|---|---|
| 7b.1 | Camera | — | **ELP-USBFHD01M-L36**, 3.6 mm | ⓘ $0 | 1 | Kyle has spares. Same model as TendWright's fleet, so `cameras.py` / `camserve.py` work unchanged |
| 7b.2 | AprilTags | print | tag36h11, 25 mm, one per station | — | 7 | Arm registers against these — measured pose vs commanded |
| 7b.3 | Ring light | Amazon | small LED ring or bar | ⓘ ~$12 | 1 | Tag detection needs consistent illumination more than brightness |
| 7b.4 | USB cable | Amazon | 2 m, through the drag chain | ⓘ ~$8 | 1 | Must survive the ±135° sweep plus Z stroke |

---

## 8. Decisions and flags

### 🔴 The pneumatic wrist is dropped — $220 → $20

`cell-design.md` §5.2 specifies a **pneumatic 180° rotary actuator with
adjustable hard stops**, reasoned as: it only ever needs two positions, so no
servo is required. That reasoning was about *control simplicity* and it was
sound. The pricing kills it.

Live pricing 2026-07-26: **Airtac HRQ10 $220.50, HRQ20 $252.54.** The wrist would
have cost more than every stepper on the machine combined.

A NEMA 17 with a belt reduction and two hard stops does the same job for ~$20,
costs one driver slot out of the eight (we use six), and is already the
motion-control pattern used by every other axis. The "two positions only"
argument does not justify a 10× premium.

Kept from the original reasoning: hard stops still set the two positions
mechanically; the motor only has to *reach* them.

### The Z-architecture gate dissolves at prototype scale

The Z decision was parked pending the funnel capture window, because the choice
was between a ~$62 commodity module (cantilevered) and a ~$150–250 platform on
posts. **At printed-prototype scale both are cheap**: three 8 mm rods, six linear
bearings and a T8 screw is **~$42** (lines 3.2–3.4) and gives the
platform-on-posts geometry outright, with the rotary axis at an unobstructed
centre.

So Phase 1 takes the good geometry now. The capture-window measurement still
matters — it decides whether the *production* build needs a stiffer stage — but
it no longer gates anything buildable.

Bonus: the T8 trapezoidal screw **self-locks**, which resolves the back-drive
safety question for Phase 1. An E-stop will not drop the arm.

### Deck is plywood or acrylic, not aluminium tooling plate

A 560 mm aluminium tooling plate is $150+ and is the wrong thing to buy while
station positions are still placeholders. Phase 1 uses 12 mm ply or acrylic
(~$25) — re-drillable, and the whole point is finding out where the holes
actually go. The tooling plate is a production-build line.

### Where the money actually is

Pneumatics are **~36%** of Phase 1. If the total needs to come down:

- Drop reed switches (−$35) — lose stroke confirmation, run open-loop on dies
- Drop the spreader cylinder and hand-set the fan for early trials (−$14 + a valve)
- Single-solenoid spring-return valves instead of double where a known
  fail-state is wanted anyway — fewer outputs, no cost change
- The compressor at $149 is 14% on its own, and is the one line that hand-actuation
  would have removed entirely

---

## 9. Not yet sourced

- **Slew/turntable bearing (3.5).** [PBC Linear SRB-P02](https://pbclinear.com/collections/plain-bearing-slewing-ring-bearings) is the right class but publishes no pricing — needs a quote. A cheap lazy-susan turntable is a possible Phase 1 stand-in; it will not hold 0.05 mm at the comb, but Phase 1 has no insertion to hold it for.
- **Exact cylinder bores and strokes** — depends on station tooling geometry that is not designed yet. Bores above are a first pass sized on required force, not on measured die resistance.
- **Guillotine and strip blade specifics** — depends on the ribbon's measured cross-section.
- **3030 extrusion cut list** — depends on the frame design, which depends on the deck diameter being confirmed at 560 mm.
