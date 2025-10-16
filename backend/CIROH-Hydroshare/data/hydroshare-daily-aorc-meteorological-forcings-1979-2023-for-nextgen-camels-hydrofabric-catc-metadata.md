# HydroShare Resource Metadata: Daily AORC meteorological forcings (1979-2023) for Nextgen-CAMELS-Hydrofabric Catchments (v2.2)

## Resource Identification
- **Title**: Daily AORC meteorological forcings (1979-2023) for Nextgen-CAMELS-Hydrofabric Catchments (v2.2)
- **DOI**: Not explicitly provided in page
- **URL**: https://www.hydroshare.org/resource/1e934d92acdb42fa8379cd5009371150/
- **Resource ID**: 1e934d92acdb42fa8379cd5009371150

## Authors and Contributors
### Authors
- Josh Sturtevant
- Andrew W Wood
- Nels Frazier

### Owners
- Josh Sturtevant
- Andrew W Wood

### Contributors
- Nels Frazier (Lynker; NOAA Affiliate) - Alabama, US
- Andrew W Wood (NCAR; University of Colorado at Boulder) - Colorado, US

## Resource Details
- **Type**: Resource
- **Storage Size**: 5.9 MB
- **Content Type**: Single File Content
- **Sharing Status**: Public
- **Views**: 1264
- **Downloads**: 7

## Temporal Information
- **Created**: Dec 06, 2024 at 6:55 p.m. (UTC)
- **Last Updated**: Jan 02, 2025 at 8:40 p.m. (UTC)
- **Temporal Coverage**:
  - Start Date: 02/01/1979
  - End Date: 12/31/2023

## Abstract
The Analysis of Record Calibration (AORC) meteorological forcing dataset is a retrospective gridded product produced by NOAA's Office of Water Prediction (Fall et al., 2023). The AORC hourly dataset provides high resolution (800-m) gridded fields for seven meteorological variables ('forcings'), used as time series inputs for calibration of the current NOAA National Water Model (NWMv3), among other modeling and analysis applications. The upcoming v4 update of the NWM will adopt a catchment-based modeling approach centered on an NHDPlus-based NextGen Hydrofabric (Johnson et al., 2024).

In view of this transition, we provide a remapped daily version of the AORC forcings (with the addition of maximum and minimum temperature) to the Hydrofabric catchments representing a large-sample watershed subset – i.e., for the 671 CAMELS basins (Newman et al., 2015; Addor et al., 2017; see https://ral.ucar.edu/solutions/products/camels) The associated CAMELS-Hydrofabric v2.2 data are provided as a separate Hydroshare resource, "Nextgen-CAMELS-Hydrofabric v2.2: NOAA Next Generation Water Resources Modeling Framework Hydrofabric for the CAMELS Basins". The remapping was performed by calculating catchment areal-mean forcing values using a spatially-conservative remapping technique developed previously at the NSF National Center for Atmospheric Research (NCAR). Specifically, the 'poly2poly.py' script is used to generate spatial weights relating the AORC grid to the catchment Hydrofabric polygons, and associated scripts then apply the weights efficiently over all the timesteps in the dataset. Catchment averages are adjusted to account for missing input grid values, where necessary. The remapped dataset of n = 54,667 catchments is available in netCDF format and designed to meets the standards of the Next Generation Water Resources Modeling Framework (Nextgen) – such as variable naming and epoch start date formatting – making it model-ready off the shelf. This retrospective 1979-2023 forcing dataset, together with the hydrofabric divides, nexus, and flowpath layers, provides a core input required for running the Nextgen modeling framework at a Hydrofabric resolution across the CAMELS basins. Note, an earlier lumped-basin version of these forcings is available at: https://www.hydroshare.org/resource/c738c05278a34bc9848dd14d61cffab9/ (Frame et al, 2024).

## Spatial Coverage
### Geographic Extent
- **Coordinate System**: WGS 84 EPSG:4326
- **Coordinate Units**: Decimal degrees
- **Bounding Box**:
  - North Latitude: 50.0000°
  - South Latitude: 24.0000°
  - East Longitude: -65.0000°
  - West Longitude: -125.0000°
- **Place/Area Name**: CONUS

## Subject Keywords
- Model Forcings
- Nextgen
- Hydrologic Modeling
- CAMELS

## Resource Contents

### 1. example_usgs09081600.ngen-hf.v2_2.aorc_20230101.png
- **Size**: 5.9 MB
- **Type**: png File, Single File Content
- **Description**: A single file with file specific metadata

## Funding Sources

### 1. National Oceanic and Atmospheric Administration
- **Award Title**: Cooperative Institute for Research to Operations in Hydrology (CIROH)
- **Award Number**: NA22NWS4320003
- **URL**: https://ror.org/02z5nhe81

## Acknowledgements
- This dataset was supported by a project grant to the Colorado School of Mines (CSM) from the NOAA Cooperative Institute for Research to Operations in Hydrology (CIROH). CIROH is funded via the NOAA Cooperative Agreement with The University of Alabama (NA22NWS4320003).
- We are grateful to Mike Robbert at CSM for his assistance in transferring the large AORC dataset onto Mines HPC systems to facilitate the remapping process.

## References
- Fall, Greg, David Kitzmiller, Sandra Pavlovic, Ziya Zhang, Nathan Patrick, Michael St. Laurent, Carl Trypaluk, Wanru Wu, and Dennis Miller. "The Office of Water Prediction's Analysis of Record for Calibration, Version 1.1: Dataset Description and Precipitation Evaluation," December 2023. https://doi.org/10.1111/1752-1688.13143.
- Addor, N., Newman, A. J., Mizukami, N. and Clark, M. P.: The CAMELS data set: catchment attributes and meteorology for large-sample studies, Hydrol. Earth Syst. Sci., 21, 5293–5313, doi:10.5194/hess-21-5293-2017, 2017.
- Frame, J. M., A. W. Wood, N. Frazier (2024). AORC atmospheric forcing data across CAMELS US basins, 1980 - 2024, HydroShare, http://www.hydroshare.org/resource/c738c05278a34bc9848dd14d61cffab9
- Johnson, J. Michael, Arash Modesari Rad, Trey C. Flowers, and Fred L. Ogden. "The NOAA Next Generation Water Resource Modeling Framework Hydrofabric." In 104th AMS Annual Meeting. AMS, 2024. https://ams.confex.com/ams/104ANNUAL/meetingapp.cgi/Paper/436827.
- Newman, A. J., et al., 2015: Development of a large-sample watershed-scale hydrometeorological data set for the contiguous USA, https://doi.org/10.5194/hess-19-209-2015
- Newman, A. J., et al., 2017: Benchmarking of a Physically Based Hydrologic Model. J. Hydrometeor., 18, 2215–2225, https://doi.org/10.1175/JHM-D-16-0284.1.
- NOAA Analysis of Record for Calibration (AORC) Dataset was accessed on 2024-11-07 from https://registry.opendata.aws/noaa-nws-aorc.

## License
- **License Type**: Creative Commons Attribution CC BY
- **License URL**: http://creativecommons.org/licenses/by/4.0/

## Citation
Sturtevant, J., A. W. Wood, N. Frazier (2025). Daily AORC meteorological forcings (1979-2023) for Nextgen-CAMELS-Hydrofabric Catchments (v2.2), HydroShare, http://www.hydroshare.org/resource/1e934d92acdb42fa8379cd5009371150

## Access Options
### Available Through:
- MATLAB Online
- CyberGIS-Jupyter for Water
- CUAHSI JupyterHub
- CIROH 2i2c JupyterHub

## Research Significance
This resource provides essential meteorological forcing data for hydrologic modeling across 671 CAMELS basins using the Next Generation Water Resources Modeling Framework. The dataset represents a critical advancement in supporting catchment-based modeling approaches, offering model-ready forcing data that bridges the transition from gridded to catchment-based hydrologic modeling frameworks.