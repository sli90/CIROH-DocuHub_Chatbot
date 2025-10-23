# Project Title: **hydrotools**

## Project Objective  
**OWPHydroTools** is a Python library developed by NOAA’s Office of Water Prediction (OWP) to support hydrologic data scientists. It simplifies retrieving, evaluating, and exporting hydrologic and environmental data using familiar data structures such as `pandas.DataFrame`, `geopandas.GeoDataFrame`, and `numpy.array`. The goal is to make hydrologic data analysis more accessible, consistent, and reproducible.

## Core Functionalities  
- Provides modular tools (“subpackages”) for specific hydrologic data operations:  
  - **events:** Methods for event-based evaluations of hydrometric time series.  
  - **nwm_client:** Retrieval of National Water Model (NWM) data from sources such as Google Cloud Platform and NOMADS.  
  - **metrics:** Computation of common hydrologic evaluation metrics.  
  - **nwis_client:** Easy-to-use interface for retrieving data from the USGS NWIS Instantaneous Values Web Service.  
  - **svi_client:** Programmatic access to CDC’s Social Vulnerability Index (SVI).  
  - **_restclient:** Generic REST client with built-in caching for GET requests.  
- Adheres to NOAA-OWP naming standards for consistent data labeling.  
- Allows lightweight installation of only the required subpackages.  
- Supports efficient handling of large datasets through canonical labeling and categorical data types.  
- Ensures UTC-based, time-zone-naive timestamps across all methods.  

## Technical Stack  
- **Languages:** Python (>= 3.8).  
- **Libraries:** pandas, geopandas, numpy.  
- **Data Access:** REST APIs (USGS NWIS, NWM, CDC SVI).  
- **Testing Framework:** pytest (as used in GitHub workflows).  

## Setup and Usage  
### Installation  
It is recommended to install HydroTools within a virtual environment. Example setup:  
```bash
# Create and activate environment
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip

# Install all tools
python3 -m pip install hydrotools

# Or install a single subpackage (e.g., NWIS Client)
python3 -m pip install hydrotools.nwis_client
```  

### Data Structure Notes  
- Canonical columns (shared across subpackages) include standardized labels such as `value`, `value_time`, `variable_name`, `measurement_unit`, and `series`.  
- Non-canonical labels (subpackage-specific) include fields like `usgs_site_code`, `nwm_feature_id`, `nws_lid`, and event boundaries (`start`, `end`).  
- Categorical data types (`pandas.Categorical`) are used for efficiency but may require conversion or adjustments for certain operations or geospatial outputs.  

## Project Context & Domain  
- **Domain:** Hydrology / Data Science.  
- **Affiliation:** NOAA Office of Water Prediction (OWP).  
- **Purpose:** Facilitate reproducible, standards-compliant hydrologic data retrieval, analysis, and evaluation.  

## Input / Output  
**Input:**  
- Hydrologic and environmental data from external APIs and web services (e.g., NWIS, NWM, CDC SVI).  

**Output:**  
- Processed datasets returned as `pandas.DataFrame`, `geopandas.GeoDataFrame`, or `numpy.array` objects suitable for analysis and visualization.  
