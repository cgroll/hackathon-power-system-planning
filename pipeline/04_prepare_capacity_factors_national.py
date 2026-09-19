"""Build Track B's national, fixed-capacity capacity-factor series for
Germany: official PECD zone-level capacity factors (pipeline/02's
intermediate output, full 1980-2025 range), collapsed to national with a
plain, **unweighted** mean across zones -- not capacity-weighted.

Pure data script -- no charts. Deliberately *not* weighted by real MaStR
installed capacity, even though the small MaStR zone-month panels exist
(pipeline/03): building a correctly capacity-weighted national series from
real MaStR data is Track A's own exercise (see PROJECT.md, 2026-09-18,
"Track A/B overlap" discussion) -- if Track B did that same join here, it
would hand Track A participants an already-solved reference implementation
sitting right next to it in the same repo. Track B accepts the resulting
regional-weighting error (e.g. wind's 6-7 zones are roughly federal-state
sized, so this is coarse -- Bavaria counts the same as
Mecklenburg-Vorpommern regardless of how much wind capacity either
actually has) as a documented, deliberate simplification: Dunkelflaute
events are typically Germany-wide weather phenomena, so the *timing* of
scarcity is reasonably preserved even if the exact *level* isn't
capacity-precise. `hpsp/capacity_assumptions.py`'s single national GW
figure (which *is* MaStR-sourced) is what teams multiply this capacity
factor by -- that's a cited fact, not a methodology, so no overlap there.

Output: data/processed/capacity_factors_de_national.parquet, hourly,
1980-2025, columns wind_onshore / wind_offshore / solar (capacity factors
in [0, 1]).
"""

import pandas as pd

from hpsp.paths import ProjPaths


def _national_mean(cf: pd.DataFrame, label: str) -> pd.Series:
    """Unweighted mean across zone columns, dropping zones with no CF
    coverage at all (checked empirically 2026-09-18: some PEOF zones are
    entirely NaN in the wind-offshore product, e.g. DE013_OFF for 2024) --
    an all-NaN column would otherwise silently drop out of the mean's
    denominator anyway via pandas' skipna default, but dropping it
    explicitly makes that visible instead of silent.
    """
    covered = cf.columns[cf.notna().any(axis=0)]
    dropped = cf.columns.difference(covered)
    if len(dropped) > 0:
        print(f"  {label}: dropping {len(dropped)} zone(s) with no CF coverage: {list(dropped)}")
    return cf[covered].mean(axis=1)


def main() -> None:
    paths = ProjPaths()
    paths.ensure_directories()

    wind_onshore_cf = pd.read_parquet(paths.capacity_factors_zonal_wind_onshore_intermediate)
    wind_offshore_cf = pd.read_parquet(paths.capacity_factors_zonal_wind_offshore_intermediate)
    solar_cf = pd.read_parquet(paths.capacity_factors_zonal_solar_intermediate)

    wind_onshore = _national_mean(wind_onshore_cf, "wind onshore").rename("wind_onshore")
    wind_offshore = _national_mean(wind_offshore_cf, "wind offshore").rename("wind_offshore")
    solar = _national_mean(solar_cf, "solar").rename("solar")

    combined = pd.concat([wind_onshore, wind_offshore, solar], axis=1, join="inner")
    combined.index.name = "timestamp"

    assert combined.notna().all().all(), "unexpected gaps after inner join"
    assert (combined.min() >= 0).all() and (combined.max() <= 1).all(), "capacity factors out of [0, 1]"

    combined.to_parquet(paths.capacity_factors_de_national)
    print(f"Saved {len(combined):,} hourly rows x {list(combined.columns)} -> {paths.capacity_factors_de_national}")
    print(f"Range: {combined.index.min()} .. {combined.index.max()}")


if __name__ == "__main__":
    main()
