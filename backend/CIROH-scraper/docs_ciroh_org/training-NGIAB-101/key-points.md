# Key Points

## Introduction

- The Next Generation Water Resources Modeling Framework (NextGen) advances the National Water Model with flexible, modular, and regionally adaptive hydrologic modeling at national scale.
- NextGen In A Box (NGIAB) packages the complex NextGen system into an open-source, containerized application for easier access and usability.
- NGIAB uses Docker and Singularity for portability across local machines, cloud platforms, and HPC systems.
- NGIAB's multi-layered architecture integrates hydrologic modeling tools, CI/CD pipelines, and supportive technologies and is complemented by a suite of extensions that allow for end-to-end workflows from data acquisition to visualization and evaluation.
- NGIAB fosters an open ecosystem where researchers, developers, and practitioners actively contribute new models, extensions, and workflows.

## Installation and Setup

- NGIAB simplifies NextGen framework deployment through Docker.
- Use `guide.sh` for interactive configuration and run execution.
- Always confirm successful setup by executing provided sample runs.

## Data Preparation

- `ngen-run/` is the standard NextGen run directory, containing the realization files that define models, parameters, and run settings; forcing data; outputs; as well as the spatial hydrofabric.
- The Data Preprocess tool simplifies preparing data for NextGen by offering a GUI and CLI for selecting catchments and date ranges, subsetting hydrofabric data, generating forcing files, and creating realization files.

## Model Execution

- To execute a NextGen run in NGIAB with full functionality, use `guide.sh` in the NGIAB container.
- A NextGen run in NGIAB can also be automatically executed post-preprocessing using the Data Preprocess tool.

## Evaluation

- Tools for Exploratory Evaluation in Hydrologic Research (TEEHR) is a Python-based package for hydrologic model evaluation.
- NGIAB uses TEEHR to assess model performance, comparing predictions against USGS streamflow and NWM data and calculating performance metrics.
- TEEHR runs automatically with the main `guide.sh` NGIAB script.

## Visualization

- The Data Visualizer (built on the Tethys Platform) provides interactive geospatial maps and time series plots for NextGen model outputs in NGIAB.
- It integrates seamlessly with NGIAB via `guide.sh` or `ViewOnTethys.sh`.
- Model outputs reside under `~/ngiab_visualizer`, with metadata stored in `ngiab_visualizer.json`.
- You can visualize Nexus points, catchment summaries, Troute variables, and TEEHR hydrographs and performance metrics.

## Calibration

- The `ngiab-cal` package is used to calibrate parameters for a NextGen model run.
- `ngiab-cal` is a command-line tool controlled via a YAML configuration file that determines parameter ranges, time periods, and evaluation metrics.

## Advanced Topics

- NGIAB supports HPC environments through Singularity, not Docker, but the workflow mirrors the local Docker use.
- Port forwarding is required to use the Data Visualizer through an SSH connection.
- Community contribution guidelines are available in each repository's GitHub page.