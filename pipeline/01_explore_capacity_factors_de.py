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
# # Exploring Germany's PECD Capacity Factors
#
# A first look at the Track B input data: `data/input/pecd/pecd_country_capacity_factors_simple_de.parquet`,
# an hourly, national capacity-factor series for German wind onshore, wind
# offshore, and solar, 1980-2025. See `book/markdown/data_sources.md` for
# where this comes from and what it simplifies away.
#
# This notebook is descriptive only -- it doesn't define a Dunkelflaute
# threshold, compute residual load, or size a battery. It's meant as an
# example of what a first-look analysis script in this repo looks like,
# not a solution to either track's tasks.

# %%
import matplotlib.pyplot as plt
import pandas as pd

from hpsp.paths import ProjPaths

paths = ProjPaths()

# %%
cf = pd.read_parquet(paths.pecd_capacity_factors_national_de)
cf.index = pd.to_datetime(cf.index)
cf.index.name = "timestamp"
cf.describe()

# %% [markdown]
# ## Full history, monthly means
#
# 46 years of hourly data is too dense to plot directly -- resampling to a
# monthly mean already shows the seasonal pattern (solar peaking in summer,
# wind in winter) and lets year-to-year variability stand out.

# %%
monthly = cf.resample("MS").mean()

fig, ax = plt.subplots(figsize=(14, 4))
for col in ["wind_onshore", "wind_offshore", "solar"]:
    ax.plot(monthly.index, monthly[col], label=col, linewidth=0.8)
ax.set_ylabel("capacity factor (monthly mean)")
ax.set_title("Germany: monthly-mean PECD capacity factors, 1980-2025")
ax.legend()
fig.savefig(paths.images_path / "01_monthly_capacity_factors.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ```{figure} ../../output/images/01_monthly_capacity_factors.png
# :name: fig-01-monthly-cf
# Monthly-mean capacity factors for wind onshore, wind offshore, and solar,
# Germany, 1980-2025.
# ```

# %% [markdown]
# ## Seasonality by calendar month
#
# Same data, viewed as a distribution per calendar month across all 46
# years -- shows both the seasonal shape and how much spread there is
# within a given month across different years.

# %%
by_month = cf.copy()
by_month["month"] = by_month.index.month

fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
for ax, col in zip(axes, ["wind_onshore", "wind_offshore", "solar"]):
    by_month.boxplot(column=col, by="month", ax=ax, showfliers=False)
    ax.set_title(col)
    ax.set_xlabel("month")
fig.suptitle("")
fig.savefig(paths.images_path / "01_seasonality_by_month.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ```{figure} ../../output/images/01_seasonality_by_month.png
# :name: fig-01-seasonality
# Distribution of hourly capacity factors by calendar month, 1980-2025.
# ```

# %% [markdown]
# ## Two contrasting weeks
#
# Zooming into hourly resolution for two specific weeks found by ranking
# all weeks 2020-2025 by their combined wind+solar mean: a calm week
# (2024-11-04 to 2024-11-11, low wind and low solar at the same time) and
# a windy week (2022-02-20 to 2022-02-27). Whether either of these counts
# as a "Dunkelflaute" -- and how you'd define that in the first place --
# is Track B's Task 1, not something this notebook decides.

# %%
fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharey=True)
windows = {
    "Calm week: 2024-11-04 to 2024-11-11": ("2024-11-04", "2024-11-11"),
    "Windy week: 2022-02-20 to 2022-02-27": ("2022-02-20", "2022-02-27"),
}
for ax, (title, (start, end)) in zip(axes, windows.items()):
    window = cf.loc[start:end]
    for col in ["wind_onshore", "wind_offshore", "solar"]:
        ax.plot(window.index, window[col], label=col, linewidth=1.0)
    ax.set_title(title)
    ax.set_ylabel("capacity factor")
axes[0].legend()
fig.tight_layout()
fig.savefig(paths.images_path / "01_sample_weeks.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ```{figure} ../../output/images/01_sample_weeks.png
# :name: fig-01-sample-weeks
# Hourly capacity factors during one calm and one windy week.
# ```

# %% [markdown]
# ## Wind vs. solar correlation
#
# A quick check of how (un)correlated wind and solar are hour-by-hour --
# relevant background for both tracks: low correlation is exactly what
# makes a wind+solar portfolio less prone to simultaneous shortfalls than
# either technology alone, but also means neither reliably compensates
# for the other on any given hour.

# %%
corr = cf[["wind_onshore", "wind_offshore", "solar"]].corr()
corr

# %% [markdown]
# ## Where to go from here
#
# - **Track B**: define a Dunkelflaute threshold, bring in real demand
#   (fetch it from SMARD yourself), and compute residual load using
#   `hpsp/capacity_assumptions.py`'s installed-capacity figures.
# - **Track A**: this national series is *not* what Track A needs -- Track
#   A validates PECD against observed generation, which requires the
#   *zonal* capacity factors and the time-varying MaStR fleet in
#   `data/input/`. See `book/markdown/data_sources.md` for that recipe,
#   and the linked video for a worked walkthrough of linking MaStR to
#   PECD zones.
