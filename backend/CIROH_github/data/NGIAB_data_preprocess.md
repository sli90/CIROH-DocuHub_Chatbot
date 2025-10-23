# Project Title: **NGIAB_data_preprocess**

## Project Objective
Tools to prepare data for running a [NextGen](https://github.com/NOAA-OWP/ngen)-based simulation using NGIAB by letting users select a catchment on an interactive map, choose a date range, and generate a runnable package with a few clicks. Intended for hydrology practitioners who want to subset hydrofabric data, compute forcings, and build NGIAB-ready configurations efficiently.

## Core Functionalities
- **Interactive map workflow:** Select a catchment/point of interest, pick a time period, and execute steps to subset, create forcings, and create a realization.
- **Hydrofabric subsetting:** Delineates the upstream network for the chosen feature and outputs a geopackage (`.gpkg`).
- **Forcings generation:** Computes weighted-mean forcings from **NWM retrospective v3** or **AORC 1 km** gridded datasets (weights via *exactextract* and computed with NumPy).
- **Configuration creation:** Produces NGIAB-ready configs (e.g., `realization.json`, `troute.yaml`, and per‑catchment settings).
- **Optional non‑interactive run:** Can automatically run NGIAB’s Docker distribution on the prepared folder.
- **CLI & Map apps:** Run via `ngiab-prep` CLI or `map_app` with UV/pipx support; includes combined flags for end‑to‑end prep.

## Technical Stack
- **Language:** Python (implied by UV/pip installation and module invocation).
- **Key Libraries/Tools:** NumPy; *exactextract*; Docker (NGIAB distribution); Astral **UV**; `pipx`/`uvx`.
- **Ecosystem/Models:** NextGen; NGIAB; optional TEEHR for evaluation (via NGIAB).
- **OS Support:** Officially supported on macOS and Ubuntu; Windows via WSL.

## Setup and Usage
- **Run without install:** Use `uvx` to invoke the CLI (`uvx ngiab-prep`) or the map app (`uvx --from ngiab-data-preprocess map_app`).
- **Install with UV:** Create a venv (`uv venv`), install (`uv pip install ngiab_data_preprocess`), then run `uv run cli --help` or `uv run map_app`.
- **Legacy pip (virtual env recommended):** `pip install 'ngiab_data_preprocess'` then `python -m map_app`.
- **Typical workflow (map app):** 1) Create subset GPKG → 2) Create Forcing from Zarrs → 3) Create Realization; outputs saved under `~/ngiab_preprocess_output/<your-input-feature>/`.

## Project Context & Domain
- **Domain:** Hydrology / Hydrologic modeling.
- **Funding & Affiliation:** Funded by **NOAA** and awarded to **CIROH** via NOAA Cooperative Agreement with **The University of Alabama** (NA22NWS4320003).
- **Data Sources:** Hydrofabric v2.2; NWM retrospective v3 forcings; AORC 1 km gridded data.

## Input / Output
**Input:** Selected feature (catchment/gage/lat‑lon), date range, Hydrofabric v2.2 geometries & attributes, and choice of forcing source (NWM v3 or AORC).  
**Output:** Subset geopackage (`.gpkg`), computed forcings, and NGIAB configuration files (`realization.json`, `troute.yaml`, per‑catchment configs); optional NGIAB run artifacts in the output folder.

## Known Limitations
- Outputs only a **single default realization** (NOAH + CFE + SLoTH).
- **Calibration:** Downloads calibrated parameters when available; falls back to defaults if not.
- **Evaluation & Visualization:** Use NGIAB interactively (via `guide.sh`) for TEEHR evaluation and visualization.
