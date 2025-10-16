# HydroShare Resource Metadata: TempEst 2 Development Data: Observed Stream Temperature, Covariates, Performance Data, and Analysis Notebooks

## Resource Identification
- **Title**: TempEst 2 Development Data: Observed Stream Temperature, Covariates, Performance Data, and Analysis Notebooks
- **DOI**: 10.4211/hs.a8b243957f7946e388d10ab206990675
- **URL**: https://www.hydroshare.org/resource/a8b243957f7946e388d10ab206990675/
- **Resource ID**: a8b243957f7946e388d10ab206990675

## Authors and Contributors
- **Author 1**: Daniel Philippus
- **Author 2**: Claudia R Corona
- **Author 3**: Katie Schneider
- **Author 4**: Ashley Rust
- **Author 5**: Terri S Hogue
- **Owner 1**: Daniel Philippus
- **Owner 2**: CUAHSI Hydroshare Publisher

## Resource Details
- **Type**: Resource
- **Storage Size**: 1.7 GB
- **License**: Creative Commons Attribution CC BY (http://creativecommons.org/licenses/by/4.0/)
- **Content Type**: Stream Temperature Model Development Data
- **Sharing Status**: Published
- **Views**: 1495
- **Downloads**: 35
- **Comments**: 0

## Temporal Information
- **Created**: September 16, 2024 at 7:46 p.m. (UTC)
- **Last Updated**: February 4, 2025 at 3:44 p.m. (UTC)
- **Published Date**: February 4, 2025 at 3:44 p.m. (UTC)
- **Temporal Coverage**: January 2, 2001 to December 31, 2022

## Spatial Coverage
- **Place/Area Name**: Contiguous United States
- **Coordinate System**: WGS 84 EPSG:4326
- **North Latitude**: 49.0000°
- **East Longitude**: -67.3000°
- **South Latitude**: 25.1400°
- **West Longitude**: -124.0600°

## Abstract
This resource contains code and data related to the development of the TempEst 2 stream temperature remote sensing model (manuscript in review with Journal of Hydrology). The code includes the model implementation (model.R), some utility functions (valfn.R), data retrieval scripts for Google Earth Engine (eeretrieval.py and datapts.py), and a reproducible validation notebook (validation.Rmd), along with the knitted PDF of the latter (validation.pdf). The main data include stream temperature daily mean/max observations retrieved from the USGS NWIS as well as remotely-sensed and gridded observations retrieved using Google Earth Engine from NLDAS, ESA WorldCover, MODIS, ERA5, and EPA Ecoregions (using eeretrieval.py). These are contained in three files. AllData.csv includes all observations for mean temperature. ExtData.csv ("extended data") adds maximum temperature, at the expense of fewer total observations being included. Ecoregions.csv is not central to the analysis, but includes EPA Level I ecoregion classifications for convenience.

Model performance tests can be reproduced using validation.Rmd. To run validation.Rmd in full, there must be a Data directory with subdirectories Density and TSLen, a Figures directory, at least one of the main data files (AllData.csv, ExtData.csv) or equivalent, and Ecoregions.csv. A knitted version of the Notebook is included in this resource. The error map plots also use an EPA Level I Ecoregions (https://gaftp.epa.gov/EPADataCommons/ORD/Ecoregions/cec_na/na_cec_eco_l1.zip) shapefile, which is assumed to be in an Ecoregions subdirectory of the *parent* directory. This dependency can be removed by replacing the `plot.eco` function with ordinary ggplot plotting.

The two rda (RData) files contain different versions of a pre-trained model. model.rda contains a regular, pre-trained model function that can be used directly to generate predictions. krigs.rda contains a list of the actual fitted kriging models, which can be used for investigating model components (see demo.pdf).

These data and related items of information have not been formally disseminated by NOAA, and do not represent any agency determination, view, or policy.

## Keywords
- river temperature
- ungauged modeling
- modeling
- remote sensing
- contiguous united states
- stream temperature

## Files
- **AllData.csv**: 947.4 MB - All observations for mean temperature
- **Ecoregions.csv**: 85.0 KB - EPA Level I ecoregion classifications
- **ExtData.csv**: 289.4 MB - Extended data with maximum temperature
- **demo.pdf**: 249.8 KB - Model component investigation demo
- **validation.pdf**: 7.3 MB - Knitted validation notebook
- **model.R**: 16.1 KB - Model implementation
- **valfn.R**: 2.2 KB - Utility functions
- **krigs.rda**: 349.7 MB - Fitted kriging models
- **model.rda**: 189.1 MB - Pre-trained model function
- **validation.Rmd**: 44.4 KB - Reproducible validation notebook
- **datapts.py**: 115.2 KB - Data retrieval script for Google Earth Engine
- **eeretrieval.py**: 8.4 KB - Google Earth Engine retrieval script

## Available Tools
- MATLAB Online
- CUAHSI JupyterHub
- CIROH 2i2c JupyterHub

## Funding Information
- **Agency**: National Oceanic and Atmospheric Administration
- **Award Title**: Cooperative Institute for Research to Operations in Hydrology
- **Award Number**: NA22NWS4320003

## Citation
Philippus, D., C. R. Corona, K. Schneider, A. Rust, T. S. Hogue (2025). TempEst 2 Development Data: Observed Stream Temperature, Covariates, Performance Data, and Analysis Notebooks, HydroShare, https://doi.org/10.4211/hs.a8b243957f7946e388d10ab206990675
