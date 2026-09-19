"""Split pecd-replication's SMARD target_panel.parquet into Track B's
national demand and Track A's per-technology generation actuals.

Pure data script -- no charts. Verified 2026-09-18 (see PROJECT.md) that
target_panel.parquet is an unmodified, inner-joined raw SMARD download
(pecd-replication/pipeline/14_build_target_panel.py) -- no curtailment or
other adjustment applied, safe to use directly for both.

Outputs, both at target_panel.parquet's native range (2018-09-30 through
2026-08-04 as of this writing) -- wider than Track A's capacity-factor
window (2015-2025) on one side, narrower than Track B's (1980-2025) on the
other. Teams doing residual-load or potential-vs-observed math need to
intersect ranges themselves -- documented, not silently resolved (see
PROJECT.md, 2026-09-18):
  - demand_de_national.parquet: column `demand_mw` (Track B)
  - generation_de_by_technology.parquet: columns pv/wind_onshore/wind_offshore (Track A)
"""

import os

import pandas as pd

from hpsp.paths import ProjPaths

TARGET_PANEL = "/home/chris/research/pecd-replication/data/processed/target_panel.parquet"


def main() -> None:
    paths = ProjPaths()
    paths.ensure_directories()

    if not os.path.exists(TARGET_PANEL):
        raise FileNotFoundError(
            f"Expected source file not found: {TARGET_PANEL}\n"
            "This script reuses pecd-replication's already-downloaded SMARD "
            "panel instead of re-downloading from smard.de. See PROJECT.md "
            "for details."
        )
    target_panel = pd.read_parquet(TARGET_PANEL)

    demand = target_panel[["load"]].rename(columns={"load": "demand_mw"})
    demand.to_parquet(paths.demand_de_national)
    print(f"Saved demand: {len(demand):,} rows, {demand.index.min()} .. {demand.index.max()} -> {paths.demand_de_national}")

    generation = target_panel[["pv", "wind_onshore", "wind_offshore"]]
    generation.to_parquet(paths.generation_de_by_technology)
    print(f"Saved generation: {len(generation):,} rows x {list(generation.columns)}, {generation.index.min()} .. {generation.index.max()} -> {paths.generation_de_by_technology}")


if __name__ == "__main__":
    main()
