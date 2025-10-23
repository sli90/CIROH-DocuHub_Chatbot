# Project Title: **forcingprocessor**

## Project Objective  
The **Forcing Processor** converts **National Water Model (NWM)** gridded forcing data into **NextGen**-compatible catchment-averaged time series. It serves as the **pre-processing tool** for the [NextGen Research DataStream](https://github.com/CIROH-UA/ngen-datastream), ensuring hydrologic input data can be efficiently transformed and used in the Next Generation National Water Model framework.  
It is primarily intended for hydrologic researchers and practitioners working with NWM or NextGen data who need to generate or manage forcing datasets in standardized formats.

## Core Functionalities  
- **Data Conversion:** Transforms NWM gridded forcings (netCDFs) into catchment-averaged NextGen time series.  
- **Automated Weight Calculation:** Uses [exactextract](https://github.com/isciences/exactextract) to compute polygonal cell coverage and weights for catchment averaging if not provided in the geopackage.  
- **Flexible Input Support:** Accepts local file paths, S3 URIs, or URLs for geopackages and forcing data.  
- **Parallel Processing:** Supports multi-core execution with configurable process counts (`nprocs`).  
- **Visualization:** Optionally generates side-by-side **GIFs** comparing NWM and NextGen forcings for selected variables.  
- **Configurable Outputs:** Supports multiple formats (`tar`, `parquet`, `csv`, `netcdf`) and local or cloud storage options.  
- **File Name Generation:** Provides a helper tool (`nwm_filenames_generator.py`) to automatically create lists of NWM forcing filenames.  
- **Weights Reuse:** Saves computed weights as a parquet file for reuse in future runs.  

## Technical Stack  
- **Language:** Python  
- **Key Libraries/Tools:**  
  - `exactextract` (for spatial averaging)  
  - `hfsubset` (for geopackage creation)  
  - `nwmurl` (for URL generation of NWM forcing files)  
- **Data Formats:** netCDF, GeoPackage (`.gpkg`), Parquet, CSV, TAR  
- **Parallelization:** Multi-processing support via configurable cores  

## Setup and Usage  
- **Installation:**  
  ```bash
  pip install -e .
  ```  
- **Execution:**  
  Run the processor using a JSON configuration file:  
  ```bash
  python src/forcingprocessor/processor.py ./configs/conf.json
  ```  
- **Configuration:**  
  The `conf.json` file defines four main sections:  
  1. **Forcing** — Paths to NWM filename list and geopackage file.  
  2. **Storage** — Output location and file types.  
  3. **Run** — Processing parameters (verbosity, stats collection, parallelization).  
  4. **Plot** — Visualization settings for generating GIFs.  
- **Example Generator Usage:**  
  ```bash
  python nwm_filenames_generator.py conf_nwm_files.json
  ```  
- **Weights Calculation (if needed):**  
  ```bash
  python3 src/forcingprocessor/weights_hf2ds.py   --outname ./weights.parquet   --input_file ./nextgen_VPU_03W.gpkg
  ```

## Project Context & Domain  
- **Domain:** Hydrology / Hydrologic modeling and data preprocessing  
- **Affiliation:** Developed by CIROH (Cooperative Institute for Research to Operations in Hydrology) under the **University of Alabama** in coordination with **NOAA**.  
- **Purpose:** Supports the preprocessing pipeline for the **NextGen Research DataStream**, standardizing NWM input data for model-ready use.

## Input / Output  
**Input:**  
- Text file listing NWM forcing filenames (local paths, URLs, or S3 URIs).  
- GeoPackage (`.gpkg`) defining spatial domain with optional `forcing-weights` layer.  
- Optional configuration for weights calculation or plotting parameters.  

**Output:**  
- Catchment-averaged NextGen forcing datasets in chosen formats (`tar`, `parquet`, `csv`, `netcdf`).  
- Optional GIF visualizations comparing NWM and NextGen forcings.  
- Reusable weights parquet file written to metadata.  
