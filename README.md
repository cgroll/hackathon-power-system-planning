# Hackathon: Power System Planning

Starter repo for a two-track hackathon on Germany's renewable power
system, built on one shared dataset: hourly PECD v4.2 capacity factors.
See `slides/hackathon-pecd.html` for the public-facing overview of both
tracks, and [PROJECT.md](PROJECT.md#goal) for the full breakdown this repo
is meant to set teams up for:

- **Track B — Planning**: given today's (roughly estimated) installed wind
  + solar capacity and as long a historical weather record as is already
  on disk (1980-2025), how much "Dunkelflaute" (low-generation) /
  residual-load risk is there — and how much do (a) more installed
  capacity and (b) battery storage reduce it?
- **Track A — Validation**: does PECD track reality? Combine PECD capacity
  factors with the *time-varying* historic MaStR fleet to build your own
  modeled-potential series, and compare it against SMARD's observed grid
  power.

Both tracks' data is fully built and committed (see Data below).

Built from [`project-book-template-dvc`](../project-book-template-dvc) —
a MyST Jupyter Book with a [DVC](https://dvc.org/)-orchestrated pipeline,
dependencies managed by [uv](https://docs.astral.sh/uv/).

## Track B tasks

1. **Baseline stress test** — with today's installed capacity, quantify
   Dunkelflaute risk and residual-load shortfall against the historical
   weather + demand record.
2. **Capacity scaling** — vary installed capacity (e.g. double it) and see
   how much that helps.
3. **Battery storage** — add a battery and see how much better the
   installed capacity can be used; batteries won't eliminate Dunkelflaute
   risk entirely, but how close can they get to, say, 95% coverage?

This repo ships **data only** — no Dunkelflaute-threshold, residual-load,
battery-dispatch, or congestion-correction/comparison logic — so those
decisions stay the hackathon teams' to make.

## Data

All final data below is committed directly in `data/processed/` (small,
`cache: false` in `dvc.yaml`) — clone the repo and it's there, no CDS or
MaStR account needed. The pipeline that built it is documented for
reproducing or extending it yourself (see Quickstart).

**Track B** (national, fixed "today" capacity):
- `capacity_factors_de_national.parquet` — hourly, DE, wind onshore /
  wind offshore / solar, 1980-2025 (403,247 rows). Official PECD v4.2
  product, **unweighted** mean across zones (deliberately not
  capacity-weighted — that's Track A's exercise, see PROJECT.md).
- `demand_de_national.parquet` — hourly DE electricity demand (`demand_mw`),
  SMARD-based, native range 2018-09-30 through 2026-08-04.
- `hpsp/capacity_assumptions.py` — today's installed capacity per
  technology (MaStR register snapshot, 2026-06/07) — Task 2 is exactly
  "change these values and see what happens".

**Track A** (zonal capacity factors + raw MaStR ingredients — deliberately
*not* pre-combined into a potential series; building that, and comparing
it against observed generation, is the exercise):
- `capacity_factors_zonal_wind_onshore.parquet` / `..._offshore.parquet` /
  `..._solar.parquet` — hourly, per PEON/PEOF/NUTS2 zone, 2015-2025.
- `mastr_units_wind_solar.parquet` — per-unit MaStR wind + solar capacity
  records (~6.27M rows, 36 MB): technology, region_code (MaStR's own
  NUTS3-like code, not yet a PECD zone), capacity_mw, commissioning_date,
  final_shutdown_date, longitude, latitude, plus (solar-only)
  installation_type, usage_sector, main_orientation,
  main_orientation_tilt_bucket — everything needed to classify a solar
  unit into PECD's 4 technology codes — and pv_category (full feed-in vs.
  self-consumption with/without battery storage; a different axis, not
  needed for the hackathon but cheap to keep for later behind-the-meter
  analysis). Not zone-joined, not technology-classified, not
  month-aggregated.
- `pecd_region_mask_peon.parquet` / `..._peof.parquet` — PECD's
  zone-membership weight per 0.25° grid cell, Germany only (995 / 233
  rows): use with a unit's coordinates (nearest-cell snap) to assign it
  to a PEON/PEOF zone.
- `generation_de_by_technology.parquet` — SMARD actual per-technology grid
  feed-in (`pv`/`wind_onshore`/`wind_offshore`), same range as demand above.

Left as Track A's own exercise: splitting MaStR's "wind" into
onshore/offshore (hint: MaStR flags offshore with a "DEZZ"-prefixed
`region_code`), mapping solar's `region_code` to its NUTS2 parent (hint:
the first 4 characters), the coordinate → grid-cell → zone-weight lookup
for wind, turning per-unit dates into a monthly zone-capacity panel, and
finally comparing modeled potential against observed (curtailed) output —
no redispatch/curtailment data is shipped, that gap is part of the
interpretation. See [PROJECT.md](PROJECT.md#goal) for the full reasoning
behind every range/scope choice above.

## Quickstart

```bash
uv sync
make dry-run   # preview what would run
make run       # execute the pipeline (only reruns stages that are stale)
make serve     # open http://localhost:3000 — live book preview
```

Since the final data is already committed, `make run` should report
everything up to date. To reproduce the data yourself (e.g. to extend the
history further, or adapt this for another country): stages
`download_pecd_capacity_factors` and `process_pecd_capacity_factors` need
a `~/.cdsapirc` (a free Copernicus CDS account,
https://cds.climate.copernicus.eu/how-to-api) — the 1980-2025 request is
chunked into 10-year pieces (a single request that size hits the CDS
API's cost limit, see `pipeline/01`) and can take hours overall;
`prepare_mastr_track_a_inputs` and `prepare_demand_and_generation` instead
reuse already-processed output from sibling repos
(`~/research/mastr-power-capacities-germany`, `~/research/pecd-replication`)
— see each pipeline script's own docstring.

## Project layout

```
project-root/
├── hpsp/                    # Python package
│   ├── paths.py             # Centralized path config
│   ├── cds.py               # CDS API retry wrapper
│   ├── pecd_io.py           # PECD region-timeseries ZIP parser
│   └── capacity_assumptions.py  # Track B's fixed "today" capacity
├── pipeline/
│   ├── 01_download_pecd_capacity_factors.py   # CDS download, 1980-2025
│   ├── 02_process_pecd_capacity_factors.py    # Raw zips -> DE zonal parquet
│   ├── 03_prepare_mastr_track_a_inputs.py     # Raw MaStR units + PECD zone masks
│   ├── 04_prepare_capacity_factors_national.py # Track B: national, fixed capacity
│   ├── 05_prepare_capacity_factors_zonal.py    # Track A: zonal, 2015-2025
│   └── 06_prepare_demand_and_generation.py     # SMARD demand + generation split
├── book/                    # MyST book source
│   ├── notebooks/           # Executed notebooks (DVC output)
│   ├── markdown/            # Static content
│   └── myst.yml             # TOC and site settings
├── slides/                  # Public-facing hackathon overview (both tracks)
├── data/
│   ├── downloads/           # Raw CDS downloads — git-ignored
│   └── processed/           # Final deliverables — tracked in git;
│                             # _intermediate/ (build-only) — git-ignored
├── output/images/           # Figures (tracked in git)
├── dvc.yaml                 # Pipeline DAG
├── dvc.lock                 # Pipeline state (checksums) — tracked in git
├── AGENTS.md                # Detailed conventions for contributors/AI
└── PROJECT.md                # Current state, roadmap, lessons learned
```

See [AGENTS.md](AGENTS.md) for full details on adding pipeline stages,
writing analysis scripts, and DVC usage. See [PROJECT.md](PROJECT.md) for
the current state and open questions/workstream ideas.

## Enable GitHub Pages (optional)

If/when this is pushed to GitHub: **Settings → Pages → Source → GitHub
Actions**, and add a `github: <user>/<repo>` line back to `book/myst.yml`.
Every push to `main` then builds and deploys the book automatically.

## Common DVC commands

| Command | Effect |
|---------|--------|
| `dvc repro --dry` | Dry run — show what would execute |
| `dvc repro` | Run pipeline (only rebuilds what's out of date) |
| `dvc repro -f <stage>` | Force-re-run a specific stage |
| `dvc repro <stage>` | Build one specific stage (and its dependencies) |
| `dvc repro --force` | Re-run everything unconditionally |
| `dvc dag` | Print the pipeline DAG |
