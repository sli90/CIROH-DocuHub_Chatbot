# Project Title: **DEVCON_SNOW_ML**

## Project Objective  
The **DEVCON_SNOW_ML** repository provides a machine learning framework for estimating Snow-Water-Equivalent (SWE) across the western United States. The project aims to improve operational, near-real-time SWE estimation to update the snowpack state within the National Water Model (NWM) as part of the CIROH initiative.

## Core Functionalities  
- Develops and optimizes ML algorithms for SWE estimation using regionalized modeling.  
- Utilizes twenty-three sub-models tailored to unique topographical and hydroclimatic zones across the western U.S.  
- Integrates data from nearly 700 snow telemetry (SNOTEL) and California Data Exchange Center (CDEC) sites.  
- Combines observation data with lidar-derived terrain features for 1 km x 1 km SWE predictions.  
- Provides a modular ML framework enabling experimentation with different algorithms:  
  - Deep neural networks (core model).  
  - Long Short-Term Memory (LSTM) networks.  
  - Tree-based and regression algorithms (e.g., Ordinary Least Squares).  
- Incorporates evaluation metrics using the **Standardized Snow Water Equivalent Evaluation Tool (SSWEET)**.  
- Offers a Jupyter workbook for demonstration, training, and evaluation of SWE prediction algorithms.  

## Technical Stack  
- **Languages:** Python.  
- **Frameworks/Libraries:** Not specified.  
- **Data Sources:**  
  - NASA Airborne Snow Observatory (ASO) LiDAR-derived SWE.  
  - Copernicus 90m Digital Elevation Model (DEM).  
  - NRCS Snow Telemetry (SNOTEL) station SWE observations.  
  - CDEC monitoring data.  
  - VIIRS fraction snow-covered area (fSCA).  
- **Infrastructure:** AWS S3 and Box for cloud-hosted data access.  

## Setup and Usage  
1. Refer to the `Getting Started` guide for virtual environment setup using the provided `environment.yml` file.  
2. Run the example Jupyter Notebook to reproduce the core SWE modeling workflow.  
3. Users are encouraged to modify and test different ML architectures to refine prediction accuracy, particularly in elevation-sensitive regions.  
4. Model performance evaluation is conducted using SSWEET.  

## Project Context & Domain  
- **Domain:** Hydrology / Snow Modeling / Machine Learning.  
- **Affiliation:** Cooperative Institute for Research to Operations in Hydrology (CIROH), Alabama Water Institute (University of Alabama), and University of Utah.  
- **Purpose:** Enhance snowpack characterization and forecasting by improving the efficiency, scalability, and accuracy of machine learning models for SWE prediction.  

## Input / Output  
**Input:**  
- Pre-processed training datasets (~7,000 grid points) including snow telemetry, lidar, DEM, and satellite-derived features.  
- Model configuration and training parameters defined within Jupyter notebooks.  

**Output:**  
- High-resolution (1 km) SWE predictions.  
- Evaluation metrics (RMSE, R²) for algorithm performance.  
- Comparative performance analyses of multiple ML architectures.  
