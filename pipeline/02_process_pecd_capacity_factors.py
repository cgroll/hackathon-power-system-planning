"""Process downloaded PECD v4.2 capacity factor ZIPs (pipeline/01) into
Germany-only, wide-format hourly parquet files, full available range
(1980-2025).

Pure data processing -- no charts. This is a build-only *intermediate*
artifact (data/processed/_intermediate/, not tracked in git, see
.gitignore) -- both pipeline/04 (Track B: national aggregation, full
range) and pipeline/05 (Track A: 2015-2025 zonal slice) read from here, so
this only needs computing once regardless of how many tracks use it.

Output, per technology:
  - capacity_factors_zonal_wind_onshore.parquet: columns = 7 PEON zones (DE01..DE07)
  - capacity_factors_zonal_wind_offshore.parquet: columns = PEOF zones (DE0xx_OFF)
  - capacity_factors_zonal_solar.parquet: MultiIndex columns (technology, region) --
    4 PECD PV sub-types x DE NUTS2 regions
"""

import pandas as pd

from hpsp.paths import ProjPaths
from hpsp.pecd_io import load_region_timeseries_zips

SOLAR_TECHNOLOGIES = ["60", "61", "62", "63"]


def main() -> None:
    paths = ProjPaths()
    paths.ensure_directories()

    solar_parts = {}
    for tech in SOLAR_TECHNOLOGIES:
        zips = paths.pecd_capacity_factor_zips("solar", tech)
        print(f"Loading solar tech {tech} ({len(zips)} year-chunk file(s)) ...")
        df = load_region_timeseries_zips(zips)
        print(f"  {len(df):,} rows x {len(df.columns)} DE NUTS2 regions - {df.index.min()} .. {df.index.max()}")
        solar_parts[tech] = df

    solar = pd.concat(solar_parts, axis=1, names=["technology", "region"])
    # PECD's solar CF timestamps run 1 hour ahead of true UTC -- confirmed
    # empirically in ~/research/pecd-replication (shifting back by 1 hour
    # roughly halves the MAE against SMARD's actual PV generation). Not
    # present in the wind product. See that project's
    # pipeline/26_analyse_solar_bias_drivers.py for the analysis.
    solar.index = solar.index - pd.Timedelta(hours=1)
    solar.to_parquet(paths.capacity_factors_zonal_solar_intermediate)
    print(f"Saved solar: {solar.shape} -> {paths.capacity_factors_zonal_solar_intermediate}\n")

    onshore_zips = paths.pecd_capacity_factor_zips("wind_onshore", "30")
    print(f"Loading wind onshore (PEON, {len(onshore_zips)} year-chunk file(s)) ...")
    wind_onshore = load_region_timeseries_zips(onshore_zips)
    print(f"  {len(wind_onshore):,} rows x {len(wind_onshore.columns)} DE PEON zones: {sorted(wind_onshore.columns)}")
    wind_onshore.to_parquet(paths.capacity_factors_zonal_wind_onshore_intermediate)
    print(f"Saved wind onshore -> {paths.capacity_factors_zonal_wind_onshore_intermediate}\n")

    offshore_zips = paths.pecd_capacity_factor_zips("wind_offshore", "20")
    print(f"Loading wind offshore (PEOF, {len(offshore_zips)} year-chunk file(s)) ...")
    wind_offshore = load_region_timeseries_zips(offshore_zips)
    print(f"  {len(wind_offshore):,} rows x {len(wind_offshore.columns)} DE PEOF zones: {sorted(wind_offshore.columns)}")
    wind_offshore.to_parquet(paths.capacity_factors_zonal_wind_offshore_intermediate)
    print(f"Saved wind offshore -> {paths.capacity_factors_zonal_wind_offshore_intermediate}")


if __name__ == "__main__":
    main()
