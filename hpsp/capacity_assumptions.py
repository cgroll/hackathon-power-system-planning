"""Installed renewable capacity for Germany, "today" -- Track B's fixed
capacity assumption (Task 1's baseline; Task 2 asks teams to vary this).

Source: `~/research/mastr-power-capacities-germany`'s already-processed
Marktstammdatenregister (MaStR) bulk-dump snapshot (~12 GB raw, processed
once by that sibling project -- not re-derived here), same latest-month
figures pipeline/03/04 use to weight the capacity-factor *shape*
regionally. Updated 2026-09-18, replacing an earlier hand-rounded estimate
(63 / 9 / 100 GW from public reporting) that undercounted actual installed
capacity by ~10-20%.

These are still a fixed, single national number per technology -- not
regionally resolved (see pipeline/03's zone-level panels for that) and not
time-varying (Track A's `capacity_by_zone_month_*` files are, for
comparing against historical actuals). Treat this as an adjustable
starting point: Task 2 explicitly asks teams to change these values and
see what happens, and re-deriving them straight from
`~/research/mastr-power-capacities-germany` is one good way to keep them
current.
"""

from typing import Final

# GW of installed capacity, as of the latest available MaStR register
# month at the time this was written (2026-07 wind, 2026-06 solar) --
# see module docstring for provenance.
INSTALLED_CAPACITY_GW: Final[dict[str, float]] = {
    "wind_onshore": 69.75,
    "wind_offshore": 10.86,
    "solar": 111.21,
}

INSTALLED_CAPACITY_ASSUMPTIONS_NOTE: Final[str] = (
    "Germany's installed renewable capacity, MaStR register snapshot as of "
    "2026-06/07 (wind onshore 69.75 GW, wind offshore 10.86 GW, solar "
    "111.21 GW). See module docstring in hpsp/capacity_assumptions.py."
)


def installed_capacity_mw() -> dict[str, float]:
    """Installed capacity in MW (same technologies as `INSTALLED_CAPACITY_GW`)."""
    return {tech: gw * 1000.0 for tech, gw in INSTALLED_CAPACITY_GW.items()}
