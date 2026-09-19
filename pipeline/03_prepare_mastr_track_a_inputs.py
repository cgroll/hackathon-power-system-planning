"""Prepare Track A's raw(ish) MaStR ingredients: per-unit wind/solar
capacity records (including the raw fields needed to classify solar units
into PECD's 4 PV technology codes), plus small PECD region-mask lookup
tables for assigning a wind unit's (longitude, latitude) to its PEON/PEOF
zone.

Pure data script -- no charts. Deliberately does *not* do the zone-join,
the solar-technology classification, or the month-by-month aggregation --
those are Track A's own exercise (see PROJECT.md, 2026-09-18: "Track A/B
overlap", and the follow-up decisions on how raw Track A's MaStR data
should be). This script only:

  1. Filters MaStR's full unit-level `capacity_events.parquet` (all
     technologies, 8.9M rows) down to solar + wind, keeping the columns
     needed to do a zone-join and a commissioning/shutdown-date
     aggregation.
  2. Joins in `installation_type`/`usage_sector`/`pv_category` (already in
     `capacity_events.parquet`) plus `main_orientation`/
     `main_orientation_tilt_bucket` from a *separate* raw MaStR table
     (`solar_technical_detail.parquet`, joined via `unit_id`) -- together
     the first three (not `pv_category`) are exactly what's needed to
     classify each solar unit into PECD's 4 technology codes (60/61/62/63),
     see pipeline/02's docstring for what those mean. `pv_category` is a
     different axis entirely (full feed-in vs. self-consumption, with or
     without a battery) -- not needed for the hackathon's Track A exercise,
     but cheap to carry along (one more low-cardinality category) for
     later behind-the-meter/self-consumption analysis (see PROJECT.md,
     2026-09-18). The join itself is just relational plumbing (not part
     of the exercise, same reasoning as the mask-cropping below), so it
     happens here and `unit_id` is dropped afterwards -- shipping both raw
     tables separately with `unit_id` intact so teams could join them
     themselves would have cost ~40 MB extra for no pedagogical benefit
     (checked empirically 2026-09-18: `unit_id` alone is what makes a
     MaStR extract expensive, since it's fully unique and barely
     compresses -- see also the size note below).
  3. Crops PECD's PEON/PEOF region masks (full-Europe rasters, ~85 MB
     each) down to a small, Germany-only, nonzero-weight-only lookup
     table -- pure data-volume housekeeping, not part of the exercise
     (nobody learns something by cropping a NetCDF's spatial extent; the
     interesting part is what you do with the cropped table).

What's *not* done here, on purpose -- this is Track A's job:
  - Assigning each wind unit to a PEON/PEOF zone: snap its coordinate to
    the nearest 0.25-degree grid cell, then read that cell's fractional
    zone weights from the mask table below (a cell can straddle more than
    one zone).
  - Splitting MaStR's single "wind" technology into onshore/offshore --
    MaStR marks offshore units with a "DEZZ"-prefixed `region_code`.
  - Mapping solar's `region_code` (NUTS3-like) up to PECD's NUTS2 zones --
    the first 4 characters of a German NUTS code *are* its NUTS2 parent,
    a string operation, not a spatial join.
  - Classifying each solar unit into PECD's 4 technology codes from
    `installation_type`/`usage_sector`/`main_orientation`/
    `main_orientation_tilt_bucket` (the rule: ground-mounted ->
    utility-scale, split fixed/tracking by orientation; otherwise
    rooftop, split residential/industrial by usage sector).
  - Turning per-unit commissioning/shutdown dates into a monthly
    zone-capacity panel.

Requires ~/research/mastr-power-capacities-germany's already-processed
`capacity_events.parquet`, its raw `solar_technical_detail.parquet`, and
PEON/PEOF region-mask NetCDFs -- that repo's own pipeline built these from
the ~12 GB MaStR bulk dump and a CDS mask download respectively;
re-running either from scratch is exactly the setup cost this project
avoids. If that repo isn't available (e.g. a different machine), this
raises a clear FileNotFoundError.
"""

import os

import pandas as pd
import xarray as xr

from hpsp.paths import ProjPaths

MASTR_DOWNLOADS = "/home/chris/research/mastr-power-capacities-germany/data/downloads/pecd"
MASTR_PROCESSED = "/home/chris/research/mastr-power-capacities-germany/data/processed"
MASTR_UNITS_RAW = "/home/chris/research/mastr-power-capacities-germany/data/downloads/mastr_units_raw"

RELEVANT_TECHNOLOGIES = ["solar", "wind"]
UNIT_COLUMNS = [
    "unit_id", "technology", "region_code", "capacity_mw",
    "commissioning_date", "final_shutdown_date", "longitude", "latitude",
    "installation_type", "usage_sector", "pv_category",
]
SOLAR_DETAIL_COLUMNS = ["unit_id", "main_orientation", "main_orientation_tilt_bucket"]
CATEGORICAL_COLUMNS = [
    "technology", "region_code", "installation_type", "usage_sector", "pv_category",
    "main_orientation", "main_orientation_tilt_bucket",
]

# Generous bounding box around Germany -- just to shrink the shipped file,
# not for precision: the actual zone assignment uses the mask's own
# per-cell weights, not this box.
LAT_RANGE = (56, 46)
LON_RANGE = (4, 16)


def _require(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Expected source file not found: {path}\n"
            "This script reuses already-processed MaStR output from "
            "~/research/mastr-power-capacities-germany instead of "
            "re-processing the ~12 GB MaStR bulk dump. See PROJECT.md for "
            "details."
        )
    return path


def _crop_region_mask(nc_path: str) -> pd.DataFrame:
    ds = xr.open_dataset(nc_path)
    de_zones = sorted(z for z in ds["region"].values.tolist() if str(z).startswith("DE"))
    mask = ds["mask"].sel(region=de_zones, latitude=slice(*LAT_RANGE), longitude=slice(*LON_RANGE))
    df = mask.to_dataframe(name="weight").reset_index()
    ds.close()
    return df[df["weight"] > 0].rename(columns={"region": "zone_id"}).reset_index(drop=True)


def main() -> None:
    paths = ProjPaths()
    paths.ensure_directories()

    events = pd.read_parquet(_require(f"{MASTR_PROCESSED}/capacity_events.parquet"), columns=UNIT_COLUMNS)
    units = events[events["technology"].isin(RELEVANT_TECHNOLOGIES)].copy()

    detail = pd.read_parquet(_require(f"{MASTR_UNITS_RAW}/solar_technical_detail.parquet"), columns=SOLAR_DETAIL_COLUMNS)
    n_before = len(units)
    units = units.merge(detail, on="unit_id", how="left")
    assert len(units) == n_before, "join must not change row count"

    # unit_id has done its job (linking the two source tables) and is
    # dropped now -- see module docstring for why shipping it would be
    # expensive for no pedagogical benefit.
    units = units.drop(columns=["unit_id"])
    for col in CATEGORICAL_COLUMNS:
        units[col] = units[col].astype("category")

    units.to_parquet(paths.mastr_units_wind_solar, compression="zstd")
    print(
        f"Saved {len(units):,} MaStR units ({units['technology'].value_counts().to_dict()}) "
        f"-> {paths.mastr_units_wind_solar}"
    )

    peon_mask = _crop_region_mask(_require(f"{MASTR_DOWNLOADS}/peon_region_mask.nc"))
    peon_mask.to_parquet(paths.pecd_region_mask_peon)
    print(f"Saved PEON region mask: {len(peon_mask):,} nonzero (zone, cell) rows -> {paths.pecd_region_mask_peon}")

    peof_mask = _crop_region_mask(_require(f"{MASTR_DOWNLOADS}/peof_region_mask.nc"))
    peof_mask.to_parquet(paths.pecd_region_mask_peof)
    print(f"Saved PEOF region mask: {len(peof_mask):,} nonzero (zone, cell) rows -> {paths.pecd_region_mask_peof}")


if __name__ == "__main__":
    main()
