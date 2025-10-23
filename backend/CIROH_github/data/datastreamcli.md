# Project Title: **datastreamcli**

## Project Objective  
**DataStreamCLI** is a standalone command-line tool that automates the complete workflow from **preprocessing input data** for [NextGen](https://github.com/NOAA-OWP/ngen) to executing the **NextGen simulation** through [NextGen In a Box (NGIAB)](https://github.com/CIROH-UA/NGIAB-CloudInfra).  
It serves as the workflow tooling for the [NextGen Research DataStream](https://github.com/CIROH-UA/ngen-datastream), enabling users to run NextGen efficiently, reproducibly, and with integrated support for **hfsubset**, **NGIAB**, and **TEEHR**.

## Core Functionalities  
- **Automated workflow:** Handles the full NextGen workflow—from data preprocessing to simulation execution.  
- **Integration with external tools:** Supports tools such as `hfsubset`, NGIAB, and TEEHR.  
- **Model configuration automation:** Generates configurations for available NextGen models.  
- **Interactive setup:** Includes an interactive script (`datastream_guide`) to guide users through setup and command formation.  
- **Documentation suite:** Provides detailed documentation covering available models, datastream options, standard directory structures, and internal workflow breakdowns.  
- **Status monitoring:** Includes a `STATUS.md` file for tracking tool and integration availability.  
- **Reproducibility:** Ensures consistent simulation runs via standardized inputs and configurations.  

## Technical Stack  
- **Programming Language:** Not specified.  
- **Frameworks / Libraries:** Not specified.  
- **Integrated Tools:** NextGen, NGIAB, hfsubset, and TEEHR.  
- **License:** GNU General Public License v3.0 or later.  

## Setup and Usage  
1. **Installation:**  
   - Follow the [Installation Guide](https://github.com/CIROH-UA/datastreamcli/blob/main/INSTALL.md) to prepare the environment.  

2. **Interactive Guide:**  
   - Run the [DataStreamCLI guide](https://github.com/CIROH-UA/datastreamcli/blob/main/scripts/datastream_guide) to explore repository functions and form commands interactively.  

3. **Example Workflow:**  
   - Obtain a hydrofabric file (e.g., using `hfsubset`).  
   - Run a 24-hour NextGen simulation:  
     ```bash
     ./scripts/datastream -s 202006200100                          -e 202006210000                          -C NWM_RETRO_V3                          -d $(pwd)/data/datastream_test                          -g $(pwd)/palisade.gpkg                          -R $(pwd)/configs/ngen/realization_sloth_nom_cfe_pet_troute.json                          -n 4
     ```
   - Outputs will be located at:  
     ```
     $(pwd)/data/datastream_test/ngen-run/outputs
     ```

## Project Context & Domain  
- **Domain:** Hydrology / Environmental Modeling / Workflow Automation.  
- **Affiliation:** Not specified.  
- **Purpose:** Simplify, standardize, and automate NextGen model runs using reproducible, CLI-based workflows.  

## Input / Output  
**Input:**  
- Hydrofabric files (e.g., `.gpkg`).  
- NextGen configuration JSONs and run parameters.  
- Command-line arguments defining time domain and model setup.  

**Output:**  
- NextGen simulation outputs generated in the specified data directory.  
