# Decision log

Running log of decisions that shape the machine. Newest last. Every entry names
who decided and when, so a stale doc can always be traced back to the call that
made it stale.

---

**2026-07-24 — CableCell is its own project.** Kyle: "building this cable making
cell is a new project." Registered as Hive app 9. TendWright is CableCell's first
*customer*, not its owner.

**2026-07-24 — Rotary dial architecture.** Six fixed stations on a bolt circle,
one arm carries the work. Chosen over a linear rail: mechanical detents beat a
long rail staying square, each station is a bolt-on sector module (which is how
"other connectors later" arrives), and a ~300 mm circle fits five working
stations in less bench space than a 900 mm rail.

**2026-07-24 — Housing feed is a hand-loaded printed stick cartridge.** Swappable
per connector family. This is the roadmap seam for other connectors.

**2026-07-24 — Build the ribbon-fed applicator, don't buy it.** No off-the-shelf
clone applicator exists for 5264/SPOX. Donor is an XH2.5 OTP clone bought as a
chassis and mechanism reference. Punch/anvil route order: transplant → buy
inserts → machine. Sedeke custom-tooling quote is the parallel path.

**2026-07-24 — Supervisor is a spare NUC on Ubuntu; Pi 5 cut.** The split-brain
design already puts all real-time work on a dedicated motion MCU, so the
supervisor is architecture-independent. Kyle has a stack of NUCs. Cost
$100–140 → $0. Knock-on: USB camera instead of Pi Camera 3 on CSI.

**2026-07-25 — Pneumatic press route dropped.** Kyle: "the pneumatic I found — if
it's not what we need, skip it." The press will be a conventional electric
applicator press. Knock-on: de-risk A needs no compressed air, so the compressor
and filter/regulator defer to cell build — $165 out of the buy-now bucket, and
air leaves the critical path entirely.

**2026-07-25 — Terminal packaging resolved.** Molex 0008701039 ships only as Cut
Tape (min 100) or Tape & Reel (min 12,000). No loose-piece exists, so every form
is carrier-strip and applicator-feedable. This was the risk that could have
killed the applicator subproject.

**2026-07-25 — The BOM markdown is the sourcing deliverable, not an Amazon List.**
The Amazon List UI is slow, flaky and token-expensive. Search there; record here.

**2026-07-26 — CableCell gets its own repo** at `C:\Projects\CableCell`,
following the TendWright pattern. Design docs move out of
`overwatch/reports/cable-robot-cell/`. No git remote configured yet — public vs.
private undecided.

**2026-07-26 — Modeling split: MuJoCo for layout truth, FreeCAD for manufacturing
truth.** Blender is a mesh modeler with no constraints and no true circles; CAD
is B-rep and tolerance appears only at tessellation, which we control. MuJoCo
tessellates everything anyway, so precision never lived in the sim. FreeCAD
chosen over Onshape Free (all free-tier documents are public) and Fusion Personal
(license churn): it reads STEP natively, exports STL at controlled deviation,
produces dimensioned drawings via TechDraw, and is scriptable in Python. FreeCAD
1.0 fixed the topological naming problem that made it unusable historically.
Blender retained for renders, mockups and blockouts.

**2026-07-26 — Two shut-height standards found; applicator leads, press follows.**
135.78 mm (Molex/TE/Mecal) vs 119.7 mm (Chinese OTP clone) — a 16 mm mismatch
that makes the two incompatible. Adds a fifth question to the line 10 seller
message, and makes the applicator purchase the gate on the press purchase. See
`datums.md`.

**2026-07-26 — FreeCAD approved and installed** (1.1.2, winget). Tool install
only; nothing enters `pyproject.toml`.

**2026-07-26 — The press is the layout datum, not the dial.** Kyle. Place the
press first; its anvil fixes θ₄ and one bolt-circle point, its crimp height fixes
Z₄. The pivot then goes at R₀ from there and the other six stops follow. A
30–50 kg machine with a fixed vertical ram does not get to be a bolt-on sector
module.

**2026-07-26 — Do not attempt to reproduce the press.** Kyle: preliminary
research indicates the crimp station is not easy to reproduce with our own
system. Buy it. Revisit building one as a possible side project *later*, once we
have a unit in hand to analyse. Note this is narrower than the applicator
subproject, which remains a build.

**2026-07-26 — Base-mounted Z axis added.** Kyle: "the main arm that rotates can
also have a vertical span... a base with a vertical movement extension setup,
with the rotator anchored on the top of that." Stack is base → Z stage → rotary →
arm, so Z carries the whole rotating assembly. Commodity ballscrew linear stage
class (SFU1605 + dual rails + NEMA 17/23, $62–200).

Consequences:
- **Work-line Z is no longer a single datum.** It becomes a per-station table
  Z₁…Z₇ in config, calibrated at commissioning. This removes the dependency chain
  that previously blocked the entire layout on the applicator's wire height.
- **Rotation clearance becomes vertical** (lift, rotate, descend) instead of
  radial, decoupling station tooling design from the arm's sweep path.
- Axis count 5 → 6 steppers (θ, Z, R, S, F, H). BTT Octopus has 8 slots — no
  re-sizing.
- New risks: Z-carriage compliance at the bottom of a long lever adds to the comb
  deflection budget; ballscrews back-drive, so an E-stop could drop the arm
  unless braked or a self-locking leadscrew is used; Z changes the ribbon's free
  length, so the payout reference position must include a Z.
- Homing gains an ordering rule: Z homes up before θ may rotate.

**2026-07-26 — Repo is public, dual-licensed MIT + CC BY 4.0.** MIT covers
software; CC BY 4.0 covers docs, CAD, hardware designs and BOMs. Reason for the
split: MIT is a software license and maps badly onto a STEP file or a design doc.
Reason for CC BY specifically: it requires *visible attribution*, which is what
Kyle meant by "free to use with a citation" — MIT only requires notice
preservation, which is weaker and does not oblige anyone to credit him anywhere a
human will see.

Apache-2.0 was considered and **rejected**. It was raised for its explicit patent
grant, but that grant runs *from* the author *to* users — as sole author, Kyle
would be granting away rights to any patent he later holds on the applicator
mechanism. For a solo inventor with a plausible novel mechanism, no explicit grant
preserves more optionality. Neither MIT nor CC BY grants patent rights, and that is
deliberate.

**2026-07-26 — The Z stage cannot be a single coaxial ballscrew module.** Found by
the MuJoCo rough-in: a rotary axis cannot pass through the middle of a linear
rail, and the pivot needs the space the rail wants. Options are (a) cantilever the
rotor off one module's carriage, (b) a Z platform on 3–4 guide posts with one
off-axis ballscrew, (c) move Z onto the arm. Also found: the press body passes
through the deck disc (130→340 mm radius against a 280 mm deck) — fix by
scalloping the tooling plate where the press lands.

**2026-07-26 — The deflection budget is about variance, not strength.** Kyle:
these cables are small and light, worst case 3–4 ft, nowhere near a pound. Correct
and decisive — a 1.2 m length of the ribbon is ~15–20 g against a ~2 kg rotating
assembly, so payload is ~1% of moving mass and irrelevant to any load
calculation.

The real budget is *arriving inside the insertion funnel's capture window*
(pencilled ±0.3 mm, ≈1.5 mrad across the whole stack at 200 mm reach). That makes
it a precision problem, and precision cares about **variance**: with a constant
~20 g payload, a cantilever's sag is *repeatable*, and repeatable sag folds into
the station Z table as calibration rather than error. What defeats a cantilever is
backlash, stick-slip and thermal drift, not droop.

**Consequence: the Z architecture decision is deferred and explicitly gated on
measuring the funnel capture window in de-risk B (657.3).** Option (a) is now the
likely answer. Measuring it costs $20 of PLA; insuring against it costs $150 of
ballscrew. This promotes 657.3 from "an experiment" to a prerequisite for a design
decision.

**2026-07-26 — Cable length envelope confirmed at ~1000 mm.** Kyle: "3.3 ft is
perfectly fine for now, way larger than any early prototype I have planned." The
figure in `cell-design.md` stands; the payout trough is sized to it.
