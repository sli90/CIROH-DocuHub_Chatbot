# HydroShare Resource Metadata: Python Notebook for Retrieving Retrospective National Water Model Forecasts

## Resource Identification
- **Title**: Python Notebook for Retrieving Retrospective National Water Model Forecasts
- **DOI**: 10.4211/hs.5caaa9919c2e490eb735aebc5e741c35
- **URL**: https://www.hydroshare.org/resource/5caaa9919c2e490eb735aebc5e741c35/
- **Resource ID**: 5caaa9919c2e490eb735aebc5e741c35

## Authors and Contributors
- **Author**: Dan Ames
- **Owner**: Dan Ames

## Resource Details
- **Type**: Resource
- **Storage Size**: 12.3 KB
- **License**: Creative Commons Attribution CC BY (http://creativecommons.org/licenses/by/4.0/)
- **Content Type**: Jupyter Notebooks
- **Sharing Status**: Public & Shareable
- **Views**: 2376
- **Downloads**: 147
- **+1 Votes**: 2
- **Comments**: 1

## Temporal Information
- **Created**: November 17, 2023 at 10:34 p.m. (UTC)
- **Last Updated**: October 10, 2024 at 5:15 p.m. (UTC)
- **Temporal Coverage**: February 1, 1979 to December 31, 2020

## Spatial Coverage
- **Coordinate System**: WGS 84 EPSG:4326
- **North Latitude**: 48.8412°
- **East Longitude**: -48.6914°
- **South Latitude**: 23.7728°
- **West Longitude**: -137.8125°

## Abstract
This python notebook demonstrates a simple method for retrieving time series data from the Amazon Web Services (AWS) archive of the U.S. National Water Model retrospective streamflow forecasts for one or more reach id's (also known as COMIDs) for a specified date range. Note that this notebook uses the 42-year (February 1979 through December 2020) retrospective simulation using version 2.1 of the National Water Model. The AWS archive and description of the data can be found here: https://registry.opendata.aws/nwm-archive/. This notebook uses the xarray library to connect to the data store as an anonymous user. The connection results in a zarr store from which data can be extracted using the method shown in the script. This method is not optimized for parallel computing so it will be slow if you specify a lot of reach ids. The results are written to a local CSV file that can be opened in Excel or another spreadsheet. There are many optimizations that can be done to improve data access, but this notebook is intentionally simple for the novice user who is trying to work with National Water Model retrospective data stored in AWS.

## Keywords
- ciroh
- streamflow
- nwm
- aws
- national water model
- forecast
- retrospective

## Files
- **nwm_xarray_zarr_v2.ipynb**: 9.1 KB
- **nwm_xarray_zarr.ipynb**: 3.1 KB

## Related Resources
- Part of collection: **Curated List of Datasets for the CIROH Portal**
  - Owner: Dan Ames
  - URL: https://www.hydroshare.org/resource/302dcbef13614ac486fb260eaa1ca87c/

## Available Tools
- MATLAB Online
- CUAHSI JupyterHub
- CIROH 2i2c JupyterHub

## Important Note
As mentioned in the comments, the s3fs module changed and may break the notebook. To use the notebook, specify the version of s3fs to install:
```
!pip install s3fs==0.4
```

## Citation
Ames, D. (2024). Python Notebook for Retrieving Retrospective National Water Model Forecasts, HydroShare, http://www.hydroshare.org/resource/5caaa9919c2e490eb735aebc5e741c35
