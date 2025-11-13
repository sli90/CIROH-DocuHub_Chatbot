# Project Title: **OPG-CNN-Northern-Utah-CIROH-Workshop**

## Project Objective  
The **OPG-CNN-Northern-Utah-CIROH-Workshop** repository provides materials for a workshop on applying Convolutional Neural Networks (CNNs) to predict Orographic Precipitation Gradients (OPGs) in complex terrain. The project aims to improve precipitation forecasts by downscaling coarse-resolution climate model outputs using CNNs trained on ERA5 data.

## Core Functionalities  
- Introduces participants to CNNs and their applications in hydro-meteorology.  
- Explains CNN structure, learning processes, and Explainable AI (XAI) techniques.  
- Guides users in customizing CNNs through hyperparameter tuning and architectural modifications.  
- Provides scripts for predicting Orographic Precipitation Gradients (OPGs) in northern Utah.  
- Demonstrates the downscaling of ERA5 reanalysis data for liquid precipitation.  
- Includes both cloud-based (CIROH 2i2c JupyterHub) and local setup instructions.  

## Technical Stack  
- **Languages:** Python  
- **Frameworks/Libraries:** Not specified  
- **Dependencies:** Provided via `environment.yml` and `requirements.txt` files.  

## Setup and Usage  
### Using CIROH JupyterHub  
1. Fork the repository on GitHub.  
2. Access the [CIROH 2i2c JupyterHub](https://ciroh.awi.2i2c.cloud/).  
3. Select the `Medium` server configuration (11GB RAM, 4 CPUs).  
4. Choose the image: `DevCon24 workshop : CNN for downscaling climate forcing variables`.  
5. Clone your forked repository and activate the notebook environment.  
6. Register the kernel in JupyterHub and select it from the Jupyter interface.  

### Using a Personal Computer  
1. Fork and clone the repository.  
2. Create a Python environment:  
   ```bash
   conda env create -f environment.yml
   conda activate cnn_env
   ```  
3. Register the environment kernel:  
   ```bash
   python -m ipykernel install --user --name=YOUR-ENV-NAME
   ```  

## Project Context & Domain  
- **Domain:** Hydro-meteorology / Machine Learning / Climate Modeling  
- **Affiliation:** Cooperative Institute for Research to Operations in Hydrology (CIROH)  
- **Purpose:** To provide training and hands-on experience in CNN-based downscaling for precipitation modeling.  

## Input / Output  
**Input:**  
- ERA5 reanalysis data (pressure and single levels)  
- Orographic precipitation gradient (OPG) datasets for northern Utah  

**Output:**  
- CNN-predicted OPG fields and precipitation downscaling results  

## Folder Structure  
```
├── datasets                   # Pre-processed ERA5, facets, observed precipitation, and OPGs
├── figures                    # Generated figures from workshop scripts
├── pre-processing             # Scripts for dataset pre-processing
├── scripts                    # CNN Workshop scripts
├── README.md                  # Documentation file
├── environment_jupyter.yml    # Environment setup for JupyterHub
└── requirements.txt           # Python package dependencies
```

## Data Sources  
- **Bohne et al. (2020):** Climatology of Orographic Precipitation Gradients (Western U.S.)  
- **ECMWF ERA5:** Hourly reanalysis data from the Copernicus Climate Data Store (1988–2017)  
