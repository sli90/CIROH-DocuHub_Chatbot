# Project Title: **NWM_ML**

## Project Objective  
The **NWM-ML** project extends the NOAA National Water Model (NWM) using machine learning to improve streamflow predictions affected by water resource infrastructure across the Western United States. The project aims to enhance the NWM's 30-day operational forecasts into season-to-season water supply forecasting tools to support environmental management, agriculture, and urban water use planning.

## Core Functionalities  
- Couples the National Water Model with machine learning workflows for improved streamflow prediction.  
- Integrates multiple data sources, including hydrological, climatological, and land cover datasets.  
- Trains models for application in the Great Salt Lake (GSL) basin with plans to expand to the Upper Colorado River Basin.  
- Demonstrates a proof-of-concept integrated water resources management tool linking NWM with lake and wetland modules.  
- Utilizes the physically based NWM v2.1 retrospective dataset (with future integration of NWM v3.0).  
- Incorporates seasonal cycle representation through sine and cosine functions to model annual hydrological variability.  

## Technical Stack  
- **Base Model:** NOAA National Water Model (NWM).  
- **Machine Learning Framework:** Not specified.  
- **Data Sources:**  
  - **StreamStats:** Basin area, mean elevation, land cover types, and basin slope (>30°).  
  - **NWM:** v2.1 retrospective flow data resampled to daily resolution.  
  - **Seasonality Metrics:** Sine and cosine series representing 12-month hydrological cycles.  
  - **US Bureau of Reclamation:** Upstream catchment storage (% of capacity).  
  - **NRCS (National Resource Conservation Service):** Snow-water-equivalent (SWE) from SNOTEL monitoring sites.  
  - **NLDAS / NOAA Analysis of Record for Calibration:** Daily precipitation, mean annual precipitation, and temperature.  
  - **USGS (United States Geological Survey):** Streamflow monitoring information for colocated NHDPlus reaches used for model training/testing.  

## Setup and Usage  
- Model training and testing are performed using NWM retrospective data and observed streamflow records.  
- The workflow integrates catchment-level attributes and seasonal indices to improve streamflow correction.  
- Demonstration and testing are centered in the Great Salt Lake basin, with expansion planned for the Upper Colorado River Basin.  
- Specific setup instructions are not provided in the README.  

## Project Context & Domain  
- **Domain:** Hydrology / Machine Learning / Water Resources Management.  
- **Affiliation:** NOAA (National Oceanic and Atmospheric Administration), CIROH (Cooperative Institute for Research to Operations in Hydrology), The University of Alabama.  
- **Purpose:** Enhance NWM streamflow prediction accuracy by accounting for anthropogenic and climatic factors using machine learning.  

## Input / Output  
**Input:**  
- Retrospective NWM flow data.  
- Catchment characteristics (e.g., area, slope, elevation, storage capacity).  
- Snow, precipitation, and temperature data from multiple national monitoring sources.  
- USGS streamflow data for model calibration and validation.  

**Output:**  
- Corrected streamflow predictions for improved water resource management.  
- Machine learning model performance evaluations for hydrologic forecasting improvement.  

## Funding Acknowledgement  
This project is funded by the **National Oceanic and Atmospheric Administration (NOAA)** and awarded to the **Cooperative Institute for Research to Operations in Hydrology (CIROH)** through the **NOAA Cooperative Agreement with The University of Alabama (NA22NWS4320003)**.
