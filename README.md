# Hackathon: Power System Planning

Starter repo for a two-track hackathon on Germany's renewable power
system, built on the official PECD v4.2 capacity-factor product and MaStR
register data. See `slides/hackathon-pecd.html` for the public-facing
overview of both tracks, and [PROJECT.md](PROJECT.md) for the current
state:

- **Track B — Planning**: given today's (roughly estimated) installed wind
  + solar capacity and 46 years of historical weather (1980-2025), how much
  "Dunkelflaute" (low-generation) / residual-load risk is there — and how
  much do (a) more installed capacity and (b) battery storage reduce it?
- **Track A — Validation**: does PECD track reality? Combine PECD capacity
  factors with the *time-varying* historic MaStR fleet to build your own
  modeled-potential series, and compare it against SMARD's observed grid
  power.

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

This repo ships input data, not solutions — no Dunkelflaute-threshold,
residual-load, battery-dispatch, or congestion-correction/comparison
logic — so those decisions stay the hackathon teams' to make.

## Data

`data/input/` is fetched automatically — `dvc repro`'s first stage
downloads a shared archive of [energy-data-hub](https://github.com/cgroll/energy-data-hub)'s
output (a project that handles the CDS/MaStR downloads and parsing so this
repo doesn't have to) and unpacks it. Run `make run` and it's there — no
CDS/MaStR account, no manual copying. It's **git-ignored, not committed**
to this repo's history. See [`book/markdown/data_sources.md`](book/markdown/data_sources.md)
for the full breakdown, including a [video walkthrough](https://youtu.be/vS_A549w3Ss)
of linking MaStR data to PECD's weather zones.

**Track B** (national, ready to use):
- `data/input/pecd/pecd_country_capacity_factors_simple_de.parquet` —
  hourly, DE, wind onshore / wind offshore / solar, 1980-2025.
- `hpsp/capacity_assumptions.py` — today's installed capacity per
  technology (MaStR register snapshot) — Task 2 is exactly "change these
  values and see what happens".
- Electricity demand is **not** shipped — fetch it yourself from
  [SMARD](https://www.smard.de/home/downloadcenter/download-marktdaten)
  for the residual-load calculation.

**Track A** (zonal capacity factors + raw MaStR ingredients — deliberately
*not* pre-combined into a potential series; building that, and comparing
it against observed generation, is the exercise):
- `data/input/pecd/pecd_wind_onshore_capacity_factors.parquet` /
  `..._offshore.parquet` / `pecd_solar_capacity_factors.parquet` — hourly,
  per PEON/PEOF/NUTS2 zone, 2015-2025.
- `data/input/mastr/solar.parquet` / `wind.parquet` / `solar_technical_detail.parquet`
  — per-unit MaStR records, not zone-joined or aggregated.
- `data/input/pecd/peon_region_mask.nc` / `peof_region_mask.nc` — PECD's
  zone-membership weights per 0.25° grid cell, all of Europe.
- `data/input/regions/lau_nuts_correspondence.parquet` — municipality →
  NUTS3 crosswalk, needed to map solar units to a zone.
- SMARD generation-by-technology is **not** shipped either — same source
  as above, fetch it yourself.

## Quickstart

```bash
uv sync
make dry-run   # preview what would run
make run       # execute the pipeline (only reruns stages that are stale)
make serve     # open http://localhost:3000 — live book preview
```

`make run` first downloads `data/input/` (skipped on later runs — see
`persist: true` in [AGENTS.md](AGENTS.md)), then builds the two example
notebooks shipped in this repo (`pipeline/00_explore_input_data.py` and
`pipeline/01_explore_capacity_factors_de.py`). Add your own pipeline
stages the same way as you build out either track — see
[AGENTS.md](AGENTS.md) for the conventions.

## Project layout

```
project-root/
├── hpsp/                    # Python package
│   ├── paths.py             # Centralized path config
│   └── capacity_assumptions.py  # Track B's fixed "today" capacity
├── pipeline/
│   ├── download_input_data.py              # Fetches data/input/ (this repo's only network stage)
│   ├── 00_explore_input_data.py            # Example: inventory of data/input/
│   ├── 01_explore_capacity_factors_de.py   # Example: first-look analysis
│   └── _strip_jupytext_metadata.py         # Shared post-processing helper
├── book/                    # MyST book source
│   ├── notebooks/           # Executed notebooks (DVC output)
│   ├── markdown/            # Static content
│   └── myst.yml             # TOC and site settings
├── slides/                  # Public-facing hackathon overview (both tracks)
├── data/
│   ├── input/                # Fetched from energy-data-hub — git-ignored
│   └── processed/            # Your own pipeline's outputs (empty until you add a stage)
├── output/images/           # Figures (tracked in git)
├── dvc.yaml                 # Pipeline DAG
├── dvc.lock                 # Pipeline state (checksums) — tracked in git
├── AGENTS.md                # Detailed conventions for contributors/AI
└── PROJECT.md                # Current state and next steps
```

See [AGENTS.md](AGENTS.md) for full details on adding pipeline stages,
writing analysis scripts, and DVC usage. See [PROJECT.md](PROJECT.md) for
the current state and what's next.

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
