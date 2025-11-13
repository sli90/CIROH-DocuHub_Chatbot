# Project Title: **NGIAB-HPCInfra**

## Project Objective  
The **NextGen In A Box (NGIAB)** project provides a **containerized and user-friendly solution** for running the **NextGen National Water Resources Modeling Framework** locally or on high-performance computing (HPC) systems.  
This repository enables users to execute NextGen simulations using **Singularity containers**, offering flexibility to control inputs, configurations, and execution in both **serial and parallel modes**.

## Core Functionalities  
- Run NextGen locally or on HPC systems using Singularity containers.  
- Automatically detect system architecture (ARM or x86) and pull the appropriate container image.  
- Download and run the latest Singularity NextGen image from Docker Hub.  
- Allow users to specify and attach input data directories for simulations.  
- Support Serial, Parallel, and Interactive Shell execution modes.  
- Provide commands to download pre-packaged sample datasets (AWI-007, AWI-008, AWI-009).  
- Include a `guide.sh` script for model execution guidance.  
- Provide a Singularity definition file (`singularity_ngen.def`) and sample execution script (`HelloNGEN.sh`).  

## Technical Stack  
- **Languages:** Shell (Bash)  
- **Containerization:** SingularityCE  
- **Supported Architectures:** ARM and x86  
- **Dependencies:** SingularityCE, wget, tar, git  
- **Data Sources:** Pre-packaged datasets available via AWS S3 (e.g., AWI-007, AWI-008, AWI-009).  
- **External Tools:** Not specified.  

## Setup and Usage  
1. **Access a Compute Node:**  
   Request an interactive compute session on your HPC system (example using SLURM):  
   ```bash
   srun --partition=<partition_name> --nodes=1 --ntasks=1 --time=<hh:mm:ss> --pty bash
   ```  

2. **Install or Validate SingularityCE:**  
   ```bash
   singularity --version
   ```  
   If not installed, follow the [installation guide](https://docs.sylabs.io/guides/4.0/admin-guide/installation.html#installation-on-linux).  

3. **Prepare Input Data:**  
   ```bash
   mkdir -p NextGen/ngen-data
   cd NextGen/ngen-data
   wget --no-parent https://ciroh-ua-ngen-data.s3.us-east-2.amazonaws.com/AWI-009/AWI_16_10154200_009.tar.gz
   tar -xf AWI_16_10154200_009.tar.gz
   ```  

4. **Run the Simulation:**  
   ```bash
   git clone https://github.com/CIROH-UA/NGIAB-HPCInfra.git
   cd NGIAB-HPCInfra
   ./guide.sh
   ```  

5. **Execution Options:**  
   - Serial Mode  
   - Parallel Mode  
   - Interactive Shell Mode  

## Project Context & Domain  
- **Domain:** Hydrology / Water Resources Modeling / HPC Simulation  
- **Affiliation:** Cooperative Institute for Research to Operations in Hydrology (**CIROH**) and The University of Alabama  
- **Funding:** National Oceanic & Atmospheric Administration (**NOAA**) under Cooperative Agreement **NA22NWS4320003**  
- **Purpose:** Enable users to execute NextGen hydrologic simulations using Singularity containers on HPC systems  

## Input / Output  
**Input:**  
- Pre-downloaded or custom hydrologic datasets (e.g., `.tar.gz` files)  
- Configuration and realization files for simulations  
- User-defined parameters for simulation type and architecture  

**Output:**  
- Not specified.  
