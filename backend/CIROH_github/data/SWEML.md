# Project Title: **SWEML**

## Project Objective  
The **Snow Water Equivalent Machine Learning (SWEML)** project uses machine learning to advance snow state modeling. It produces high-resolution (1 km) SWE predictions across the Western U.S. and the Upper Colorado River Basin, using data from SNOTEL and CDEC sites combined with lidar-derived terrain features. The system aims to enhance snowpack monitoring and forecasting capabilities through an operational deep learning workflow.

## Core Functionalities  
- Predicts 1 km x 1 km resolution SWE (Snow Water Equivalent) inferences.  
- Integrates nearly 700 snow telemetry (SNOTEL) and California Data Exchange Center (CDEC) stations.  
- Combines SWE observations with lidar-derived terrain features and seasonality metrics.  
- Trains region-specific multilayered perceptron (MLP) models for SWE prediction.  
- Provides hindcast simulations and visualizations of SWE for key snow regions.  
- Evaluates model performance using the Standardized Snow Water Equivalent Evaluation Tool (SSWEET).  
- Includes an interactive visualization of SWE estimates across the Western U.S.  
- Offers a tutorial and full workflow in a Jupyter Book format.  

## Technical Stack  
- **Language:** Python (version 3.8 or later).  
- **Frameworks/Libraries:** TensorFlow, LightGBM, Pandas, NumPy, GeoPandas, Rasterio, Shapely, Xarray, Matplotlib, Cartopy, EarthPy, TQDM, Folium, RichDEM, PyProj, Requests.  
- **Visualization:** Matplotlib, Folium, and Jupyter Notebook.  
- **Tools:** GeoWeaver for workflow management, Binder for interactive exploration.  

## Setup and Usage  
- The workflow retrieves SWE observations from SNOTEL and CDEC for the selected date.  
- Data are preprocessed into a model-ready dataframe including terrain, seasonal, and historical SWE features.  
- Model training uses 75% of NASA ASO and snow course data (2013–2018) with 25% held for testing.  
- Evaluation is performed on the 2019 water year hindcast simulation.  
- The Jupyter Book provides step-by-step tutorials for data preparation, model training, evaluation, and workflow management.  

## Project Context & Domain  
- **Domain:** Hydrology / Snow Modeling / Machine Learning.  
- **Affiliation:** CIROH (Cooperative Institute for Research to Operations in Hydrology), The University of Alabama, NASA, NOAA, and USGS.  
- **Purpose:** Advance snow state modeling and forecasting using deep learning techniques for operational hydrology applications.  

## Input / Output  
**Input:**  
- SWE observations from SNOTEL and CDEC stations.  
- Lidar-derived terrain features, latitude, longitude, elevation, and seasonality metrics.  
- Metadata and grid definitions in GeoJSON and CSV formats.  

**Output:**  
- High-resolution (1 km) SWE predictions.  
- Hindcast SWE simulations and interactive visualizations.  
- Evaluation metrics and performance plots for SWE prediction accuracy.  
