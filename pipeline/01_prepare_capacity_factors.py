"""Prepare hourly national PECD capacity factors for Germany.

Pure data script — no visualizations.

This does **not** call the Copernicus CDS API. It reads already-downloaded,
already-processed PECD v4.2 output from the sibling `pecd-replication`
project (see `~/research/pecd-replication`, in particular
`pipeline/37_build_residual_load_inputs.py` and `pecdr/full_year.py`), which
did the CDS downloads and the capacity-weighted zone-to-national aggregation
once already. Re-running that from scratch needs a free CDS/Copernicus
account and takes hours — pointless friction for a 3h hackathon slot, so we
just reuse the parquet outputs that already exist on disk.

If `~/research/pecd-replication` is not available (e.g. on a different
machine), this script will raise a clear `FileNotFoundError` — see that
project's README for how to regenerate the source files it reads here.

Output: `data/processed/capacity_factors_de_national.parquet`, hourly,
2019-01-01 through 2025-12-31, columns `wind_onshore`, `wind_offshore`,
`solar` (all unitless capacity factors in [0, 1]).

Wind onshore/offshore national series are PECD-zone capacity-weighted
already (using MaStR-derived capacity weights) — see `pecd-replication`.
Solar has no ready-made national series, so this script derives one as a
plain, *unweighted* mean capacity factor across all NUTS2 zones and all 4
PECD PV sub-technologies (industrial/residential rooftop, utility fixed/
tracking). That ignores where PV capacity is actually concentrated (e.g.
Bavaria has much more than Bremen) — a reasonable stretch goal for a team is
to redo this with real regional capacity weights.
"""

import pandas as pd

from hpsp.paths import ProjPaths

PECD_REPLICATION_PROCESSED = "/home/chris/research/pecd-replication/data/processed"

START = "2019-01-01 00:00:00"
END = "2025-12-31 23:00:00"


def _require(path: str) -> str:
    import os

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Expected source file not found: {path}\n"
            "This script reuses already-processed output from "
            "~/research/pecd-replication instead of re-downloading from "
            "the CDS API. See that project's README to regenerate it."
        )
    return path


def load_wind_national(filename: str) -> pd.Series:
    path = _require(f"{PECD_REPLICATION_PROCESSED}/{filename}")
    df = pd.read_parquet(path, columns=["national"])
    return df["national"].loc[START:END]


def load_solar_national() -> pd.Series:
    path = _require(f"{PECD_REPLICATION_PROCESSED}/pecd_solar_capacity_factors.parquet")
    df = pd.read_parquet(path)
    # MultiIndex columns (sub_technology_code, nuts2_zone) — see module
    # docstring for why this is an unweighted mean.
    national = df.loc[START:END].mean(axis=1)
    national.name = "solar"
    return national


def main() -> None:
    paths = ProjPaths()
    paths.ensure_directories()

    wind_onshore = load_wind_national("wind_onshore_full_year_cf.parquet").rename("wind_onshore")
    wind_offshore = load_wind_national("wind_offshore_full_year_cf.parquet").rename("wind_offshore")
    solar = load_solar_national()

    combined = pd.concat([wind_onshore, wind_offshore, solar], axis=1, join="inner")
    combined.index.name = "timestamp"

    assert combined.notna().all().all(), "unexpected gaps after inner join"
    assert (combined.min() >= 0).all() and (combined.max() <= 1).all(), "capacity factors out of [0, 1]"

    combined.to_parquet(paths.capacity_factors_de_national)
    print(f"Saved {len(combined):,} hourly rows x {list(combined.columns)} → {paths.capacity_factors_de_national}")
    print(combined.describe())


if __name__ == "__main__":
    main()
