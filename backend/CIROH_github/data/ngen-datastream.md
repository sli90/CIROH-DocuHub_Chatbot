# Project Title: **ngen-datastream**

## Project Objective  
The **NextGen Research DataStream** aims to make hydrologic simulations more transparent, collaborative, and reproducible. It provides an open-source, community-editable configuration of the [NextGen Framework](https://github.com/NOAA-OWP/ngen), enabling researchers and hydrologists to contribute to improving streamflow predictions. By publicly sharing forcings, outputs, and configurations, the project allows regional experts to iteratively refine and enhance hydrologic modeling capabilities hosted in the AWS cloud.

## Core Functionalities  
- Provides an **array of daily NextGen-based hydrologic simulations** hosted on AWS.  
- Offers a **community-editable configuration** to improve streamflow predictions collaboratively.  
- Includes **DataStreamCLI**, a backend tool that:
  - Automates data collection and input formatting for NextGen runs.  
  - Orchestrates NextGen execution through *NextGen In a Box (NGIAB)*.  
  - Manages outputs efficiently and reproducibly.  
  - Integrates with tools such as **hfsubset**, **NextGen In A Box**, and **TEEHR**.  
- Supplies an **interactive CLI guide** to help users understand and configure runs.  
- Provides **infrastructure documentation**, including AWS architecture and current project status.  
- Hosts **open discussions and contribution guides** to foster community collaboration.  

## Technical Stack  
- Programming Languages: Not specified.  
- Frameworks/Libraries:  
  - NextGen In A Box (NGIAB)  
  - hfsubset  
  - TEEHR  
- Infrastructure: AWS Cloud, Terraform (for Infrastructure as Code).  

## Setup and Usage  
Users install `DataStreamCLI` by following the installation guide. The interactive guide script helps users explore the repository and construct commands for simulations.  
Basic usage involves:  
1. Obtaining a hydrofabric file (e.g., via `hfsubset`).  
2. Running `DataStreamCLI` with parameters specifying start/end times, configuration, and hydrofabric input.  
3. Viewing simulation outputs in the designated `ngen-run/outputs` directory.  

## Project Context & Domain  
- **Domain:** Hydrology / Environmental Modeling.  
- **Institutions:** Developed under the **Center for Hydrometeorology and Remote Sensing (CIROH)** and linked to **NOAA’s NextGen Framework**.  
- **Hosting:** AWS Cloud infrastructure.  
- **Purpose:** Enhance accessibility, collaboration, and reproducibility in hydrologic modeling and streamflow prediction.  

## Input / Output  
**Input:**  
- Hydrofabric geopackage file (e.g., watershed boundaries, flowlines, network, forcing weights).  
- NextGen model configuration JSON files.  
- Time domain parameters for simulation.  

**Output:**  
- NextGen simulation results stored in a local directory structure (`ngen-run/outputs`).  
- Data includes processed hydrologic model outputs for streamflow and related variables.  
