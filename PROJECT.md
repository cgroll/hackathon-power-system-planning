# Project State

Tracks the current state and next steps for this project.
See [AGENTS.md](AGENTS.md) for structure/tooling conventions.

## Goal

Hackathon starter repo covering **both tracks** of `slides/hackathon-pecd.html`
(the public-facing overview of this hackathon). Both tracks share one
underlying dataset family: Germany's hourly PECD v4.2 capacity factors,
the official Copernicus product. Teams get a ready-to-use dataset staged
in `data/input/` — no CDS/MaStR account, no waiting on downloads.

### Track B — Planning (Dunkelflaute + battery sizing)

Three escalating tasks:

1. **Baseline stress test** — take today's (roughly estimated) installed
   wind + solar capacity and the full historical weather record
   (1980-2025). How much Dunkelflaute (low-generation) risk is there? How
   do you even define/measure a Dunkelflaute event? How much energy is
   missing overall, relative to demand (residual load)?
2. **Capacity scaling** — vary the installed capacity (e.g. double wind
   and/or solar) and re-run the same stress test. How much does more
   installed capacity actually buy you?
3. **Battery storage** — add a battery and see how much better the
   installed capacity can be used (shifting midday solar output into the
   evening, etc.). Batteries are not expected to eliminate Dunkelflaute
   risk entirely — a good stretch question is how far batteries + extra
   capacity get you toward a *partial* target (e.g. 95%, not 100%,
   renewable coverage of demand).

Uses a fixed, "today" installed-capacity assumption (`hpsp/capacity_assumptions.py`)
— no fleet history needed. Demand data isn't shipped; fetch it from SMARD
(see [Data](#data)).

### Track A — Validation (does PECD match reality?)

Compare:

- **Modeled**: official PECD capacity factors (zone-level: PEON onshore /
  PEOF offshore / NUTS2 solar) × the **time-varying** MaStR installed
  fleet (per-unit records, not a fixed "today" number) → modeled
  generation.
- **Observed**: SMARD's actual per-technology grid feed-in — which is,
  by construction, already post-congestion/curtailment.
- The task: compare modeled vs. observed and interpret the gap (partly
  curtailment, partly behind-the-meter solar self-consumption invisible
  to SMARD). No redispatch/curtailment data is shipped — building the
  "adjusted observed" correction is part of the exercise, same
  "ingredients, not the answer" principle as everywhere else in this
  repo.

Track A needs data Track B doesn't (time-varying, **zone-level** MaStR
capacity + PECD capacity factors, so teams build the modeled/potential
series themselves; SMARD *generation* actuals per technology, fetched
separately) — Track B needs data Track A doesn't (a fixed **national**
capacity number, SMARD *demand*). See [Data](#data) for the concrete
file list for each.

**By design, this starter repo stops at staging input data for both
tracks.** No Dunkelflaute-threshold, residual-load, battery-dispatch,
zone-linking, or congestion-correction/comparison logic is pre-built —
defining and answering those is exactly what the tasks above ask teams
to do.

## Data

All input data lives in `data/input/`, copied from
[energy-data-hub](https://github.com/cgroll/energy-data-hub) — **git-ignored,
not committed to this repo's history**, but included in the checkout/archive
teams start from. Full breakdown, column reference, and the
MaStR↔PECD linking recipe: [`book/markdown/data_sources.md`](book/markdown/data_sources.md),
plus a [video walkthrough](https://youtu.be/vS_A549w3Ss) of that same
linking exercise.

SMARD data (both demand and generation) is **intentionally not shipped**
— fetching and aligning it with the hourly PECD timestamps is part of
both tracks' exercise, not a pre-solved input.

Two files in `data/input/` exceed GitHub's 100MB per-file limit
(`mastr/solar.parquet`, ~202MB; `pecd_country_capacity_factors_simple.parquet`,
the all-Europe file, ~222MB) — not a problem while `data/input/` stays
git-ignored, but worth knowing if the distribution approach changes later
(options: Git LFS, trimming columns, or dropping the all-Europe file
since Track B only needs the DE one).

## Current State

Input data is staged and one example analysis exists:
`pipeline/01_explore_capacity_factors_de.py` → `book/notebooks/01_explore_capacity_factors_de.ipynb`,
a descriptive first look at Track B's national capacity-factor series
(seasonality, a calm vs. a windy week, wind/solar correlation) — shows
the analysis-script pattern this repo uses, not a solution to either
track's tasks. `dvc repro` runs clean end-to-end.

Nothing else is pre-built: no Dunkelflaute definition, no residual-load
or battery logic, no MaStR↔PECD zone linking, no SMARD data. That's the
hackathon.

## Next Steps

For hackathon teams:

**Track A** (see [`book/markdown/data_sources.md`](book/markdown/data_sources.md)
for the full recipe):
1. Assign each MaStR unit to a PECD zone (solar via the NUTS crosswalk,
   wind via the region masks).
2. Classify solar units into PECD's 4 technology codes.
3. Turn per-unit commissioning/shutdown events into a time-varying,
   zone-level monthly capacity panel.
4. Combine with PECD's zonal capacity factors into a modeled
   potential-generation series, fetch SMARD's observed generation, and
   compare.

**Track B**:
1. Define a Dunkelflaute threshold and quantify baseline risk against
   real demand (fetch from SMARD).
2. Vary installed capacity and re-run.
3. Add a battery model and see how much it helps.
