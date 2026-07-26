# CableCell

A benchtop robot cell that takes 22 AWG 3-conductor servo ribbon off a spool and
produces finished cables — split, strip, crimp Molex 5263 chain terminals, insert
into Mini-SPOX 5264 housings (50-37-5033, TRUE 2.50 mm pitch) on both ends, at a
commanded length.

> Load 20 housings into the cassette, a spool of ribbon, and a reel of pins.
> Tell the software: **3 cables, 5 inch total length.** It makes them and they
> drop into the collect bin as they complete.

**Architecture:** rotary indexing dial — six fixed stations on a bolt circle,
one arm carries the work to each. See `docs/cell-design.md`.

**First customer:** TendWright's STS3215 servo bus needs ~6–10 exact-length
joint-to-joint runs. That is a customer relationship, not ownership — CableCell
is its own project.

## Status

**Planning / design / simulation.** No code, no hardware, nothing ordered. The
sequence is deliberate: plan → research → design → simulate → source → build.
We do not buy until the sim says the layout closes.

## Layout

| Folder | Contents |
|---|---|
| `docs/` | Design of record, prior-art survey, decision log, sourcing index |
| `components/` | `registry.yaml` — the join between the BOM and the sim |
| `bom/` | Rendered buy lists with live vendor links |
| `cad/` | Vendor STEP files as downloaded, before conversion |
| `sim/` | MuJoCo rough-in: datums, scene assembly, reach/collision studies |
| `hardware/` | Printed and machined parts, once they exist |

## The component registry

`components/registry.yaml` is the single source of truth that both the BOM and
the simulation read. One entry per physical component: spec, vendor link, price,
sourcing status, and its model (CSG primitive parameters, or a mesh path once we
have a real one). Two lists that describe the same machine will drift; one list
that renders two views cannot.

## Modeling split

- **MuJoCo + CSG primitives** — layout and motion truth. Does the arm reach every
  station, does anything collide, does the cycle close. Precision does not live
  here; MuJoCo tessellates everything anyway.
- **FreeCAD (B-rep)** — manufacturing truth. Reads vendor STEP without fidelity
  loss, exports STL for the sim at a controlled deviation, and produces the
  dimensioned fabrication drawings via TechDraw.
- **Blender** — renders, visual mockups, quick blockouts.

## Hive

- **App:** CableCell (id 9) · modules Design / Applicator / Stations / Motion / Sourcing
- **Plan:** #657 — sourcing, de-risk bench, DIY ribbon-fed applicator

## License

This repository is dual-licensed, because it contains two different kinds of
work and a software license does not cleanly cover a CAD file.

| What | License | File |
|---|---|---|
| Software — `sim/`, scripts, anything executable | **MIT** | [`LICENSE`](LICENSE) |
| Documentation, CAD, hardware designs, BOMs — `docs/`, `cad/`, `hardware/`, `components/`, `bom/` | **CC BY 4.0** | [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt) |

In plain terms: **take the code and do what you like as long as you keep the
copyright notice; take the designs and do what you like as long as you credit
me.** CC BY requires visible attribution in a way MIT does not — MIT only asks
that the license text travels with copies, which is notice preservation rather
than credit.

Neither license grants patent rights explicitly. That is deliberate.

Copyright (c) 2026 Kyle Bricker.
