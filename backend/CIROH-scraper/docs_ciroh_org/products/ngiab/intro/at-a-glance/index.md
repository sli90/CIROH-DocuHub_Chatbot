---
title: NGIAB at a Glance
source: https://docs.ciroh.org/docs/products/ngiab/intro/at-a-glance
scraped_date: 2025-07-31
---

# NGIAB at a Glance

Explore the NextGen In A Box (NGIAB) ecosystem through the interactive tabs below.

Click on Key Features, Capabilities, or Access Methods to learn more.

* * *

## Key Features

| NGIAB and Extensions | Key features | NOAA-OWP Tools/Libraries Utilized |
| --- | --- | --- |
| [Data Preprocess](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-preprocessor/) | - Specializes in initial data preparation<br>- Handles subsetting and forcing processing<br>- Supports basic data processing tasks<br>- Helps with running NGIAB | - t-route<br>- hydrotools<br>- hydrofabric tools |
| NGIAB Implementation<br>( [Cloud](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-docker/), [HPC](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-singularity/)) | - Focused specifically on model execution<br>- Core engine for running simulations<br>- Does not handle pre/post-processing tasks |  |
| [TEEHR Evaluation](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-teehr/) | - Handles both input and output processing<br>- Supports full workflow, from data preparation to cloud deployment | Built to evaluate OWP model outputs |
| [Data Visualizer](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-visualizer/) | - Focused on analysis and validation<br>- Supports data processing and output analysis | Designed for OWP hydrofabric visualization |
| [DataStreamCLI](https://docs.ciroh.org/docs/products/research-datastream/) | - Complete workflow for creating inputs for and executing NGIAB and managing outputs<br>- Backend of the NextGen Research DataStream<br>- Discrete tooling for tasks like forcing processing and BMI file generation | - ngen-cal<br>- t-route<br>- hydrofabric tools |
| [NGIAB-Cal](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-calibration/) | - Simplifies hydrologic model calibration for NGIAB workflows<br>- Creates calibration directory and configurations within the NGIAB folder structure<br>- Runs calibration process using Docker<br>- Copies calibrated parameters to model configurations | - ngen-cal |

## Capabilities

| Capabilities | [Data Preprocess](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-preprocessor/) | NGIAB Implementation<br>( [Cloud](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-docker/), [HPC](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-docker/)) | [TEEHR Evaluation](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-teehr/) | [Data Visualizer](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-visualizer/) | [DataStreamCLI](https://docs.ciroh.org/docs/products/research-datastream/) | [NGIAB-Cal](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-calibration/) |
| --- | --- | --- | --- | --- | --- | --- |
| GUI | ✅ | - | - | ✅ | - | - |
| Hydrofabric Subsetting | ✅ | - | - | ✅ (view only) | ✅🔨 | - |
| NetCDF Forcing Processing | - | - | ✅ | - | ✅🔨 | - |
| Zarr Forcing Processing | ✅ | - | ✅ | - | - | - |
| Forcing Metadata Generation | ✅ | - | - | - | ✅🔨 | - |
| Calibration Configuration Generation | ✅ | - | - | - | ✅🔨 | ✅ |
| NGIAB Input Generation | ✅ | - | - | - | ✅🔨 | - |
| Remote NGIAB Run | - | - | - | - | ✅ | - |
| Local NGIAB Run | - | ✅ | - | - | ✅ | - |
| NGIAB Output Analysis | - | - | ✅ | ✅ | - | - |
| NGIAB Output (in cloud) | - | - | ✅ | - | ✅ | - |
| Calibrated Parameter Output | - | - | - | - | - | ✅ |
| Integrated into NGIAB | - | N/A | - | ✅ | - | ✅ |

## Access Methods

| Access method | [Data Preprocess](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-preprocessor/) | NGIAB Implementation<br>( [Cloud](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-docker/), [HPC](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-docker/)) | [TEEHR Evaluation](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-teehr/) | [Data Visualizer](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-visualizer/) | [DataStreamCLI](https://docs.ciroh.org/docs/products/research-datastream/) | [NGIAB-Cal](https://docs.ciroh.org/docs/products/ngiab/components/ngiab-calibration/) |
| --- | --- | --- | --- | --- | --- | --- |
| Docker | - | ✅ | ✅ | ✅ | ✅ | ✅ |
| Python Package (pip/uv) | ✅ | ✅ | ✅ | - | - | ✅ |
| Web Interface | ✅ | - | - | ✅ | - | - |
| Notebook (ipynb) | - | - | ✅ | - | - | - |
| Singularity (HPC) | - | ✅ | - | - | - | - |