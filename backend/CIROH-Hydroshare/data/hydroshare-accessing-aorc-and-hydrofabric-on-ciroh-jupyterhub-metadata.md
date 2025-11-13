# HydroShare Resource Metadata: Accessing AORC and Hydrofabric on CIROH JupyterHub

## Resource Identification
- **Title**: Accessing AORC and Hydrofabric on CIROH JupyterHub
- **DOI**: Not explicitly provided in page
- **URL**: https://www.hydroshare.org/resource/ec43b15ed20744f39bc757f7b2e4d51e/
- **Resource ID**: ec43b15ed20744f39bc757f7b2e4d51e

## Authors and Contributors
### Authors
- Irene Garousi-Nejad

### Owners
- Irene Garousi-Nejad

## Resource Details
- **Type**: Resource
- **Storage Size**: 93.9 KB
- **Content Type**: Geographic Feature Content
- **Sharing Status**: Public
- **Views**: 587
- **Downloads**: 0

## Temporal Information
- **Created**: May 29, 2025 at 1:17 p.m. (UTC)
- **Last Updated**: May 29, 2025 at 1:19 p.m. (UTC)

## Abstract
This resource includes data and codes to access, analyze and work with high community value datasets (AORC, Hydrofabric) through the use of JupyterHub computing platforms linked to HydroShare (CIROH Jupyterhub on 2i2c specifically).

## Spatial Coverage
### Geographic Extent
- **Coordinate System**: WGS 84 EPSG:4326
- **Coordinate Units**: Decimal degrees
- **Bounding Box**:
  - North Latitude: 40.6591°
  - South Latitude: 40.5827°
  - East Longitude: -111.5470°
  - West Longitude: -111.7931°

## Subject Keywords
- AORC
- CIROH
- Big Cottonwood Creek
- Hydrofabric

## Resource Contents

### 1. watershed (Folder)
- **Type**: Geographic Feature Aggregation
- **Description**: GeoFeatureLogicalFile containing watershed data
- **Web Services**: Available via WMS and WFS

### 2. collect-aorc-v1.1.ipynb
- **Size**: 23.5 KB
- **Type**: Jupyter Notebook
- **Description**: Code that collects meteorological data from AORC version 1.1 dataset for a domain of interest and computes averages across sub-catchments

### 3. ngen-hydrofabric-subset.ipynb
- **Size**: 16.6 KB
- **Type**: Jupyter Notebook
- **Description**: Code that creates a subset of hydrofabric data

### 4. readme.md
- **Size**: 1.4 KB
- **Type**: Markdown file
- **Description**: Overview of resource contents and purpose

### 5. getData.py
- **Size**: 5.8 KB
- **Type**: Python script
- **Description**: Used to get SNOTEL data, called in the snow-retrieval-workflow jupyter notebook

### 6. subset.py
- **Size**: 11.0 KB
- **Type**: Python script
- **Description**: Used to subset the NGen Hydrofabric in the ngen-hydrofabric-subset.ipynb jupyter notebook

### Additional Content Files (mentioned in readme):
- **img**: Folder containing images rendered in jupyter notebooks
- **nwm_utils**: Folder containing supplementary code
- **sample-data**: Folder containing input data for basic-fim-mapping.ipynb and flow-duration-analysis.ipynb notebooks
- **basic-fim-mapping.ipynb**: Code for basin flood inundation mapping
- **flow-duration-analysis.ipynb**: Code for retrieving and analyzing streamflow data
- **snow-retrieval-workflow.ipynb**: Code for retrieving snow water equivalent data

## Data Services
### Web Map Service (WMS)
- **URL**: https://geoserver.hydroshare.org/geoserver/HS-ec43b15ed20744f39bc757f7b2e4d51e/wms?request=GetCapabilities

### Web Feature Service (WFS)
- **URL**: https://geoserver.hydroshare.org/geoserver/HS-ec43b15ed20744f39bc757f7b2e4d51e/wfs?request=GetCapabilities

## Funding Sources

### 1. National Oceanic and Atmospheric Administration (NOAA), University of Alabama
- **Award Title**: CIROH: Enabling collaboration through data and model sharing with CUAHSI HydroShare
- **Award Number**: NA22NWS4320003

## License
- **License Type**: Creative Commons Attribution CC BY
- **License URL**: http://creativecommons.org/licenses/by/4.0/

## Citation
Garousi-Nejad, I. (2025). Accessing AORC and Hydrofabric on CIROH JupyterHub, HydroShare, http://www.hydroshare.org/resource/ec43b15ed20744f39bc757f7b2e4d51e

## Access Options
### Available Through:
- MATLAB Online
- CyberGIS-Jupyter for Water
- CUAHSI JupyterHub
- CIROH 2i2c JupyterHub
- Jupyter Notebook Viewer (built-in)

## Research Significance
This resource provides essential tools and workflows for accessing and analyzing high-value hydrology datasets (AORC meteorological forcings and NextGen Hydrofabric) through cloud-based computing platforms. The included Jupyter notebooks enable researchers to:
- Subset and retrieve hydrofabric data for specific watersheds
- Access and process AORC meteorological forcing data
- Perform flood inundation mapping
- Analyze flow duration curves
- Retrieve and analyze snow water equivalent data

The integration with CIROH JupyterHub on 2i2c infrastructure makes these advanced hydrologic modeling capabilities accessible to the broader research community without requiring local computational resources.