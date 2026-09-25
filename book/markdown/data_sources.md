---
title: "Data Sources"
---

# Where this data comes from

Everything under `data/input/` is copied, unmodified, from
[energy-data-hub](https://github.com/cgroll/energy-data-hub) — a shared
data-ingestion project (not part of this repo) that downloads and lightly
parses PECD, MaStR, SMARD, and region-geometry data for several related
projects. Copying it here means this repo has a working data starting
point right after cloning, no CDS or MaStR account needed. Because it's
just a copy, if you want to know exactly how a file was produced (the raw
download, the parsing, any unit conversions), the hub's own repository —
in particular `edh/pecd.py` and `edh/mastr.py` — is the authoritative
place to look, not this repo.

`data/input/` is **git-ignored, not committed** — it ships as part of the
repo checkout/archive you were given, not via git history.

Two related public sources, if you want to go further upstream than the
hub itself:
- **[PECD v4.2](https://cds.climate.copernicus.eu/datasets/sis-energy-pecd)**
  (Copernicus Climate Data Store) — the official capacity-factor and
  region-mask product this repo's weather data comes from.
- **[Marktstammdatenregister](https://www.marktstammdatenregister.de/MaStR/Datendownload)**
  (MaStR) — the German Federal Network Agency's public register of
  essentially every unit in the electricity and gas market. The full bulk
  export is multiple GB of XML; parsing it reliably typically goes via
  [open-mastr](https://github.com/OpenEnergyPlatform/open-MaStR), which is
  what the hub uses.

**Recommended viewing:** [this video](https://youtu.be/vS_A549w3Ss) walks
through linking MaStR register data to PECD's weather zones — exactly the
exercise Track A's data below is set up for.

**Not included at all:** SMARD generation and demand data. Both tracks
need it (Track A to compare against, Track B for residual load) — fetch
it yourself from the [SMARD download center](https://www.smard.de/home/downloadcenter/download-marktdaten),
so that step (what series, what resolution, how to align it with the
hourly PECD timestamps) is part of the exercise rather than pre-solved.

# Track B: national, ready-to-use capacity factors

`data/input/pecd/`:

- **`pecd_country_capacity_factors_simple_de.parquet`** — hourly national
  capacity factors for Germany, 1980-2025. Columns: `wind_onshore`,
  `wind_offshore`, `solar` (all in `[0, 1]`). No further processing
  needed — this is Track B's ready starting point.
- **`pecd_country_capacity_factors_simple.parquet`** — the same, for all
  ~53 PECD countries (wide, `(technology, country)` columns). Only useful
  if your team wants a cross-country comparison; Germany is the same data
  as the file above.

**Known simplification, worth knowing before you rely on it:** the solar
capacity factor in *both* files blends PECD's 4 PV sub-technologies
(industrial/commercial rooftop, residential rooftop, utility fixed-tilt,
utility tracking) using **Germany's own market mix as the weighting**,
applied to every country. For Germany this is a reasonable weighting; for
any other country in the all-Europe file, treat its solar series as
illustrative, not authoritative — a country with a very different
rooftop/utility split (e.g. Spain) will get a blend biased toward
Germany's mix. Wind (onshore area-weighted, offshore unweighted, from
PECD's own zone geometry) has no equivalent issue.

# Track A: raw ingredients for a validation exercise

Track A asks: does PECD's modeled capacity factor, combined with the
*real, time-varying* installed fleet, actually track observed grid
generation? That needs three things, all under `data/input/`, deliberately
**not pre-combined** — building the combination is the exercise:

## Zonal PECD capacity factors (`data/input/pecd/`)

- `pecd_wind_onshore_capacity_factors.parquet` — hourly, 2015-2025,
  columns `DE01`-`DE07` (Germany's 7 PEON onshore-wind zones).
- `pecd_wind_offshore_capacity_factors.parquet` — hourly, 2015-2025,
  columns `DE011_OFF` etc. (Germany's 6 PEOF offshore-wind zones).
- `pecd_solar_capacity_factors.parquet` — hourly, 2015-2025, MultiIndex
  columns `(technology, region)`: PECD's 4 PV sub-technology codes
  (`60`/`61`/`62`/`63`) × Germany's NUTS2 regions.

## PECD region masks (`data/input/pecd/`)

- `peon_region_mask.nc` / `peof_region_mask.nc` — rasterized
  zone-membership weights on a 0.25°×0.25° grid, **all of Europe** (not
  pre-cropped to Germany — filter `region` to values starting `"DE"`
  yourself, a one-line `xarray` selection). Dims: `(region, latitude,
  longitude)`; data variable `mask` is the fraction of that cell's area
  inside that region.

## MaStR unit-level records (`data/input/mastr/`, `data/input/regions/`)

- **`solar.parquet`** (~6.3M rows) — per-unit MaStR solar records.
  Columns include `unit_id`, `municipality_key` (a LAU/Gemeindeschlüssel
  code, not a NUTS code directly), `longitude`/`latitude` (present for
  only a small share of rows — solar mostly doesn't need them, see
  below), `net_capacity_kw`, `commissioning_date`, `final_shutdown_date`,
  `usage_sector`, `installation_type`, `technology`.
- **`solar_technical_detail.parquet`** — `main_orientation` and
  `main_orientation_tilt_bucket` per unit; join to `solar.parquet` via
  `unit_id`.
- **`wind.parquet`** (~43K rows) — per-unit MaStR wind records. Same core
  columns as solar, plus **`wind_onshore_or_offshore`**
  (`"Windkraft an Land"` / `"Windkraft auf See"` — the onshore/offshore
  split is already given directly, no derivation needed) and
  `sea_location` (which sea, offshore units only).
- **`lau_nuts_correspondence.parquet`** (`data/input/regions/`) — maps
  `municipality_key` → `nuts3_code`. Needed for solar (see below); wind
  doesn't need it since it has coordinates.

**Caveats worth knowing:** `commissioning_date` has some placeholder
1900-01-01 values (treat as unknown, not a real installation date);
`final_shutdown_date` is mostly missing, meaning still active, not
missing data; roughly 3% of wind units have no coordinates at all.

# Using Track A's data: the linking exercise

This repo deliberately stops before doing any of the following — building
it is the exercise (see the [video](https://youtu.be/vS_A549w3Ss) for a
worked walkthrough of the same steps):

**1. Assign each unit to a PECD zone.**
- *Solar → NUTS2*: join `solar.parquet.municipality_key` to
  `lau_nuts_correspondence.parquet` to get `nuts3_code`, then take its
  first 4 characters (NUTS codes are hierarchical by construction — a
  NUTS3 code's first 4 characters *are* its NUTS2 parent).
- *Wind → PEON/PEOF*: round each unit's `(longitude, latitude)` to the
  nearest 0.25° grid point in the matching region mask, then read that
  cell's zone weights. A cell can straddle more than one zone — split the
  unit's capacity proportionally rather than picking one "winning" zone.
  `wind.parquet`'s own `wind_onshore_or_offshore` column tells you which
  mask file to use, no separate derivation needed.

**2. Classify each solar unit into PECD's 4 technology codes** (60 =
industrial rooftop, 61 = residential rooftop, 62 = utility-scale fixed,
63 = utility-scale tracking):
- `installation_type == "Freiflächensolaranlage"` (ground-mounted) →
  utility-scale (62/63); everything else (rooftop, balcony) → rooftop
  (60/61).
- Within rooftop: `usage_sector == "Haushalt"` or missing → residential
  (61); any other named sector → industrial (60).
- Within utility-scale: tracked (`main_orientation == "nachgeführt"` or
  `main_orientation_tilt_bucket == "Nachgeführt"`, from
  `solar_technical_detail.parquet`) → tracking (63); otherwise → fixed
  (62).

**3. Turn per-unit events into a time-varying capacity series.** For any
given month, a unit counts as installed if `commissioning_date` is on or
before that month and (`final_shutdown_date` is missing or after it).
Summed by zone (and, for solar, by technology code) and month, this gives
the time-varying installed-capacity panel needed to combine with PECD's
zonal capacity factors.

**4. Combine and compare.** Capacity-weight each zone's PECD capacity
factor by that month's installed capacity, sum to a national
potential-generation series per technology (PV, wind onshore, wind
offshore), and compare against SMARD's observed per-technology grid
feed-in (fetched separately, see above). The gap between modeled
potential and observed generation is partly curtailment/redispatch (not
shipped here — interpreting the gap is part of the exercise), and partly
behind-the-meter solar self-consumption that never reaches the grid
connection SMARD meters (a self-consuming system's output is invisible to
SMARD regardless of curtailment).
