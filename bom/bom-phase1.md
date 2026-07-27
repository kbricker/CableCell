# Phase 1 BOM — motion system + ribbon prep

**Plan:** 657.6 · **Scope:** the arm (Z, θ, R, S, W) plus S1 feed/measure/cut,
S2 slit/fan, S3 strip. Crimp and insert are out of scope.

**Nothing here is ordered.** This is a buy list; clicking is Kyle's.

**Live sourcing pass 2026-07-27** in Kyle's logged-in Chrome session. Per the
`source-bom` skill, every line carries a verification mark:

- ✅ price read off the live product page, dated
- ⚠️ product class confirmed live, exact variant not pinned
- ⓘ **unsourced** — a planning figure, explicitly not a price

Sourcing rationale per category is in [`docs/sourcing-index.md`](../docs/sourcing-index.md).

---

## 0. Totals

| Module | Cost | Sourced |
|---|---|---|
| §1 Cell infrastructure | ~$239 | 6 of 8 ✅ |
| §2 Pneumatics | ~$359 | 10 of 12 ✅ |
| §3 Main arm | ~$222 | 7 of 9 ✅ |
| §4 Station 1 — feed / measure / cut | ~$65 | 3 of 6 ✅ |
| §5 Station 2 — split + fan | **$0–32** | printed; fallback only if wedge fails |
| §6 Station 3 — strip | ~$32 | 1 of 2 ✅ |
| §7 Printed parts — filament | **$28** | 2 of 2 ✅ |
| §7c Consumables — ribbon, reference cables | **$28** | 4 of 4 ✅ |
| §7b Arm camera | ~$20 | camera owned |
| **Phase 1 total** | **~$993–1,025** | **~33 of 46 lines priced live** |

Roughly **83% of the cost** now sits on lines priced off a real page, up from
about 20% before this pass. The remaining ⓘ lines are small consumables plus the
two station tooling sections, which depend on geometry not yet fixed.

**Biggest correction: the motion controller was estimated at ~$110 and is
$53.99** — 2× high, in the *opposite* direction to the slew-ring miss which was
5× low. Guesses err both ways. That is the argument for not making them.

Excluded because already owned or on `bom-v1.md`: NUC supervisor ($0), the ribbon
($9.30 ×2), the arm camera (Kyle has spares).

---

## 1. Cell infrastructure

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 1.1 | Motion controller | [BTT Octopus V1.1](https://www.amazon.com/dp/B094Y77FQN) `B094Y77FQN` | ✅ **$53.99** | 1 | 8 driver slots for 6 axes. Spare **heater/fan MOSFET outputs drive the solenoid valves** — see §2 |
| 1.2 | Stepper drivers | [BTT TMC2209 pack](https://www.amazon.com/dp/B07ZQ3C1XW) `B07ZQ3C1XW` | ✅ **$26.99** | 2 | 6 axes; two packs |
| 1.3 | 24 V / 350 W PSU | [MEAN WELL LRS-350-24](https://www.amazon.com/dp/B07VRK86SP) `B07VRK86SP` | ✅ **$35.97** | 1 | Steppers, valve coils, sensors |
| 1.4 | 3030 extrusion, 500 mm ×4 | [3030 T-slot 4-pack](https://www.amazon.com/dp/B0DP28NX2D) `B0DP28NX2D` | ✅ **$39.99** | 1 | Frame and deck supports |
| 1.5 | Extrusion hardware | corner brackets, T-nuts, M5 cap screws | ⓘ ~$30 | 1 | **Unsourced** — depends on the frame design |
| 1.6 | Deck plate | **Kyle supplies and cuts.** 1/2" plywood, **22-1/16" OD**, 7" centre hole, 15-3/4" bolt circle | **$0** | 1 | Full imperial spec + drilling template: [`docs/deck-cut-sheet.md`](../docs/deck-cut-sheet.md). Deliberately *not* aluminium tooling plate — see §8 |
| 1.7 | E-stop, hard-wired | [22 mm mushroom, 1NC latching](https://www.amazon.com/dp/B09YD2PNC5) `B09YD2PNC5` | ✅ **$8.99** | 1 | Cuts 24 V to motors and valves directly, not via software |
| 1.8 | Drag chain | [10×20 mm, 1 m open type](https://www.amazon.com/dp/B0BGKC1BPZ) `B0BGKC1BPZ` | ✅ **$12.99** | 1 | Must take the ±135° sweep **and** the Z stroke |
| 1.9 | Wiring, connectors, ferrules | 18–22 AWG, JST-XH, heatshrink | ⓘ ~$30 | 1 | **Unsourced** |

**Subtotal ~$239** · 6 of 8 priced live (deck supplied by Kyle)

---

## 2. Pneumatics

The chain per actuator is **cylinder → flow controls → solenoid valve (on a
shared manifold) → MOSFET output**. The cylinder has no electrical connection;
the valve is what the controller talks to.

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 2.1 | Compressor | [California Air Tools 1P1060S](https://www.amazon.com/dp/B01LYHYHEA) `B01LYHYHEA` | ✅ **$149.00** *(07-25)* | 1 | 56 dBA, oil-free, 1 gal, 1.20 CFM @ 90 psi |
| 2.2 | Filter + regulator | [NANPU 1/4" NPT](https://www.amazon.com/dp/B07TPCGWPY) `B07TPCGWPY` | ✅ **$15.99** *(07-25)* | 1 | **Deliberately not a full FRL** — a lubricator injects oil into the air, the last thing we want near crimp tooling |
| 2.3 | Valve manifold, 6 station | [US Solid 4V210-08 ×6 + base, 24 V](https://www.amazon.com/dp/B098NMSZ6Z) `B098NMSZ6Z` | ⚠️ ~$58 | 1 | 5/2, 24 VDC. Anchors: 4-station $37.56, 8-station $80.30 |
| 2.4 | Cylinder — body clamp | [Baomain SDA16×10](https://www.amazon.com/dp/B01LLQ6GEK) `B01LLQ6GEK` | ✅ **$7.99** | 1 | On the arm; clamps the unsplit ribbon behind the comb |
| 2.5 | Cylinder — guillotine | [Baomain SDA20×20](https://www.amazon.com/dp/B01LMMXDXA) `B01LMMXDXA` | ✅ **$11.47** | 1 | Needs the most force of the five |
| 2.6 | Cylinder — slit blades | Baomain SDA20×20 `B01LMMXDXA` | ✅ **$11.47** | 1 | |
| 2.7 | Cylinder — spreader | Baomain SDA16 class | ⚠️ ~$8 | 1 | 16×20 variant, same family as 2.4 |
| 2.8 | Cylinder — strip blades | Baomain SDA20×20 `B01LMMXDXA` | ✅ **$11.47** | 1 | |
| 2.9 | Flow controls (meter-out) | [10 pc, 6 mm × M5 push-to-connect](https://www.amazon.com/dp/B0G4BWS1HK) `B0G4BWS1HK` | ✅ **$13.49** | 1 | **Two per cylinder, not optional.** Without them cylinders slam at full line pressure — fatal to slit-depth repeatability |
| 2.10 | Reed switches | [Baomain cylinder magnetic sensor](https://www.amazon.com/dp/B01IZAFRWC) `B01IZAFRWC` | ✅ **$8.29** ea | 4 | Extended + retracted confirmation. Turns "fire and hope" into "fire and confirm" — required before the arm may rotate away from a die |
| 2.11 | Tubing | [TAILONZ 6 mm OD PU, 10 m](https://www.amazon.com/dp/B0DM1YWDTR) `B0DM1YWDTR` | ✅ **$18.99** | 1 | |
| 2.12 | Air pressure switch | [QWORK 90–120 psi](https://www.amazon.com/dp/B08FBCDNR5) `B08FBCDNR5` | ✅ **$19.97** | 1 | Refuse to run on low air — a half-stroke die is worse than no stroke |

**Subtotal ~$359** · 10 of 12 priced live

**Wiring note:** valve coils draw ~170–330 mA at 24 V — far past a logic pin.
Drive from the Octopus's MOSFET outputs. **Flyback protection is mandatory:**
either DIN 43650 connectors with surge suppression, or a diode across each coil.
Skipping it kills outputs.

---

## 3. Main arm

Five axes: **Z** lift, **θ** rotate, **R** extend, **S** cross-slide, **W** wrist.

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 3.1 | Steppers | [NEMA 17 42×40, 0.41 N·m, 1.5 A](https://www.amazon.com/dp/B0FHHVPJF1) `B0FHHVPJF1` | ✅ **$14.84** ea | 6 | Z, θ, R, S, W, F(feed). 5.0★ |
| 3.2 | **θ spindle bearings** | [uxcell 6810-2RS 8-pack](https://www.amazon.com/dp/B0H1LVWD99) `B0H1LVWD99` | ✅ **$26.99** | 1 | **$3.37 each** — the 8-pack beats [VXB's $24.99 singles](https://vxb.com/search?q=6810) by 7×. Paired 50 mm apart: 240 N radial each vs ~6,200 N static, **26× margin** |
| 3.3 | Z stage — guide rods | 8 mm hardened rod, 200 mm | ⓘ ~$14 | 3 | **Unsourced** |
| 3.4 | Z stage — linear bearings | [LM8UU 12-pack](https://www.amazon.com/dp/B0F1YGLS8X) `B0F1YGLS8X` | ✅ **$10.99** | 1 | Two per post, plenty spare |
| 3.5 | Leadscrews | [T8 200 mm + brass nut](https://www.amazon.com/dp/B07B63CVSJ) `B07B63CVSJ` | ✅ **$8.19** ea | 3 | Z, R, S. **T8 trapezoidal self-locks** — an E-stop will not drop the arm |
| 3.6 | θ — belt reduction | [GT2 20T + 60T + belt](https://www.amazon.com/dp/B0D5HMMGKG) `B0D5HMMGKG` | ✅ **$9.99** | 1 | 3:1. Resolution and holding torque against station reaction |
| 3.7 | R — linear rail | [MGN12H 250 mm + carriage](https://www.amazon.com/dp/B0BYV8SYPG) `B0BYV8SYPG` | ✅ **$17.99** | 1 | The shared "extend into the station" motion |
| 3.8 | S — cross-slide rail | [uxcell MGN9 100 mm + MGN9C](https://www.amazon.com/dp/B0D54LNVKX) `B0D54LNVKX` | ✅ **$9.99** | 1 | 20 mm stroke, selects conductor 1/2/3 |
| 3.9 | Couplers, collars | 5×8 flexible couplers, shaft collars | ⓘ ~$18 | 1 | **Unsourced** |

**Subtotal ~$222** · 7 of 9 priced live

### 💡 Worth pricing before ordering: integrated leadscrew motors

The pass surfaced [NEMA 17 with an **integrated T8 leadscrew shaft**, 150 mm,
0.4 N·m, **$14.38**](https://www.amazon.com/dp/B0CX8Z2MGT) `B0CX8Z2MGT` — the same
price as a plain motor. For Z, R and S that replaces *motor + coupler + separate
screw* with one part, removing an alignment error source and improving
concentricity. Could take ~$30 out **and** simplify three axes. Check the
available lengths against our strokes first.

### 🔴 A lazy-susan turntable was proposed here and withdrawn

Rated for **axial** load on a table, not moment. Under a 200 mm cantilever they
tip, and their millimetre-scale axial play would have invalidated the very
stiffness test that justifies building Phase 1 at the full R₀. **Do not buy one.**

The paired spindle is plausibly the **production** answer too, not a stand-in —
better per dollar than a slew ring for this load case, and it shrank the Z
platform from 248 mm to 165 mm.

### Slew-ring fallback, if the spindle shows runout

Bore and OD are **not independent** — PBC catalogue, 2026-07-26:

| bore | OD | cheapest |
|---|---|---|
| 20 mm | 80 mm | $93.69 |
| 30 mm | 100 mm | $127.23 |
| 50 mm | 150 mm | $164.19 |
| 60 mm | 160 mm | $199.35 |
| 100 mm | **185 mm** | $289.65 |

A 100 mm bore comes with a 185 mm OD, not the 120 mm once assumed. That ripples
into the Z platform, which is why `Z_POST_CIRCLE_R` is **derived** in `layout.py`
rather than hand-set — typing it by hand caused two clashes.

---

## 4. Station 1 — feed / measure / cut

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 4.1 | Spool | printed, 110 mm OD, 8 mm bore | — | 1 | **The ribbon ships as a loose roll**, so hub, flange and bore are ours. Holds 17.9 m vs a 15.24 m stock roll |
| 4.2 | Hanger + dancer arm | printed | — | 1 | Passive payoff; the dancer flag doubles as spool-empty detect |
| 4.3 | Dancer spring | extension spring assortment | ⓘ ~$8 | 1 | Also on `bom-v1.md` line 7 |
| 4.4 | **Measuring encoder** | [600 P/R incremental optical, 5–24 V](https://www.amazon.com/dp/B0G52C5BW1) `B0G52C5BW1` | ✅ **$14.99** | 1 | **Owns cable length accuracy.** With the wheel below: **0.0417 mm/count** |
| 4.5 | Measuring wheel | printed, **Ø31.83 mm = 100.00 mm circumference** | — | 1 | Length in mm is `counts × 100 / 2400`. **No rubber tyre** — a compliant surface changes effective circumference, the exact error this wheel exists to avoid |
| 4.6 | Drive rollers | knurled shaft + polyurethane idler | ⓘ ~$15 | 1 | **Unsourced** — printed housing exists (`drive_roller_block`) |
| 4.7 | PTFE guide tube | [Quickun 2 mm ID / 4 mm OD](https://www.amazon.com/dp/B08Q7X1J2Z) `B08Q7X1J2Z` | ✅ **$6.99** | 1 | Sets a repeatable presentation point regardless of spool behaviour |
| 4.8 | Guillotine blade | replaceable chisel/utility blade | ⓘ ~$10 | 1 | **Unsourced.** Must **shear, not crush** — a crushed end will not enter the comb channels |
| 4.9 | Spool-empty sensor | [IR slot/photo-interrupter modules](https://www.amazon.com/dp/B0CHDRF497) `B0CHDRF497` | ✅ **$9.99** | 1 | Reads the dancer flag |

**Subtotal ~$65** · 3 of 6 purchased lines priced live

---

## 5. Station 2 — split + fan

**Ribbon geometry is now confirmed from the vendor spec, not deferred.** The
listing states conductor OD **1.40 mm**, 60 × 0.08 mm tinned copper (0.302 mm²,
genuine 22 AWG), PVC. Three conductors co-extruded tangent, so pitch = **1.40 mm**
and overall width = **4.20 mm**. `cell-design.md`'s 2.5 mm was the *connector*
cavity pitch borrowed by mistake.

🟢 **And the ribbon is designed to be pulled apart by hand** — that is what flat
JR/Futaba servo wire is *for*. The web is deliberately weak, which likely
collapses this station from a precision slitting die into a **printed splitting
wedge**. See [`docs/stations.md`](../docs/stations.md) §2.

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 5.1 | Splitting wedge | printed | — | 1 | **Replaces the two-blade die**, pending a 5-second hand test on the real ribbon |
| 5.2 | Spreader plate | printed, 1.40 → 8 mm over 25 mm | — | 1 | **7.5° splay** — no set in the insulation |
| 5.3 | Slitting blades + depth adjust + anvil | scalpel blades, M3 fine-pitch, ground flat | ⓘ ~$32 | 1 | **Only if the wedge route fails.** Held as the fallback, not the plan |

**Subtotal $0 if the wedge works, ~$32 if not** — plus, on the wedge route, one
fewer cylinder, valve and pair of flow controls (**−$8, −1 manifold station**).

**The test costs nothing:** when the ribbon arrives, zip 25 mm apart by hand and
watch whether the tear runs straight. That decides the station.

---

## 6. Station 3 — strip

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 6.1 | V-blade die, 3-position | HSS or repurposed stripper blades at 8 mm comb pitch | ⓘ ~$22 | 1 | **Unsourced.** One stroke scores all three — equal strip length by construction |
| 6.2 | Depth stop shims | [brass shim stock assortment](https://www.amazon.com/dp/B09V5LPSNB) `B09V5LPSNB` | ✅ **$9.92** | 1 | Wrong depth = nicked strands = the crimp fails a pull test two stations later |
| 6.3 | Slug waste chute | printed | — | 1 | Slugs drop away, not into the mechanism |

**Subtotal ~$32**

*(The pull-off is done by the arm retracting 4 mm — no dedicated actuator, but it
is why **R needs ≥50 N thrust** and therefore a leadscrew, not a belt.)*

---

## 7. Printed parts — and which filament each takes

Fifteen modelled. Generate with `freecadcmd cad/build_parts.py` — FCStd + STEP +
STL from the same `sim/layout.py` dimensions the simulation uses.

**The split rule:** *PETG where sustained load, creep or impact dominates. PLA+
where dimensional accuracy or fine features dominate.*

PLA creeps under constant room-temperature stress in a way PETG does not, so
anything permanently loaded is PETG. But PLA+ holds sharper features and better
dimensional accuracy, which matters more than toughness on the parts whose *fit*
is the functional requirement.

| Part | Filament | Vol cm³ | Qty | Why this material |
|---|---|---|---|---|
| `z_platform` | **PETG** | 268.9 | 1 | Carries the entire rotating assembly, permanently loaded |
| `station_mount` | **PETG** | 46.6 | 7 | Structural, permanently loaded |
| `spindle_shaft` | **PETG** | 94.1 | 1 | Bearing seats under constant load |
| `spool_hanger` | **PETG** | 81.0 | 1 | 150 mm upright under constant dancer tension — the classic PLA creep case |
| `guillotine_holder` | **PETG** | 75.1 | 1 | Repeated impact from the blade stroke |
| `drive_roller_block` | **PETG** | 67.0 | 1 | Constant spring preload at the nip |
| `radial_carriage` | **PETG** | 21.2 | 1 | Takes the ~50 N pull-off thrust |
| `wrist_mount` | **PETG** | 12.0 | 1 | Repeated flip loads and hard-stop impact |
| `spool` | PLA+ | 116.6 | 1 | Light, intermittent load; big flat print where PLA+ warps less |
| `camera_mount` | PLA+ | 29.5 | 1 | Light; slotted for adjustment |
| `guide_tube_mount` | PLA+ | 14.4 | 1 | Light; press-fit bore wants accuracy |
| `comb` | PLA+ | 9.3 | 1 | **1.8 mm channels are the functional fit** — sharper features beat toughness here, and load is guide-only |
| `dancer_arm` | PLA+ | 6.2 | 1 | Light |
| `spreader_plate` | PLA+ | 6.0 | 1 | Finest features in the build — 1.45 → 8 mm diverging slots |
| `measuring_wheel` | PLA+ | 5.3 | 1 | **Concentricity is everything** — PLA+ is the more dimensionally stable choice |

### Filament quantity

At ~60% effective density (walls plus ~40% infill):

| Material | Solid cm³ | With infill | Grams | Spools |
|---|---|---|---|---|
| **PETG** | 945.5 | 567 | **~720 g** | 0.72 |
| **PLA+** | 187.3 | 112 | **~139 g** | 0.14 |

**One 1 kg spool of each covers the whole build with margin** — and PETG is the
one you will actually consume, since `z_platform` and seven `station_mount`s are
62% of the total volume between them.

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 7.1 | PETG, 1 kg | [eSUN PETG 1.75 mm](https://www.amazon.com/dp/B07FXVGYKL) `B07FXVGYKL` | ✅ **$12.99** | 1 | Cheaper eSUN PETG line. Alt [`B0BN4Y1G2S`](https://www.amazon.com/dp/B0BN4Y1G2S) $21.99 |
| 7.2 | PLA+, 1 kg | [eSUN PLA+ 1.75 mm](https://www.amazon.com/dp/B07FQDKR28) `B07FQDKR28` | ✅ **$15.29** | 1 | The PLA+ you already run |

**Filament subtotal ~$28.**

Print notes and orientations in [`cad/README.md`](../cad/README.md). Still to
model: slug chute, body-clamp mount, cross-slide carrier.

## 7b. Arm camera

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 7b.1 | Camera | **ELP-USBFHD01M-L36**, 3.6 mm | **$0** | 1 | Kyle has spares. Same model as TendWright's fleet, so `cameras.py` / `camserve.py` work unchanged |
| 7b.2 | AprilTags | tag36h11, 25 mm, printed | — | 7 | Arm measures actual pose vs commanded at each stop |
| 7b.3 | Ring light | small LED ring or bar | ⓘ ~$12 | 1 | **Unsourced.** Tag detection needs consistent illumination more than brightness |
| 7b.4 | USB cable | 2 m, through the drag chain | ⓘ ~$8 | 1 | **Unsourced.** Must survive ±135° sweep plus Z stroke |

---

## 7c. Consumables — ribbon and reference cables

Carried over from `bom-v1.md`; these are Phase 1 items and belong here too.
**Re-verified live 2026-07-27.**

| # | Item | Pick | Price | Qty | Notes |
|---|---|---|---|---|---|
| 7c.1 | **Ribbon stock** | [YXQ 22 AWG servo cable, 50 ft](https://www.amazon.com/dp/B0CQ1V38RF) `B0CQ1V38RF` | ✅ **$9.30** | 2 | ⚠️ **Only 11 left in stock.** 22 AWG, 60 cores × 0.08 mm, black/red/white JR, 1.4 mm OD. One spool dev scrap, one for real cables |
| 7c.2 | Ribbon — alternate | [OliYin 50 ft 22 AWG 3-pin](https://www.amazon.com/dp/B071VN9DF1) `B071VN9DF1` | ✅ **$14.80** | — | **In Stock**, no quantity warning. Same 60-core spec. Use if 7c.1 sells out |
| 7c.3 | Ribbon — alternate 2 | [22 AWG servo extension, 50 ft](https://www.amazon.com/dp/B0F3D3SBBP) `B0F3D3SBBP` | ✅ **$14.99** | — | 20 left |
| 7c.4 | **Reference cables** | [waveshare 5264-3PIN, 6 pcs](https://www.amazon.com/dp/B0GVDFXF7Q) `B0GVDFXF7Q` | ✅ **$9.99** | 1 | **The factory-crimp yardstick.** True 5264 3-pin — the exact target connector. Measure its crimp height and pull force before cutting a single terminal |

**Consumables subtotal ~$28** (2× ribbon + reference cables).

**Buy the ribbon now.** It is the one Phase 1 line with a stock warning, it is
cheap, and **every station's tooling geometry depends on measuring its real
cross-section** — the ~1.45 mm conductor pitch that S2's blades depend on is
currently derived, not measured.

---

## 8. Decisions and flags

### The pneumatic wrist is dropped — $220 → $15

`cell-design.md` §5.2 specified a **pneumatic 180° rotary actuator**, reasoned as:
the wrist needs only two positions, so no servo. Sound on *control simplicity*.
Live pricing killed it — **Airtac HRQ10 $220.50, HRQ20 $252.54**, more than every
stepper on the machine combined. A NEMA 17 with a belt and two hard stops does the
same job for **$14.84** on a spare driver slot. Hard stops stay; the motor only
has to reach them.

### Deck is plywood or acrylic, not aluminium tooling plate

A 560 mm aluminium plate is $150+ and is the wrong thing to buy while station
positions are still placeholders. Ply or acrylic is re-drillable, and finding out
where the holes actually go is the whole point of Phase 1.

### Where the money is

Pneumatics are **~35%** of Phase 1, and the compressor alone is **14%**. If the
total needs to come down:

- Drop reed switches (−$33) — lose stroke confirmation, run dies open-loop
- Drop the spreader cylinder and hand-set the fan for early trials (−$8 + a valve)
- Integrated leadscrew motors (§3) — possibly ~$30 out *and* three axes simpler

---

## 9. Do NOT buy here

| Item | Why | Instead |
|---|---|---|
| Housings / terminal chain on Amazon | Packaging form decides whether an applicator can feed them, and Amazon listings are repackaged and unverifiable | Mouser / DigiKey — `bom-v1.md` |
| Machine applicator on Amazon | **Confirmed absent.** Two searches returned only hand ratcheting crimpers | eBay — `bom-v1.md` line 10 |
| Lazy-susan turntable | Rated for axial load, not moment. Tips under a cantilever | Paired 6810 spindle, line 3.2 |
| **AM-10 pneumatic crimper** | 🔴 Wrong machine class — a die-set plier that cannot feed a terminal chain | — |

---

## 10. Sourcing status

**~33 of 49 lines priced off a live page**, covering roughly 83% of the cost.

Still ⓘ **unsourced**, and why:

- **S3 tooling** (1 line) — the V-blade die geometry is not fixed.
- **S2 is now resolved on paper** — the vendor spec settled the ribbon geometry
  that was previously being deferred to "measure on arrival", and the
  hand-separable construction points at a printed wedge rather than a bought die.
  What remains is a materials question no datasheet answers: does the tear run
  straight for 25 mm. Answered by hand, free, the day the ribbon lands.
- **Consumables and hardware** (6 lines) — extrusion fasteners, wiring, dancer
  spring, drive rollers, guillotine blade, ring light, USB cable. Small, and most
  depend on the frame design.
- **Deck plate** — a local cut, not a catalogue item.

**Two estimates have now been checked against reality, and both were wrong in
different directions:** the rotary bearing 5× low, the motion controller 2× high.
That is why guesses get marked ⓘ rather than dressed up as prices.
