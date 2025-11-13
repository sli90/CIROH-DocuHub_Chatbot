# Project Title: **Community-Streamflow-Evaluation-System (CSES)**

## Project Objective  
The **Community-Streamflow-Evaluation-System (CSES)** is a Python-based tool designed to evaluate hydrological model performance using a standardized NHDPlus data model. It enables users to assess modeled streamflow against over 5,000 in situ USGS monitoring sites through interactive visualization and analysis tools.

## Core Functionalities  
- Evaluates modeled streamflow performance using NHDPlus data and colocated USGS/NWIS monitoring sites.  
- Provides three primary analysis methods:  
  - **State-based LULC (Land Use Land Cover) Evaluation** using StreamStats.  
  - **HUC-level (Hydrologic Unit Code) Evaluation** for watershed-scale analysis.  
  - **USGS Station-based (Reach) Evaluation** for site-specific comparisons.  
- Allows fast access to observed and predicted data from the Alabama Water Institute-hosted AWS S3 datasets.  
- Supports interactive maps and performance visualizations through the `holoviews` package.  
- Designed for evaluating National Water Model (NWM) retrospective data (v2.1, with v3.0 coming soon).  

## Technical Stack  
- **Language:** Python (Version 3.9.12)  
- **Dependencies:** Listed in `requirements.txt`  
- **Visualization Tools:** holoviews  
- **Data Source:** AWS S3-hosted NWM v2.1 retrospective and USGS/NWIS observations  

## Setup and Usage  
1. Create a Python virtual environment.  
2. Install dependencies using the included `requirements.txt` file.  
3. Refer to the `Getting Started.md` guide for setup instructions.  
4. Choose one of the three main evaluation classes for analysis:  
   - `Eval_State()` for state-level StreamStats-based analysis.  
   - `HUC_Eval()` for hydrologic unit evaluation.  
   - `Reach_Eval()` for individual USGS site evaluation.
5. Input parameters include start date, end date, and model version (NWM v2.1).  

## Project Context & Domain  
- **Domain:** Hydrology / Streamflow Modeling / Data Evaluation  
- **Affiliation:** Alabama Water Institute, University of Alabama  
- **Purpose:** Provide a scalable, standardized framework to assess and improve hydrological model performance across diverse watersheds and land use types.  

## Input / Output  
**Input:**  
- NWM modeled streamflow data (v2.1 retrospective)  
- USGS/NWIS in situ streamflow observations  
- User-defined parameters (start date, end date, HUCs, or USGS site IDs)  

**Output:**  
- Statistical performance metrics and comparative plots of modeled vs. observed streamflow.  
- Interactive maps visualizing spatial distribution of model accuracy and performance.  

## License  
Licensed under the GitHub license specified in the repository.  
