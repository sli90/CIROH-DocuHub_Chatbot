# Project Title: **ciroh_pyngiab**

## Project Objective  
The **ciroh_pyngiab** repository provides tools and configurations to run the **NextGen In A Box (NGIAB)** hydrologic modeling workflow entirely within a **Python or Jupyter environment**.  
It integrates NGIAB capabilities—such as data preprocessing and model execution—into JupyterHub-compatible environments, enabling researchers to perform end-to-end hydrologic simulations using the NextGen framework.

## Core Functionalities  
- **JupyterHub-compatible NGIAB:**  
  - Provides a version of NGIAB that can run on JupyterHub platforms (e.g., 2i2c), adapted from the standard NGIAB built on `rockylinux9`.  
  - Builds upon the `pangeo/pangeo-notebook` image to ensure compatibility with CIROH’s 2i2c infrastructure.  
  - Includes scripts such as `Dockerfile` and `docker_run.sh` for local image creation and deployment.  
- **Python Wrapper Libraries:**  
  - Wraps NGIAB’s data preprocessing and model execution shell scripts for direct use from Python.  
  - Enables execution of the NextGen model framework directly from a Jupyter Notebook or Python script without terminal commands.  
- **Integrated Tools:**  
  - Preinstalled utilities include [`ngiab_data_preprocess`](https://github.com/CIROH-UA/NGIAB_data_preprocess) for data subsetting, forcing generation, and realization creation.  
  - Contains example tests, unit test files, and CI/CD workflow configurations.  
- **Sample Data:**  
  - Example datasets are included under `/tests/` in the container image.  
  - Users may also follow the NGIAB “Quick Start Guide” to manually download additional data.  

## Technical Stack  
- **Languages:** Python, Shell  
- **Containerization:** Docker  
- **Base Image:** `pangeo/pangeo-notebook:2024.04.08`  
- **Dependencies:** NGIAB, NextGen, ngiab_data_preprocess  
- **Environment:** Compatible with JupyterHub and local Docker environments  
- **Installation:** Available via pip using `pip install git+https://github.com/fbaig/ciroh_pyngiab.git`  

## Setup and Usage  
### 1. Access Preconfigured JupyterHub Environments  
- **Production:** [CIROH 2i2c JupyterHub](http://staging.ciroh.awi.2i2c.cloud/)  
- **Staging/Dev:** [CIROH 2i2c JupyterHub (Staging)](http://staging.ciroh.awi.2i2c.cloud/)  
- **Local Deployment:**  
  - Build local image with `Dockerfile` or `docker_run.sh`.  
  - Access via `http://127.0.0.1:8888/` after running:  
    ```bash
    docker run -it            -v "${PWD}":/shared/            -p 8888:8888            quay.io/fbaig25/ngiab-2i2c:latest            jupyter lab --ip 0.0.0.0 /shared
    ```  
- **Upcoming:** Support for [I-GUIDE JupyterHub](https://jupyter.iguide.illinois.edu/).  

### 2. Python Wrapper Example  
Execute NGIAB via Python:  
```python
from pyngiab import PyNGIAB

data_dir = './AWI_16_2863657_007'
test_ngiab = PyNGIAB(data_dir)
test_ngiab.run()
```  
For serial mode:  
```python
test_ngiab_serial = PyNGIAB(data_dir, serial_execution_mode=True)
test_ngiab_serial.run()
```  

### 3. Data Preprocessing Example  
Run data subsetting, forcing generation, and realization creation:  
```bash
python -m ngiab_data_cli -i cat-5173 -a --start 2022-01-01 --end 2022-02-28
```  

## Project Context & Domain  
- **Domain:** Hydrology / Hydrologic modeling / Computational workflows.  
- **Affiliation:** Cooperative Institute for Research to Operations in Hydrology (**CIROH**), The University of Alabama.  
- **Purpose:** Streamline end-to-end hydrologic modeling within Jupyter environments, combining NGIAB and NextGen frameworks for research and development.  

## Input / Output  
**Input:**  
- Catchment ID, date ranges, configuration files, and hydrologic datasets.  
- Preprocessing utilities for data subsetting and forcing generation.  

**Output:**  
- NextGen model execution results and generated realization files.  
- Processed hydrologic data and analysis-ready outputs.  
