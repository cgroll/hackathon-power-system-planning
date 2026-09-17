# Hackathon: Power System Planning

Starter repo for a hackathon workstream on Germany's renewable power
system: given today's (roughly estimated) installed wind + solar capacity,
how much "Dunkelflaute" (low-generation) risk is there, and how much does
battery storage reduce it?

Built from [`project-book-template-dvc`](../project-book-template-dvc) —
a MyST Jupyter Book with a [DVC](https://dvc.org/)-orchestrated pipeline,
dependencies managed by [uv](https://docs.astral.sh/uv/).

## Data

- **Capacity factors** (hourly, DE, 2019-2025, wind onshore/offshore, solar):
  reused from the already-downloaded/processed PECD v4.2 replication in
  `~/research/pecd-replication` — no Copernicus/CDS API key needed to run
  this repo's own pipeline. See `pipeline/01_prepare_capacity_factors.py`.
- **Installed capacity**: a rough, hand-entered approximation for Germany
  "today" (~63 GW wind onshore, ~9 GW wind offshore, ~100 GW solar) in
  `hpsp/capacity_assumptions.py` — intentionally **not** pulled from the
  Marktstammdatenregister (MaStR), to skip that setup cost for a short
  hackathon slot. A good stretch goal: swap in a real MaStR-derived number
  from `~/research/mastr-power-capacities-germany`.

## Quickstart

```bash
uv sync
make dry-run   # preview what would run
make run       # execute the pipeline: prep capacity factors → starter notebook
make serve     # open http://localhost:3000 — live book preview
```

`make run` produces `book/notebooks/02_dunkelflaute_battery_starter.ipynb`,
a worked (but deliberately simplified) example of a Dunkelflaute + battery
analysis — see its own introduction for the simplifications and where to
push further.

## Project layout

```
project-root/
├── hpsp/                    # Python package
│   ├── paths.py             # Centralized path config
│   └── capacity_assumptions.py  # Rough installed-capacity numbers
├── pipeline/
│   ├── 01_prepare_capacity_factors.py       # Pure data: reuse PECD output
│   └── 02_dunkelflaute_battery_starter.py   # Analysis → notebook
├── book/                    # MyST book source
│   ├── notebooks/           # Executed notebooks (DVC output)
│   ├── markdown/            # Static content
│   └── myst.yml             # TOC and site settings
├── data/                    # Git-ignored data (cached by DVC)
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
