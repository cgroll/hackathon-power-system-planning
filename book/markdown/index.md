---
title: Welcome
---

# Hackathon: Power System Planning

Starter project for a hackathon workstream on Germany's renewable power
system, working up to three tasks:

1. **Baseline stress test** — with today's (roughly estimated) installed
   wind + solar capacity and the historical weather record, how much
   "Dunkelflaute" (low-generation) risk is there? How much energy is
   missing overall, relative to demand?
2. **Capacity scaling** — how much does more installed capacity
   (e.g. double wind/solar) actually help?
3. **Battery storage** — how much better can a battery let you use the
   installed capacity you have? Batteries won't eliminate Dunkelflaute
   risk entirely — how far can they get you toward a partial target, e.g.
   95% (not 100%) renewable coverage of demand?

Alongside this planning track, there's a second, validation-focused
track: does the PECD weather-derived data actually match reality? See
[Data Sources](data_sources.md) for both tracks' input data.

## About

Hourly capacity factors for German wind onshore, wind offshore, and solar
come from the official [PECD v4.2](https://cds.climate.copernicus.eu/datasets/sis-energy-pecd)
product, and installed-capacity figures from the
[Marktstammdatenregister](https://www.marktstammdatenregister.de/MaStR/Datendownload)
(MaStR). Both are staged in `data/input/`, copied from
[energy-data-hub](https://github.com/cgroll/energy-data-hub) — a shared
data-ingestion project that downloads and lightly parses this data so
individual projects like this one don't each need their own CDS/MaStR
account and multi-GB download. See [Data Sources](data_sources.md) for
exactly what's included, and this
[video walkthrough](https://youtu.be/vS_A549w3Ss) for how to link MaStR
unit data to PECD's weather zones — the core step behind the validation
track.

This starter deliberately stops at staging the input data: defining a
Dunkelflaute threshold, computing residual load against real demand, and
building a battery-dispatch model, or building and validating a
modeled-potential series against observed generation, are left for your
team to build.

## How to read this book

[Data Sources](data_sources.md) walks through what's in `data/input/` and
where it comes from. [Exploring Germany's PECD Capacity Factors](01_explore_capacity_factors_de.ipynb)
is a small example notebook showing the kind of first-look analysis a
`pipeline/` script in this repo produces — a starting pattern, not a
solution to either track's tasks.
