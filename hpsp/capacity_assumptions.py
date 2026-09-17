"""Approximate installed renewable capacity for Germany, "today".

These are deliberately **rough, rounded, hand-entered** figures, not a
Marktstammdatenregister (MaStR) query — the point of this project is to let
hackathon teams start immediately on the *Dunkelflaute*/battery question
without first standing up a MaStR download pipeline (~12 GB raw dump, see
`~/research/mastr-power-capacities-germany` for the "do it properly" version
if a team wants to swap these out later).

Source: rounded to the nearest GW from public reporting (Bundesnetzagentur /
Fraunhofer ISE Energy-Charts) on Germany's installed capacity around
2024/2025. Treat these as an order-of-magnitude starting point, not ground
truth — a good stretch goal for any team is to replace this module with a
real MaStR-derived number and see how much the answer changes.
"""

from typing import Final

# GW of installed capacity, approximately as of 2025.
INSTALLED_CAPACITY_GW: Final[dict[str, float]] = {
    "wind_onshore": 63.0,
    "wind_offshore": 9.0,
    "solar": 100.0,
}

INSTALLED_CAPACITY_ASSUMPTIONS_NOTE: Final[str] = (
    "Rounded, hand-entered approximate values for Germany's installed "
    "renewable capacity (~2025), not derived from MaStR. See module "
    "docstring in hpsp/capacity_assumptions.py."
)


def installed_capacity_mw() -> dict[str, float]:
    """Installed capacity in MW (same technologies as `INSTALLED_CAPACITY_GW`)."""
    return {tech: gw * 1000.0 for tech, gw in INSTALLED_CAPACITY_GW.items()}
