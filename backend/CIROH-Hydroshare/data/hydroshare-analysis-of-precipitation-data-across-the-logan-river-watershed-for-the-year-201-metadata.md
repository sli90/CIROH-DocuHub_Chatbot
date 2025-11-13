# HydroShare Resource Metadata: Analysis of precipitation data across the Logan River Watershed for the Year 2010

## Resource Identification
- **Title**: Analysis of precipitation data across the Logan River Watershed for the Year 2010
- **DOI**: Not explicitly provided in page
- **URL**: https://www.hydroshare.org/resource/b1379f00121e456f958f9e22e913aa8a/
- **Resource ID**: b1379f00121e456f958f9e22e913aa8a

## Authors and Contributors
### Authors
- Irene Garousi-Nejad
- Anthony M. Castronova

### Owners
- Irene Garousi-Nejad
- Anthony M. Castronova

### Contributors
- CUAHSI (Consortium of Universities for the Advancement of Hydrological Science) - Massachusetts, US

## Resource Details
- **Type**: Resource
- **Storage Size**: 2.2 MB
- **Content Type**: Single File Content, Geographic Feature Content
- **Sharing Status**: Public
- **Views**: 2616
- **Downloads**: 1172
- **+1 Votes**: 2

## Temporal Information
- **Created**: May 09, 2023 at 12:44 p.m. (UTC)
- **Last Updated**: May 28, 2024 at 3:54 p.m. (UTC)
- **Analysis Period**: Year 2010

## Abstract
This resource was first created for a live demo during an online I-GUIDE VCO meeting on May 9, 2023. It was then modified for another live demo during the 1st annual CIROH users and developers conference in Salt Lake City, May 16-18. Recently, it was used for the National Water Center Summer Institute 2023.

It contains codes and inputs for a precipitation analysis across the Logan River Watershed. In this analysis, we will obtain modeled precipitation from two products: AORC and PRISM, compare the basin's average daily precipitation, and save results back to HydroShare.

## Spatial Coverage
### Geographic Extent
- **Coordinate System**: WGS 84 EPSG:4326
- **Coordinate Units**: Decimal degrees
- **Bounding Box**:
  - North Latitude: 42.0947°
  - South Latitude: 41.7099°
  - East Longitude: -111.4716°
  - West Longitude: -111.7957°
- **Location**: Logan River Watershed, Utah

## Subject Keywords
- IGUIDE VCO
- 2023CIROHDevCon
- NWCSI2023
- ClemsonAGM8710
- 2024CIROHDevCon
- AORC
- Logan River Watershed
- PRISM
- Precipitation Analysis

## Resource Contents

### 1. logan-watershed-huc12.shp
- **Type**: Shapefile
- **Description**: Shapefile of the Logan River Watershed containing seven features (HUC 12 catchments). This file is a subset of the National Hydrography Dataset (NHD) retrieved from the USGS website.

### 2. Daily_PRISM_Precipitation_in_2010_for_LoganRiverWatershed.csv
- **Type**: CSV file
- **Description**: PRISM daily precipitation spatially averaged across the Logan River Watershed. Created using query-daily-prism-precipitation.ipynb.

### 3. query-daily-prism-precipitation.ipynb
- **Type**: Jupyter Notebook (Python)
- **Description**: Computational notebook that downloads PRISM precipitation data and clips them for the Logan River Watershed.

### 4. query-aorc-and-compare-with-prism.ipynb
- **Type**: Jupyter Notebook (Python)
- **Description**: Computational notebook that retrieves AORC forcing data, clips them for the Logan River Watershed, and compares with PRISM precipitation data.

### 5. readme.md
- **Type**: Markdown file
- **Description**: Documentation explaining the resource and its files.

### 6. case-study-logan-river-watershed.png
- **Type**: Image file
- **Description**: Image showing the geographical location of the study site, referenced in the readme file.

## Data Sources

### Analysis of Record for Calibration (AORC)
The Analysis of Record for Calibration (AORC) is a gridded record of near-surface weather conditions covering the continental United States and Alaska and their hydrologically contributing areas. It is defined on a latitude/longitude spatial grid with a mesh length of ~800 m (30 arc seconds), and a temporal resolution of one hour. Elements include hourly total precipitation, temperature, specific humidity, terrain-level pressure, downward longwave and shortwave radiation, and west-east and south-north wind components. It spans the period from 1979 at Continental U.S. (CONUS) locations / 1981 in Alaska, to the near-present. This suite of eight variables is sufficient to drive most land-surface and hydrologic models and is used to force the calibration run of the National Water Model (NWM).

### Parameter-elevation Regressions on Independent Slopes Model (PRISM)
The PRISM Climate Data from Oregon State University is a gridded product covering the Conterminous United States. It combines climate observations from a wide range of monitoring networks with sophisticated modeling techniques to establish a local climate-elevation relationship for each grid cell. This dataset spans from 1895 to the present and can be used to analyze short- and long-term climate patterns. The PRISM dataset is available at two distinct spatial scales: a publicly available 4 km version and a more refined 800 m resolution dataset available for a fee.

### Watershed Boundary Dataset (WBD)
The Watershed Boundary Dataset (WBD) is a seamless, national hydrologic unit dataset. Hydrologic units represent the area of the landscape that drains to a portion of the stream network. WBD contains eight levels of progressive hydrologic units (HUC) identified by unique 2- to 16-digit codes. The case study region was selected from the HUC 12 watershed boundaries for the Great Basin.

## Case Study Description
The Logan River Watershed is a snowmelt-dominated watershed located in the Bear River mountain range east of Logan, Utah. Most precipitation falls in the form of snowfall during winter months and as rain during spring and summer time. Water flows southwest through mostly natural land cover.

## Data Services
### Web Map Service (WMS)
- **URL**: https://geoserver.hydroshare.org/geoserver/HS-b1379f00121e456f958f9e22e913aa8a/wms?request=GetCapabilities

### Web Feature Service (WFS)
- **URL**: https://geoserver.hydroshare.org/geoserver/HS-b1379f00121e456f958f9e22e913aa8a/wfs?request=GetCapabilities

## Funding Sources

### 1. National Science Foundation
- **Award Title**: HDR Institute: Geospatial Understanding through an Integrative Discovery Environment
- **Award Number**: 2118329
- **URL**: https://www.nsf.gov/

### 2. National Oceanic and Atmospheric Administration
- **Award Title**: CIROH: CUAHSI HydroShare Modernization
- **Award Number**: A22-0306-S004
- **URL**: https://www.noaa.gov/

## Related Resources
- **Executable Platform**: https://jupyterhub.cuahsi.org/
- **References**: Horsburgh, J. S., S. S. Black (2021). HydroShare Python Client Library (hsclient) Usage Examples, HydroShare, http://www.hydroshare.org/resource/7561aa12fd824ebb8edbee05af19b910

## License
- **License Type**: Creative Commons Attribution CC BY
- **License URL**: http://creativecommons.org/licenses/by/4.0/

## Citation
Garousi-Nejad, I., A. M. Castronova (2024). Analysis of precipitation data across the Logan River Watershed for the Year 2010, HydroShare, http://www.hydroshare.org/resource/b1379f00121e456f958f9e22e913aa8a

## Access Options
### Available Through:
- CUAHSI JupyterHub (Python 3.8 server)
- Direct download from HydroShare
- Web services (WMS/WFS) for GIS integration

### How to Run Computational Notebooks:
To access the CUAHSI JupyterHub, you have two options:
1. Right-click on any of the Jupyter Notebooks within this resource and choose the CUAHSI JupyterHub option
2. Open the entire resource by clicking on the "Open with" button located at the top right corner of the landing page
Once in the resource, select the Python 3.8 server and follow the steps provided in the notebooks.

## Research Significance
This resource provides a comprehensive precipitation analysis framework for the Logan River Watershed, demonstrating the integration of multiple precipitation data products (AORC and PRISM) for hydrologic analysis. The included computational notebooks enable researchers to:

- Compare high-resolution precipitation datasets from different sources
- Calculate basin-averaged precipitation values
- Understand spatial and temporal precipitation patterns in snowmelt-dominated watersheds
- Apply similar methodologies to other watersheds

The resource has been used extensively for educational purposes, including demonstrations at major conferences (CIROH DevCon, I-GUIDE VCO) and training institutes (National Water Center Summer Institute), making it a valuable teaching tool for hydrologic data analysis and integration workflows.