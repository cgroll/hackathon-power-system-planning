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
    def downloads_path(self) -> Path:
        """Raw downloaded data."""
        return self.data_path / "downloads"

    @property
    def processed_data_path(self) -> Path:
        """Processed/transformed data."""
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

    @property
    def intermediate_data_path(self) -> Path:
        """Build-only intermediate outputs -- not tracked in git (see .gitignore).

        Distinct from `processed_data_path` (which holds the final,
        git-tracked Track A/B deliverables) so the two are never confused:
        anything here is fully rebuildable from `data/downloads/` and isn't
        itself something a hackathon team should read from.
        """
        return self.processed_data_path / "_intermediate"

    @property
    def pecd_downloads_path(self) -> Path:
        """Raw PECD v4.2 CDS downloads (pipeline/01)."""
        return self.downloads_path / "pecd"

    # ------------------------------------------------------------------ #
    # PECD raw downloads (pipeline/01)                                     #
    # ------------------------------------------------------------------ #

    def pecd_capacity_factor_zip(self, kind: str, technology: str, start_year: int, end_year: int) -> Path:
        """Raw CDS capacity-factor download, all of Europe, one 10-year chunk.

        `kind` is one of "solar", "wind_onshore", "wind_offshore";
        `technology` is PECD's technology code (e.g. "60" for solar
        industrial rooftop, "30" for existing onshore wind). Chunked by
        year range (not one file per `kind`/`technology`) because a single
        1980-2025 request exceeds the CDS API's per-request cost limit —
        see pipeline/01's module docstring.
        """
        return self.pecd_downloads_path / f"{kind}_tech{technology}_{start_year}-{end_year}.zip"

    def pecd_capacity_factor_zips(self, kind: str, technology: str) -> list[Path]:
        """All downloaded year-chunk zips for one (kind, technology), sorted by start year."""
        return sorted(self.pecd_downloads_path.glob(f"{kind}_tech{technology}_*.zip"))

    # ------------------------------------------------------------------ #
    # Intermediate zonal capacity factors, full 1980-2025 (pipeline/02)    #
    # ------------------------------------------------------------------ #

    @property
    def capacity_factors_zonal_wind_onshore_intermediate(self) -> Path:
        """Germany-only PEON wind-onshore capacity factors, hourly, full 1980-2025 range."""
        return self.intermediate_data_path / "capacity_factors_zonal_wind_onshore.parquet"

    @property
    def capacity_factors_zonal_wind_offshore_intermediate(self) -> Path:
        """Germany-only PEOF wind-offshore capacity factors, hourly, full 1980-2025 range."""
        return self.intermediate_data_path / "capacity_factors_zonal_wind_offshore.parquet"

    @property
    def capacity_factors_zonal_solar_intermediate(self) -> Path:
        """Germany-only NUTS2 solar capacity factors, hourly, full 1980-2025 range.

        MultiIndex columns (technology, region): 4 PECD PV sub-types x DE
        NUTS2 regions.
        """
        return self.intermediate_data_path / "capacity_factors_zonal_solar.parquet"

    # ------------------------------------------------------------------ #
    # Track A deliverables: zonal capacity factors + raw MaStR ingredients #
    # (pipeline/03, 05, 06)                                                #
    # ------------------------------------------------------------------ #

    @property
    def mastr_units_wind_solar(self) -> Path:
        """Per-unit MaStR wind + solar capacity records (Track A raw ingredient).

        Built by pipeline/03_prepare_mastr_track_a_inputs.py. Columns:
        technology ("solar"/"wind" -- onshore/offshore not yet split),
        region_code (MaStR's own NUTS3-like code, not a PECD zone),
        capacity_mw, commissioning_date, final_shutdown_date, longitude,
        latitude, installation_type, usage_sector, main_orientation,
        main_orientation_tilt_bucket (the last 4 are solar-only, NaN for
        wind -- everything needed to classify a solar unit into PECD's 4
        technology codes, see pipeline/03's docstring for the rule), and
        pv_category (solar-only: full_feed_in / self_consumption_no_storage
        / self_consumption_with_storage / unknown -- a different axis, not
        needed for the technology split, not used by anything in this
        repo's hackathon scope, but cheap to carry along for later
        behind-the-meter/self-consumption analysis, see PROJECT.md,
        2026-09-18). No unit_id: already used internally to join the
        orientation columns in from a separate MaStR table, then dropped
        -- keeping it would have added ~40 MB for no pedagogical benefit
        (it's a join key, not part of the classification exercise).
        Deliberately *not* zone-joined, technology-classified, or
        month-aggregated -- that's Track A's exercise, see the script's
        module docstring.
        """
        return self.processed_data_path / "mastr_units_wind_solar.parquet"

    @property
    def pecd_region_mask_peon(self) -> Path:
        """PEON (wind onshore) zone-membership weights per 0.25-degree grid cell, Germany only.

        Built by pipeline/03, cropped from PECD's full-Europe region mask.
        Columns: zone_id, latitude, longitude, weight (nonzero only) --
        the fractional area of that cell covered by that zone. Use with
        `mastr_units_wind_solar`'s coordinates (nearest-cell snap) to
        assign each unit to a PEON zone (Track A's exercise).
        """
        return self.processed_data_path / "pecd_region_mask_peon.parquet"

    @property
    def pecd_region_mask_peof(self) -> Path:
        """Same as `pecd_region_mask_peon`, for PEOF (wind offshore) zones."""
        return self.processed_data_path / "pecd_region_mask_peof.parquet"

    @property
    def capacity_factors_zonal_wind_onshore(self) -> Path:
        """Germany-only PEON wind-onshore capacity factors, hourly, 2015-2025 (Track A)."""
        return self.processed_data_path / "capacity_factors_zonal_wind_onshore.parquet"

    @property
    def capacity_factors_zonal_wind_offshore(self) -> Path:
        """Germany-only PEOF wind-offshore capacity factors, hourly, 2015-2025 (Track A)."""
        return self.processed_data_path / "capacity_factors_zonal_wind_offshore.parquet"

    @property
    def capacity_factors_zonal_solar(self) -> Path:
        """Germany-only NUTS2 solar capacity factors, hourly, 2015-2025 (Track A)."""
        return self.processed_data_path / "capacity_factors_zonal_solar.parquet"

    @property
    def generation_de_by_technology(self) -> Path:
        """SMARD actual per-technology grid feed-in: pv, wind_onshore, wind_offshore (Track A)."""
        return self.processed_data_path / "generation_de_by_technology.parquet"

    # ------------------------------------------------------------------ #
    # Track B deliverables: national, fixed "today" capacity (pipeline/04, 06) #
    # ------------------------------------------------------------------ #

    @property
    def capacity_factors_de_national(self) -> Path:
        """Hourly national capacity factors for DE (wind onshore/offshore, solar).

        Built by pipeline/04_prepare_capacity_factors_national.py: official
        PECD zone-level product, capacity-weighted to national using
        *today's* (latest available month's) fixed MaStR snapshot, 1980-2025.
        Columns: wind_onshore, wind_offshore, solar (all in [0, 1]).
        """
        return self.processed_data_path / "capacity_factors_de_national.parquet"

    @property
    def demand_de_national(self) -> Path:
        """Hourly national electricity demand for DE, MW (Track B, `demand_mw` column)."""
        return self.processed_data_path / "demand_de_national.parquet"

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def ensure_directories(self) -> None:
        """Create all standard directories if they do not yet exist."""
        dirs = [
            self.downloads_path,
            self.pecd_downloads_path,
            self.processed_data_path,
            self.intermediate_data_path,
            self.images_path,
            self.reports_path,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
