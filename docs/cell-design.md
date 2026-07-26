# CableCell v1 — Full Design Document

**Date:** 2026-07-24 · **Hive:** app 9 (CableCell), plan #657
**Supersedes:** the layout sketches in `exploration-and-thumbnail.md` (that doc remains the prior-art survey and decision log).
**Architecture:** rotary dial (Kyle 2026-07-24) — fixed stations on a bolt circle, one arm carries the work to them.

---

## 1. The job this machine exists to do

> Load 20 housings into the cassette, a spool of ribbon, and a reel of pins. Tell the software: **3 cables, 5 inch total length.** It makes them and they drop into the collect bin as they complete.

That is the acceptance test, stated as a spec:

| | |
|---|---|
| **Input consumables** | 20× Molex 50-37-5033 housings (cassette) · 1 spool 22 AWG 3-conductor servo ribbon · 1 reel Molex 0008701039 terminal chain |
| **Job command** | `qty=3, length=127.0 mm (5.00"), recipe=SPOX-3P` |
| **Output** | 3 finished cables, connector on both ends, in the collect bin |
| **Consumed** | 6 housings, 18 terminals, ~420 mm of ribbon (3 × 127 mm + kerf/lead-in) |
| **Untouched** | 14 housings still in the cassette |
| **Unattended** | Yes — operator loads, presses Run, walks away |

**Length definition (matters, gets calibrated):** *total length* = tip of connector A to tip of connector B. The machine works internally in **ribbon length** and applies a per-recipe constant (`connector_offset`) for the amount of wire consumed inside each housing. Calibrate once by measuring a produced cable; store in the recipe.

**Length envelope:** minimum ~90 mm (set by 2 × split length + handling clearance), maximum ~1000 mm (set by the payout trough). 127 mm sits comfortably in range.

**Capacity per load:** 20 housings = 10 cables. A 15 m ribbon spool at 127 mm = ~110 cables. A 5000-terminal reel = ~830 cables. **Housings are the binding constraint** — by design, since they're the one thing a human loads by hand.

---

## 2. Machine overview

A rotary indexing cell. Six stations sit on a bolt circle. One **arm** pivots between them and extends radially into whichever station it faces. Nothing else moves the workpiece.

```
                       ┌──────── S2 SLIT + FAN ────────┐
                       │                                │
        S1 FEED / CUT ─┤          ●  pivot              ├─ S3 STRIP
        (spool, rollers│         ╱                      │
         guillotine)   │        ╱  arm  ──► extends     │
                       │       ╱   radially into        │
        S6 DROP ───────┤          whichever station     ├─ S4 CRIMP
        (collect bin + │          it is facing          │   (press +
         reject bin)   │                                │    applicator)
                       └──────── S5 INSERT ─────────────┘
                                 (housing cassette,
                                  nest, pusher)
```

**Why rotary:** repeatability comes from mechanical detents at each sector rather than a long rail staying square; each station is a bolt-on module in its own sector (which is precisely how "other connectors later" arrives — a new insert sector plus a new cassette); and the circle fits the working stations in less bench space than a 900 mm rail. The reject bin costs nothing — it is simply another angular position.

> **Bolt circle corrected 2026-07-26.** This section previously claimed a ~300 mm circle. It does not close: seven stops (six stations plus reject) with a 210 mm-wide press need **274.4° of a 270° arc** at R₀ = 150 mm. The working value is **R₀ = 200 mm** — a 400 mm circle — which needs 201.8° and leaves 68° spare. Minimum viable is ~175 mm. Computed by `sim/studies/fit_check.py`; table in `docs/datums.md`. The original figure was written for *five* stations, before the press was understood as a standalone machine.

**Working arc, not a full turn.** The arm sweeps ~270° and returns. The trailing ribbon sweeps with it but never wraps the pivot, so no slip ring and no rotary air union are needed — a service loop and drag chain carry power and air to the arm.

### 2.1 The arm (the only thing that moves the work)

Three things ride on the arm:

- **Comb** — the gripper. Not a plain clamp: a **3-channel guide** that keeps each conductor individually addressable. The channels *guide*; they do not clamp. The **ribbon body is clamped** behind the split, so each conductor can slide freely in its own channel — which is what lets a pusher advance one conductor at a time at the insert station.
- **Cross-slide** — a short lateral axis (~20 mm) that indexes which conductor sits on the station work line. One conductor at a time to the crimp anvil; one conductor at a time to the insertion axis. Comb channel pitch is **8 mm**, deliberately *not* the 2.5 mm connector pitch — see §5.4.
- **Wrist** — a 180° flip. Needed because the two ends of a cable are born pointing in opposite directions (§3, step 7). It only ever needs two positions, so it is a **pneumatic rotary actuator with adjustable hard stops**, not a servo.

---

## 3. Full cycle — one cable, step by step

Running the 3 × 127 mm job. Steps 1–13 repeat three times.

**End A (still attached to the spool — the spool is the anchor)**

1. **Present.** Feed rollers advance ribbon until ~30 mm protrudes past the guillotine at S1.
2. **Grip.** Arm at S1, comb closes on the ribbon body; ~28 mm of tail projects radially outward.
3. **Slit + fan (S2).** A two-blade die notches both webs back 25 mm from the tip. A spreader plate then splays the three tails into the comb's 8 mm channels. Ribbon body stays clamped throughout.
4. **Strip (S3).** A 3-position V-blade die closes on all three conductors at comb pitch; the arm retracts ~4 mm to slip the slugs. Strip length 2.5–3 mm. Three slugs drop to the waste chute.
5. **Crimp ×3 (S4).** For each conductor *i*: cross-slide indexes conductor *i* onto the anvil line → station wire-clamp holds it → press fires one stroke → applicator crimps the terminal and severs it from the carrier → load cell records the force curve → cross-slide advances 8 mm. Carrier scrap exits to its own bin. Three pins now stand on the fanned tails at 8 mm spacing.
6. **Insert ×3 (S5).** Escapement drops one housing from the cassette into the nest; nest clamp closes. Then for each conductor *i*: cross-slide brings conductor *i* onto the **fixed insertion axis** → pusher finger closes on the wire ~5 mm behind the pin → drives forward until the housing lance clicks → pulls back 1.5 mm against a stop (retention test, load cell) → releases → **nest indexes one 2.5 mm pitch** so the next cavity arrives on the same fixed axis. Already-inserted conductors travel *with the housing*, so nothing is strained and the tooling only ever works at one spot. Camera checks black/red/white land in cavities 1/2/3. Nest clamp opens; end A is complete.

**Payout and cut**

7. **Pay out.** Arm returns to a defined **payout reference position** holding the finished end A, so the tube-to-comb distance is a known constant. Feed rollers pay out ribbon until `ribbon_length = 127 mm − connector_offset`, measured by the independent encoder wheel (not by counting steps — ribbon slips). Slack sags into the payout trough.
8. **Hand off.** Arm releases end A into the trough and returns to S1, gripping the ribbon on the *piece* side of the guillotine.
9. **Cut.** Guillotine severs. The arm now holds the cable by end B; the finished connector A dangles in the trough. The spool's new leading end waits at the tube for the next cable.
10. **Flip.** Wrist rotates 180°, so end B's tail now projects radially outward exactly as end A's did in step 2. **Every station sees identical geometry for both ends** — this is what the wrist buys, and why it isn't optional.

**End B**

11. **Repeat 3–6** on end B. Same stations, same tooling, same motions, second housing.
12. **Drop.** Arm indexes to S6 over the collect bin, comb and body clamp open, finished cable falls. On any fault flag (crimp force out of band, retention fail, camera mismatch) the arm drops at the **reject** angle instead and logs why.
13. **Next.** Feed rollers advance the spool's new leading end past the guillotine. Go to step 2.

**Job end:** after cable 3, the machine parks, reports `3/3 complete, 0 rejects, 6 housings used, 14 remaining`, and idles.

---

## 4. Cycle time

| Phase | Ops | Est. |
|---|---|---|
| Grip + slit + fan + strip | 4 moves, 3 strokes | ~12 s |
| Crimp ×3 | 3 index + 3 strokes | ~15 s |
| Insert ×3 | 3 index + 3 push/verify + 3 nest index | ~20 s |
| **Per end** | | **~47 s** |
| Payout, handoff, cut, flip | | ~15 s |
| **Per cable** (2 ends + payout) | | **~110 s** |
| **3 × 127 mm job** | | **~5.5 min** |

Commercial machines do this in 7–9 s per cable. We are ~15× slower and roughly 40× cheaper — the right trade for batches of ten.

---

## 5. Mechanical parts — what each one is for

### 5.1 Frame and rotary axis

| Part | Function |
|---|---|
| Aluminum extrusion frame (3030) + 10 mm tooling-plate deck | Rigid datum (Datum A). Every station bolts to the deck on the same bolt circle, so station geometry is set by hole position, not by shimming. |
| **Z stage** — commodity ballscrew linear module (SFU1605 + dual rails + NEMA 17/23) | **Carries the entire rotating assembly.** Lets each station have its own engagement height instead of forcing all seven to one shimmed plane, and provides vertical clearance for rotation. Stack is base → Z → rotary → arm. Stiffness-critical: it sits at the bottom of a long lever, so its compliance shows up magnified at the comb. Prefer the shortest travel that works. See `datums.md`. |
| **Main bearing** — large-bore thin-section or tapered roller, ~80–100 mm | Carries the arm. Must take the *radial extension load* and the reaction from insertion pushes without deflecting more than ~0.05 mm at the comb. |
| Arm rotary drive — NEMA 17 + 5:1 belt reduction, or NEMA 23 direct | Indexes between sectors. Reduction buys resolution and holding torque against station reaction forces. |
| **Detent/index plate** — hardened bushing + spring-loaded or pneumatic plunger per sector | Repeatability. The stepper gets *near* the sector; the detent puts it *exactly* there. This is why rotary beats linear on precision-per-dollar. |
| Drag chain / service loop | Carries the arm's air lines (comb clamp, wrist), stepper cable, and sensor wiring across a ±135° sweep **plus the Z stroke**. No slip ring needed. |

### 5.2 The arm assembly

| Part | Function |
|---|---|
| Radial slide — MGN12 rail + carriage, belt or leadscrew, NEMA 17 | The shared "extend into the station" motion. Every station uses it; this is the big saving of the rotary layout. |
| **Comb** — machined or printed 3-channel guide, hardened channel inserts | Keeps each conductor individually addressable and at a known pitch. Channels guide only. Swappable per connector recipe. |
| **Body clamp** — pneumatic cylinder + serrated pad | Clamps the *unsplit ribbon* behind the comb. This is the actual grip; it takes all handling load, so conductors stay free to slide. |
| Cross-slide — MGN9 + 20 mm leadscrew, NEMA 17 | Indexes conductor *i* onto the work line at crimp and insert. |
| **Wrist** — pneumatic 180° rotary actuator with adjustable stops | Flips end B into end A's orientation. Two positions only, so no servo. |

### 5.3 S1 — Feed / measure / cut

| Part | Function |
|---|---|
| Spool holder + spring dancer arm | Passive payoff at constant light tension; dancer flag doubles as spool-empty detect. |
| Drive rollers (knurled steel + polyurethane idler, spring preload) NEMA 17 | Pays ribbon out and pulls it back. |
| **Measuring wheel + rotary encoder** (independent of the drive) | Owns cable length accuracy. Never trust drive-roller steps — ribbon slips. Closed loop on this encoder. |
| PTFE-lined guide tube | Delivers the ribbon to a repeatable presentation point regardless of spool behaviour. |
| **Guillotine** — hardened blade + anvil, pneumatic | Square full-width cut. Blade geometry must not crush the ribbon end (a crushed end won't enter the comb channels). |
| Payout trough | Receives slack and the dangling finished end A during payout. Keeps a 1 m cable out of the mechanism. |

### 5.4 S2 — Slit + fan

| Part | Function |
|---|---|
| **Two-blade slitting die**, depth-adjustable to 0.05 mm, pneumatic | Notches both webs simultaneously to the recipe's split length (25 mm). Depth control is the whole game — too shallow and it won't zip, too deep and it nicks copper. |
| Spreader plate — diverging slots, pneumatic | Splays the three slit tails from ribbon pitch (~2.5 mm) out to comb pitch (8 mm) and captures them in the comb channels. |
| Backing anvil | Supports the ribbon so the blades cut rather than push. |

**Why 8 mm and not 2.5 mm:** the fan pitch is a free parameter, and widening it is what removes the pin-to-pin collision risk at the crimp anvil. Convergence back to the connector's 2.5 mm never happens mechanically — pins are inserted one at a time, so the cross-slide handles it in software.

### 5.5 S3 — Strip

| Part | Function |
|---|---|
| 3-position V-blade die at comb pitch, pneumatic | Scores all three conductors in one stroke — equal strip length by construction. |
| Depth stop, per-recipe shim | Sets score depth for 22 AWG. Wrong depth = nicked strands = the crimp fails a pull test later. |
| Slug waste chute | The three insulation slugs drop away rather than into the mechanism. |

(The *pull-off* is done by the arm retracting 4 mm — no dedicated actuator.)

### 5.6 S4 — Crimp

| Part | Function |
|---|---|
| **Bench press, 1.5–2 T, 30–40 mm stroke** (electric motor-and-cam) | The force. Dumb by design; all per-terminal intelligence lives in the applicator. Pneumatic route dropped 2026-07-25. **Bought, never built** (Kyle 2026-07-26) — and placed *first*, as the layout datum: its anvil fixes θ₄ and one bolt-circle point, its crimp height fixes Z₄. |
| **Mini-applicator** for Molex 5263 chain — donor XH2.5 clone, custom-tooled unit, or our own build | Indexes one terminal per stroke off the bandolier, forms wire + insulation crimps, severs the carrier. **The one part we do not improvise** (see the applicator subproject, §9). |
| Terminal reel arm + drag brake (spring steel strip) | Constant back-tension on the chain. Loose chain = mis-feed = the single most common failure mode on real machines. |
| Chain guide + terminal-present optical sensor | Detects mis-feed *before* a stroke fires on an empty anvil. |
| Station wire clamp, pneumatic | Holds the conductor axially during the crimp stroke. |
| **Load cell + amplifier on the press ram** | Crimp-force curve per stroke — the standard in-line QA signal. Out-of-band → flag the cable for the reject bin. |
| Carrier scrap chute + bin | Severed carrier strip has to go somewhere. |

### 5.7 S5 — Insert

| Part | Function |
|---|---|
| **Housing cassette** — printed stick magazine, keyed cross-section, spring follower | Holds ~25 housings in one orientation. The friction-lock ramp keys them so they physically cannot load backwards. **Swappable per connector family** — this is the roadmap seam. |
| Escapement — sliding shutter, pneumatic | Releases exactly one housing per cycle. |
| Nest — pocket matching the housing profile + pneumatic clamp | Holds the housing rigidly and backs it up against insertion force. |
| **Nest index slide** — NEMA 17 + leadscrew, 2.5 mm steps | Brings cavity *i* to the fixed insertion axis. *The housing moves, not the wires* — this is the design's key move. |
| Funnel guide — tapered entry, ±0.3 mm capture | Forgives pin position error at the cavity mouth. |
| **Pusher** — finger/collet on a short pneumatic stroke + load cell | Closes on the **wire ~5 mm behind the pin** (never on the pin — a pin must not be loaded through its crimp), drives until the lance clicks, then pulls back 1.5 mm against a stop for the **retention test**. |
| Housing-present + low-stack optical sensors | Don't fire into an empty nest; warn before the cassette runs out. |
| Camera (USB) + LED ring | Verifies black/red/white in cavities 1/2/3 before the housing leaves the nest. USB rather than CSI since the supervisor is a NUC. |

### 5.8 S6 — Output

| Part | Function |
|---|---|
| Collect bin + chute | Finished cables drop here as they complete. |
| Reject bin | A separate angular position — costs one bracket. A machine without a reject path silently ships bad parts. |

### 5.9 Guarding

| Part | Function |
|---|---|
| Polycarbonate guard around the press + arm sweep, interlock switch | The press is 1.5 T. Guarding is not optional. |
| E-stop, hard-wired | Cuts 24 V motor and valve power directly — not via software. |

---

## 6. Electrical / electronic parts — what each one is for

### 6.1 Compute

| Part | Function |
|---|---|
| **Spare NUC on Ubuntu** (8 GB, SSD) | Supervisor. Job queue, cable state machine, recipes, calibration constants, web HMI, camera inspection, logging, and the agent that reports cell status into Hive. Pi 5 cut 2026-07-24: the split-brain design already makes the supervisor architecture-independent, Kyle has a stack of NUCs, and x86 + a real SSD beats ARM + SD card for a machine running unattended jobs. $0. |
| **Motion controller** — BTT Octopus (8 driver slots) or Duet 3 Mini, running Klipper or grblHAL | Real-time step generation and endstop handling. The supervisor cannot hold microsecond step timing while serving a UI; this split is standard practice. 8 slots leaves headroom for the 6 axes. |
| 24 V / 350 W PSU | Steppers, valves, sensors. |

### 6.2 Motion — 6 stepper axes

| Axis | Motor | Purpose |
|---|---|---|
| θ — arm rotate | NEMA 17 + 5:1 reduction | Index between station sectors |
| **Z — assembly lift** | **NEMA 17/23 + SFU1605 ballscrew** | **Per-station engagement height; lift to clear tooling before rotating** |
| R — arm extend | NEMA 17 + leadscrew/belt | Radial move into every station |
| S — comb cross-slide | NEMA 17 + 20 mm leadscrew | Select conductor 1/2/3 |
| F — ribbon feed | NEMA 17 + rollers | Payout and retract; length |
| H — housing nest index | NEMA 17 + leadscrew, 2.5 mm steps | Bring cavity *i* to the insertion axis |

Drivers: 6× TMC2209 (quiet, and sensorless homing removes switches if it proves reliable).

**Z holding is a safety item, not a performance one.** A ballscrew is efficient
enough to back-drive under load, so on a vertical axis carrying the whole
rotating assembly an E-stop could drop the arm. Resolve deliberately: self-locking
trapezoidal leadscrew, or ballscrew plus motor brake, or ballscrew plus
counterbalance. **Open.**

**Homing order:** Z homes to its up position before θ is permitted to rotate, or
the arm can sweep into station tooling on power-up.

### 6.3 Pneumatics — ~10 actuators

Compressor (1–2 gal quiet, ~$150) · **filter + regulator** — deliberately *not* a full FRL, since a lubricator injects oil into the air and that is the last thing we want near crimp tooling · 10-station manifold · 24 V solenoid valves (5/2 double-acting, 3/2 single-acting) · MOSFET outputs from the motion board or a driver breakout.

**Air is deferred to cell build.** With the press electric rather than pneumatic, nothing in the de-risk phase needs compressed air — $165 out of the near-term bucket (2026-07-25).

1. Body clamp · 2. Wrist 180° rotary · 3. Slit blades · 4. Spreader · 5. Strip blades · 6. Guillotine · 7. Press ram · 8. Insert pusher · 9. Housing escapement · 10. Nest clamp

Plus the sector detent plunger if it is pneumatic rather than sprung.

### 6.4 Sensors

| Sensor | Purpose |
|---|---|
| 5× home/endstop switches (θ, Z, R, S, H) | Datum on power-up. Z homes up first — see §6.2. |
| **Ribbon measuring encoder** | Closed-loop cable length — the accuracy-critical sensor |
| **Load cell + HX711/ADS1232 on press ram** | Crimp force curve → crimp QA |
| **Load cell on insert pusher** | Insertion click + pull-back retention test |
| Terminal-present optical (applicator) | Catch chain mis-feed before a wasted stroke |
| Housing-present (nest) + low-stack (cassette) | Don't insert into nothing; warn before running dry |
| Ribbon-out / dancer flag | Spool empty |
| Air pressure switch | Refuse to run on low air — a half-stroke crimp is worse than no crimp |
| USB camera + LED ring | Wire color/position verification |
| Guard interlock + E-stop | Safety |

---

## 7. Control software

**Layers.** Klipper/grblHAL on the MCU (motion primitives) ← Python supervisor on the NUC (state machine, recipes, QA) ← web HMI (job entry, status) + Hive agent (fleet reporting).

**Recipe** (per connector family — the "other connectors later" seam, in data rather than code):
```
SPOX-3P: conductors=3, cavity_pitch=2.5, comb_pitch=8.0,
         split=25.0, strip=2.75, insert_depth=6.0, pullback=1.5,
         crimp_force_band=[x,y], connector_offset=<calibrated>,
         cassette=SPOX-3P-v1, applicator=MOLEX-5263
```

**Job:** `{qty, length_mm, recipe}` → a queue of cable state machines, each running the §3 sequence.

**Every station reports pass/fail.** A cable that fails crimp force, retention, or camera check is flagged, completes its cycle, and drops in the reject bin with a logged reason. Nothing silently ships.

**Faults that stop the run:** no air, terminal mis-feed, cassette empty, spool empty, guard open, any axis losing home.

**Calibration constants** (stored, re-measurable): `connector_offset`, feed reference offset, per-sector angular positions, **per-station engagement heights Z₁…Z₇**, `Z_clear`, **payout reference Z**, strip depth shim, insertion depth, crimp force band.

The per-station Z table is what the base-mounted Z axis buys: station heights
become seven numbers touched off at commissioning rather than a single plane every
station must be mechanically shimmed to. `payout_z` matters because changing Z
changes the ribbon's free length between S1's guide tube and the comb — payout is
length-critical, so it only ever happens at one height.

**HMI:** enter qty + length + recipe, press Run, watch progress. Machine reports `n/N complete, r rejects, h housings remaining`.

---

## 8. What still needs proving before fabrication

Ranked. Items 1–2 are the printed-mockup work already in plan #657.

1. **Crimp quality with a real applicator** (de-risk A). Everything downstream assumes a good pin.
2. **Insertion + pull-back repeatability** (de-risk B), including the funnel's real capture window — which sets how good the arm's positioning must be.
3. **Slit depth window** on the actual ribbon — the difference between "zips cleanly" and "nicked strand."
4. **Fan geometry** — is 8 mm comb pitch enough clearance at the applicator throat, and does a 25 mm split give enough splay without an ugly finished cable?
5. **Arm stiffness under insertion load** — total compliance from Z carriage → rotary bearing → arm → radial slide → comb, versus the funnel's capture window. The Z stage sits at the bottom of a long lever, so its angular deflection is magnified at the comb; it is now the first term in this budget, not an afterthought.
6. **Slack behaviour during payout** — does the trough actually control a 127 mm cable's dangling end, and a 1 m one?
7. **Z travel envelope** — what max(Zᵢ) − min(Zᵢ) actually turns out to be once the press crimp height and station tooling heights are known. Drives stage cost and stiffness; wants the smallest defensible number.

---

## 9. Relationship to the applicator subproject

§5.6 lists the applicator as bought. Kyle's decision is to **build a ribbon-fed applicator** for the 5263 chain as a parallel subproject (its own module, `CableCell/Applicator`). The interface contract keeps the two tracks independent: **standard mini-applicator envelope and shank, side feed, same shut height.** Whatever we build drops into the same press and the same S4 bracket as the purchased donor — so the cell can be finished and producing cables on bought tooling while the applicator build proceeds on its own timeline, and swapping it in later is a bolt change.

---

## 10. Cost roll-up

| Bucket | Est. |
|---|---|
| Consumables (housings, terminals, ribbon) | ~$100 |
| Press + applicator + metrology | ~$560–800 |
| Compressor + filter/regulator + valves + manifold + cylinders | ~$400 |
| Compute (NUC $0, motion board, PSU, wiring) | ~$250 |
| Motion (6 steppers, drivers, rails, bearing, belts) | ~$400 |
| **Z stage** (ballscrew module + brake or leadscrew) | **~$100–250** |
| Frame, deck, printed stations, blades, dies | ~$350 |
| Sensors (encoder, 2 load cells, optical, camera) | ~$150 |
| **Total** | **~$2,300–2,700** |

Against ~$15–60k for the commercial equivalent — and it makes exactly the cable we need, in batches of ten, from a cassette a human can load in under a minute.
