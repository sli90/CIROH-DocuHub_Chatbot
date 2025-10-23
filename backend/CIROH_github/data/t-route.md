# Project Title: **t-route**

## Project Objective  
**T-Route (Tree-Based Channel Routing)** is a dynamic, modular routing model designed to handle one-dimensional (1-D) channel routing in vector-based river network data. It provides a fast and flexible solution for routing streamflows through river networks such as those in the **National Water Model (NWM)** and the **NextGen framework**.  
The tool enables heterogeneous application of routing models—such as Muskingum-Cunge for headwater streams and Diffusive Wave for high-order rivers—allowing efficient use of computational resources and scalability across hydrologic systems.

## Core Functionalities  
- **Multi-model routing:** Supports Muskingum-Cunge, Diffusive Wave, and Dynamic Wave routing methods.  
- **Compatibility:** Works with **NHDPlus High Resolution datasets** and **HY_Features** (OGC WaterML 2.0 Surface Hydrology Features model).  
- **Flexible architecture:** Combines hydrologic and hydraulic routing within the same network.  
- **Modular design:** Independent modules for reservoirs, data assimilation, and flow routing.  
- **Heterogeneous routing:** Enables mixed routing model configurations within a single domain.  
- **Python + Fortran integration:** Core routing algorithms implemented in Fortran, orchestrated by Python.  
- **Parallelization:** Supports large-scale routing through acyclic network traversal.  
- **Demonstration data:** Includes example runs such as the Lower Colorado River, TX test case.  

## Technical Stack  
- **Languages:** Python and Fortran  
- **Core Components:**  
  - Python: Pre-processing, traversal framework, time-series data handling  
  - Fortran: Routing model engines (Muskingum-Cunge, Diffusive Wave)  
- **Dependencies:** NetCDF-Fortran libraries, Python 3.10, standard build tools (CMake, gfortran, pip).  
- **Platform Support:** macOS, Linux, and Windows (via WSL).  
- **Documentation:** Installation guides for macOS and Linux/WSL are included in the repository.  

## Setup and Usage  
### Installation Overview  
1. **System preparation:** Install Python 3.10, Fortran compilers, and NetCDF libraries.  
2. **Clone and set up environment:**  
   ```bash
   git clone https://github.com/CIROH-UA/t-route.git
   cd t-route
   python3.10 -m venv troute_env
   source troute_env/bin/activate
   pip install -r requirements.txt
   ```  
3. **Build NetCDF Fortran libraries:** Follow UCAR installation steps and link them to the compiler script.  
4. **Compile T-Route:**  
   ```bash
   ./compiler.sh
   ```  
5. **Run example model:**  
   ```bash
   cd test/LowerColorado_TX
   python3 -m nwm_routing -f -V4 test_AnA_V4_NHD.yaml
   ```  
6. **Troubleshooting:** Permission and compilation issues can be resolved using `chmod` or checking library paths.  

## Project Context & Domain  
- **Domain:** Hydrology / Channel routing / Water resource modeling.  
- **Affiliation:** Developed under the **NOAA Office of Water Prediction (OWP)**.  
- **Purpose:** Provides high-performance, flexible routing capabilities for hydrologic models such as the **National Water Model (NWM) 3.0** and the **NextGen framework**.  
- **Mission Alignment:** Supports NOAA’s goal of providing state-of-the-science hydrologic forecasting and decision-support tools for emergency management and water resource planning.  

## Input / Output  
**Input:**  
- Lateral inflows for each node in a river network.  
- Network topology data (e.g., NHDPlus HR or HY_Features).  
- Configuration files defining routing parameters and model selection.  

**Output:**  
- Simulated streamflow time series at network nodes.  
- Optional data assimilation outputs and routing diagnostics.  

## Known Issues  
Refer to the repository’s GitHub Issues page for ongoing improvements and bug tracking.  

## Getting Help  
For technical support, contact the T-Route maintainers:  
- dongha.kim@noaa.gov  
- sean.horvath@noaa.gov  
- amin.torabi@noaa.gov  
- jurgen.zach@noaa.gov  

## Getting Involved  
Contributors are encouraged to fork the repository and submit pull requests. Ongoing work includes improving parallel processing performance and expanding I/O capabilities. Contribution guidelines will be added to `CONTRIBUTING.md`.  

## License  
Open-source under the terms specified in:  
1. [TERMS](TERMS.md)  
2. [LICENSE](LICENSE)  

## Credits and References  
Acknowledgments to Drs. Ehab Meslehe, Fred Ogden, and the NCAR WRF-Hydro development team for foundational contributions. Continued leadership and support from Dr. Trey Flowers.  
