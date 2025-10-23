# Project Title: **Tethys-CSES**

## Project Objective  
The **Community Streamflow Evaluation System (CSES)** is a Tethys web application developed to evaluate hydrological model performance using a standardized NHDPlus data model. It allows users to assess modeled streamflow at over 5,000 in-situ USGS monitoring sites, offering interactive visualizations for comprehensive hydrologic analysis.

## Core Functionalities  
- Provides evaluation of modeled streamflow against USGS observations.  
- Supports multiple evaluation methods:  
  - **State Evaluation Methods:** Evaluate hydrological model performance by state.  
  - **Reach Evaluation Methods:** Analyze stream reaches using NWIS site data.  
  - **HUCid Evaluation Methods:** Assess hydrologic unit codes (HUCs) within selected basins.  
- Uses retrospective datasets from the National Water Model (NWM v2.1, with v3.0 planned).  
- Enables interactivity for exploring models, states, date ranges, and locations.  
- Hosts all colocated USGS and NWM data in AWS S3 for quick access and reproducible analysis.  

## Technical Stack  
- **Framework:** Tethys Platform (Web-based).  
- **Languages:** Python.  
- **Data Sources:** USGS/NWIS, NWM v2.1 retrospective dataset.  
- **Hosting:** AWS S3 Cloud Storage.  

## Setup and Usage  
- Default configuration evaluates streamflow for Alabama and Great Salt Lake regions using NWM v2.1 data.  
- Users can interactively select:  
  - States, reaches, or HUCs.  
  - Model type and date range (recommended ≤ 1 year).  
- If plots do not display, the selected model or observational data may be unavailable.  

## Project Context & Domain  
- **Domain:** Hydrology / Water Modeling.  
- **Affiliation:** Alabama Water Institute (AWI), Cooperative Institute for Research to Operations in Hydrology (CIROH), ESIP, NASA, NOAA, and USGS.  
- **Purpose:** Facilitate large-scale hydrologic model evaluation and visualization through a community-accessible web platform.  

## Input / Output  
**Input:**  
- User-selected parameters such as state, reach, HUC, model type, and date range.  

**Output:**  
- Interactive plots and visualizations comparing modeled and observed streamflow data.  

## Funding Acknowledgement  
Funding provided through the **NOAA Cooperative Agreement (NA22NWS4320003)** with The University of Alabama, under CIROH, and supported by **NASA, NOAA, and the USGS** via the **ESIP Lab**.
