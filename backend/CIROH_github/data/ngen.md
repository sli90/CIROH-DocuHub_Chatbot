# Project Title: **ngen**

## Project Objective  
The **Next Gen Water Modeling Framework Prototype** (ngen) is designed to modernize and improve hydrologic modeling by addressing limitations in traditional models when applied across varying spatial and temporal scales. It adopts a **data-centric approach**, organizing hydrologic data first and mapping appropriate solutions to that data. This enables more flexible, scalable, and modular simulation of hydrologic processes.  
The framework serves hydrologic researchers, developers, and water resource modelers seeking a more transparent and extensible modeling system capable of handling complex interactions across catchments.

## Core Functionalities  
- **Data-centric modeling architecture:** Prioritizes organizing hydrologic data before assigning modeling algorithms.  
- **Component encapsulation:** Models are organized into catchments and nexuses connected by well-defined APIs to simulate water movement.  
- **Polymorphic and modular design:** Enables flexible model configurations and mixing of multiple formulations within one simulation.  
- **Recursive abstraction:** Allows nesting of high-resolution or “complex” realizations within catchments for multi-scale representation.  
- **Distributed processing:** Supports partitioned and parallel model execution.  
- **Testing framework:** Includes automated testing using **Google Test** for unit and integration validation.  
- **Debugging and development tools:** Supports debugging via **CMake**, `gdb`, `lldb`, or **GitPod** (browser-based VSCode environment).  
- **Extensive documentation and examples:** Includes structural diagrams, dependency listings, installation instructions, and usage examples for both serial and distributed runs.  

## Technical Stack  
- **Language:** C++ (minimum standard: C++14)  
- **Build System:** CMake  
- **Testing Framework:** Google Test  
- **Optional Development Tools:** GitPod, gdb/lldb for debugging  
- **Dependencies:** Listed in `doc/DEPENDENCIES.md`  
- **Version:** 0.1.0 (initial development release)  

## Setup and Usage  
- **Installation:** Follow instructions in `INSTALL.md` to compile and configure.  
- **Basic usage:**  
  - Run the ngen executable with paths to input GeoJSONs and configuration files:  
    ```bash
    ngen ./data/catchment_data.geojson "" ./data/nexus_data.geojson "" ./data/refactored_example_realization_config.json
    ```  
  - Subset catchments/nexuses using comma-separated IDs or use `"all"` for full runs.  
  - Use the `--info` flag to view compile-time configuration details.  
- **Testing:** Build and execute tests with CMake targets (`test_all`, `test_unit`, or `test_integration`).  
- **Debugging:** Enable `-g` compile flag and debug via `gdb`, `lldb`, or GitPod with VSCode extensions.  

## Project Context & Domain  
- **Domain:** Hydrology / Computational modeling.  
- **Affiliation:** Developed under the **NOAA Office of Water Prediction (OWP)**.  
- **Purpose:** Advance the Next Generation Water Modeling Framework by improving modularity, scalability, and data-driven model integration for research and operational hydrology.

## Input / Output  
**Input:**  
- Catchment and nexus GeoJSON files (hydrofabric).  
- JSON realization and partition configuration files.  
- Optional distributed processing parameters.  

**Output:**  
- Hydrologic simulation results (format not specified).  
- Diagnostic and log files generated during execution.  
