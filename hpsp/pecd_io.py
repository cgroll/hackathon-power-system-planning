"""Shared I/O helper for PECD's region-aggregated-timeseries ZIP format.

Adapted from `~/research/pecd-replication/pecdr/pecd_io.py`
(`load_region_timeseries_zip`) — self-contained here rather than imported
cross-repo.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd


def load_region_timeseries_zips(zip_paths: list[Path], region_prefix: str = "DE") -> pd.DataFrame:
    """Load and concatenate several year-chunked `load_region_timeseries_zip`
    downloads (see pipeline/01's chunking, needed to stay under the CDS
    API's per-request cost limit) into one sorted, de-duplicated DataFrame.
    """
    parts = [load_region_timeseries_zip(p, region_prefix) for p in zip_paths]
    combined = pd.concat(parts).sort_index()
    if combined.index.duplicated().any():
        combined = combined[~combined.index.duplicated(keep="first")]
    return combined


def load_region_timeseries_zip(zip_path: Path, region_prefix: str = "DE") -> pd.DataFrame:
    """Read a PECD region-aggregated-timeseries ZIP (one CSV per year inside)
    into a wide, hourly-indexed DataFrame.

    Each CSV has metadata header rows before the real `Date,...` header, and
    region columns for all of Europe (e.g. `DE01`..`DE07` for PEON,
    `DE11`.. for NUTS2). `region_prefix` filters columns down to one
    country's zones instead of loading all of Europe's.
    """
    parts = []
    with zipfile.ZipFile(zip_path) as z:
        for csv_name in z.namelist():
            with z.open(csv_name) as f:
                text = io.TextIOWrapper(f, encoding="utf-8")
                header_idx = next(i for i, line in enumerate(text) if line.startswith("Date,"))
            with z.open(csv_name) as f:
                df = pd.read_csv(
                    f,
                    skiprows=header_idx,
                    parse_dates=["Date"],
                    index_col="Date",
                    usecols=lambda c: c == "Date" or c.startswith(region_prefix),
                )
            parts.append(df)
    combined = pd.concat(parts).sort_index()
    combined.index.name = "timestamp"
    if combined.index.duplicated().any():
        combined = combined[~combined.index.duplicated(keep="first")]
    return combined
