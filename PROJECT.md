# Project State

Tracks the current state, roadmap, and lessons learned for this project.
See [AGENTS.md](AGENTS.md) for structure/tooling conventions.

## Goal

Hackathon starter repo covering **both tracks** of `slides/hackathon-pecd.html`
(the actual public-facing overview of this hackathon — treat it as more
authoritative than older planning docs where they disagree, see the open
question below). Both tracks share one underlying dataset: Germany's
hourly PECD v4.2 capacity factors, official product (not a from-scratch
physics replication — see Lessons Learned, 2026-09-18). Teams get a
ready-to-use historical dataset — no CDS/MaStR account, no waiting on
downloads.

### Track B — Planning (Dunkelflaute + battery sizing)

Three escalating tasks:

1. **Baseline stress test** — take today's (roughly estimated) installed
   wind + solar capacity and the full historical weather record. How much
   Dunkelflaute (low-generation) risk is there? How do you even define/
   measure a Dunkelflaute event? How much energy is missing overall,
   relative to demand (residual load)?
2. **Capacity scaling** — vary the installed capacity (e.g. double wind
   and/or solar) and re-run the same stress test. How much does more
   installed capacity actually buy you?
3. **Battery storage** — add a battery and see how much better the
   installed capacity can be used (shifting midday solar output into the
   evening, etc.). Batteries are not expected to eliminate Dunkelflaute
   risk entirely — a good stretch question is how far batteries + extra
   capacity get you toward a *partial* target (e.g. 95%, not 100%,
   renewable coverage of demand).

Uses a **fixed, "today"** installed-capacity assumption (see
`hpsp/capacity_assumptions.py`) — no fleet history needed.

### Track A — Validation (does PECD match reality?)

Compare, per the slide's own framing:

- **Modeled**: official PECD capacity factors (zone-level: PEON onshore /
  PEOF offshore / NUTS2 solar) × the **time-varying** MaStR installed
  fleet (monthly snapshots by technology, not today's fixed number) →
  modeled generation. `pecdr.residual_load.potential_mw()` in
  `pecd-replication` already implements exactly this combination
  generically.
- **Observed**: SMARD's actual per-technology grid feed-in — which is,
  by construction, already post-congestion/curtailment.
- The task: compare modeled vs. observed and interpret the gap (partly
  curtailment). **Decided 2026-09-18:** we do not fetch or ship separate
  redispatch/curtailment data for this — building the "adjusted observed"
  correction the slide's kicker calls "the crux" is exactly the exercise,
  same "ingredients, not the answer" principle as everywhere else in this
  repo. This also drops redispatch data entirely from what needs
  preparing (see Next Steps) — a real scope reduction, not just a
  deferral.

Track A needs data Track B doesn't (time-varying, **zone-level** MaStR
capacity + PECD capacity factors, so teams build the modeled/potential
series themselves; SMARD *generation* actuals per technology) — Track B
needs data Track A doesn't (a fixed **national** capacity number, SMARD
*demand*). See Next Steps for the concrete file list for each.

**By design, this starter repo stops at data preparation for both
tracks.** No Dunkelflaute-threshold, residual-load, battery-dispatch, or
congestion-correction/comparison logic is pre-built — defining and
answering those is exactly what the tasks above ask teams to do. (See
[Next Steps](#next-steps) for where the repo still falls short of that
data-only target and what pre-built analysis needs to be removed to get
there.)

**Resolved 2026-09-18:** "Workstream 2" in the older
`~/research/hackathon-vibe-coding-strom/PROJECT.md` and "Track A" here are
the same thing — the slide deck is the more current description and takes
precedence where the two differ (that older doc itself may be worth
updating later, out of scope for this repo). Consequence: the older doc's
warning still applies — `residual_load_inputs.parquet` should **not** be
handed to Track A as-is, since it likely bakes in exactly the
congestion-adjustment (and/or capacity-weighting) step that's supposed to
be the exercise. Track A's shipped data should stop at the same
"ingredients, not the answer" point Track B already aims for: raw
time-varying, zone-level MaStR capacity, raw zone-level official PECD
CFs, raw SMARD per-tech generation + demand — no redispatch/curtailment
data (see Goal, Track A: decided not needed at all, not just deferred) —
the congestion correction and the modeled-vs-observed comparison are for
teams to build.

## Current State

Rebuilt 2026-09-18/19, replacing the 2026-09-17 setup described in Lessons
Learned below. **`dvc repro` runs clean end-to-end** (verified 2026-09-19;
`dvc status` reports everything up to date; `dvc.lock` regenerated from
scratch to drop stale entries from the old pipeline). Six pure-data
pipeline stages, all run against real data:

- `pipeline/01_download_pecd_capacity_factors.py` — CDS download, official
  PECD v4.2, wind onshore (PEON) / offshore (PEOF) / solar (NUTS2),
  1980-2025, chunked into 10-year requests (30 total) to stay under the
  CDS API's per-request cost limit. **Completed**: all 30 chunks
  downloaded, ~1.6 GB in `data/downloads/pecd/` (git-ignored).
- `pipeline/02_process_pecd_capacity_factors.py` — parses the raw zips into
  Germany-only zonal parquet, full 1980-2025 range (403,248 hourly rows —
  exactly 46 years including leap days, verified gap-free at the 10-year
  chunk boundaries). Build-only intermediate (`data/processed/_intermediate/`,
  git-ignored). Includes the empirically-verified 1-hour solar timestamp
  correction carried over from `pecd-replication`.
- `pipeline/03_prepare_mastr_track_a_inputs.py` — Track A: raw(ish) MaStR
  unit-level wind + solar records (6,269,286 rows, 36.4 MB, incl. the
  fields needed to classify solar units into PECD's 4 technology codes and
  `pv_category` for later self-consumption analysis) + cropped PEON/PEOF
  region masks (995 / 233 rows). See "Track A/B overlap" and "How raw is
  raw" in Lessons Learned for how this replaced an earlier, more
  pre-aggregated design.
- `pipeline/04_prepare_capacity_factors_national.py` — Track B: unweighted
  mean across zones (not capacity-weighted, see "Track A/B overlap" in
  Lessons Learned) → `capacity_factors_de_national.parquet`, 403,247 hourly
  rows, 1980-2025 (one hour short of the full range at the very end —
  an expected, negligible artifact of the solar timestamp shift landing
  exactly on the last hour of 2025-12-31; not a bug). 3 PEOF zones with no
  CF coverage (`DE013_OFF`/`DE014_OFF`/`DE015_OFF`) correctly dropped from
  both sides of the mean, not just silently down-weighted.
- `pipeline/05_prepare_capacity_factors_zonal.py` — Track A: same zonal CF,
  sliced to 2015-2025 (96,432 rows wind / 96,431 solar — same one-hour
  edge effect on solar).
- `pipeline/06_prepare_demand_and_generation.py` — splits
  `pecd-replication`'s `target_panel.parquet` into
  `demand_de_national.parquet` (Track B, 68,539 rows) and
  `generation_de_by_technology.parquet` (Track A, same range).
- `hpsp/capacity_assumptions.py` — refreshed to the MaStR register snapshot
  (wind onshore 69.75 GW, wind offshore 10.86 GW, solar 111.21 GW, as of
  2026-06/07), replacing the old hand-rounded 63/9/100 GW estimate.
- `dvc.yaml` / `.gitignore` / `AGENTS.md` — six stages wired up; final
  Track A/B parquet outputs declared `cache: false` (git-tracked directly);
  raw downloads and the zonal intermediate keep the default
  DVC-cache-and-gitignore behavior.

All 9 final `data/processed/*.parquet` deliverables exist, pass basic
sanity checks (no unexpected NaNs outside the documented PEOF gap, values
in `[0, 1]` for capacity factors, row counts match expected hour counts),
and total ~107 MB — comfortably under GitHub's 100 MB *per-file* limit
(largest single file: `capacity_factors_zonal_solar.parquet` at 51.6 MB).

**Not yet done:** none of this has been `git add`/committed yet (the
rewrite touched pipeline scripts, `hpsp/`, `dvc.yaml`, `.gitignore`,
`pyproject.toml`, and all of `data/processed/`) — ask before committing,
per this session's standing git-safety rule. `book/markdown/index.md` and
`README.md`'s task framing were updated earlier in the redesign but should
get one more pass once the data is actually committed, to remove any
remaining "not yet wired up" language now that it is.

## Known simplifications in the current (pre-redesign) code

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
  ordinary low-wind nights, not just "newsworthy" events.
- History is 2019-2025 only, and there is no demand/residual-load data at
  all yet — see Next Steps, both are addressed there.

## Next Steps

Gap between the current state above and the target picture in Goal,
roughly in priority order:

- [ ] **Switch all three technologies to the official PECD product**,
  replacing wind's current "own ERA5 replication" source
  (`wind_onshore_full_year_cf.parquet` / `..._offshore...`) as well as
  solar's unweighted-mean placeholder. **Decided 2026-09-18**, confirmed
  after reading the slide deck: neither Track A nor Track B needs
  `pecd-replication`'s bias-corrected physics replication (own ERA5 →
  GWA2 bias correction → per-plant power curve, ~10 pipeline stages,
  1.3 GB raw ERA5) — that was that project's own research exercise,
  orthogonal to both hackathon tracks. Both tracks only need the plain
  official product: `pecd_wind_onshore_capacity_factors.parquet` (PEON),
  `pecd_wind_offshore_capacity_factors.parquet` (PEOF),
  `pecd_solar_capacity_factors.parquet` (NUTS2). **Two different year
  ranges needed per track (decided 2026-09-18, see Lessons Learned for
  the CDS-availability check behind this):**
  - **Track B: 1980-2025.** Verified directly against the CDS API
    (`sis-energy-pecd` catalogue `constraints.json`) that PECD v4.2
    historical ERA5-reanalysis capacity factors are *listed* as available
    all the way back to 1950 for all three technologies. Picked 1980 over
    the full 1950 as a practical cutoff: pre-1979 ERA5 predates the
    satellite era and is markedly less constrained by observations, not
    reliable enough for a Dunkelflaute stress test. **Correction,
    2026-09-18 (later the same day):** the CDS API rejected a single
    46-year request outright ("cost limits exceeded") — see the download
    entry in Lessons Learned. That means `pecd-replication`'s 11-year
    2015-2025 choice may well have been bumping up against this same
    per-request limit, not the arbitrary choice this section originally
    claimed; downloading in 10-year chunks (implemented in pipeline/01)
    works around it either way. **This is not already on disk** anywhere
    (`pecd-replication` only has 2015-2025) — needs an actual fresh CDS
    download for 1980-2014 (or the full 1980-2025 range, chunked), not
    just a reuse-only pipeline step like everything else so far. Estimated
    download size: ~1.7 GB raw (all-Europe, zone-level, all 3
    technologies) based on the 2015-2025 zips (~410 MB total) scaled by
    the ~4.2x more years — small once aggregated down to a national
    series, and only needed once, by whoever preps this repo's data (not
    by hackathon participants).
  - **Track A: 2015-2025 stays as-is** (already downloaded, no new work).
    Extending it back to 1980 would be wasted effort: Track A's usable
    range is bounded by the time-varying MaStR capacity panels (start
    2015-01) and by SMARD actuals (`target_panel.parquet` starts
    2018-09-30) regardless of how far back the capacity factors go — more
    weather history before 2015 has nothing to combine with for that
    track.
  
  **Superseded 2026-09-18 (later the same day) — see "Track A/B overlap"
  in Lessons Learned:** originally planned to capacity-weight *both*
  tracks' national/zonal aggregation using the same small MaStR
  zone-month panels. Reversed for Track B only, once it became clear that
  would mean pre-solving, inside Track B's own data prep, the exact
  "fetch and correctly use real MaStR data" exercise Track A is meant to
  be about. **Track B now uses a plain, unweighted mean across zones**
  (`pipeline/04`) — no MaStR zone data involved at all. Track A still
  needs the small MaStR zone-month panels (`pipeline/03`), though exactly
  how raw vs. pre-joined that data should be is now its own open question
  (see below).
  - Download script (still needed, unaffected by the above):
    adapted from `pecd-replication/pipeline/16_download_pecd_capacity_factors.py`
    into this repo's `pipeline/01_download_pecd_capacity_factors.py` (had
    to add year-chunking — see the download-chunking Lessons Learned entry).
- [ ] **Prepare Track B's data** — national, fixed-capacity, long history:
  - `data/processed/capacity_factors_de_national.parquet`: official-PECD-based,
    **unweighted mean across zones** (not capacity-weighted — see the
    superseded note above), **1980-2025** (requires the fresh CDS download
    noted above — not available from existing on-disk data).
  - `data/processed/demand_de_national.parquet` (new): the `load` column
    of `pecd-replication`'s `target_panel.parquet` — verified 2026-09-18
    to be an unmodified, inner-joined raw SMARD download (see
    `pipeline/14_build_target_panel.py`), not derived/adjusted. Native
    range 2018-09-30 through 2026-08-04 (corrects an earlier, wrong note
    here that said 2019-2025 — that range belongs to a different file,
    `residual_load_inputs.parquet`). **Decided 2026-09-18:** ship at this
    native range rather than truncating to match the capacity factors;
    document the resulting overlap (2018-09-30 – 2025-12-31) for
    residual-load math.
- [ ] **Prepare Track A's data** — zonal, time-varying, no redispatch data
  needed (see Goal). Verified 2026-09-18 that zone codes line up directly,
  no remapping step needed:
  - `data/processed/capacity_factors_zonal.parquet` (new): the raw
    zone-level official PECD product, as downloaded —
    `pecd_wind_onshore_capacity_factors.parquet` (7 PEON zones, columns
    `DE01`-`DE07`), `pecd_wind_offshore_capacity_factors.parquet` (6 PEOF
    zones, `DE011_OFF` etc.), `pecd_solar_capacity_factors.parquet`
    (NUTS2 × 4 PECD sub-technologies, `DE11` etc.), 2015-2025.
  - **Decided 2026-09-18, option (a):** ship raw(ish) MaStR unit-level
    data, not a pre-aggregated zone-month panel — see "How raw is raw"
    in Lessons Learned for why the geospatial join turned out much
    cheaper than first assumed (no shapefiles/GIS libraries needed).
    `pipeline/03_prepare_mastr_track_a_inputs.py` produces:
    - `mastr_units_wind_solar.parquet`: per-unit MaStR records (solar +
      wind, ~6.27M rows) — technology, region_code (MaStR's own
      NUTS3-like code), capacity_mw, commissioning_date,
      final_shutdown_date, longitude, latitude, plus (solar-only)
      installation_type, usage_sector, main_orientation,
      main_orientation_tilt_bucket — everything needed to classify a
      solar unit into PECD's 4 technology codes (60/61/62/63), see
      pipeline/03's docstring for the rule — and pv_category
      (full_feed_in / self_consumption_no_storage /
      self_consumption_with_storage / unknown). **Added 2026-09-18,
      after the fact:** `pv_category` is a different axis (feed-in/
      self-consumption behavior, not PECD technology), not needed for
      Track A's hackathon scope, but essentially free to carry along
      (one more low-cardinality category, +~1 MB) for later
      behind-the-meter/self-consumption work — `pecd-replication` already
      has a worked example of what that looks like (regression-estimated
      self-consumption coefficient, with `full_feed_in` capacity as a
      built-in falsification check, since that category is legally
      required to have zero self-consumption). Out of scope to build
      here, just worth not throwing away the column that enables it
      later. **Decided 2026-09-18:** the
      last two orientation columns live in a *separate* raw MaStR table
      in the sibling repo; joined in here (via `unit_id`, then dropped)
      rather than shipping both raw tables with `unit_id` intact for
      teams to join themselves — the join is plumbing, not the exercise,
      and keeping `unit_id` around would have cost ~40 MB for no
      pedagogical benefit (checked empirically: `unit_id` alone, being
      fully unique across 6.27M rows, is what makes a MaStR extract
      expensive). Final size: 36.4 MB (incl. `pv_category`), comfortably under GitHub's 100 MB
      per-file limit — no Git LFS or external hosting needed.
    - `pecd_region_mask_{peon,peof}.parquet`: PECD's region masks,
      cropped from full-Europe rasters (~85 MB each) down to Germany's
      nonzero-weight cells only (995 / 233 rows) — (zone_id, latitude,
      longitude, weight) lookup tables.
    Left as Track A's own exercise, deliberately not done here: splitting
    "wind" into onshore/offshore (MaStR flags offshore with a
    "DEZZ"-prefixed region_code), mapping solar's region_code to its
    NUTS2 parent (first 4 characters), snapping a wind unit's coordinate
    to its nearest 0.25° grid cell and reading that cell's fractional
    zone weights from the mask table, classifying each solar unit into
    PECD's 4 technology codes, and the month-by-month
    commissioning/shutdown aggregation itself.
  - `data/processed/generation_de_by_technology.parquet` (new): the `pv` /
    `wind_onshore` / `wind_offshore` columns of the same `target_panel.parquet`
    used for Track B's demand — one shared source file, two derived
    outputs (see file-layout decision below).
  - Explicitly **not** shipping: any redispatch/curtailment data, and not
    `residual_load_inputs.parquet` (see the resolved open question above).
- [ ] **File layout, decided 2026-09-18:** one shared `data/processed/`
  directory (not per-track subfolders), track association conveyed by
  filename (`_national`/`_de_national` for Track B, `_zonal`/`by_zone` for
  Track A) — matches the repo's existing flat layout, avoids duplicating
  `target_panel.parquet`-derived data under two paths.
- [ ] **Refresh the installed-capacity reference values.** The current
  hand-entered numbers (63 / 9 / 100 GW) are noticeably below the MaStR
  bulk-dump snapshot in `~/research/mastr-power-capacities-germany`
  (≈69.75 / 10.86 / 111.5 GW wind onshore / offshore / solar, register
  state 2026-07). Worth citing that snapshot (with its as-of date) as the
  default instead of the rougher public-reporting estimate, while keeping
  it clearly labelled as a fixed, adjustable default rather than ground
  truth. SMARD itself is a demand/generation source, not an installed-
  capacity lookup — MaStR is the right reference to point teams at for
  "what is actually installed today."
- [ ] **Remove the pre-built analysis**
  (`pipeline/02_dunkelflaute_battery_starter.py`, its DVC stage, the
  generated notebook, and the two output images). It already computes
  Dunkelflaute event statistics and a battery sensitivity curve — exactly
  what Tasks 1 and 3 ask hackathon teams to build themselves. **Decided
  2026-09-18: delete it outright** (not relocate to an appendix) — the
  repo should ship data only.
- [ ] **Ship (but don't run by default) a CDS download + NUTS→national
  aggregation pipeline**, adapted from `pecd-replication`'s
  `pipeline/16_download_pecd_capacity_factors.py`,
  `10_compute_wind_onshore_full_year.py` /
  `32_compute_wind_offshore_full_year.py`, and a new solar equivalent using
  `pecdr/capacity_weighting.py`. Purpose: let anyone with their own
  `~/.cdsapirc` reproduce this repo's data from scratch, or adapt it for a
  different country — without that path being required for the hackathon's
  default `dvc repro`.
- [ ] Update `book/markdown/index.md` and `README.md` once the above lands,
  so the book's own "About" text matches the data actually shipped (this
  pass already updated the task framing, but the data description there
  still says 2019-2025 / no demand / hand-entered capacity).
- [ ] Run `dvc repro` (or `make run`) once end-to-end to confirm the DVC
  stage wiring (jupytext execution, `_strip_jupytext_metadata.py`) still
  works after the stage changes above.
- [ ] Decide whether to push this to GitHub before the hackathon (currently
  local-only; `book/myst.yml` has no `github:` line and GitHub Pages isn't
  enabled).

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

### 2026-09-18 — Target-picture redesign

- Reframed the Goal as three explicit, escalating tasks (baseline stress
  test → capacity scaling → battery storage) instead of one open-ended
  question, and made explicit that this repo should ship **data only** —
  the existing `pipeline/02_dunkelflaute_battery_starter.py` pre-builds
  the answer to Tasks 1 and 3, which now reads as a design mistake to
  unwind rather than a feature, once the tasks are named explicitly.
- Surveyed sibling repos before deciding anything: `pecd-replication`
  already has 2015-2025 official-PECD data on disk (longer than this
  repo's 2019-2025 window, no new download needed) and reusable
  capacity-weighting code for solar that just was never called from here;
  `mastr-power-capacities-germany` has materially higher capacity numbers
  than this repo's hand-typed ones; the broader hackathon PROJECT.md
  confirms MaStR (not SMARD) is the right reference for installed
  capacity, and flags a separate, non-overlapping workstream already
  responsible for time-varying fleet reconstruction — this repo should
  stick to a fixed present-day capacity assumption.
- Decided residual load / demand coverage is central enough to the target
  picture that pulling in SMARD demand can't stay an "optional, if there's
  time" item anymore — moved it into Next Steps as a required data output,
  with the 2015 vs. 2019 coverage mismatch flagged as an open decision
  rather than silently resolved.

### 2026-09-18 — Slide deck surfaces a second track, changes the data-source call

- User added `slides/hackathon-pecd.html`, the actual public-facing
  overview of the hackathon, describing two tracks: Track A (validate
  PECD against SMARD-observed, congestion-corrected grid power, using a
  time-varying MaStR fleet) and Track B (the planning workstream this repo
  already targeted). Decided to cover both tracks in this one repo rather
  than treating Track A as someone else's problem.
- Reading the slide's own description of Track A's method (official PECD
  CF × MaStR fleet snapshots, no mention of a physics replication) was
  the confirming evidence for the PECD-source decision above: not just
  Track B, but *neither* track needs `pecd-replication`'s bias-corrected
  own-physics replication. That machinery turned out to be that project's
  own internal research question (does a from-scratch physics model beat
  official PECD?), not a dependency of either hackathon track — good
  reminder to check what a sibling repo's output actually *is* before
  reusing it, rather than assuming the fanciest-looking available file is
  the right one.
- Found that `pecd-replication`'s `pecdr.residual_load.potential_mw()`
  already implements Track A's exact "modeled" formula (capacity-weighted
  CF × time-varying zone capacity, undone back into absolute MW) — a
  reminder that this sibling repo tends to have already built the generic
  piece needed, just not always wired into a persisted, ready-to-use
  national file.
- Surfaced (but did not resolve) a real tension: an older, broader
  planning doc explicitly warns against using
  `residual_load_inputs.parquet` for a "Workstream 2 fleet reconstruction"
  because it pre-empts that exercise's result — but it's not yet clear
  whether "Workstream 2" there is the same thing as the slide's "Track A"
  (which takes the fleet as *given*, not something to reconstruct) or a
  third, different exercise. Recorded as an open question rather than
  guessing, since picking wrong would either hand Track A participants a
  pre-solved answer or block them on data that was actually fine to use.

### 2026-09-18 — Concrete data plan for both tracks, verified file-by-file

- Resolved the open question from the previous session: "Workstream 2" in
  the older broader planning doc and "Track A" here are the same thing,
  slide takes precedence.
- User's instinct that Track A needs **zone-level**, not national, PECD
  data (to combine with MaStR zone-level capacity into a potential series)
  checked out — and led to a genuine scope reduction, not just an
  addition: since the congestion/curtailment correction is explicitly part
  of what teams build (not something we ship pre-computed), Track A needs
  *no* redispatch/curtailment data at all. Earlier sessions had this as an
  open, possibly-substantial investigation; it's now just "not needed."
- Verified concretely (not assumed) that the pieces fit together:
  zone codes in the official PECD product (`DE01`...`DE07` PEON,
  `DE011_OFF` etc. PEOF, `DE11` etc. NUTS2) match the region codes in the
  small MaStR monthly capacity panels directly — no remapping needed. One
  trap found and avoided: `mastr-power-capacities-germany`'s own NUTS2
  panel uses MaStR's own solar categories (full-feed-in/self-consumption),
  not PECD's 4 sub-technology codes — the correctly-mapped file for
  combining with PECD solar data is `pecd-replication`'s own
  `solar_capacity_by_nuts2_month.parquet`, which looks similar but isn't
  the same thing.
- Also verified `target_panel.parquet`'s exact provenance (read
  `pipeline/14_build_target_panel.py`): a plain inner join of raw
  per-series SMARD downloads, no adjustment — confirms it's safe to use
  directly for both Track A's generation actuals and Track B's demand,
  and corrected an earlier wrong note in this file about its date range
  (2019-2025, which actually belongs to `residual_load_inputs.parquet`;
  `target_panel.parquet`'s real range is 2018-09-30 to 2026-08-04).

### 2026-09-18 — Track B's history extended to 1980, checked against CDS directly

- User pushed back on the 2015 start date for Track B: no obvious reason
  to inherit `pecd-replication`'s own cutoff rather than going back
  further, given a weather-extremes stress test benefits from more years.
  Rather than guess whether 2015 was a real data limit, queried the CDS
  API directly (`https://cds.climate.copernicus.eu/api/catalogue/v1/collections/sis-energy-pecd`
  → `constraints.json`): PECD v4.2 historical ERA5-reanalysis capacity
  factors for wind onshore/offshore/solar are listed as available for
  **1950-2025**, confirming 2015 was `pecd-replication`'s own arbitrary
  choice, not a platform limit.
  - Also measured actual raw download sizes from the zips already on disk
    (2015-2025: ~410 MB across all 3 technologies, all of Europe,
    zone-level) to answer the "is this too much data" question with a
    number instead of a guess: linearly scaled, even the full 1950-2025
    range would be single-digit GB, not a storage concern.
- Settled on **1980**, not the full 1950, as Track B's new start year:
  ERA5 before the 1979 satellite era is materially less
  observation-constrained, a real quality concern for a stress-test
  dataset even though the CDS API happily serves it.
- Consequence worth remembering: this is the first data change in this
  project that actually **requires running a fresh CDS download**
  ourselves (1980-2014 isn't on disk anywhere) rather than only
  reusing/reshaping already-downloaded sibling-repo output — changes the
  "no external account needed" story for *building* this repo's data
  (still true for hackathon *participants*, who only ever see the
  already-processed result).
- Track A's range deliberately stays at 2015-2025: its ceiling is set by
  the time-varying MaStR capacity panels (2015-01 onward) and SMARD
  actuals (2018-09-30 onward), not by capacity-factor availability, so
  extending its weather history further back would just be unusable
  extra download volume.

### 2026-09-18 — Implementation session: six pipeline stages built, one real download bug found and fixed

- Built and wired up all six pipeline stages from the data plan
  (`01_download_pecd_capacity_factors.py` through
  `06_prepare_demand_and_generation.py`), removed the old
  `pipeline/01_prepare_capacity_factors.py` and
  `pipeline/02_dunkelflaute_battery_starter.py` (+ its notebook/images),
  refreshed `hpsp/capacity_assumptions.py` to the MaStR snapshot, and
  rewired `dvc.yaml`/`.gitignore`/`AGENTS.md` for the `cache: false`
  git-tracking decision. `pipeline/03` and `06` (no CDS dependency) ran
  and verified clean on the first try.
- Before committing to the full download, smoke-tested with a single
  small CDS request (wind offshore, 2024 only) — worth doing: it
  surfaced a real data-quality issue, not just a plumbing check. Three
  PEOF zones (e.g. `DE013_OFF`) are entirely `NaN` in PECD's
  capacity-factor product for that year despite carrying nonzero MaStR
  capacity. Naively summing `(cf * weights)` with plain `.sum()` would
  have silently biased the weighted national average low (weight counted
  in the denominator, zero contributed to the numerator via pandas'
  skip-NaN summation). Fixed in `pipeline/04` by dropping any zone with
  no CF coverage from *both* sides of the ratio, with a printed warning —
  the kind of bug that would have shipped a plausible-looking but wrong
  number if the smoke test had been skipped.
- The full 1980-2025 request then failed immediately and non-transiently:
  CDS returned `403 cost limits exceeded, your request is too large` on
  the very first (solar) call. Root-caused by comparing to
  `pecd-replication`'s working 11-year request — not obviously "11 is
  fine, 46 is 4x too much" without knowing the exact cost formula, so
  picked a conservative 10-year chunk size (`pipeline/01`'s
  `CHUNK_SIZE_YEARS`) rather than searching for the exact boundary.
  Consequence: `hpsp/paths.py`'s zip-path helper and `pipeline/02`'s
  loader both had to become chunk-aware (glob + concat instead of one
  file per technology) — a real example of a "verified" assumption
  (**"no per-year looping is needed", stated confidently in pipeline/01's
  original docstring after the small-request test passed**) turning out
  to only hold at small scale. Also revises this file's own earlier claim
  that pecd-replication's 2015 start was "arbitrary" — see the correction
  in Goal, Track B, above.
- Process-management lesson, not a data one: a background download
  launched via `nohup ... & disown` inside a foreground Bash call is
  invisible to the harness's own completion tracking — a `pgrep -f
  <script name>` health-check in a companion Monitor loop then
  self-matched the Monitor's own shell command line (which contains that
  same string as literal text) and reported "still running" forever,
  even after the real process had already crashed. Fixed by re-running
  the actual long command directly under `Bash(..., run_in_background:
  true)` instead, so the harness tracks the real process and notifies on
  its actual exit — simpler and correct, should have been the first
  approach rather than a manual `nohup`/`Monitor` combination.

### 2026-09-18 — Track A/B overlap: Track B's "proper" weighting was accidentally Track A's exercise

- While the download ran in the background, user asked a sharp question:
  Track B's plan (weight PECD zones by real, MaStR-derived capacity to
  get a good national series) is mechanically the same thing Track A is
  supposed to teach — if Track B's data prep already does that correctly,
  what's left for Track A to build? Confirmed this was real, not just a
  superficial mechanics overlap.
- User then refined what Track A's core lesson should actually be: less
  about the time-varying-vs-fixed distinction (which is what the original
  slide-derived framing emphasized), more about teams *fetching and
  correctly using real MaStR data themselves* — closer to the project's
  founding tension (this repo exists specifically to let teams skip the
  ~12 GB MaStR setup cost) than to the slide's "congestion correction is
  the crux" framing. Checked how raw "raw" could realistically go:
  `capacity_events.parquet` (unit-level MaStR extract, 8.9M rows all
  technologies, 6.2M of those solar alone since every rooftop PV system
  is its own MaStR unit) uses MaStR's own Kreis-level `region_code`, not
  PECD's PEON/PEOF/NUTS2 zones — genuinely raw MaStR data would require a
  geospatial join against PECD zone masks this repo has no infrastructure
  for yet, adding a GIS task on top of Track A's other work. Recorded as
  an open (a)/(b) question in Next Steps rather than picking one, since
  it changes how much building remains and is a real hackathon-difficulty
  calibration call.
- Resolved the immediate conflict without waiting for that open question:
  **Track B's national aggregation (`pipeline/04`) now uses a plain,
  unweighted mean across zones**, not the MaStR-capacity-weighted version
  originally planned — removing any real-MaStR-data dependency from
  Track B entirely. `hpsp/capacity_assumptions.py`'s single national GW
  figure stays MaStR-sourced (that's a cited fact, not a shared
  methodology, so no overlap). `pipeline/03`'s already-aggregated
  zone-month panels remain in the repo as Track A's current placeholder
  input, but are explicitly flagged as possibly too pre-processed pending
  the (a)/(b) decision. `dvc.yaml`'s `prepare_capacity_factors_national`
  stage no longer depends on `prepare_capacity_weights`.
- General lesson: building the "more correct" version of something isn't
  automatically the right call in a repo that's teaching two different
  things side by side — here, fixing a known simplification (unweighted
  mean) for Track B would have been actively counterproductive once a
  second track exists whose whole point is teaching that exact fix.

### 2026-09-18 — How raw is raw: the geo-join turned out to be cheap

- Before picking between the (a)/(b) options left open above, user asked
  to actually read the geo-join code in `mastr-power-capacities-germany`
  rather than estimate its difficulty from a distance — good instinct,
  since the estimate had been wrong. Findings: no shapefiles, no
  polygon-intersection at runtime, and specifically **no postal-code
  lookup** (a guess worth explicitly ruling out). The real mechanism:
  - Solar → NUTS2 is a pure string operation: a German NUTS3-like code's
    first 4 characters *are* its NUTS2 parent (NUTS codes are
    hierarchical by construction).
  - Wind onshore/offshore split is a string check: MaStR marks offshore
    units with a "DEZZ"-prefixed `region_code`.
  - Wind → PEON/PEOF zone is the only step needing coordinates, and even
    that is just: round a unit's (lon, lat) to its nearest 0.25° grid
    index (`nearest_grid_index`, 4 lines of numpy), then look up that
    cell's precomputed fractional zone-membership in PECD's own "region
    mask" product (a rasterized NetCDF Copernicus/ECMWF already
    publishes) and fractionally split the unit's capacity across zones
    accordingly. `fractional_zone_weights()` in that repo is ~35 lines
    including the rare border-cell fallback (nearest zone by weighted
    centroid). All the actual GIS work (turning zone polygons into a
    per-cell coverage raster) was already done once by Copernicus when
    they built the mask product — nothing left to "join" against a
    shapefile at request time.
  - This directly resolved the (a)/(b) question in favor of (a): shipping
    genuinely raw MaStR units is not the scope-creep it looked like from
    a distance, since the one geospatial step is a small, self-contained
    numpy lookup, not a GIS subsystem.
- Implemented as `pipeline/03_prepare_mastr_track_a_inputs.py` (replacing
  the old `03_prepare_capacity_weights.py`): filters MaStR's 8.9M-row,
  all-technology `capacity_events.parquet` down to solar + wind (~6.27M
  rows), and crops PECD's two ~85 MB full-Europe region-mask NetCDFs down
  to Germany-only, nonzero-weight tables (995 / 233 rows — the cropping
  itself is pure data-volume housekeeping, not part of the exercise, same
  reasoning as filtering PECD zone timeseries to Germany elsewhere in
  this repo).
- Caught before committing anything: the filtered unit-level extract was
  125 MB as first written — over GitHub's 100 MB per-file push limit,
  which would have silently broken "push this repo to GitHub" the moment
  anyone tried it. Root cause was avoidable, not inherent to the data:
  `unit_id` is fully unique across 6.27M rows (compresses to nothing) and
  isn't needed for a zone/month capacity aggregation anyway; `technology`/
  `region_code` were plain strings instead of `category` dtype. Dropping
  `unit_id` + categoricals + zstd (over the default snappy) compression
  brought it to 37 MB. Worth checking output file sizes against that
  100 MB ceiling as a matter of course whenever a `cache: false` output
  is unusually large, not just when something already feels big.
