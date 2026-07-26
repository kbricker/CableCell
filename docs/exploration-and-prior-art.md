# Cable-Making Robot Cell — Context Exploration + Implementation Thumbnail

**Date:** 2026-07-24
**Ask (Kyle):** A cell that is fed a spool of 2–3-conductor wire ribbon and, per cable: separates the conductors, strips them, crimps a pin on each, inserts the pins into a linear connector housing, pays out the ribbon to a requested length, then terminates the far end the same way. Output: a finished cable of length L with a connector on each end.

**Target part (pinned, from `TendWright/docs/wiring-hardware.md`):** **Molex Mini-SPOX 5264**, 3-position, **true 2.50 mm pitch** (not 2.54 — the Dupont/KK/XH lookalikes don't latch): housing **50-37-5033**, female crimp terminal **0008701039** (5263 series, 22–28 AWG, chain/reel form), on **22 AWG 3-conductor flat servo ribbon** (black/red/white = GND/Vcc/Signal). Both cable ends take the identical housing; this is the Feetech STS3215 servo-bus cable for the TendWright arm. See §2.7 for what this pins down.

---

## 1. What exists — the landscape

### 1.1 This machine class exists commercially (good news: proven decomposition)

The exact flow you described — ribbon in, split/strip/crimp both ends — is a shipping product category from the Chinese mid-market automation vendors:

- **Kingsing KS-T532** ("Automatic Ribbon Cable Stripping and Crimping Machine"): integrates *cut-to-length, stripping, conductor splitting, and dual-end terminal crimping* in one machine. AWG 18–28, cut length 60–1000 mm, strip 1–7 mm, ~400–550 cycles/hour, five servo axes, a mechanical-arm feed for length accuracy, independent terminal orientation per end, optional crimp-force monitoring. That is your spec minus housing insertion.
- **Kingsing housing-insertion line**: dual-head machines that add *housing insertion at both ends* on top of cut/strip/crimp, supporting single- and double-row housings, different housings per end, and crossed insertion patterns, with CCD vision for wire sequence checks.
- **JCWelec / WirePro / East World**: dedicated flat-ribbon slit-cut-strip machines (split length adjustable 0–60 mm per end, ribbon widths to ~20 mm), some with crimp + tin-solder stations.

Takeaway: nobody has to invent the process. The industry-standard station decomposition is **feed/measure → slit (split web) → strip → crimp → (insert) → cut**, done to the leading end first, then re-done to the trailing end after payout. These machines cost roughly $15k–60k; the interesting project is a benchtop DIY-scale version.

### 1.2 The industrial high end (architecture to steal, not buy)

- **Schleuniger CrimpCenter / Komax Zeta**: fully automatic cut-strip-crimp with wire feed up to 12 m/s and a **swivel arm** that presents the wire end to each fixed processing station in turn. Key architectural idea: *the wire end travels to the stations; the stations never move.* Zeta 620 does ~360 dual-ended cables/hour in a 2.1 × 1.5 m footprint.
- **Komax Omega 740/750**: adds fully automatic **block loading** (housing insertion) on both ends without interim wire storage. Insertion is: housing held in an indexed pallet, terminal pushed axially into the cavity until the housing lance clicks, then a **pull-back test** confirms retention.
- **Crimp applicator anatomy** (TE / ETCO / Mecal): the crimp itself is always a purchased **mini-applicator** — a self-contained tool that takes terminals on a bandolier reel, indexes one terminal per stroke via a cam-driven feed finger, and closes wire + insulation crimps over an anvil in a single ~40 mm press stroke (bench presses ~1.5–2 tonnes). The press is dumb; all the per-terminal intelligence lives in the applicator.

### 1.3 DIY / open-source state of the art

- Wire **cut + strip** is a solved hobby problem: many Arduino/stepper builds (Mr Innovative's cutter-stripper, sandy9159's GitHub project, Hackaday builds) — feed rollers + a movable blade that either scores (strip) or cuts through, ~$100 in parts.
- Automated **crimping** at hobby scale is essentially absent — the community stops at hand tools (Hackaday's "Inside the Secret World of Crimping" is the reference read). This is the hard station, and the reason to buy a real mini-applicator + small press rather than 3D-print one.
- Automated **housing insertion** at hobby scale: nothing found. This would be the genuinely novel part of the build.

### 1.4 The IDC counterpoint (worth one paragraph of honesty)

Ribbon cable's native termination is **IDC** — press a connector onto the *unstripped* ribbon; all conductors terminate simultaneously, no separate/strip/crimp/insert at all. An IDC-press station would collapse stations 2–5 into one pneumatic squeeze and is how industry handles ribbon whenever it can. **For our pinned target it doesn't apply:** Mini-SPOX 5264 is a crimp-only system (no IDC variant), and 22 AWG servo ribbon isn't IDC stock anyway — so the full crimp-and-insert cell below is genuinely required. Noted for honesty, closed as not applicable.

---

## 2. Thumbnail: benchtop cable cell v0

### 2.1 Concept in one sentence

A linear benchtop machine (~900 × 400 mm) where the ribbon stays stationary and a small **end-effector shuttle** carries the ribbon end through five fixed stations — slit, strip, crimp, insert — once for the leading end, then pays out length L, cuts, and repeats the sequence on the trailing end with the ribbon flipped 180° by the shuttle's rotary wrist.

```
 spool ──> dancer ──> feed rollers ──> [SHUTTLE zone] ──> guillotine ──> exit tray
 (A)       (B)        (C, encoder)          │              (G)
                                            │ shuttle gripper w/ 180° wrist (D)
                                            ▼ visits, in order:
                              ┌──────────────────────────────┐
                              │ S1 slitter  (web knife)      │
                              │ S2 stripper (V-blades + pull)│
                              │ S3 crimp    (mini-applicator │
                              │              + servo press)  │
                              │ S4 insert   (housing nest +  │
                              │              pusher + pull   │
                              │              -back check)    │
                              └──────────────────────────────┘
```

### 2.2 Stations

**A. Spool + dancer.** Passive payoff with a spring dancer arm for constant light tension; a flag sensor for "spool empty."

**B/C. Feed + measure.** Pinch rollers on a NEMA17 with an independent measuring-wheel encoder (don't trust roller steps — ribbon slips). This axis owns cable length accuracy; ±1 mm over 1 m is achievable, matching commercial ±(0.5 + 0.2 %·L) mm specs.

**D. Shuttle.** The one real robot in the cell: a linear axis (~300 mm) along the station row, a gripper that clamps the ribbon ~30 mm behind the working end, a small vertical axis, and a 180° rotary wrist. The wrist is what makes double-ended work possible: for the trailing end the ribbon is flipped so the same stations, same geometry, treat it identically. (This mirrors the CrimpCenter swivel-arm philosophy: stations fixed, wire end moves.)

**E — S1. Slitter.** For bonded ribbon, a heated or plain razor blade in a slot die notches the web between conductors for the last ~25 mm; then a spreader comb fans the 2–3 now-free tails into a fixed 2.54 mm-pitch (or wider, see 2.4) guide. Split length adjustable exactly like the commercial 0–60 mm spec.

**F — S2. Stripper.** Classic V-blade pair on a small stepper closes to a gauge-specific depth, then the *shuttle* pulls back ~3–5 mm to slip the insulation. One conductor at a time (shuttle steps across the pitch), or all-at-once with a multi-V blade comb if the pitch is fixed. Strip length 2–3 mm for 2.54 mm pins.

**G — S3. Crimp.** **Buy, don't build:** a genuine mini-applicator for the chosen terminal (SXH / KK 2759 / Dupont-clone bandolier reels are cheap) driven by a servo ballscrew press (~2 t) or a compact pneumatic press. Terminal feed, alignment, and crimp form all come free with the applicator. The shuttle presents one stripped conductor per stroke, stepping across the row. Add a load cell for crude crimp-force monitoring — that's the standard QA signal.

**H — S4. Insertion.** The novel station. Housing feed first: unlike the terminals (bandolier reel), **5264 housings ship loose in a bag** — there is no engineered feed form. Commercial block loaders solve this with a vibratory bowl + linear track that orients and singulates them; that's tuning-intensive overkill at benchtop scale. v1 answer (confirmed by Kyle 2026-07-24): a **hand-loaded 3D-printed stick magazine** — a vertical channel whose cross-section matches the housing profile so it only fits one way (the friction-lock ramp keys orientation), gravity- or spring-fed, with a simple escapement (sliding shuttle plate) that drops exactly one housing into the nest per cycle. Loading ~25 housings takes under a minute of operator time and covers ~12 cables; a low-stack sensor gives warning. The magazine is a swappable printed cartridge — one per housing type, which is exactly the right seam for the "other connectors later" roadmap. (Upgrade path if hand-loading ever becomes the bottleneck: mini vibratory bowl, the commercial answer.) From there the nest sits on a small indexing axis that positions cavity *i* on the machine centerline. Sequence per pin: shuttle aligns pin to cavity mouth (a tapered guide funnel forgives ~±0.3 mm), pushes axially ~6 mm until the housing lance clicks, then pulls back 1–2 mm against a stop — the **pull-back retention test**, the single most valuable QA step in commercial block loading. Insert order: outermost cavity first so already-inserted wires don't shadow the funnel.

**I — Guillotine.** Full-width shear that separates the finished cable *after* the trailing end has been processed (order of operations below). Finished cable drops to a tray.

### 2.3 Process order (one cable)

1. Feed ribbon leading end to shuttle; shuttle grips.
2. Leading end: slit → strip → crimp ×N → insert ×N (this end is now "connectorized," hanging from the shuttle).
3. Shuttle releases; feed rollers pay out length L (encoder-verified) past the guillotine.
4. Shuttle re-grips at the guillotine side; guillotine cuts. The cut creates two ends: the **trailing end of the finished cable** (in the shuttle, flipped 180° by the wrist) and the **new leading end of the spool** (parked).
5. Trailing end: slit → strip → crimp ×N → insert ×N → drop finished cable.
6. Next cable starts at step 1 with the already-cut new leading end — zero waste between cables.

This is exactly the commercial dual-end sequencing, and it means cycle time ≈ 2 × (end-treatment time) + payout. With ~4 s per pin across strip/crimp/insert and 3 pins/end, a ~60–90 s cable is realistic for v0 (commercial: ~7–9 s).

### 2.4 The three hard problems, ranked

1. **Crimp quality** — solved by purchasing the mini-applicator; do not attempt DIY crimp tooling, this is where every hobby attempt dies. Budget item, ~$300–800 used/clone per terminal type.
2. **Insertion reliability** — pin tip position after crimping varies; the funnel guide + compliant gripper (slight lateral float) + pull-back test is the mitigation stack. Expect this to be 60 % of the debugging hours.
3. **Ribbon slitting without nicking conductors** — blade depth control to ~0.1 mm; a shaped slot die per ribbon geometry makes it repeatable. Pre-scored/"zippable" ribbon (or discrete-wire bonded pairs) makes this station nearly trivial — worth choosing the wire stock around.

### 2.5 Control + rough BOM

Control: one motion controller (grbl-HAL / Klipper on a Pi, or a Duet) — 6–7 stepper axes (feed, shuttle X/Z, wrist, housing index, stripper blades, press if servo), ~10 sensors (encoder, blade home switches, terminal-out, housing-out, spool-out, load cell), pneumatics optional. UI: enter L and quantity — same contract as the hobby wire-cutter builds.

| Block | Est. cost |
|---|---|
| Frame, rails, 3D-printed stations | $250 |
| Steppers/drivers/controller/PSU | $300 |
| Mini-applicator + terminal reels | $300–800 |
| Press (servo ballscrew or air) | $200–400 |
| Blades, slot die, guillotine | $100 |
| Housing magazine + nest | $50 (printed) |
| Sensors, encoder, load cell | $100 |
| **Total** | **~$1.3–2k** |

### 2.6 Suggested build path (de-risk order)

1. **Bench-validate S3**: press + applicator crimping hand-fed stripped ribbon tails — proves the money station.
2. **S4 prototype**: hand-crimped pigtails inserted by a manual-jig version of the funnel/pusher/pull-back — proves the novel station before any motion control exists.
3. Feed/measure/cut module (known-solved hobby territory).
4. Slit + strip stations.
5. Shuttle + wrist, integrate, then the state machine for dual-end sequencing.

Steps 1–2 together are a weekend-scale experiment and would retire most of the project risk before committing to the full frame.

### 2.2b Rotary architecture (Kyle 2026-07-24 — adopted over the linear sketch)

**"Shuttle and stations," restated plainly.** A *station* is a fixed piece of tooling that does one operation and never moves from its spot (blade, strip jaws, crimp press, housing nest). The *shuttle* is the one thing that moves the workpiece: it holds the ribbon end and carries it to each station in turn. The alternative — moving four tool heads to a stationary wire — needs four times the motion hardware, which is why every commercial machine moves the wire instead (Schleuniger's swivel arm, Komax's transfer arms).

**Kyle's version: put the stations on a bolt circle, not in a line.** The shuttle becomes a pivot arm that indexes rotationally between station sectors and *extends radially* into whichever station it's facing. This is the classic **dial / rotary indexing machine**, and it beats the linear sketch on three counts:

- **Two axes instead of two, but better ones.** Rotary index + radial extend. A rotary index can drop into hard detents at each station, so repeatability comes from mechanical stops rather than from a long linear rail staying square.
- **Stations become bolt-on modules.** Each occupies a sector; adding, removing, or swapping one is a bracket change. That is *exactly* the seam the "other connectors later" roadmap needs — a new connector family becomes a new insert-station sector plus a new magazine cartridge.
- **Compact.** A ~300 mm circle holds five stations in less bench space than a 900 mm rail.

**Station sectors (working arc, not a full turn):** feed/cut → slit → strip → crimp → insert, plus a **park** position where the finished end A waits during payout. Keep the arm inside a ~200–270° arc so the trailing ribbon sweeps but never wraps the pivot. (Full 360° is only safe if the ribbon feeds through the rotation center — and twisting 3-conductor ribbon is not worth it.) The **feed/cut sector is a station like any other**: feed rollers pay out length L there, the guillotine lives there, and it's where the arm picks up each new end.

### 2.2c The per-pin problem — and the trick that dissolves it

Kyle's instinct is correct: **crimp and insert are inherently one-conductor-at-a-time operations.** The applicator crimps one terminal per stroke; each pin goes into its own cavity. This is not a weakness of our design — the industrial block loaders do exactly this, one lead at a time (the foundational patent is literally titled *"Single lead insertion connector block loading apparatus"*). So we're in good company. The question is only *what moves* to make it happen.

**The gripper is a 3-slot comb, not a clamp.** Each conductor sits in its own channel. That one change turns "handle a floppy trio" into "handle three individually addressable conductors," and it is what makes per-pin work tractable.

**At the crimp station — move the ribbon, index the conductor.** Add a small lateral **cross-slide** to the arm (one cheap axis). Present conductor 1 to the anvil, crimp, shift one pitch, present conductor 2, crimp, shift, conductor 3. The applicator never moves. This directly answers Q2's collision worry: the fan pitch at the crimp station is set by the comb, **not** by the 2.5 mm connector pitch — spread the conductors as wide as the split length allows (10–15 mm is free), and finished pins simply aren't near the applicator throat when the next conductor arrives.

**At the insert station — move the housing, not the wires.** This is the key move, and it resolves the awkward part. Naive version: insert conductor 1, then shift the comb to bring conductor 2 over — but conductor 1 is now anchored in the housing, so shifting strains or backs out the pin you just placed. Invert it:

> **The insertion axis is fixed. The housing nest indexes one pitch per pin. The comb releases one conductor at a time.**

Insert conductor 1 into cavity 1 on the fixed insertion line; release it from the comb; index the *nest* one pitch so cavity 2 arrives on that same line; feed conductor 2; repeat. Already-inserted conductors travel **with their housing**, so they're never strained — the geometry stays identical for every pin, and the funnel/pusher tooling only ever has to work at one spot.

**What pushes.** Never the pin itself — a pin must not be loaded through its crimp. A small pusher finger closes on the **wire ~5 mm behind the pin** and drives it forward until the housing lance clicks, then pulls back against a stop for the retention test.

**Resulting motion budget (rotary architecture):**

| Motion | Type | Notes |
|---|---|---|
| Arm rotary index | stepper/servo | detents at each station sector |
| Arm radial extend | stepper/servo | shared by every station — the big win |
| Comb cross-slide (conductor select) | stepper | serves both crimp indexing and insert feeding |
| Ribbon feed / payout | stepper + encoder wheel | owns cable length accuracy |
| Housing nest index | stepper | one pitch per pin |
| Comb jaws, slitter, strip jaws, guillotine, crimp press, insert pusher | **pneumatic** | on/off actuators — cheap, strong, and Kyle's already going air for the press |

Five motion axes, six air cylinders. That is a very buildable machine, and the pneumatic column is why the compressor turns out to be load-bearing rather than incidental.

**Status:** this supersedes the linear layout in §2.2. Q1 is answered (rotary arm + comb + cross-slide); Q2 is answered in principle by decoupling fan pitch from connector pitch, and still wants the printed mockup before anything is machined.

### 2.6b Maturity check — what this document is and isn't

**Settled (high confidence):** the process decomposition and its order; that it's buildable at benchtop scale; the target part and everything it constrains; buy-the-crimp-tooling; hand-loaded printed housing cartridge; dual-end via 180° flip. These are validated against shipping commercial machines and are unlikely to change.

**Thumbnail-grade (mechanism kinematics):** everything about *how one gripper presents a bonded trio of conductors to four stations* is drawn at the level of "and then the shuttle does it." That's where the real engineering hours are. The open questions below are not nitpicks — Q1 and Q2 could force an architecture change.

### 2.6c Open engineering questions

**Q1 — ANSWERED (§2.2b/2.2c): rotary arm + 3-slot comb + cross-slide.** Original text kept for the record. ~~Can one shuttle really serve all four stations?~~ The core bet. Each conductor must reach the strip blades, the crimp anvil, and a housing cavity: three different heights, three different approach directions, plus the two idle conductors need restraining while the third is worked. Commercial machines handle *single discrete wires* with a swivel arm; nobody found handles a bonded trio this way. Fallback architectures if it fails: (a) fully separate the three conductors early and treat the cell as three parallel single-wire lanes; (b) stations move to the wire instead; (c) an intermediate transfer gripper per station.

**Q2 — LARGELY ANSWERED (§2.2c): decouple fan pitch from connector pitch — the comb spreads conductors 10–15 mm at the crimp station so finished pins are nowhere near the applicator throat. Still wants the printed mockup to confirm clearances.** Original text: After conductor 1 is crimped, a ~10 mm pin protrudes on a wire whose neighbor is 2.5 mm away and still bonded to it. Presenting conductor 2 to the applicator puts pin 1 in the same space as the applicator body/terminal track. Candidate answers: crimp order + swing the finished pin clear; splay the fan much wider (longer split); or crimp from a spread fixture that holds all three at a pitch far larger than 2.5 mm and only converges them at insertion. **This is the single most likely thing to break the current layout** and deserves a cardboard/printed mockup before anything is machined.

**Q3 — Splay geometry vs. finished-cable quality.** Split length must be long enough for the fan angle the crimp and insert stations need, short enough that the finished cable doesn't have an ugly floppy transition. There's a real optimum; find it by hand-building a few cables first.

**Q4 — Where does the finished end live during payout and flip?** Once end A is connectorized it dangles for the entire payout of length L, then gets flipped. The rotary layout gives this a natural home: a **park sector** with a clamp that holds the finished connector while the feed station pays out. Remaining detail is the flip path — the arm must present end B to the stations in the same orientation end A had, without dragging the finished connector. Partially answered by §2.2b.

**Q5 — Registration of a floppy ribbon.** The insertion funnel forgives ~±0.3 mm; a 1 m tail of unsupported ribbon does not naturally deliver that. Needs a clamp-close-to-the-work discipline at every station, and probably a fixed reference edge the ribbon is pressed against.

**Q6 — Insertion force reaction path.** Push on the wire behind the pin (standard practice — the pin must not be loaded through its crimp), with the housing backed up hard against a stop. Detail is unspecified and affects gripper design.

**Q7 — Per-pin QA depth for v1.** Crimp-force curve per stroke (needs a load cell + a learned reference), or post-hoc sample pull tests? v1 likely samples; decide before writing the state machine, since in-line QA changes the reject path.

### 2.7 What the pinned part (Mini-SPOX 5264) locks in

- **All fixed-pitch tooling is 2.50 mm, not 2.54:** spreader comb, multi-V strip comb, insertion nest cavity spacing. Off-by-0.04 mm per position is exactly the trap the TendWright doc warns about for hand parts; same trap applies to machine fixtures.
- **Terminal 0008701039 ships in chain/reel form** — which is precisely what a mini-applicator eats. Molex makes applicators for the 5263 terminal chain; a used/clone unit for this family is the S3 buy. 2 T crimp force class, strip length 2.5–3 mm (matches the doc's hand workflow).
- **22 AWG 3-conductor servo ribbon is peelable bonded web** — the S1 slitter drops from "precision slot die" to "notch and zip," with a nick-free margin far wider than solid IDC ribbon. Hardest-problem #3 mostly evaporates.
- **Both ends take the identical housing, straight-through pinout (1=GND, 2=Vcc, 3=Signal).** After the wrist's 180° flip the conductor order presents mirrored, so the S4 housing indexer simply runs its cavity sequence in reverse for end B (3→1 instead of 1→3). Zero extra hardware — just sequencing. Color-position verification (black/red/white in cavities 1/2/3) is a natural cheap camera check before the housing leaves the nest.
- **Retention check matters more than usual:** 5264 is a friction-lock housing driving 12 V servo power on a daisy-chain bus — a backed-out terminal browns out every servo downstream. The pull-back test in S4 is non-negotiable.
- **Immediate customer:** the TendWright arm needs ~6–10 exact-length joint-to-joint runs (~12–20 crimps) — a perfect first production batch and acceptance test for the cell.

---

## Sources

- [Kingsing KS-T532 ribbon strip/split/crimp machine](https://www.kingsing.com/product/1678.html)
- [Kingsing crimp + housing-insertion machine family](https://www.kingsing.com/product/list-Housing_Sleeve.html) and [KS example](https://www.kingsing.com/product/1177.html)
- [JCWelec ribbon slit-cut-strip machines](https://www.jcwelec.com/product/slit-cut-strip.html) and [IDC press machine](https://www.jcw-wirestripping.com/jcw-324-flat-ribbon-cable-idc-connector-crimping-machine.html)
- [WirePro SF-SE4 flat ribbon cut/slit/strip](https://www.wireproauto.com/product/sf-se4-flat-ribbion-cable-automatic-cutting-slitting-stripping-machine/)
- [Schleuniger CrimpCenter family](https://www.schleuniger.com/en-us/products/cut-strip-terminate/crimpcenter/)
- [Komax automated wire processing](https://www.komaxgroup.com/en-us) / [Omega 745 block loader](https://www.komaxgroup.com/en-in/products/harness-manufacturing/omega-745) / [Omega 750 S announcement](https://wiringharnessnews.com/komax-introduces-the-omega-750-s-revolutionizing-fully-automated-wire-harness-assembly/)
- [Assembly Magazine: fully automatic stripping/crimping](https://www.assemblymag.com/articles/98855-fully-automatic-stripping-crimping) and [cut/strip/crimp machine roundup](https://www.assemblymag.com/articles/96081-whats-new-with-cut-strip-and-crimp-machines)
- [ETCO bench press + applicator](https://www.etco.com/wire-crimping-press-complete-with-terminal-applicator/) · [What is a crimping applicator](https://www.terminal-crimping.com/news/What-Is-a-Crimping-Applicator-28.html) · [TE applicator catalog](https://www.te.com/content/dam/te-com/documents/application-tooling/global/1-1773864-9_TE-Applicators_Catalog.pdf) · [Mecal applicator diagnostics](https://www.mecalbystarn.com/2019/04/23/primer-in-diagnosing-crimp-applicator-issues/)
- [US4308659 — single-lead connector block loading apparatus](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4308659) · [US4040167 — separating and fitting ribbon-cable conductors into connector housings](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4040167)
- [Hackaday: automated wire prep machine](https://hackaday.com/2020/12/09/this-automated-wire-prep-machine-cuts-and-strips-the-wire/) · [sandy9159 DIY wire cutter/stripper (GitHub)](https://github.com/sandy9159/DIY-Wire-cutting-and-stripper-Machine-Arduino-project) · [Hackaday: Inside the Secret World of Crimping](https://hackaday.com/2019/02/28/inside-the-secret-world-of-crimping/)
