# Cable Cell v1 — Shopping List + DIY Applicator Subproject

**Date:** 2026-07-24 · Companion to `exploration-and-thumbnail.md`
**Scope:** everything needed for the two de-risk experiments (crimp bench + insertion jig) **and** the build-our-own ribbon-fed pin applicator subtask (Kyle 2026-07-24). Full-cell motion hardware (steppers, rails, frame) deferred until de-risk passes — that part of the BOM is stable commodity stuff.

**Consumables target:** Molex Mini-SPOX 5264 system — housing **50-37-5033**, terminal chain **0008701039** (5263 series), 22 AWG 3-conductor servo ribbon. Prices researched 2026-07-24; volatile, verify at checkout.

---

## 1. Consumables (feed the experiments)

| Item | Part / search | Qty | Est. | Notes |
|---|---|---|---|---|
| Housings | Molex **50-37-5033** — [Newark](https://www.newark.com/molex/50-37-5033/connector-rcpt-3pos-1row-2-5mm/dp/57H1785) · [Mouser](https://www.mouser.com/ProductDetail/Molex/50-37-5033?qs=AplfTeSvkkCfnVdKv8UuEg%3D%3D) | **100** | ~$15–25 | Ships loose in a bag. 100 = magazine-cartridge dev + insertion-jig scrap + real cables. |
| Terminal chain | Molex **0008701039** — [DigiKey](https://www.digikey.com/en/products/detail/molex/0008701039/765268) | **500–1000** as Cut Tape | **~$11–22** | ✅ **RESOLVED 2026-07-25 — chain form confirmed available, and cheap.** DigiKey lists only Cut Tape (min 100 @ $0.0222 ea) and Tape & Reel (min 12,000 @ $0.0177 ea ≈ $212). **No loose-piece/bulk option exists**, which for a stamped open-barrel terminal means every form is on the carrier strip — i.e. applicator-feedable. Cut Tape at a few hundred pieces is the right de-risk order; the 12,000 reel (~666 cables) is the production form for later. *Verify the strip is continuous carrier, not embossed pocket tape, on arrival — high confidence from the packaging codes but worth eyeballing.* |
| Ribbon | "22 AWG 3 wire flat servo cable spool", 50 ft, black/red/white | 1–2 spools | ~$20/ea | Same stock as the TendWright wiring doc. One spool is dev scrap, one for real cables. |
| Known-good reference | [Waveshare 5264 cable 6-pack](https://www.amazon.com/waveshare-5264-3PIN-Servo-Compatible-servos/dp/B0GVDFXF7Q) | 1 | ~$10 | Factory crimps to measure and compare against ours (crimp height, pull force). |

## 2. De-risk A — crimp bench (press + applicator)

| Item | Pick / search | Est. | Notes |
|---|---|---|---|
| **Bench press** | ⚠️ **Estimate was WRONG — re-verified 2026-07-25, see `bom-v1.md` §6.** The linked [TZ 1.5T on Amazon](https://www.amazon.com/dp/B07G5PD2T6) is **$1,690.11** today (4–5 wk lead), not $250–500 — that listing is the US 110 V variant and carries a huge premium. Real market: [1.5T press, $238.88 free ship](https://www.ebay.com/itm/157443920594) — but **220 V**. | **~$240 (220 V)** or ~$1,690 (110 V) | 30 mm stroke, 1.5 T, AWG18–30 class — exactly our regime. Takes standard mini-applicators. Permanent S3 power unit, not a throwaway. **220 V is not fatal** — US homes have 240 V split-phase on dryer/range circuits. Frequency stays 60 Hz vs the machine's 50 Hz design, so it runs ~20% fast; tolerable on a cam press but it shifts cycle timing. |
| **Donor/reference applicator** | ⚠️ **Price revised 2026-07-24 after a live eBay pass — see `bom-v1.md` §5 for verified candidates.** Floor for a complete OTP applicator is ~$230–260 + ~$70–80 CN shipping. Best current pick: [OTP Horizontal Mold, $247.94 or Best Offer](https://www.ebay.com/itm/357379481619) (side feed confirmed in the listing). Genuine precision tier for reference: [$1,546](https://www.ebay.com/itm/168452577707). | **~$320 landed** (was $80–160 — stale) | **Check first** whether a clone exists tooled for "5264 / SPOX 2.5" or "Molex 2.5" terminals — sellers list dozens of series; if yes, buy that one and de-risk A is done same-day. If not, buy the **JST-XH 2.5** version anyway as the donor chassis + mechanism reference (XH terminal is a close cousin: 2.5 mm pitch, side-feed open-barrel, 22–28 AWG class). |
| Crimp-height mic | 0–25 mm point/blade micrometer, cheap import | ~$30 | Crimp height is THE quality number (spec class ±0.05 mm). Point anvil needed — flat calipers lie on the B-form. |
| Pull tester | Digital hanging/luggage force scale, 0–20 kg + wire clamp | ~$20 | 22 AWG open-barrel target ≈ 8+ kgf pull-out. Formal rigs later; this finds bad crimps now. |
| Loupe / USB microscope | any 10x loupe or cheap USB scope | ~$15–25 | Reading the crimp cross-section wings; also the future camera-check dev unit. |

## 3. De-risk B — insertion jig (mostly printed)

| Item | Pick | Est. | Notes |
|---|---|---|---|
| Terminal extractor | "2.54mm / mini terminal extractor blade" | ~$5 | Same do-over tool as the wiring doc. Insertion-jig dev scraps lots of loaded housings. |
| Printed parts | funnel guide, housing nest, pusher slide, pull-back stop, stick-magazine cartridge prototype | $0 | Design work, not shopping. First article of the v1 swappable cartridge. |
| Spring assortment | small compression springs kit | ~$10 | Magazine follower + escapement return. |

## 4. The big subtask — DIY ribbon-fed pin applicator

Goal: our own applicator body sized for the 5263 terminal chain — bandolier in, one crimped pin per press stroke, ribbon-fed like the commercial units.

**Sanity note before the fun:** the applicator *mechanism* (frame, ram, cam-driven feed finger, drag brake) is 1930s technology and a genuinely great build — totally within reach. The **punch + anvil profile** is the one precision part (it defines the B-crimp form and the ±0.05 mm crimp height). The plan below builds the mechanism and *sources* proven tooling geometry three ways, cheapest-proven first:

1. **Transplant** — if the donor clone's punch/anvil turns out compatible with 5263 terminal geometry (measure against factory-crimp reference), reuse it. $0.
2. **Buy inserts** — punch/anvil die sets for specific Molex terminal series are sold as spares: [CrimpStore applicator wire dies](https://crimp.store/collections/applicator-wire-dies/applicator) · [applicator components](https://crimp.store/collections/applicator-tooling) · [Allied/RS crimper replacement parts](https://www.alliedelec.com/connector-and-crimp-tooling/crimper-replacement-parts/). ~$50–150.
3. **Machine our own** — A2/D2 tool steel or hardened 4140, wire-EDM or careful mill+stone, dimensioned from the Molex 5263 terminal drawing + measured factory crimps. The fallback that always works, most hours.

| Item | Pick / search | Est. | Notes |
|---|---|---|---|
| Donor applicator | (already bought in §2) | — | Chassis, ram geometry, feed cam, drag brake — measure everything, keep what works. |
| Punch/anvil route 2 | CrimpStore / RS die set for Molex 5263-class terminal | $50–150 | Order after measuring donor + terminals — need the terminal drawing in hand. |
| Tool steel stock | A2 or O1 flat stock, small pieces | ~$30 | Route 3 and for custom feed-finger/track parts regardless. |
| Ground flat plate | 10–15 mm aluminum tooling plate offcuts | ~$40 | Applicator body plates. |
| Linear guidance | 2× MGN9 rail offcuts or ground rod + bronze bushings | ~$30 | Ram guide. Commercial applicators use a dovetail; rail is easier for us. |
| Cam follower + spring kit | small bearing cam follower, die springs assortment | ~$25 | Feed finger actuation off ram stroke — the classic mechanical feed: ram down = crimp, ram up = cam advances chain one pitch. |
| Bandolier path hardware | thin spring steel strip (drag brake), small rollers, reel arm (printed + skate bearing) | ~$25 | Chain guidance from reel to anvil; drag brake gives constant back-tension (standard practice). |
| Reference reading | [TE applicator catalog (anatomy drawings)](https://www.te.com/content/dam/te-com/documents/application-tooling/global/1-1773864-9_TE-Applicators_Catalog.pdf) · [Mecal applicator diagnostics primer](https://www.mecalbystarn.com/2019/04/23/primer-in-diagnosing-crimp-applicator-issues/) · [OCETA applicator catalog](https://www.oceta.com/images/catalogue/pdf/1604586889-catalogue-applicators.pdf) | $0 | Free mechanism documentation — exploded views, feed-cam timing, shut-height conventions. |

**Interface contract (so it drops into the cell later):** standard mini-applicator envelope + shank so the bench press drives it unmodified; chain feed axis horizontal (side-feed); crimp zone reachable by the S2→S3 shuttle path from the thumbnail.

## 5. Cell computer (safe to buy now)

Kyle 2026-07-24: "I assume it will have its own cell computer" — yes, and the **supervisor half is architecture-independent**, so it can be ordered with the de-risk batch. Split the brain in two, the standard machine-control split:

| Item | Pick | Est. | Notes |
|---|---|---|---|
| Supervisor | ~~Raspberry Pi 5~~ → **spare NUC on Ubuntu** (Kyle has a stack; cell1-class boxes are the fallback) | **$0** | ✅ **RESOLVED 2026-07-24 (Kyle): no Pi needed.** Runs the job queue ("make 6 cables: 120 mm ×2, 240 mm ×4"), the state machine, logging, the web HMI, and later the camera color-position check. Also the natural place for a small agent that reports cell status into Hive. Because the split-brain design puts *all* real-time work on the motion MCU, the supervisor is architecture-independent — so a spare PC is a free swap, and a better one (more CPU/RAM for vision, real SSD instead of SD, native x86 dev). Rationale + downstream impacts in `bom-v1.md` §4. |
| Touchscreen (optional) | 7" DSI or any HDMI panel | ~$60 | Or skip — a browser HMI on the network is fine and better for a machine you stand next to with both hands full. |
| Camera (later) | **USB camera** (was Pi Camera 3 on CSI) | ~$25–35 | Q7 / color-position check. Buy when the insertion station is real. Switched from CSI to USB because the supervisor is now a NUC/x86 box — no CSI connector. The Jiusion USB scope already covers dev/bench use. |
| **Motion controller** | **DEFER** — BTT/SKR-class board or Duet, chosen once axis count settles | ~$60–180 | Depends on Q1: one shuttle (~6–7 axes) vs. three parallel lanes (very different board). Don't guess. |

Step generation belongs on a dedicated MCU (Klipper/grblHAL pattern: Pi thinks, MCU does the microsecond timing) — a Pi alone can't hold step timing while running a UI.

## 6. Deferred (full cell — order after de-risk passes)

Steppers ×6–7 + drivers + motion board (~$300), rails/extrusion/printed stations (~$250), guillotine blades (~$50), sensors + encoder + load cell (~$100), pneumatic cylinders + valves if the air route wins (~$120). No surprises expected; all commodity. **Deliberately not orderable tomorrow** — Q1/Q2 in the design doc can change the axis count and therefore this whole bucket.

---

## Totals

| Bucket | Est. |
|---|---|
| Consumables (§1) | ~$85–105 |
| Crimp bench (§2) | ~$395–725 |
| Insertion jig (§3) | ~$15 |
| DIY applicator subtask (§4, beyond donor) | ~$150–300 |
| **Order now, total** | **~$650–1,150** |
| Deferred full-cell motion (§5) | ~$700 |

**Long-lead / order-first:** press (freight from CN possible), terminal chain reel (confirm continuous-strip packaging), donor applicator (seller stock varies). Everything else is days-not-weeks.

## Sourcing results (2026-07-24 hunt)

**Check #1 answered: no off-the-shelf clone is tooled for 5264/SPOX/5263.** The clone catalogs cover XH2.54, PH2.0, SH1.0, ZH1.5, CH3.96, 1.25(GH-class), SM, 4.8, and Molex 5557 — Mini-SPOX isn't in any variant list found. Two viable paths, run both in parallel:

1. **Buy the XH2.5 donor now** — (Amazon listing found 2026-07-24 went stale same day; Kyle sourcing his own.) Live eBay candidates at last check: [multi-series OTP applicator XH2.54/1.25/SM/3.96/5557 (~$80)](https://www.ebay.com/itm/306469875505) · [same family + PH2.0](https://www.ebay.com/itm/316914857998) · [horizontal mold (~$92)](https://www.ebay.com/itm/405176349626) · [(~$160)](https://www.ebay.com/itm/226948649574). **Buy-checklist for whatever listing is in front of you:** ① variant choice = **XH2.54** (true 2.5 mm pitch — closest cousin to SPOX); ② **side feed** (matches 5263 chain and the cell's shuttle path); ③ OTP-standard body/shank so a generic bench press drives it; ④ mechanical (cam-fed) rather than requiring the seller's proprietary press. First test on arrival: run the 5263 chain through it and measure crimps against the factory reference; feed pitch has a real chance of matching, crimp profile maybe-close. Worst case it's the donor chassis we planned anyway.

**Pneumatic note (Kyle 2026-07-24: "gonna need that compressor"):** if the sourced unit/press is pneumatic — fine, arguably better. Crimping is intermittent low-CFM work: a small 1–2 gal "quiet" compressor (~$100–150) covers it with headroom, and compressed air is a gift to the rest of the cell later — S4 insertion pusher, guillotine, stripper clamp all love small pneumatic cylinders (the commercial ribbon machines are servo + pneumatic hybrids for exactly this reason). Add inline filter/regulator/dryer (~$25) — applicator tooling hates moisture.
2. **Custom-tooled applicator, quote in flight** — Chinese applicator makers tool OTP applicators to a customer's terminal as routine business: [Sedeke custom applicator page](https://www.automaticwirestrip.com/terminal-crimping-applicator/) (info@sedeke.com, side/end feed, 30 or 40 mm stroke, mechanical or pneumatic) and [Alibaba custom terminal-die applicator listings](https://www.alibaba.com/product-detail/Terminal-die-crimping-applicator-mould-for_1601014544952.html). Ask price for "OTP applicator tooled for Molex 5263 (0008701039) chain terminals, side feed" — expect a few hundred dollars. If reasonable, this is the money-for-time play: a purpose-tooled unit arrives while we build the ribbon-fed applicator subtask on our own timeline, and its punch/anvil doubles as route-2 tooling for our build.

Useful reference found on the way: [Keszoox Mini-SPOX 5264 selection guide](https://keszoox.com/blogs/news/molex-mini-spox-connector-guide) (part-number matrix for the whole family) and [Molex 207129 ratcheting hand tool for SPOX 2.5](https://se.rs-online.com/web/p/crimp-tools/2222945) (~proper hand crimper for the family — worth adding to §2 as the manual fallback while machine work is in progress).

## Remaining checks before clicking buy

1. DigiKey packaging on 0008701039 — confirm chain (strip) form, not loose-piece, and whether full-reel order code differs.
2. Press stroke/shank standard on the chosen unit ("OTP standard" vs "mini-applicator standard") — the DIY applicator's shank spec copies whatever the press takes; the custom-quote vendor should be told which press we bought.
