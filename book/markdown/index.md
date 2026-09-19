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

## About

Hourly capacity factors for German wind onshore, wind offshore, and solar
come from the PECD v4.2 replication in `~/research/pecd-replication`.
Installed capacity is a rough, hand-entered approximation (see
`hpsp/capacity_assumptions.py`) — deliberately **not** derived from the
Marktstammdatenregister, to avoid the setup overhead of a ~12 GB bulk
download for a short hackathon slot.

This starter deliberately stops at data preparation: defining a
Dunkelflaute threshold, computing residual load against real demand, and
building a battery-dispatch model are the three tasks above, left for your
team to build — not pre-solved here.

## How to read this book

The chapters are structured as executed notebooks. Each notebook corresponds
to a pipeline script in `pipeline/` that was run by DVC.
