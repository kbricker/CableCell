# Industrial sourcing index

Where to find parts, tools and CAD models for machine-building projects.
Organised by **what you are trying to buy**, because that is how you actually
use it — not alphabetically, and not as a link dump.

**Verification convention.** ✅ = hit live during a sourcing pass, with the date.
Everything else is general knowledge and should be treated as a starting point,
not a fact. Same rule as the BOM: an unverified link is a claim.

**Started** 2026-07-26 for CableCell, but deliberately written to be
project-agnostic — the next machine reuses it.

---

## 1. Crimp and applicator tooling

The hardest category to search, because the vocabulary is unusual and consumer
search engines return hand crimpers no matter what you ask for. Learn the words:
an **applicator** is the tooling that feeds a terminal chain and forms the crimp;
a **press** is the dumb machine that drives it; a **die set** is something else
entirely and will not feed a chain.

### Connector OEMs (the authoritative source)

| Source | Good for | Notes |
|---|---|---|
| [Molex Application Tooling](https://www.molex.com/en-us/products/application-tooling) ✅ 2026-07-26 | ATS specification PDFs per applicator, Mini-Mac and FineAdjust lines, custom tooling | The ATS docs are fully dimensioned drawings — the authoritative source for shut height and applicator geometry |
| [TE Application Tooling](https://www.te.com/en/products/application-tooling/applicators.html) ✅ 2026-07-26 | Applicator catalogue, AMP tooling | [Catalogue PDF](https://www.te.com/content/dam/te-com/documents/application-tooling/global/1-1773864-9_TE-Applicators_Catalog.pdf) |
| JST | Side-feed applicator manuals via distributor datasheets | Manuals often mirrored on DigiKey's media server |

### Applicator and press vendors

| Source | Good for | Notes |
|---|---|---|
| [Mecal by Starn](https://www.mecalbystarn.com/applicators-evs-side-feed-mini-applicator/) ✅ 2026-07-26 | EVS side-feed mini applicators | States the 135.8 mm ±0.02 shut-height standard explicitly |
| [ETCO](https://www.etco.com/application-equipment/) ✅ 2026-07-26 | Mighty-Mini applicators, presses, die sets | US-based; one-piece cast bodies, thick base plates |
| [Kingsing](https://www.kingsing.com/product/428.html) ✅ 2026-07-26 | Pneumatic side-feed and end-feed applicators | **119.7 mm shut height** — the clone standard, not the Western one |
| [crimpapplicator.com](https://www.crimpapplicator.com/product/123.html) ✅ 2026-07-26 | Left/right side-feed applicators | Also 119.7 mm |
| [Eastontech / ew-wirestripping](https://www.ew-wirestripping.com/Products/1/3/50/Terminal-crimping-machine.html) ✅ 2026-07-26 | 1.5T–5T terminal crimping presses | The class CableCell's press comes from |
| [Errebishop](https://errebishop.com/en/automatic-stripping-and-crimping/10328-15t15kn-taped-terminal-crimping-machine-for-mini-applicators-with-30mm-stroke.html) ✅ 2026-07-26 | Presses with real published specs | One of the few listings that publishes footprint/weight/power |
| [JCWelec](https://www.jcw-wirestripping.com/jcw-30cps-otp-type-pneumatic-horizontal-feed-terminal-crimp-applicator.html) ✅ 2026-07-26 | OTP-type pneumatic horizontal-feed applicators | |
| Sedeke — `info@sedeke.com` | **Custom applicator tooled to your terminal** | The route when no off-the-shelf applicator exists for your connector. Needs a press shank spec attached to any quote request |

### High end (reference and used-market targets)

Komax, Schleuniger, Artos, Metzner, Eubanks, Carpenter Mfg. Far beyond hobby
budget new, but worth knowing the names — they are what shows up on the used
market, and their documentation is the best free education available on how
these machines actually work.

### 🔴 Two traps this project already hit

1. **Die-set pliers are not applicator presses.** A machine marketed as
   "pneumatic, automatic, 14 die sets" crimps loose terminals hand-fed one at a
   time. It cannot feed a chain and cannot mount a standard applicator. Chain
   feed is usually the whole premise — check for it explicitly.
2. **"Standard" shut height means two different things.** 135.78 mm ±0.02
   (Molex/TE/Mecal, Western) vs **119.7 mm** (Chinese OTP clones). A 16 mm
   mismatch makes applicator and press incompatible. **Always ask which.**

---

## 2. Electronic components, connectors, terminals

| Source | Good for | Notes |
|---|---|---|
| [DigiKey](https://www.digikey.com) ✅ 2026-07-25 | Terminals, connectors, **packaging clarity** | Best in class for telling you whether a part ships as Cut Tape, Tape & Reel or loose-piece — which for crimp terminals decides whether an applicator can feed it |
| [Mouser](https://www.mouser.com) ✅ 2026-07-25 | Same catalogue, different stock | Also mirrors manufacturer datasheets and CAD |
| [Newark / Farnell](https://www.newark.com) ✅ 2026-07-25 | Third opinion on stock and price | |
| Arrow | Occasionally stocks what the others do not | Not verified |
| LCSC | Cheap passives and connectors, direct from Shenzhen | Not verified; long shipping |

**Packaging is a first-class spec for crimp terminals.** Loose-piece terminals
cannot be machine-fed. Confirm the carrier form before ordering, and re-confirm
on arrival that it is continuous carrier strip rather than embossed pocket tape.

---

## 3. Mechanical raw stock, fasteners, tooling

| Source | Good for | Notes |
|---|---|---|
| **[McMaster-Carr](https://www.mcmaster.com)** | Fasteners, tool steel, ground plate, springs, bearings, raw stock — and **a STEP file on essentially every part page** | The single most useful site in this document. No login for CAD, next-day delivery. "Source it and model it" is one click. Prices are all-in rather than cheapest |
| [Misumi](https://us.misumi-ec.com) | **Configurable** parts — shafts cut to length, extrusion, precision plates, linear components | CAD download with a free account. The configurator is the point: specify a shaft to 0.1 mm and it ships |
| [MSC Industrial](https://www.mscdirect.com) | Cutting tools, metrology, shop supply | |
| [Grainger](https://www.grainger.com) / [Zoro](https://www.zoro.com) | General MRO | Zoro is Grainger's cheaper consumer-facing channel — same catalogue, often lower price |
| [Fastenal](https://www.fastenal.com) | Fasteners in quantity, local branches | |

---

## 4. Motion — linear, rotary, transmission

| Source | Good for | Notes |
|---|---|---|
| [StepperOnline (OMC)](https://www.omc-stepperonline.com) | NEMA steppers, drivers, **ballscrew linear stages**, planetary gearboxes | Best price-per-quality in the hobby-to-light-industrial band |
| [VXB](https://vxb.com/products/100mm-cnc-linear-stage-sfu1605-sbr16) ✅ 2026-07-26 | Bearings, and **prebuilt SFU1605 linear stages** | Carries the exact Z-stage class CableCell needs |
| [OpenBuilds](https://openbuildspartstore.com) | V-slot extrusion, linear kits, plates | Good ecosystem docs; lighter duty than ballscrew stages |
| [ServoCity / Actobotics](https://www.servocity.com) | Hobby-grade shafts, hubs, gears, brackets that all fit each other | Excellent for prototyping mechanisms fast |
| Hiwin / THK / PBC Linear / igus | Industrial linear rails and bearings | igus publishes free CAD and sends samples generously |
| [Boca Bearings](https://www.bocabearings.com) | Specialty and thin-section bearings | Not verified |
| SDP/SI, Ruland, Lovejoy | Precision gears, couplings, timing belts | Not verified |

---

## 5. Pneumatics

| Source | Good for | Notes |
|---|---|---|
| [SMC](https://www.smcusa.com) / [Festo](https://www.festo.com) | Cylinders, valves, manifolds, rotary actuators — and **online configurators that emit STEP for the exact part number** | The configurator CAD is the reason to start here even if you buy elsewhere |
| [Clippard](https://www.clippard.com) | **Small-bore** cylinders and valves | The right scale for benchtop machines where SMC/Festo start too big |
| [AutomationDirect](https://www.automationdirect.com) | Valves, manifolds, sensors, fittings, PLCs | Free datasheets and CAD, US stock, genuinely good prices |
| Bimba | Cylinders | Not verified |

**Note for crimp work:** use a filter + regulator, deliberately *not* a full FRL.
A lubricator injects oil into the air, which is the last thing you want near
crimp tooling.

---

## 6. Vendor CAD and 3D models

The difference between a rough-in that takes a day and one that takes a week.

| Source | Format | Notes |
|---|---|---|
| **McMaster-Carr** | STEP | Per-part, no login. Best-in-class |
| [TraceParts](https://www.traceparts.com) | STEP, native | Huge aggregator — SMC, Festo, Hiwin, THK, igus. Free account |
| [3D ContentCentral](https://www.3dcontentcentral.com) | STEP, SolidWorks | Dassault-run, vendor-published |
| [GrabCAD](https://grabcad.com) | Mixed, **often STL** | User-uploaded — NEMA motors, MGN rails, generic hardware. Quality varies, verify dimensions. STL directly usable in MuJoCo |
| Molex / TE / JST product pages | STEP, IGES | Per-part connector and terminal models |
| SMC / Festo configurators | STEP | Exact ordered configuration |
| [Printables](https://www.printables.com) / Thingiverse | STL | Printed parts, spool holders, motor mounts |
| Onshape public documents | Native, exports STEP/STL | Searchable; everything on the free tier is public |

**MuJoCo eats STL/OBJ/MSH, not STEP.** Convert with FreeCAD (`Import` → `Mesh`,
scriptable headless) at a controlled deviation. Prefer sources that publish STL
directly when the part is only being visualised.

---

## 7. Surplus, used and auction

Where 5-figure industrial machines become 3-figure ones. Worth checking before
buying any press, applicator or metrology tool new.

| Source | Good for | Notes |
|---|---|---|
| [eBay](https://www.ebay.com) ✅ 2026-07-25 | Applicators, presses, tooling, metrology | The real market for clone applicators. Best Offer means price is negotiable. Watch shipping from CN — often $70–80 |
| Surplus Record | Used industrial machinery listings | Not verified |
| Machinio | Aggregates dealer inventory | Not verified |
| HGR Industrial Surplus | Bulk industrial surplus, photographed | Not verified |
| Bid on Equipment / IRS Auctions | Auction-format industrial | Not verified |
| [Surplus Center](https://www.surpluscenter.com) | Hydraulics, motors, odd mechanical | Not verified |

---

## 8. Direct import

| Source | Good for | Notes |
|---|---|---|
| AliExpress | Ballscrew stages, steppers, extrusion, OTP applicators | Same factories as the eBay listings, often cheaper, slower |
| Alibaba | Volume, and **talking to the actual manufacturer** | The route for custom tooling enquiries |
| [Robotdigg](https://www.robotdigg.com) | Niche automation and 3D-printer mechanical parts | Not verified |

**Import gotcha:** listing prices frequently include import fees but exclude a
substantial shipping charge that only appears at checkout. Budget landed cost,
never listed cost — this project's applicator estimate was off by 2× for exactly
this reason.

---

## 9. Metrology

| Source | Good for |
|---|---|
| McMaster, MSC, Grainger | Micrometers, calipers, gauge blocks, indicators |
| Amazon | Surprisingly competitive on iGaging/Mitutoyo-class instruments |

**Crimp height needs a point micrometer**, not calipers — flat anvils read a
B-crimp wrong. A general double-point mic (~$60) does the same job as a branded
"crimp height micrometer" (~$104–184).

---

## Workflow: finding tooling for an unusual part

The method that worked for CableCell, generalised:

1. **Get the OEM part number and its family** — not the marketplace description.
   Terminal chain 0008701039 in the Molex 5263 family, not "2.5 mm crimp pins."
2. **Check the OEM's own application tooling catalogue first.** They publish
   dimensioned specs even when they will not sell you a $250 tool.
3. **Search the specialist vendors** (§1) by *terminal family*, not by connector.
   Applicators are tooled to terminals.
4. **Check the used market** before accepting a new price.
5. **If nothing exists off the shelf, get a custom quote** — Sedeke-class vendors
   tool to a customer's terminal. Attach your press's shank spec.
6. **Verify the interface before buying**: shut height, feed direction, shank
   standard, and whether feed is mechanical (cam off the ram) or needs the
   vendor's own press. A tool that cannot mount is worth nothing.
7. **Confirm packaging** for anything consumable — carrier strip vs loose-piece
   decides whether the tooling can feed it at all.
