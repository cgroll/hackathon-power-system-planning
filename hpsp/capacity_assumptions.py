"""Installed renewable capacity for Germany, "today" -- Track B's fixed
capacity assumption (Task 1's baseline; Task 2 asks teams to vary this).

Source: a Marktstammdatenregister (MaStR) register snapshot, via
[energy-data-hub](https://github.com/cgroll/energy-data-hub) (see
`book/markdown/data_sources.md`), which itself consolidates the MaStR
parsing this figure was originally derived from. Updated 2026-09-18,
replacing an earlier hand-rounded estimate (63 / 9 / 100 GW from public
reporting) that undercounted actual installed capacity by ~10-20%.

This is a fixed, single national number per technology -- not regionally
resolved and not time-varying (the raw MaStR unit records in
`data/input/mastr/` are, if you build a time-varying panel yourself for
Track A). Treat this as an adjustable starting point: Task 2 explicitly
asks teams to change these values and see what happens.
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
