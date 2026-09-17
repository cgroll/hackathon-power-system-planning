---
title: Welcome
---

# Hackathon: Power System Planning

Starter project for a hackathon workstream on Germany's renewable power
system: given today's (roughly estimated) installed wind and solar
capacity, how much "Dunkelflaute" risk is there, and how much does battery
storage help?

## About

Hourly capacity factors for German wind onshore, wind offshore, and solar
(2019-2025) come from the PECD v4.2 replication in
`~/research/pecd-replication`. Installed capacity is a rough, hand-entered
approximation (see `hpsp/capacity_assumptions.py`) — deliberately **not**
derived from the Marktstammdatenregister, to avoid the setup overhead of a
~12 GB bulk download for a short hackathon slot.

The starter analysis notebook is a worked example, not a finished answer —
see its own introduction for the simplifications it makes and where a team
should push further (real demand data, regionally resolved capacity,
battery power limits, round-trip losses, alternative Dunkelflaute
definitions, ...).

## How to read this book

The chapters are structured as executed notebooks. Each notebook corresponds
to a pipeline script in `pipeline/` that was run by DVC.
