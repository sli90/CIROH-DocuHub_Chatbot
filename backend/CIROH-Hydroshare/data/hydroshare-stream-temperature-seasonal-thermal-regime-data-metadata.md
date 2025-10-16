# HydroShare Resource Metadata: Stream Temperature Seasonal Thermal Regime Data

## Resource Identification
- **Title**: Stream Temperature Seasonal Thermal Regime Data
- **DOI**: 10.4211/hs.7d960b7fdfee480895fd845bade1b75a
- **URL**: https://www.hydroshare.org/resource/7d960b7fdfee480895fd845bade1b75a/
- **Resource ID**: 7d960b7fdfee480895fd845bade1b75a

## Authors and Contributors
- **Author 1**: Daniel Philippus
- **Author 2**: Claudia R Corona
- **Author 3**: Terri S Hogue
- **Owner 1**: Daniel Philippus
- **Owner 2**: CUAHSI Hydroshare Publisher

## Resource Details
- **Type**: Resource
- **Storage Size**: 687.3 MB
- **License**: Creative Commons Attribution CC BY (http://creativecommons.org/licenses/by/4.0/)
- **Content Type**: Single File Content
- **Sharing Status**: Published
- **Views**: 1476
- **Downloads**: 20
- **Comments**: 0

## Temporal Information
- **Created**: January 10, 2024 at 9:34 p.m. (UTC)
- **Last Updated**: September 16, 2024 at 8:16 p.m. (UTC) (Metadata update)
- **Published Date**: July 11, 2024 at 1:36 p.m. (UTC)
- **Temporal Coverage**: October 16, 1964 to January 1, 2023

## Spatial Coverage
- **Place/Area Name**: United States
- **Coordinate System**: WGS 84 EPSG:4326
- **North Latitude**: 70.5000°
- **East Longitude**: -67.2500°
- **South Latitude**: 19.7100°
- **West Longitude**: -163.6800°

## Abstract
This resource contains analysis code and downloaded stream temperature data (from USGS NWIS) used to develop an analysis of stream seasonal thermal regimes in the United States. The R Notebook, `analysis.Rmd`, will reproduce all supporting analysis and generate figures when run with the data files downloaded into a `Data` subdirectory of the working directory. `analysis.Rmd` calls more involved functions from `functions.R`. The knitted version of the notebook is also included as `analysis.pdf`.

To run the Notebook, in the working directory there must be a `Data` directory containing the data files and a `Figures` directory with a `MovingWindowSeasons` subdirectory, where figures will be stored. For map generation, `functions.R` will also look for an EPA Level I Ecoregions (https://gaftp.epa.gov/EPADataCommons/ORD/Ecoregions/cec_na/na_cec_eco_l1.zip) shapefile in an `Ecoregions` directory.

These data and related items of information have not been formally disseminated by NOAA, and do not represent any agency determination, view, or policy.

## Keywords
- stream seasonal thermal regime
- united states
- stream annual temperature cycle
- stream temperature

## Files
- **ecoregions.csv**: 160.5 KB
- **GageData.csv**: 493.4 MB
- **GageTemperatures.csv**: 190.4 MB
- **analysis.pdf**: 800.7 KB
- **GageInfo.txt**: 119.1 KB
- **GageList.txt**: 2.4 MB (Single File Content)
- **functions.R**: 15.9 KB
- **analysis.Rmd**: 37.7 KB

## Related Resources
- Referenced by: Philippus, Daniel, Claudia R. Corona and Terri S. Hogue 2024. "Improved Annual Temperature Cycle Function For Stream Seasonal Thermal Regimes." JAWRA Journal of the American Water Resources Association. https://doi.org/10.1111/1752-1688.13228

## Available Tools
- MATLAB Online
- CyberGIS-Jupyter for Water
- CUAHSI JupyterHub
- CIROH 2i2c JupyterHub

## Funding Information
- **Agency**: National Oceanic and Atmospheric Administration
- **Award Title**: Cooperative Institute for Research to Operations in Hydrology
- **Award Number**: NA22NWS4320003

## Citation
Philippus, D., C. R. Corona, T. S. Hogue (2024). Stream Temperature Seasonal Thermal Regime Data, HydroShare, https://doi.org/10.4211/hs.7d960b7fdfee480895fd845bade1b75a
