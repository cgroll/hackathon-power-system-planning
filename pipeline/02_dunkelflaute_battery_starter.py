# ---
# jupytext:
#   text_representation:
#     format_name: percent
# kernelspec:
#   display_name: Python 3
#   language: python
#   name: python3
# ---

# %% [markdown]
# # Dunkelflaute & Battery Sizing — Starter Analysis
#
# This notebook is a **worked example**, not the final answer — it exists so
# a hackathon team can see the shape of a result before building their own,
# deeper version. It answers two simplified questions from today's German
# renewable fleet's hourly PECD capacity factors (2019-2025) and a rough,
# hand-entered installed-capacity assumption (see `hpsp/capacity_assumptions.py`,
# **not** derived from MaStR):
#
# 1. How often, and for how long, does combined wind + solar output drop
#    below a low-generation ("Dunkelflaute") threshold?
# 2. How much does adding battery storage reduce the number of hours the
#    fleet falls short of a simple illustrative target output level?
#
# **Simplifications a team should push on:**
# - The "target output" here is just the fleet's own multi-year average
#   generation, *not* real electricity demand — swap in
#   `~/research/pecd-replication/data/processed/target_panel.parquet`
#   (SMARD `load`) or `residual_load_inputs.parquet` (`D_grid_mw`) for a
#   real demand-coverage version.
# - The battery model has no round-trip losses and no power (MW) limit,
#   only an energy (MWh) capacity limit — see `simulate_battery` below.
# - Installed capacity is a single rough number per technology, not a
#   regionally resolved or time-varying (fleet growth) one.

# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from hpsp.capacity_assumptions import INSTALLED_CAPACITY_GW, installed_capacity_mw
from hpsp.paths import ProjPaths

paths = ProjPaths()
paths.ensure_directories()

cf = pd.read_parquet(paths.capacity_factors_de_national)
capacity_mw = installed_capacity_mw()

generation_mw = pd.DataFrame({tech: cf[tech] * mw for tech, mw in capacity_mw.items()})
generation_mw["total"] = generation_mw.sum(axis=1)

total_installed_mw = sum(capacity_mw.values())
print("Installed capacity (GW):", INSTALLED_CAPACITY_GW)
print(f"Total installed: {total_installed_mw / 1000:.0f} GW")

# %% [markdown]
# ## 1. How much Dunkelflaute is there today?
#
# Illustrative definition: an hour counts as "Dunkelflaute" when combined
# wind + solar output is below 10% of total installed capacity. This
# threshold is a simplification for a starting point — there is no single
# agreed-upon definition in the literature; a good extension is to compare
# a few thresholds (5%/10%/20%) or require several consecutive low hours.

# %%
DUNKELFLAUTE_THRESHOLD_FRACTION = 0.10
threshold_mw = DUNKELFLAUTE_THRESHOLD_FRACTION * total_installed_mw

is_low = generation_mw["total"] < threshold_mw
n_years = (generation_mw.index[-1] - generation_mw.index[0]).days / 365.25

# Identify contiguous low-generation events.
event_id = (is_low != is_low.shift(fill_value=False)).cumsum()
events = (
    pd.DataFrame({"is_low": is_low, "event_id": event_id})
    .loc[is_low]
    .groupby("event_id")
    .size()
    .rename("duration_hours")
)

print(f"Dunkelflaute hours/year (avg): {is_low.sum() / n_years:.0f}")
print(f"Number of events/year (avg): {len(events) / n_years:.1f}")
print(f"Longest single event: {events.max()} hours ({events.max() / 24:.1f} days)")

# %% [markdown]
# **Reality check on the number above:** ~2,600 hours/year (~30% of the
# year) sounds alarming, but a large share of that is just ordinary
# nights with low wind, since solar is (correctly) ~0 for ~12h/day and
# contributes nothing to push the total back above the threshold. That is
# expected, not newsworthy — real Dunkelflaute analyses usually look at a
# *lower* threshold, a *longer* minimum event duration (e.g. >=6h), or
# wind-only. Treat this as a reminder to sanity-check the metric, not as a
# final headline number — a natural first task for a team.

# %%
fig, ax = plt.subplots(figsize=(10, 4))
ax.hist(events.values, bins=range(1, int(events.max()) + 2), edgecolor="white", linewidth=0.3)
ax.set_xlabel("Event duration (hours)")
ax.set_ylabel("Number of events")
ax.set_title(f"Dunkelflaute event durations, {generation_mw.index[0].year}-{generation_mw.index[-1].year}")
fig.tight_layout()
fig.savefig(paths.images_path / "02_dunkelflaute_event_durations.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ```{figure} ../../output/images/02_dunkelflaute_event_durations.png
# :name: fig-02-dunkelflaute-event-durations
# Distribution of Dunkelflaute event durations (hours below 10% of installed
# capacity), full 2019-2025 period.
# ```

# %% [markdown]
# ## 2. How much does a battery help?
#
# Simple rule-based battery, no forecasting: charge with any surplus above
# the target output (up to the battery's energy capacity), discharge to
# cover any shortfall below it (down to empty). No round-trip losses, no
# MW power limit — a real design would need both.


# %%
def simulate_battery(generation_mw: pd.Series, target_mw: float, battery_capacity_mwh: float) -> pd.Series:
    """Return the residual shortfall (MW, >= 0) after battery support, hour by hour."""
    shortfall = np.zeros(len(generation_mw))
    net_mw = generation_mw.to_numpy() - target_mw  # +surplus / -deficit, 1h steps so MWh == MW
    soc_mwh = battery_capacity_mwh / 2  # start half full
    for i, net in enumerate(net_mw):
        if net >= 0:
            soc_mwh = min(battery_capacity_mwh, soc_mwh + net)
            shortfall[i] = 0.0
        else:
            deficit = -net
            discharge = min(soc_mwh, deficit)
            soc_mwh -= discharge
            shortfall[i] = deficit - discharge
    return pd.Series(shortfall, index=generation_mw.index)


target_mw = generation_mw["total"].mean()
print(f"Illustrative target output: {target_mw / 1000:.1f} GW (fleet's own multi-year average, NOT real demand)")

battery_sizes_gwh = [0, 5, 20, 50, 100, 200]
results = []
for size_gwh in battery_sizes_gwh:
    shortfall = simulate_battery(generation_mw["total"], target_mw, size_gwh * 1000)
    shortfall_hours = (shortfall > 0).sum()
    results.append({"battery_gwh": size_gwh, "shortfall_hours_per_year": shortfall_hours / n_years})

battery_results = pd.DataFrame(results)
print(battery_results)

# %%
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(battery_results["battery_gwh"], battery_results["shortfall_hours_per_year"], marker="o")
ax.set_xlabel("Battery capacity (GWh)")
ax.set_ylabel("Shortfall hours / year\n(below own average target output)")
ax.set_title("Illustrative battery sensitivity curve")
fig.tight_layout()
fig.savefig(paths.images_path / "02_battery_sensitivity.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ```{figure} ../../output/images/02_battery_sensitivity.png
# :name: fig-02-battery-sensitivity
# Hours per year the fleet falls short of its own illustrative target
# output, as a function of battery energy capacity. Not a real demand-
# coverage curve — see the simplifications noted above.
# ```
