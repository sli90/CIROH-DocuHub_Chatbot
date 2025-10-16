# HydroShare Resource Metadata: Demonstration of the National Water Model's Applicability to Community Resilience Planning: Cincinnati Use Case

## Resource Identification
- **Title**: Demonstration of the National Water Model's Applicability to Community Resilience Planning: Cincinnati Use Case
- **DOI**: 10.4211/hs.0ef4366e7711478fa2637f5049b4881a
- **URL**: https://www.hydroshare.org/resource/0ef4366e7711478fa2637f5049b4881a/
- **Resource ID**: 0ef4366e7711478fa2637f5049b4881a

## Authors and Contributors
- **Author 1**: Irene Garousi-Nejad
- **Author 2**: Anthony M. Castronova
- **Author 3**: Kristin B. Raub
- **Owner 1**: Irene Garousi-Nejad
- **Owner 2**: Anthony M. Castronova

## Resource Details
- **Type**: Resource
- **Storage Size**: 646.1 MB
- **License**: Creative Commons Attribution CC BY (http://creativecommons.org/licenses/by/4.0/)
- **Content Type**: Geographic Raster Content
- **Sharing Status**: Public
- **Views**: 2154
- **Downloads**: 330
- **+1 Votes**: 1
- **Comments**: 0

## Temporal Information
- **Created**: June 13, 2024 at 12:33 p.m. (UTC)
- **Last Updated**: September 12, 2024 at 7:46 p.m. (UTC)

## Spatial Coverage
- **Coordinate System**: WGS 84 EPSG:4326
- **North Latitude**: 39.1524°
- **East Longitude**: -82.5652°
- **South Latitude**: 37.4323°
- **West Longitude**: -84.8962°
- **Location**: Fowler Creek Watershed, Kentucky

## Abstract
This resource provides codes and data to demonstrate a use case for evaluating the National Water Model (NWM) locally and enhancing its accessibility. The objective is to explore how NOAA's NWM can be utilized by a new audience of potential users. The NWM, managed by NOAA's National Water Center, is a comprehensive hydrologic model focusing on river and streamflow data. It offers insights into historical water conditions (with a 40-year retrospective capability), current water status, and future projections (ranging from 18 hours to 10-day and 30-day forecasts). Since its initial release in 2016, the NWM has been updated to version 3.0, with several planned enhancements and new services, including the Next Generation Framework and Flood Inundation Mapping, which are expected to be introduced within the next 24 months.

Working Group's Project: "Evaluating the NWM as a Data Source for Resilient Transportation Planning" and "Building Trust Around Predictive Hydrologic Resources"

Funding for this project was provided by the National Oceanic and Atmospheric Administration (NOAA), awarded to the Cooperative Institute for Research on Hydrology (CIROH) through the NOAA Cooperative Agreement with The University of Alabama, NA22NWS4320003

## Keywords
- FEMA
- CIROH
- Fowler Creek
- Flood Inundation Mapping
- Community Resilience Planning
- ciroh_portal_data
- National Water Model

## Files
- **hydroTable_0.csv**: 164.6 MB - Pre-computed stage-discharge values for every reach
- **Figure**: Folder - Images comparing flood inundation maps (FIM approach vs FEMA)
- **nwm_utils**: Folder - Supplementary code
- **rem_zeroed_masked_0**: GeoRaster folder - Height Above Nearest Drainage values
- **demDerived_reaches_split_filtered_addedAttributes_crosswalked_0.gpkg**: 19.5 MB - DEM-derived reach geometries for visualization
- **gw_catchments_reaches_filtered_addedAttributes_crosswalked_0.gpkg**: 40.1 MB - Vector data and attributes for river reaches
- **create-inundation-maps-using-FIM-xarray.ipynb**: 16.7 KB - Code to create flood inundation maps using FIM method
- **retrieve-nwm-v3-retrospective-streamflow-data.ipynb**: 12.7 KB - Code to retrieve NWM streamflow data
- **readme.md**: 9.2 KB - Detailed documentation
- **21117CV000B.pdf**: 5.7 MB - FEMA Flood Insurance Study report for Kenton County, Kentucky
- **21117C_20150619.zip**: 7.7 MB - FEMA flood maps

## Case Study Details
- **Focus Area**: Fowler Creek watershed, part of Licking River watershed (HUC 05100101) in Kentucky
- **NWM Feature ID**: 2087827 (corresponds to NHDPlus Permanent_Identifier)
- **Maximum Peak Flow (NWM)**: 66.42 cms
- **FEMA 100-year Flood Discharge**: 5220 cfs (147.8 cms)

## Data Services
### Web Map Service
https://geoserver.hydroshare.org/geoserver/HS-0ef4366e7711478fa2637f5049b4881a/wms?request=GetCapabilities

### Web Coverage Service
https://geoserver.hydroshare.org/geoserver/HS-0ef4366e7711478fa2637f5049b4881a/wcs?request=GetCapabilities

## Related Resources
- Referenced by: https://globalresilience.northeastern.edu/wp-content/uploads/2024/06/NWM-Cincinnati.pdf
- References: FEMA flood maps and products
- References: NOAA-OWP inundation-mapping project
- References: NWM retrospective data on AWS
- Can be executed by: CIROH Production JupyterHub

## Funding Information
- **Agency**: National Oceanic and Atmospheric Administration (NOAA)
- **Award Title**: COOPERATIVE INSTITUTE FOR RESEARCH TO OPERATIONS IN HYDROLOGY (CIROH)
- **Award Number**: NA22NWS4320003

## Citation
Garousi-Nejad, I., A. M. Castronova, K. B. Raub (2024). Demonstration of the National Water Model's Applicability to Community Resilience Planning: Cincinnati Use Case, HydroShare, http://www.hydroshare.org/resource/0ef4366e7711478fa2637f5049b4881a