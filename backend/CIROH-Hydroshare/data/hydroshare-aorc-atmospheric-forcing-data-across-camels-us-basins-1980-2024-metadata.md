# HydroShare Resource Metadata: AORC atmospheric forcing data across CAMELS US basins, 1980 - 2024

## Resource Identification
- **Title**: AORC atmospheric forcing data across CAMELS US basins, 1980 - 2024
- **DOI**: 10.4211/hs.c738c05278a34bc9848dd14d61cffab9
- **URL**: https://www.hydroshare.org/resource/c738c05278a34bc9848dd14d61cffab9/
- **Resource ID**: c738c05278a34bc9848dd14d61cffab9

## Authors and Contributors
### Authors
- Jonathan Martin Frame
- Andrew W Wood
- Nels Frazier

### Owners
- Jonathan Martin Frame
- CUAHSI Hydroshare Publisher

### Contributors
- Andrew W Wood (NCAR; University of Colorado at Boulder) - Colorado, US
- Nels Frazier (Lynker; NOAA Affiliate) - Alabama, US

## Resource Details
- **Type**: Resource
- **Storage Size**: 3.7 GB
- **Content Type**: Not specified
- **Sharing Status**: Published
- **Views**: 1907
- **Downloads**: 202
- **+1 Votes**: 2

## Temporal Information
- **Created**: Aug 07, 2024 at 12:51 a.m. (UTC)
- **Last Updated**: Jan 06, 2025 at 3:35 p.m. (UTC)
- **Published Date**: Jan 06, 2025 at 3:35 p.m. (UTC)
- **Temporal Coverage**:
  - Start Date: 10/01/1980
  - End Date: 04/01/2024

## Abstract
These data are atmospheric forcings from NOAA's Analysis of Record for Calibration (AORC 2024) summarized over the CAMELS catchments (Addor et al. 2017), however, the delineations over those CAMELS basins were updated by Andy Wood (2024) using the basin boundaries produced for the USGS GagesII effort (Falcone 2011).

Data collected using this repository code: https://github.com/jmframe/CIROH_DL_NextGen/tree/main/forcing_prep, which should be somewhat derivative of this: https://github.com/CIROH-UA/ngen-datastream/tree/main/forcingprocessor.

## Spatial Coverage
### Geographic Extent
- **Coordinate System**: WGS 84 EPSG:4326
- **Coordinate Units**: Decimal degrees
- **Bounding Box**:
  - North Latitude: 50.2107°
  - South Latitude: 24.2550°
  - East Longitude: -65.7422°
  - West Longitude: -126.7383°
- **Place/Area Name**: CONUS selected basins (CAMELS)

## Subject Keywords
- Atmospheric forcing
- Temperature
- Downward Long-Wave Radiation
- Downward Short-Wave Radiation
- Analysis of Record for Calibration (AORC)
- Humidity
- U-Component of Wind
- CAMELS US
- Air Pressure
- V-Component of Wind
- Precipitation

## Meteorological Variables

The dataset contains eight variables representing meteorological conditions:

### 1. Total Precipitation (APCP_surface)
- **Description**: Hourly total precipitation for Calibration (AORC) dataset
- **Units**: kg m⁻² or mm

### 2. Air Temperature (TMP_2maboveground)
- **Description**: Temperature at 2 m above-ground-level (AGL)
- **Units**: K (Kelvin)

### 3. Specific Humidity (SPFH_2maboveground)
- **Description**: Specific humidity at 2 m AGL
- **Units**: g g⁻¹

### 4. Downward Long-Wave Radiation Flux (DLWRF_surface)
- **Description**: Longwave (infrared) radiation flux at the surface
- **Units**: W m⁻²

### 5. Downward Short-Wave Radiation Flux (DSWRF_surface)
- **Description**: Downward shortwave (solar) radiation flux at the surface
- **Units**: W m⁻²

### 6. Pressure (PRES_surface)
- **Description**: Air pressure at the surface
- **Units**: Pa (Pascals)

### 7. U-Component of Wind (UGRD_10maboveground)
- **Description**: West-east component of the wind at 10 m AGL
- **Units**: m s⁻¹

### 8. V-Component of Wind (VGRD_10maboveground)
- **Description**: South-north component of the wind at 10 m AGL
- **Units**: m s⁻¹

**Note**: The data include a timestamp from Coordinated Universal Time (UTC; AORC 2021).

## Data Processing Information
- **Processing Code**: https://github.com/jmframe/CIROH_DL_NextGen/tree/main/forcing_prep
- **Derivative Code**: https://github.com/CIROH-UA/ngen-datastream/tree/main/forcingprocessor
- **Basin Delineations**: Updated by Andy Wood (2024) using USGS GagesII boundaries

## References
- Addor, N., Newman, A. J., Mizukami, N., and Clark, M. P.: The CAMELS data set: catchment attributes and meteorology for large-sample studies, Hydrol. Earth Syst. Sci., 21, 5293–5313, https://doi.org/10.5194/hess-21-5293-2017, 2017.

- AORC. 2021. Analysis of Record for Calibration Version 1.1 - Sources, Methods, and Verification, National Oceanic and Atmospheric Administration (NOAA), National Weather Service (NWS), Office of Water Prediction (OWP), Silver Spring, MD. https://www.weather.gov/media/owp/operations/aorc_v1_1_methods.pdf

- AORC. 2024. NOAA Analysis of Record for Calibration (AORC) Dataset was accessed July 2024 from https://registry.opendata.aws/noaa-nws-aorc

- Falcone, J., 2011, GAGES-II: Geospatial Attributes of Gages for Evaluating Streamflow: U.S. Geological Survey data release, https://doi.org/10.5066/P96CPHOT. https://www.sciencebase.gov/catalog/item/631405bbd34e36012efa304a

- Wood. 2024. CAMELS basins delineation.

## Funding Sources

### 1. NOAA
- **Award Title**: Cooperative Institute for Research to Operations in Hydrology
- **Award Number**: NA22NWS4320003

## License
- **License Type**: Creative Commons Attribution CC BY
- **License URL**: http://creativecommons.org/licenses/by/4.0/

## Citation
Frame, J. M., A. W. Wood, N. Frazier (2025). AORC atmospheric forcing data across CAMELS US basins, 1980 - 2024, HydroShare, https://doi.org/10.4211/hs.c738c05278a34bc9848dd14d61cffab9

## Access Options
### Available Through:
- Direct download from HydroShare
- MATLAB Online
- CUAHSI JupyterHub
- CIROH 2i2c JupyterHub

## Research Significance
This comprehensive dataset provides 44 years of high-quality atmospheric forcing data across 671 CAMELS basins in the continental United States, making it an invaluable resource for:

- **Hydrologic Model Calibration and Validation**: Provides consistent, long-term forcing data for model development
- **Climate Impact Studies**: Enables analysis of climate trends and variability across diverse watersheds
- **Large-Sample Hydrology Research**: Supports comparative studies across hundreds of basins
- **Machine Learning Applications**: Offers standardized input data for data-driven hydrologic models
- **Water Resources Management**: Supports operational forecasting and planning activities

The dataset's integration with the CAMELS framework and use of updated USGS GagesII boundaries ensures compatibility with existing hydrologic research infrastructure. The inclusion of all eight essential meteorological variables at hourly resolution (aggregated to basin scale) makes this dataset suitable for driving various land-surface and hydrologic models, including the Next Generation Water Resources Modeling Framework (NextGen).

The extensive temporal coverage (1980-2024) captures multiple climate cycles and extreme events, providing robust data for understanding hydrologic responses to atmospheric forcing across different climatic and physiographic settings.