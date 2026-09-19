"""Build Track A's zonal capacity-factor deliverable: pipeline/02's
Germany-zone-level official PECD product, sliced to 2015-2025 -- the range
Track A can actually use.

Pure data script -- no charts. Deliberately narrower than Track B's
1980-2025 national series (pipeline/04): Track A's usable range is bounded
by the time-varying MaStR capacity panels (pipeline/03, start 2015-01) and
SMARD actuals (pipeline/06, start 2018-09-30) regardless of how far back
the capacity factors themselves go -- more weather history before 2015
has nothing to combine with for this track. See PROJECT.md, 2026-09-18.

Output, per technology (same shapes as the pipeline/02 intermediate, just
row-sliced):
  - capacity_factors_zonal_wind_onshore.parquet
  - capacity_factors_zonal_wind_offshore.parquet
  - capacity_factors_zonal_solar.parquet
"""

import pandas as pd

from hpsp.paths import ProjPaths

START = "2015-01-01 00:00:00"
END = "2025-12-31 23:00:00"


def main() -> None:
    paths = ProjPaths()
    paths.ensure_directories()

    jobs = [
        (paths.capacity_factors_zonal_wind_onshore_intermediate, paths.capacity_factors_zonal_wind_onshore, "wind onshore"),
        (paths.capacity_factors_zonal_wind_offshore_intermediate, paths.capacity_factors_zonal_wind_offshore, "wind offshore"),
        (paths.capacity_factors_zonal_solar_intermediate, paths.capacity_factors_zonal_solar, "solar"),
    ]
    for intermediate_path, output_path, label in jobs:
        df = pd.read_parquet(intermediate_path).loc[START:END]
        df.to_parquet(output_path)
        print(f"{label}: {len(df):,} rows x {len(df.columns)} zones, {df.index.min()} .. {df.index.max()} -> {output_path}")


if __name__ == "__main__":
    main()
