"""Project paths configuration.

All paths are resolved relative to the project root, making scripts runnable
from any working directory. Add a @property for each new data file introduced
in the pipeline.
"""

from pathlib import Path


class ProjPaths:
    """Centralized project paths.

    The root is inferred from the location of this file (hpsp/), so scripts
    run correctly regardless of the working directory they are invoked from.
    """

    def __init__(self):
        self._pkg_path = Path(__file__).resolve().parent  # hpsp/
        self._project_path = self._pkg_path.parent        # project root

    # ------------------------------------------------------------------ #
    # Top-level directories                                                #
    # ------------------------------------------------------------------ #

    @property
    def project_path(self) -> Path:
        """Root project directory."""
        return self._project_path

    @property
    def pkg_path(self) -> Path:
        """Source package directory (hpsp/)."""
        return self._pkg_path

    @property
    def pipeline_path(self) -> Path:
        """Pipeline scripts directory."""
        return self._project_path / "pipeline"

    # ------------------------------------------------------------------ #
    # Data directories                                                     #
    # ------------------------------------------------------------------ #

    @property
    def data_path(self) -> Path:
        """Main data directory."""
        return self._project_path / "data"

    @property
    def input_path(self) -> Path:
        """Input data copied from `energy-data-hub` (git-ignored, not committed).

        See `book/markdown/data_sources.md` for exactly what's here and
        where it comes from. Nothing under this directory is produced by
        this repo's own pipeline -- it's the starting material.
        """
        return self.data_path / "input"

    @property
    def input_pecd_path(self) -> Path:
        """PECD v4.2 capacity-factor data (zonal + national-aggregated)."""
        return self.input_path / "pecd"

    @property
    def input_mastr_path(self) -> Path:
        """Lightly-processed, unit-level Marktstammdatenregister (MaStR) data."""
        return self.input_path / "mastr"

    @property
    def input_regions_path(self) -> Path:
        """Region-code crosswalks (LAU/NUTS)."""
        return self.input_path / "regions"

    @property
    def processed_data_path(self) -> Path:
        """Processed/transformed data produced by this repo's own pipeline.

        Empty until a pipeline stage (yours, or the example one in
        `pipeline/01_explore_capacity_factors_de.py`) writes something here.
        """
        return self.data_path / "processed"

    # ------------------------------------------------------------------ #
    # Output directories                                                   #
    # ------------------------------------------------------------------ #

    @property
    def output_path(self) -> Path:
        """Generated outputs root."""
        return self._project_path / "output"

    @property
    def images_path(self) -> Path:
        """Chart/figure images saved by pipeline scripts."""
        return self.output_path / "images"

    @property
    def reports_path(self) -> Path:
        """Report files."""
        return self.output_path / "reports"

    # ------------------------------------------------------------------ #
    # Track A input: zonal PECD capacity factors + region masks (2015-2025) #
    # ------------------------------------------------------------------ #

    @property
    def pecd_capacity_factors_zonal_wind_onshore(self) -> Path:
        """Germany-only PEON wind-onshore capacity factors, hourly, 2015-2025.

        Columns `DE01`-`DE07` (one per PEON zone).
        """
        return self.input_pecd_path / "pecd_wind_onshore_capacity_factors.parquet"

    @property
    def pecd_capacity_factors_zonal_wind_offshore(self) -> Path:
        """Germany-only PEOF wind-offshore capacity factors, hourly, 2015-2025.

        Columns `DE011_OFF` etc. (one per PEOF zone).
        """
        return self.input_pecd_path / "pecd_wind_offshore_capacity_factors.parquet"

    @property
    def pecd_capacity_factors_zonal_solar(self) -> Path:
        """Germany-only NUTS2 solar capacity factors, hourly, 2015-2025.

        MultiIndex columns (technology, region): PECD's 4 PV sub-technology
        codes (60/61/62/63) x DE NUTS2 regions.
        """
        return self.input_pecd_path / "pecd_solar_capacity_factors.parquet"

    @property
    def pecd_region_mask_peon(self) -> Path:
        """PEON (wind onshore) zone-membership raster, all of Europe.

        NetCDF, dims (region, latitude, longitude), 0.25-degree grid.
        Subset `region` to values starting `"DE"` for Germany's zones.
        """
        return self.input_pecd_path / "peon_region_mask.nc"

    @property
    def pecd_region_mask_peof(self) -> Path:
        """Same as `pecd_region_mask_peon`, for PEOF (wind offshore) zones."""
        return self.input_pecd_path / "peof_region_mask.nc"

    # ------------------------------------------------------------------ #
    # Track B input: national-aggregated PECD capacity factors (1980-2025) #
    # ------------------------------------------------------------------ #

    @property
    def pecd_capacity_factors_national_de(self) -> Path:
        """Hourly national capacity factors for Germany, 1980-2025, ready to use.

        Columns: wind_onshore, wind_offshore, solar (all in [0, 1]). See
        `book/markdown/data_sources.md` for the aggregation method and its
        known simplifications.
        """
        return self.input_pecd_path / "pecd_country_capacity_factors_simple_de.parquet"

    @property
    def pecd_capacity_factors_national_europe(self) -> Path:
        """Same as `pecd_capacity_factors_national_de`, all ~53 PECD countries.

        Wide columns, MultiIndex (technology, country ISO2-ish code).
        **Caveat:** the solar blend uses Germany's own technology-mix
        weights for every country -- see `book/markdown/data_sources.md`.
        """
        return self.input_pecd_path / "pecd_country_capacity_factors_simple.parquet"

    # ------------------------------------------------------------------ #
    # Track A input: raw(ish) MaStR unit-level records                     #
    # ------------------------------------------------------------------ #

    @property
    def mastr_solar_units(self) -> Path:
        """Per-unit MaStR solar records (~6.3M rows), not zone-joined or aggregated."""
        return self.input_mastr_path / "solar.parquet"

    @property
    def mastr_wind_units(self) -> Path:
        """Per-unit MaStR wind records (~43K rows), not zone-joined or aggregated.

        Includes `wind_onshore_or_offshore` directly -- no derivation needed
        for the onshore/offshore split.
        """
        return self.input_mastr_path / "wind.parquet"

    @property
    def mastr_solar_technical_detail(self) -> Path:
        """Per-solar-unit orientation/tilt detail. Join to `mastr_solar_units` via `unit_id`."""
        return self.input_mastr_path / "solar_technical_detail.parquet"

    @property
    def lau_nuts_correspondence(self) -> Path:
        """LAU (municipality_key) -> NUTS3 crosswalk.

        Needed to map a solar unit's `municipality_key` to its NUTS3 region,
        then to its NUTS2 parent (first 4 characters) -- solar units mostly
        lack coordinates, so this string-based path is the way in, not the
        region masks used for wind.
        """
        return self.input_regions_path / "lau_nuts_correspondence.parquet"

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def ensure_directories(self) -> None:
        """Create all standard directories if they do not yet exist."""
        dirs = [
            self.input_path,
            self.input_pecd_path,
            self.input_mastr_path,
            self.input_regions_path,
            self.processed_data_path,
            self.images_path,
            self.reports_path,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
