"""Download PECD v4.2 capacity factor time series: solar PV (NUTS2) and wind
onshore/offshore (PEON/PEOF), 1980-2025, all of Europe (the CDS API has no
per-country filter for this product; pipeline/02 filters down to Germany).

Pure data acquisition -- no charts. One CDS request per (variable,
technology, 10-year chunk). Chunked, not one request for the full
1980-2025 range: tried the single-request version first (see PROJECT.md,
2026-09-18 "download chunking" entry) and hit a hard, non-transient CDS
error -- "cost limits exceeded, your request is too large" -- on the very
first (solar) request. `pecd-replication`'s own 11-year 2015-2025 request
worked, so 10-year chunks are a safe margin under whatever the actual
per-request limit is; each chunk is a separate, independently resumable
output file.

Start year 1980, not the full 1950 the CDS API otherwise offers for this
product (checked directly against `sis-energy-pecd`'s `constraints.json`,
see PROJECT.md 2026-09-18): ERA5 before the 1979 satellite era is markedly
less observation-constrained, not reliable enough for a Dunkelflaute
stress test. This only needs running once, by whoever prepares this repo's
data -- hackathon participants only ever see the resulting processed
output (pipeline/04), no CDS account required on their end.

Requires a ~/.cdsapirc file with a valid CDS API key
(https://cds.climate.copernicus.eu/how-to-api).
"""

import cdsapi

from hpsp.cds import retrieve_with_retries
from hpsp.paths import ProjPaths

START_YEAR = 1980
END_YEAR = 2025
CHUNK_SIZE_YEARS = 10

MONTHS = [f"{m:02d}" for m in range(1, 13)]

REQUESTS = {
    "solar_tech60": ("solar", "60"),
    "solar_tech61": ("solar", "61"),
    "solar_tech62": ("solar", "62"),
    "solar_tech63": ("solar", "63"),
    "wind_onshore_tech30": ("wind_onshore", "30"),
    "wind_offshore_tech20": ("wind_offshore", "20"),
}

VARIABLE_NAMES = {
    "solar": "solar_photovoltaic_generation_capacity_factor",
    "wind_onshore": "wind_power_onshore_capacity_factor",
    "wind_offshore": "wind_power_offshore_capacity_factor",
}

SPATIAL_RESOLUTION = {
    "solar": "nuts_2",
    "wind_onshore": "peon",
    "wind_offshore": "peof",
}


def year_chunks(start_year: int, end_year: int, chunk_size: int) -> list[tuple[int, int]]:
    """Split [start_year, end_year] into consecutive `chunk_size`-year windows."""
    chunks = []
    chunk_start = start_year
    while chunk_start <= end_year:
        chunk_end = min(chunk_start + chunk_size - 1, end_year)
        chunks.append((chunk_start, chunk_end))
        chunk_start = chunk_end + 1
    return chunks


def main(start_year: int = START_YEAR, end_year: int = END_YEAR, chunk_size: int = CHUNK_SIZE_YEARS) -> None:
    """Download every (variable, technology, year-chunk) combination.

    Defaults to the full START_YEAR-END_YEAR range in CHUNK_SIZE_YEARS-year
    chunks; pass a narrow `start_year`/`end_year` (e.g. both `2024`) to
    smoke-test the request/parsing path cheaply before committing to the
    full multi-decade download.
    """
    paths = ProjPaths()
    paths.ensure_directories()

    client = cdsapi.Client()

    for label, (kind, technology) in REQUESTS.items():
        for chunk_start, chunk_end in year_chunks(start_year, end_year, chunk_size):
            output_file = paths.pecd_capacity_factor_zip(kind, technology, chunk_start, chunk_end)
            if output_file.exists():
                print(f"{label} {chunk_start}-{chunk_end}: already downloaded -> {output_file}")
                continue

            years = [str(y) for y in range(chunk_start, chunk_end + 1)]
            request = {
                "pecd_version": "pecd4_2",
                "temporal_period": "historical",
                "origin": "era5_reanalysis",
                "variable": VARIABLE_NAMES[kind],
                "technology": technology,
                "spatial_resolution": SPATIAL_RESOLUTION[kind],
                "year": years,
                "month": MONTHS,
                "file_version": "fv1",
            }
            if kind != "solar":
                request["energy_scenario"] = "resource_grade_b"

            print(f"{label} {chunk_start}-{chunk_end}: requesting ...")
            retrieve_with_retries(client, "sis-energy-pecd", request, str(output_file))
            print(f"  saved -> {output_file}")


if __name__ == "__main__":
    main()
