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
# # Input Data Overview
#
# A quick inventory of everything under `data/input/`: for each file, the
# first five rows plus basic metadata (rows, columns, time range, missing
# values). See {doc}`../markdown/data_sources` for where the data comes from
# and what each file is meant for.
#
# The MaStR solar table has ~6.3M rows, so metadata is read column-by-column
# via `pyarrow` rather than loading every file fully into memory.

# %%
import pandas as pd
import pyarrow.parquet as pq
import xarray as xr

from hpsp.paths import ProjPaths

paths = ProjPaths()
pd.set_option("display.max_columns", 12)
pd.set_option("display.width", 200)


def head(path, n=5):
    """First `n` rows of a (flat, index-free) parquet file, without reading it all."""
    return next(pq.ParquetFile(path).iter_batches(batch_size=n)).to_pandas()


def file_info(path):
    pf = pq.ParquetFile(path)
    return {
        "file": str(path.relative_to(paths.input_path)),
        "size_MB": round(path.stat().st_size / 1e6, 1),
        "rows": pf.metadata.num_rows,
        "columns": len(pf.schema_arrow.names),
    }


def timeseries_meta(df):
    """Metadata for a timestamp-indexed capacity-factor frame."""
    idx = df.index
    steps = pd.Series(idx).diff().value_counts()
    return pd.Series(
        {
            "start": idx.min(),
            "end": idx.max(),
            "rows": len(idx),
            "years": idx.year.nunique(),
            "time step (most common)": steps.index[0],
            "irregular steps": int(steps.iloc[1:].sum()),
            "duplicate timestamps": int(idx.duplicated().sum()),
            "columns": df.shape[1],
            "missing values (total)": int(df.isna().sum().sum()),
            "columns with any NaN": int(df.isna().any().sum()),
            "value min": float(df.min().min()),
            "value max": float(df.max().max()),
        },
        name="value",
    ).to_frame()


# %% [markdown]
# ## Summary of all files

# %%
parquet_files = sorted(paths.input_path.rglob("*.parquet"))
summary = pd.DataFrame([file_info(p) for p in parquet_files])
nc_files = sorted(paths.input_path.rglob("*.nc"))
for p in nc_files:
    with xr.open_dataset(p) as ds:
        summary.loc[len(summary)] = {
            "file": str(p.relative_to(paths.input_path)),
            "size_MB": round(p.stat().st_size / 1e6, 1),
            "rows": None,
            "columns": None,
        }
summary

# %% [markdown]
# ## PECD capacity factors: national, Germany (Track B)
#
# `pecd/pecd_country_capacity_factors_simple_de.parquet` -- hourly, one
# column per technology. Solar is already a blend of the 4 PV
# sub-technologies (weighted by Germany's market mix).

# %%
cf_de = pd.read_parquet(paths.pecd_capacity_factors_national_de)
cf_de.head()

# %%
timeseries_meta(cf_de)

# %%
cf_de.describe().T

# %% [markdown]
# ## PECD capacity factors: national, all of Europe
#
# `pecd/pecd_country_capacity_factors_simple.parquet` -- same time range as
# the Germany file, with `(technology, country)` MultiIndex columns. Only
# three (blended) technologies; not every country has every technology.

# %%
cf_eu = pd.read_parquet(paths.pecd_capacity_factors_national_europe)
cf_eu.head()

# %%
timeseries_meta(cf_eu)

# %%
countries_per_tech = cf_eu.columns.to_frame(index=False).groupby("technology", sort=False)["country"]
pd.DataFrame(
    {
        "n_countries": countries_per_tech.size(),
        "countries": countries_per_tech.agg(", ".join),
    }
)

# %% [markdown]
# Sanity check: the Germany columns in the all-Europe file should match the
# Germany-only file.

# %%
(cf_eu.xs("DE", axis=1, level="country")[cf_de.columns] - cf_de).abs().max()

# %% [markdown]
# ## PECD capacity factors: zonal, Germany (Track A)
#
# Only 2015-2025, but at sub-national resolution.
#
# ### Wind onshore (PEON zones)

# %%
cf_on = pd.read_parquet(paths.pecd_capacity_factors_zonal_wind_onshore)
cf_on.head()

# %%
timeseries_meta(cf_on)

# %% [markdown]
# ### Wind offshore (PEOF zones)

# %%
cf_off = pd.read_parquet(paths.pecd_capacity_factors_zonal_wind_offshore)
cf_off.head()

# %%
timeseries_meta(cf_off)

# %% [markdown]
# Missing values per offshore zone -- some zones only have data for part of
# the period:

# %%
pd.DataFrame(
    {
        "missing_hours": cf_off.isna().sum(),
        "first_valid": cf_off.apply(pd.Series.first_valid_index),
        "last_valid": cf_off.apply(pd.Series.last_valid_index),
    }
)

# %% [markdown]
# ### Solar (4 PV sub-technologies x NUTS2 regions)
#
# Technology codes: 60 = industrial rooftop, 61 = residential rooftop,
# 62 = utility-scale fixed, 63 = utility-scale tracking. Not blended -- one
# column per `(technology, region)`.

# %%
cf_pv = pd.read_parquet(paths.pecd_capacity_factors_zonal_solar)
cf_pv.head()

# %%
timeseries_meta(cf_pv)

# %%
# Mean capacity factor per technology (averaged over regions and hours)
cf_pv.mean().groupby(level="technology").mean().rename("mean_cf").to_frame()

# %%
print("NUTS2 regions:", ", ".join(cf_pv.columns.get_level_values("region").unique()))

# %% [markdown]
# ## PECD region masks
#
# Rasterized zone-membership fractions on a 0.25° grid, all of Europe.
# Shown here: dimensions, number of regions, and the German zones.

# %%
for name, p in [("PEON (onshore)", paths.pecd_region_mask_peon), ("PEOF (offshore)", paths.pecd_region_mask_peof)]:
    with xr.open_dataset(p) as ds:
        regions = ds["region"].values.astype(str)
        de = [r for r in regions if r.startswith("DE")]
        print(f"--- {name}: {p.name}")
        print(f"dims: {dict(ds.sizes)}")
        print(f"lat: {float(ds.latitude.min())} .. {float(ds.latitude.max())}, "
              f"lon: {float(ds.longitude.min())} .. {float(ds.longitude.max())}")
        print(f"regions: {len(regions)} total, {len(de)} German: {', '.join(de)}")
        print(f"attrs: {ds.attrs}\n")

# %%
with xr.open_dataset(paths.pecd_region_mask_peon) as ds:
    de_regions = [r for r in ds["region"].values.astype(str) if r.startswith("DE")]
    mask_de = ds["mask"].sel(region=de_regions).to_dataframe().query("mask > 0")
mask_de.head()

# %% [markdown]
# ## MaStR unit-level records (Track A)
#
# Loaded column-wise; only the columns needed for the metadata are read
# for the large solar table.

# %%
def mastr_meta(path):
    cols = ["commissioning_date", "final_shutdown_date", "net_capacity_kw", "latitude"]
    df = pd.read_parquet(path, columns=cols)
    real_dates = df["commissioning_date"][df["commissioning_date"] > "1900-01-01"]
    return pd.Series(
        {
            "units": len(df),
            "commissioning_date min (excl. 1900-01-01)": real_dates.min(),
            "commissioning_date max": df["commissioning_date"].max(),
            "commissioning_date == 1900-01-01": int((df["commissioning_date"] == "1900-01-01").sum()),
            "commissioning_date missing": int(df["commissioning_date"].isna().sum()),
            "units with final_shutdown_date": int(df["final_shutdown_date"].notna().sum()),
            "units with coordinates": int(df["latitude"].notna().sum()),
            "total net capacity (GW, incl. shut down)": round(df["net_capacity_kw"].sum() / 1e6, 1),
        },
        name="value",
    ).to_frame()


# %% [markdown]
# ### Solar units

# %%
head(paths.mastr_solar_units)

# %%
mastr_meta(paths.mastr_solar_units)

# %%
pd.read_parquet(paths.mastr_solar_units, columns=["installation_type"])["installation_type"].value_counts(dropna=False).to_frame()

# %% [markdown]
# ### Solar technical detail (orientation / tilt)

# %%
head(paths.mastr_solar_technical_detail)

# %%
detail = pd.read_parquet(paths.mastr_solar_technical_detail, columns=["main_orientation", "main_orientation_tilt_bucket"])
pd.concat(
    {c: detail[c].value_counts(dropna=False) for c in detail.columns}, axis=1
)

# %%
del detail

# %% [markdown]
# ### Wind units

# %%
wind = pd.read_parquet(paths.mastr_wind_units)
wind.head()

# %%
mastr_meta(paths.mastr_wind_units)

# %%
wind.groupby("wind_onshore_or_offshore", observed=True).agg(
    units=("unit_id", "size"),
    net_capacity_GW=("net_capacity_kw", lambda s: round(s.sum() / 1e6, 1)),
)

# %% [markdown]
# ## Region crosswalk: LAU → NUTS3

# %%
lau = pd.read_parquet(paths.lau_nuts_correspondence)
lau.head()

# %%
pd.Series(
    {
        "rows": len(lau),
        "unique municipality_key": lau["municipality_key"].nunique(),
        "unique NUTS3": lau["nuts3_code"].nunique(),
        "unique NUTS2 (first 4 chars)": lau["nuts3_code"].str[:4].nunique(),
    },
    name="value",
).to_frame()
