# Project State

Tracks the current state, roadmap, and lessons learned for this project.
See [AGENTS.md](AGENTS.md) for structure/tooling conventions.

## Goal

Hackathon starter repo for the "Power System Planning" workstream: given
today's (roughly estimated) installed wind + solar capacity for Germany,
explore how much Dunkelflaute (low-generation) risk there is, and how much
battery storage reduces it. Broader hackathon context (talk outline, other
workstreams, data inventory) lives in
`~/research/hackathon-vibe-coding-strom/PROJECT.md` — this repo is the
concrete, runnable starting point for one of its workstreams.

## Current State

Set up 2026-09-17, from `project-book-template-dvc`. End-to-end pipeline
runs today without any external API key or account:

- `pipeline/01_prepare_capacity_factors.py` — pure data stage. Reuses
  already-downloaded/processed PECD v4.2 output from
  `~/research/pecd-replication` (no CDS API call). Produces hourly
  `wind_onshore` / `wind_offshore` / `solar` national capacity factors for
  Germany, 2019-2025 (61,367 rows), at
  `data/processed/capacity_factors_de_national.parquet`.
- `hpsp/capacity_assumptions.py` — rough, hand-entered installed capacity
  for Germany "today" (wind onshore 63 GW, wind offshore 9 GW, solar
  100 GW). Explicitly **not** derived from MaStR — see module docstring.
- `pipeline/02_dunkelflaute_battery_starter.py` — worked example notebook:
  Dunkelflaute event statistics (threshold + event-duration approach) and
  an illustrative rule-based battery sensitivity curve (shortfall hours/year
  vs. battery GWh). Verified end to end (`uv run python pipeline/01...`,
  then the analysis script executed directly) — both produce sane,
  documented-as-simplified numbers.

Verified: `uv sync` installs cleanly; `pipeline/01_prepare_capacity_factors.py`
runs and writes the expected parquet; the starter analysis script runs and
produces both charts. `dvc repro` / `make run` have **not** yet been run
end-to-end in this repo (should work given the scripts run standalone, but
worth confirming DVC's jupytext stage wiring before the hackathon day).

## Known simplifications (by design, documented in the code/notebook too)

- Solar national capacity factor is an **unweighted** mean across NUTS2
  zones and PECD's 4 PV sub-technologies — ignores where PV capacity is
  actually concentrated. Wind onshore/offshore reuse `pecd-replication`'s
  already capacity-weighted national series.
- Installed capacity is a single rough national number per technology, not
  regionally resolved or time-varying.
- The battery model's "target output" is the fleet's own multi-year average
  generation, not real electricity demand. No round-trip losses, no MW
  power limit — only an MWh energy cap.
- The Dunkelflaute threshold (10% of installed capacity) flags a lot of
  ordinary low-wind nights, not just "newsworthy" events — flagged
  explicitly in the notebook as a first thing for a team to sanity-check
  and improve.

These are intentional — the point is a runnable starting point for a 3h
session, not a finished analysis. See `book/markdown/index.md` and the
notebook's own introduction for the same list aimed at hackathon
participants.

## Next Steps

- [ ] Run `dvc repro` (or `make run`) once to confirm the DVC stage wiring
  (jupytext execution, `_strip_jupytext_metadata.py`) works, not just the
  scripts standalone.
- [ ] Decide whether to push this to GitHub before the hackathon (currently
  local-only; `book/myst.yml` has no `github:` line and GitHub Pages isn't
  enabled).
- [ ] Optional, before hackathon day: pull in real SMARD demand
  (`~/research/pecd-replication/data/processed/target_panel.parquet` or
  `residual_load_inputs.parquet`) to give teams a real demand-coverage
  variant alongside the current average-output starter.
- [ ] Optional: swap the hand-entered installed capacity for a real
  MaStR-derived number, or add both and compare, if a team gets there.

## Lessons Learned

### 2026-09-17 — Initial setup

- Reusing already-processed data from a sibling project
  (`~/research/pecd-replication`) instead of re-running its CDS download
  pipeline avoided the API-key/12h-download friction entirely for this
  project's data stage — same approach the broader hackathon planning doc
  (`hackathon-vibe-coding-strom/PROJECT.md`) had already flagged as the
  right call for a short session.
- No ready-made "national" solar capacity-factor series existed upstream
  (unlike wind onshore/offshore, which already had one) — built a simple
  unweighted-mean version rather than redoing the proper capacity-weighted
  aggregation, to keep this repo's own setup light; documented as a known
  simplification rather than silently accepted.
