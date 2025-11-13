# Project Title: **ngiab-cal**

## Project Objective  
**ngiab-cal** is a Python command-line interface (CLI) tool that simplifies hydrologic model calibration for **NextGen In A Box (NGIAB)** workflows. It automates the creation of calibration directories and configuration files necessary to run a modified version of **ngen-cal**, streamlining calibration setup, execution, and parameter management.

## Core Functionalities  
- Automates calibration configuration creation.  
- Runs calibration processes using Docker.  
- Copies calibrated parameters back to model configurations.  
- Generates configuration files compatible with the `ngiab_cal` branch of **ngen-cal**.  
- Supports warmup, calibration, and validation workflows.  
- Provides both basic and advanced command-line options for calibration setup.  
- Downloads USGS streamflow data for calibration.  
- Creates visual plots and validation results after calibration.  

## Technical Stack  
- **Language:** Python 3.10+  
- **Dependencies:** Docker, Internet connection for USGS data download.  
- **Containerization:** Uses Docker image `joshcu/ngiab-cal:demo`.  
- **Supported Models:** CFE (Conceptual Functional Equivalent), Noah-OWP-Modular.  
- **Calibration Algorithm:** Dynamically Dimensioned Search (DDS).  
- **Configuration Files:** YAML-based calibration settings (`ngen_cal_conf.yaml`).  

## Setup and Usage  
### Installation Options  
- **Using `uvx` (recommended):**  
  ```bash
  uvx ngiab-cal --help
  uv tool install ngiab-cal
  ```  
- **Using `pipx`:**  
  ```bash
  pipx install ngiab-cal
  ngiab-cal --help
  ```  
- **Using pip:**  
  ```bash
  pip install ngiab-cal
  python -m ngiab_cal --help
  ```  

### Basic Usage  
```bash
# Create calibration configuration
ngiab-cal /path/to/ngiab/data/folder -g USGS_GAGE_ID

# Create and run calibration (200 iterations)
ngiab-cal /path/to/ngiab/data/folder -g USGS_GAGE_ID --run -i 200

# Force recreation of calibration configuration
ngiab-cal /path/to/ngiab/data/folder -g USGS_GAGE_ID -f
```  

### Example Workflow: Calibrating CAMELS Basins  
The README includes a full Bash script example for calibrating multiple CAMELS basins, automating data preparation and calibration through `ngiab-cal` and `ngiab_data_preprocess`.  

### Calibration File Example  
The tool creates `calibration/ngen_cal_conf.yaml`, defining parameters for the calibration process, including:  
- Algorithm type (`dds`)  
- Iterations, restart, and log settings  
- Model parameter definitions (`min`, `max`, `init`)  
- Evaluation parameters (objective function, time range, basin ID)  

### Execution Process  
1. Validates input and required files.  
2. Downloads USGS streamflow data.  
3. Generates configuration files for calibration.  
4. Executes calibration inside a Docker container.  
5. Extracts calibrated parameters to update model configuration.  

## Project Context & Domain  
- **Domain:** Hydrology / Model Calibration / Water Resources Modeling.  
- **Affiliation:** CIROH (Cooperative Institute for Research to Operations in Hydrology).  
- **Purpose:** Simplify and automate NGIAB model calibration through a Python CLI integrating Docker-based ngen-cal execution.  

## Input / Output  
**Input:**  
- NGIAB directory path.  
- USGS gage ID.  
- Optional parameters (iterations, warmup days, calibration ratio, etc.).  
- Configuration templates for calibration.  

**Output:**  
- Calibration configuration file (`ngen_cal_conf.yaml`).  
- Calibration results and plots in `./calibration/Output/Calibration_Run/`.  
- Updated model configuration files with calibrated parameters.  


## Acknowledgments  
- [CIROH](https://docs.ciroh.org/) for NextGen In A Box.  
- [NGEN-CAL](https://github.com/NOAA-OWP/ngen-cal) developers.  
