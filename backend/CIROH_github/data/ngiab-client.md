# Project Title: **ngiab-client**

## Project Objective  
The **NGIAB Output and Datastream Visualizer** is a **Tethys + React web application** designed to visualize outputs from the **NextGen In A Box (NGIAB)** hydrologic modeling system.  
Developed under the **NOAA–CIROH Cooperative Agreement** with The University of Alabama, it provides an interactive platform for **geospatial, temporal, and performance analysis** of NextGen model results.  
The tool allows users to explore model outputs, visualize catchments and nexus points, and integrate **TEEHR** performance metrics for hydrologic evaluation.

## Core Functionalities  
- **Geospatial Visualization:** Displays catchments, nexus points, and river reaches.  
- **Time Series Analysis:** Interactive plots for catchments, nexus points, and `troute` variables.  
- **TEEHR Output Visualization:** Plots metrics such as Kling-Gupta Efficiency (KGE), Nash–Sutcliffe Efficiency (NSE), and relative bias.  
- **S3 Datastream Integration:** Downloads and visualizes model outputs stored in the [NextGen Datastream](https://github.com/CIROH-UA/ngen-datastream).  
- **Multi-run Management:** Supports multiple NGIAB runs via `ngiab_visualizer.json`.  
- **Dockerized Deployment:** Runs in containers for consistency across environments.  
- **Assisted & Unassisted Launch Options:** Can be started via `ViewOnTethys.sh` script or through manual Docker commands.  
- **Frontend–Backend Integration:** Combines a **React** frontend with a **Tethys (Django)** backend for dynamic web interaction.  

## Technical Stack  
- **Frontend:** React + Webpack  
- **Backend:** Tethys Platform (Django-based)  
- **Containerization:** Docker  
- **Package Managers:** npm (JavaScript), PDM (Python)  
- **Programming Languages:** Python, JavaScript  
- **Database:** SQLite (default Tethys configuration)  
- **Testing & Linting:**  
  - JavaScript: Jest, eslint, testing-library  
  - Python: pytest, flake8, yapf  
- **Supported Node Version:** Node.js 20 (via nvm)  
- **Dependency Managers:** conda / pip for Python, npm for Node modules  

## Setup and Usage  
1. **Assisted Launch (Recommended):**  
   - Run via `ViewOnTethys.sh` (from NGIAB-CloudInfra).  
   - Automatically mounts user output directories and visualizer metadata.  
   - Provides prompt for overwriting or duplicating model runs.  

2. **Unassisted Launch:**  
   - Create directories:  
     - `~/ngiab_visualizer` for model runs  
     - `~/.datastream_ngiab` for cached outputs  
   - Configure JSON metadata (`ngiab_visualizer.json`) with model paths and IDs.  
   - Define environment variables (TETHYS_REPO, PORT, paths, etc.).  
   - Run container:  
     ```bash
     docker run --rm -d -v "$MODELS_RUNS_DIRECTORY:$TETHYS_PERSIST_PATH/ngiab_visualizer"        -v "$DATASTREAM_DIRECTORY:$TETHYS_PERSIST_PATH/.datastream_ngiab"        -p "$NGINX_PORT:$NGINX_PORT"        --name "$TETHYS_CONTAINER_NAME" "${TETHYS_REPO}:${TETHYS_TAG}"
     ```  
   - Access locally at [http://localhost:80](http://localhost:80).  

3. **Development Setup:**  
   - Create Python virtual environment.  
   - Install **Tethys Platform**, **Node.js 20**, and **PDM**.  
   - Install dependencies:  
     ```bash
     pdm install
     npm install --include=dev
     ```  
   - Run both Tethys and Webpack dev servers concurrently.  

4. **Build & Test:**  
   - Build frontend: `npm run build`  
   - Lint frontend: `npm run lint`  
   - Test frontend: `npm run test`  
   - Lint backend: `flake8 .`  
   - Test backend: `pytest`  

## Project Context & Domain  
- **Domain:** Hydrology / Web visualization / Model evaluation.  
- **Affiliation:**  
  - **NOAA** (National Oceanic and Atmospheric Administration)  
  - **CIROH** (Cooperative Institute for Research to Operations in Hydrology)  
  - **The University of Alabama**  
- **Purpose:** Facilitate exploration, validation, and performance evaluation of NextGen hydrologic model outputs via an accessible, web-based interface.  

## Input / Output  
**Input:**  
- NGIAB model outputs (e.g., `ngen` results, `TEEHR` metrics).  
- Metadata JSON files (`ngiab_visualizer.json`, `.datastream_ngiab.json`).  
- Optional S3-stored datasets from NextGen Datastream.  

**Output:**  
- Interactive geospatial maps, time series plots, and performance visualizations.  
- Web interface accessible through local or hosted deployment.  
