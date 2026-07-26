# Cable Cell v1 — BOM (live-verified, all vendors)

**Verified:** Amazon 2026-07-24, eBay + press re-check 2026-07-25. Live passes in Kyle's browser session.
**Companion to:** `shopping-list-v1.md` (the reasoning) and `cell-design-v1.md` (the design of record).
**Status:** every Amazon and eBay line below was opened on its real product page and checked against the spec. Distributor lines (§1 rows 12–13) carry over from the earlier research and were *not* re-verified in this pass — flagged as such.

**Nothing here is ordered.** This is a buy list; clicking is Kyle's.

---

## 1. The BOM

| # | Item | Vendor | Pick | Unit | Ship | Qty | Spec check |
|---|---|---|---|---|---|---|---|
| 1 | Known-good reference cables | Amazon | [waveshare 5264-3PIN, 6 pcs](https://www.amazon.com/dp/B0GVDFXF7Q) `B0GVDFXF7Q` | $9.99 | $3.56 | 1 | ✅ True 5264 3-pin, the exact target connector. 3× 300 mm + 3× 900 mm. **The factory-crimp yardstick** — measure its crimp height and pull force before we cut a single terminal. |
| 2 | Ribbon stock | Amazon | [YXQ 22 AWG servo cable, 50 ft](https://www.amazon.com/dp/B0CQ1V38RF) `B0CQ1V38RF` | $9.30 | — | **2** | ✅ 22 AWG, 60 cores × 0.08 mm, black/red/white JR colors, 1.4 mm OD, flat 3-conductor. Matches the TendWright wiring doc. One spool dev scrap, one for real cables. |
| 3 | Crimp-height mic | Amazon | [iGaging 35-040-201, double point](https://www.amazon.com/dp/B00NDYTE4S) `B00NDYTE4S` | $58.50 | — | 1 | ✅ **Point anvils** — the whole reason for this line. 0–1", 0.00005". Flat calipers read the B-crimp wrong; only a point mic gets true crimp height (±0.05 mm class). Cheaper than the $104–184 "crimp height" branded units, same measurement. |
| 4 | Pull tester | Amazon | [KINGON hanging scale, 110 lb/50 kg](https://www.amazon.com/dp/B07B6SHFHV) `B07B6SHFHV` | $25.99 | — | 1 | ✅ 0.1 lb graduation, **peak/max hold** — essential, a pull test is a transient. Target ≈ 8 kgf pull-out on 22 AWG open-barrel. |
| 5 | Inspection scope | Amazon | [Jiusion 4K 50–1000× USB + metal stand](https://www.amazon.com/dp/B0CPVH11Z6) `B0CPVH11Z6` | $35.14 | — | 1 | ✅ Reads crimp wings and bell-mouth. Stand included — a handheld scope can't give repeatable crimp photos. Later doubles as the Q7 camera-check dev unit. |
| 6 | Terminal extractor | Amazon | [82-pc depinning kit](https://www.amazon.com/dp/B0922GF9W8) `B0922GF9W8` | $12.99 | — | 1 | ⚠️ Generic multi-profile, 4.3★. Covers 2.5 mm-class housings, not specifically tooled for 5264. Fine for insertion-jig scrap recovery. Precision fallback: [JRready ST5228](https://www.amazon.com/dp/B0B6FMZMH4) `B0B6FMZMH4` $29.99. |
| 7 | Spring assortment | Amazon | [Dianrui 300 pcs, 23 sizes, 304 SS](https://www.amazon.com/dp/B0BVTDP29W) `B0BVTDP29W` | $6.99 | — | 1 | ✅ Magazine follower + escapement return. 23 sizes gives room to tune follower force by trial. |
| 8 | Air prep | Amazon | [NANPU 1/4" NPT filter + regulator](https://www.amazon.com/dp/B07TPCGWPY) `B07TPCGWPY` | $15.99 | — | 1 | ⏸️ **DEFERRED to cell build — see §3.** ✅ Validated and correct when we need it: 5-micron brass, poly bowl, semi-auto drain, 0–150 psi, 20 SCFM, coupler kit + PTFE tape. **Filter+regulator, deliberately NOT a full FRL** — a lubricator injects oil into the air, the last thing we want near crimp tooling. |
| 9 | Compressor | Amazon | [California Air Tools 1P1060S, 1 gal](https://www.amazon.com/dp/B01LYHYHEA) `B01LYHYHEA` | $149.00 | — | 1 | ⏸️ **DEFERRED to cell build — see §3.** ✅ Validated: 56 dBA, oil-free, 1.20 CFM @ 90 psi, .6 HP, 29 lb. Nothing in de-risk needs air any more. |
| 10 | **Donor OTP applicator** | **eBay** | [OTP Horizontal Mold](https://www.ebay.com/itm/357379481619) `357379481619` — DYStore1, 100% | **$247.94** *or Best Offer* | $69.99 | 1 | ② **side feed confirmed in the listing** ("Horizontal Mold"). Single config, no variant guessing. ⚠️ ① XH2.54 series, ③ OTP shank, ④ cam-fed **all unconfirmed — needs a seller message first, see §5.** |
| 11 | Bench press | **eBay** | [1.5T Automatic Wire Crimping Machine](https://www.ebay.com/itm/157443920594) `157443920594` | $238.88 | free | 1 | ⚠️ **220 V, and deferred** — not a buy-now line. 30 mm stroke, 1.5 T, AWG18–30, takes standard mini-applicators. See §6 for the voltage/frequency picture and the machine-class trap. |
| 12 | Housings | Mouser / Newark | Molex **50-37-5033** — [Mouser](https://www.mouser.com/ProductDetail/Molex/50-37-5033?qs=AplfTeSvkkCfnVdKv8UuEg%3D%3D) · [Newark](https://www.newark.com/molex/50-37-5033/connector-rcpt-3pos-1row-2-5mm/dp/57H1785) | ~$0.15–0.25 | — | **100** | ⓘ *Not re-verified this pass.* Ships loose in a bag. 100 covers magazine-cartridge dev + insertion-jig scrap + real cables. |
| 13 | Terminal chain | DigiKey | Molex **0008701039** — [DigiKey](https://www.digikey.com/en/products/detail/molex/0008701039/765268) | ~$0.022 | — | **500–1000** (Cut Tape) | ⓘ *Not re-verified this pass.* ✅ Packaging resolved earlier: only Cut Tape (min 100) and Tape & Reel (min 12,000) exist — no loose-piece — so every form is carrier-strip and applicator-feedable. Verify continuous carrier, not embossed pocket tape, on arrival. |

### Totals

| Bucket | Cost |
|---|---|
| Amazon lines 1–7 (tools + consumables) | **~$168** |
| eBay applicator (line 10, landed) | **~$318** |
| Distributor consumables (lines 12–13) | ~$37 |
| **▶ BUY NOW (1–7, 10, 12–13)** | **~$523** |
| Air, deferred to cell build (lines 8–9, §3) | $165 |
| Press, deferred (line 11, §6) | $239 |
| **Everything, eventually** | **~$927** |

**What the buy-now bucket actually unblocks:** de-risk **B** (insertion jig — printed parts + hand-crimped pigtails into real housings), measuring the factory reference cables to establish the crimp-height and pull-force targets, and receiving + measuring the donor applicator to pick the punch/anvil route. De-risk **A** (machine crimping) additionally needs the press, so it waits.

---

## 2. Do NOT buy here

| Item | Why | Instead |
|---|---|---|
| ~~Raspberry Pi 5 8 GB~~ | ❌ **CUT — not needed.** Kyle has a stack of older NUCs plus cell1-class boxes. The design already made the supervisor architecture-independent, so this is a free swap. See §4. (Amazon was a trap anyway: cheapest kit $214.99 vs ~$80 board + $13 PSU direct.) | Nothing to buy. Supervisor $100–140 → **$0**. |
| Donor applicator, on Amazon | ❌ **Confirmed absent.** Two searches returned only hand ratcheting crimpers (SN-28B/SN-2549 class) — no machine applicators at any price. | eBay, line 10 |
| Housings / terminal chain, on Amazon | Packaging form matters and Amazon listings are repackaged and unverifiable | Mouser / DigiKey, lines 12–13 |
| **AM-10 pneumatic crimper** | 🔴 **Wrong machine class** — looks perfect at $159, isn't. See §6. | — |

---

## 3. Air is deferred entirely — nothing in de-risk needs it now

**Kyle 2026-07-25 dropped his pneumatic press find** ("if it's not what we need skip it"). That closes the question in §6 and has a clean knock-on effect: the press we'd actually buy (line 11) is an **electric** motor-and-cam 1.5T unit, so **de-risk A needs no compressed air at all.**

Air only comes back at cell-build time, for the ~10 pneumatic station actuators in the design (insertion pusher, guillotine, stripper clamp, wrist flip). Both air lines — the compressor (line 9) and the filter/regulator (line 8) — therefore move out of the buy-now bucket. That's **$165 deferred**, and it removes the only line that was in an unresolved hold.

Both picks stay validated and correct for when we get there; nothing needs re-researching, just re-pricing at purchase time.

### Still worth knowing: the 12 V inflator question (now moot for de-risk)

Kyle asked (2026-07-24) whether the car tire inflators he already owns are strong enough, and whether an adaptor could be made. Recorded because it will come back at cell-build time.

**The adaptor is trivial; the machine is the problem.** Plumbing an inflator to 1/4" NPT is a ~$10 fitting. Three real blockers:

1. **No tank.** The killer. Inflators are direct-drive with no receiver. A press cylinder draws a large slug of air in a fraction of a second, far above any continuous flow rate. With no tank, line pressure sags mid-stroke, so **crimp force varies shot to shot** — and crimp height is the one number the whole de-risk exists to control. We'd be measuring our air supply, not our tooling.
2. **Duty cycle.** Built to fill one tire then cool — typically 10–15 min before thermal cutoff. The cell has ~10 actuators cycling continuously.
3. **No pressure switch.** No way to hold a setpoint automatically.

**Where it genuinely works:** inflator **+ a separate 5-gal portable air tank (~$40) + the filter/regulator (line 8).** The tank does the buffering. For de-risk A — occasional manual strokes, not continuous cycling — that's legitimate, and it starts bench work for ~$40 instead of $149.

**Conclusion:** the compressor is a **permanent cell component** — the finished cell needs a tank, a pressure switch and a real duty cycle regardless. The inflator route was only ever a way to start de-risk A cheaply, and de-risk A no longer needs air. So this whole question is parked until cell build.

**When it comes back, to decide it:** check the inflator's label for max PSI (want ≥100 with headroom) and rated duty cycle.

---

## 4. Supervisor = spare NUC on Ubuntu (Pi cut)

**Decision, Kyle 2026-07-24.** The supervisor runs on existing hardware — Kyle has both cell1-class boxes and **a stack of older NUCs**. The NUC is the better pick and effectively ideal here.

**Why this is free rather than a compromise:** the split-brain design already puts *all* real-time work on a dedicated motion MCU (the Klipper/grblHAL pattern — supervisor thinks, MCU does microsecond step timing). The supervisor only runs the job queue, state machine, logging, web HMI, camera check and Hive reporting. None of that is Pi-specific, and x86 does it better: more CPU/RAM for vision, a real SSD instead of an SD card (SD corruption is a genuine long-run failure mode), native x86 dev, no ARM cross-compile friction.

**Why a NUC specifically:** it keeps every x86 advantage while erasing the only objection to a desktop — small enough to mount under the bench, quiet, ~10–20 W idle (nearer a Pi's 5 W than a tower's 30–60 W), plenty of USB, M.2/SATA SSD.

**The stack matters as much as the unit.** Spares turn a dead supervisor into a swap rather than a repair — image one, clone it, keep a cold spare. Real availability for a machine running unattended jobs. And if CableCell ever replicates, each cell gets a supervisor at zero hardware cost.

**Downstream changes:**

| Was | Now | Impact |
|---|---|---|
| Pi Camera 3 on CSI (~$35) | **USB camera** (~$25–35) | Small. Jiusion scope covers dev; a USB webcam covers the Q7 check. |
| Pi GPIO as a fallback for simple IO | **No GPIO on the supervisor** | None in practice — the design never used it. Does make the motion MCU strictly mandatory, but it already was. |
| ~$100–140 supervisor | **$0** | Bucket removed. |

**Remaining checks:** enough USB ports (camera + MCU + spare), an SSD you're happy to leave in service, 8 GB RAM ideal (4 GB workable).

**Unchanged:** the motion controller stays deferred (BTT/SKR-class or Duet) until Q1/Q2 settle the axis count.

---

## 5. Applicator — the one thing to settle before ordering line 10

**Price note:** the $80–160 estimate in `shopping-list-v1.md` was **stale**. Sorted by price+shipping ascending, the floor for a *complete* OTP applicator is ~$230–260 plus ~$70–80 shipping from China (import fees included in the listed price). Budget **~$320 landed**. The old cheap end was probably mold *inserts*, not complete units. Upper anchor: genuine precision units run [$1,546 side feed](https://www.ebay.com/itm/168452577707) to [$2,654 end feed](https://www.ebay.com/itm/168391214562) — so we're buying the $250 clone knowingly.

### Alternates to line 10

| Pick | Price | Ship | Note |
|---|---|---|---|
| [Multi-series OTP applicator](https://www.ebay.com/itm/314031005413) `314031005413` | $257.98 | $79.91 | ToolsMachinesGood (227), 99%. 2 available. Variant picker → choose **Horizontal Mold**. |
| [Same product, other seller](https://www.ebay.com/itm/146092754507) `146092754507` | $350.51 | $19.89 | ~$370 total. Fallback. |
| [Generic OTP applicator](https://www.ebay.com/itm/388629243167) `388629243167` | $231.50 | — | Cheapest complete unit. Feed type not stated. |

### 🔴 The trap: you cannot pick the terminal series at checkout

**None of these listings let you select the terminal series.** On the multi-series listing the dropdown that *looks* like it picks the series is labelled "Color" (a common CN-listing quirk) but actually selects **feed geometry** — Single / Horizontal / Straight Mold. The XH2.54 / 1.25 / SM / 3.96 / 5557 list in the title is the seller's tooling *range*, not a menu.

Checklist status:

- ② **side feed** — ✅ selectable, choose "Horizontal Mold"
- ① **XH2.54 variant** — ⚠️ confirm with seller
- ③ **OTP-standard body/shank** — ⚠️ confirm with seller
- ④ **mechanical cam-fed, not proprietary-press** — ⚠️ confirm with seller

**Message for Kyle to send** (no seller has been contacted):

> Which terminal series is this applicator tooled for — can you supply it tooled for JST XH 2.5 mm open-barrel terminals? Is the body/shank the OTP standard mount so it fits a generic bench press, and is the chain feed mechanical (cam driven off the ram) rather than requiring your own press?

Ask DYStore1 (line 10) first — side feed is already confirmed there, it's Best Offer so price can move, and it's the cheapest meeting a hard requirement outright.

**Not fatal either way:** this unit is bought as a **donor chassis and mechanism reference** — frame, ram geometry, feed cam, drag brake. If the punch/anvil suits 5263 geometry that's route 1 (transplant, $0). If not we measure it and move to route 2 (buy inserts) or route 3 (machine our own), which was always the plan.

---

## 6. Press — deferred, plus a trap worth remembering

**Not a buy-now line.** Kyle 2026-07-25: not touching 240 V yet.

**What happened:** `shopping-list-v1.md` estimated $250–500 next to a link that today rings up at **$1,690.11** ([TZ 1.5T, `B07G5PD2T6`](https://www.amazon.com/dp/B07G5PD2T6), 4–5 wk lead). That listing is the **110 V / 60 Hz US variant** and the US-spec premium is most of the price. The estimate was simply stale — corrected.

**Real market:** ~$239 free-shipped for a 1.5T press (line 11), ~$360 for the ultra-quiet class, [$993 for a press bundled with an OTP transverse (side-feed) mold](https://www.ebay.com/itm/197781797949) — though ~$240 press + ~$320 applicator separately is cheaper at ~$560.

**On voltage, for when we get there:** the cheap units are 220 V. US mains is *lower*, so it would need a step-**up** transformer, not step-down — and a transformer changes voltage only, not frequency, so matching "exact spec" (220 V / 50 Hz) would need a frequency converter, a different and pricier device. 50 Hz machines on 60 Hz mains run ~20% fast, which is generally tolerable on a cam press but shifts cycle timing and dwell at bottom of stroke. **110 V versions do exist**, so we may need none of this. Later problem.

### 🔴 Trap: the AM-10 pneumatic is the wrong class of machine

[AM-10 Pneumatic Crimping Machine, $159](https://www.amazon.com/dp/B0B8T9X2DK) `B0B8T9X2DK` looks like the perfect answer — pneumatic (dodges the voltage problem entirely and reuses the compressor), cheap, in stock, marketed "automatic".

**It is not an applicator press.** It ships "with 14 Die Sets" and its own copy says the mold changes per terminal — it's a pneumatic *plier* taking proprietary die sets. That fails twice:

1. It cannot mount a standard OTP mini-applicator, breaking the interface contract in `shopping-list-v1.md` §4.
2. More fundamentally, **it cannot feed a terminal chain.** Die-set pliers crimp loose terminals hand-fed one at a time. Chain feed is the premise the whole cell rests on — it's why the Cut Tape packaging question mattered.

$159 and several weeks to discover it can't do the one thing the cell needs.

### ✅ Closed: Kyle's pneumatic find is dropped

**Kyle 2026-07-25: "the pneumatic I found — if it's not what we need, skip it."** Done. The press will be a conventional electric applicator press (line 11) bought when we're ready to deal with the voltage question.

Two consequences, both good:

- **The pneumatic-press route is off the table**, so the interface contract has one less unknown — we're buying a machine class that takes standard mini-applicators by definition.
- **Air leaves the critical path.** With an electric press, de-risk A needs no compressed air, so the compressor and filter/regulator defer to cell build (§3) — $165 out of the buy-now bucket.

---

## 7. Still unsourced (not blocking)

The DIY applicator subproject's own BOM from `shopping-list-v1.md` §4 — tool steel, ground plate, MGN9 offcuts, cam follower + die springs, bandolier hardware. McMaster/Misumi-class buys, to be sourced once the donor applicator is measured, not before.

## 8. Amazon List (superseded)

An Amazon List named "TendWright cable cell" exists and holds 5 of the Amazon lines ([link](https://www.amazon.com/hz/wishlist/ls/3F8UKV550KEGE)). Per Kyle 2026-07-24 the List UI is **not** the deliverable — this file is. The list is left in place but unmaintained; **this file is authoritative.**
