# Project Title: **PINN_workshop_ciroh**

## Project Objective  
The **PINN_workshop_ciroh** repository provides official materials for the Physics-Informed Neural Networks (PINN) Workshop held at the CIROH Development Conference 2024. It demonstrates the application of PINNs in solving conceptual problems and Partial Differential Equations (PDEs) related to hydrology.

## Core Functionalities  
- Introduces Physics-Informed Neural Networks (PINNs) and their integration of physical laws into neural network models.  
- Provides step-by-step tutorials for implementing and training PINNs on hydrological models.  
- Includes example projects demonstrating PINNs for complex hydrological problems such as groundwater and surface water flow.  
- Supplies utility scripts for constructing and training PINNs on various PDEs in hydrology.  
- Features two hands-on Jupyter notebooks:  
  1. **heat_equation_pinn** – Solves a one-dimensional transient heat equation.  
  2. **2d_shallow_water_inverse** – Solves a two-dimensional transient shallow water equation as an inverse problem.  

## Technical Stack  
- **Languages:** Python.  
- **Frameworks/Libraries:** Not specified.  
- **Dependencies:** Defined in the `environment.yml` file for Conda setup.  

## Setup and Usage  
1. Install Conda if not already available.  
2. Clone the repository:  
   ```bash
   git clone https://github.com/AMBehroozi/PINN_workshop_ciroh.git
   cd PINN_workshop_ciroh
   ```  
3. Create and activate the Conda environment:  
   ```bash
   conda env create -f environment.yml
   conda activate pinn_workshop_env
   ```  
4. Alternatively, use the provided `setup.sh` script for automated setup.  

## Project Context & Domain  
- **Domain:** Hydrology / Machine Learning / Physics-Informed Modeling.  
- **Affiliation:** Cooperative Institute for Research to Operations in Hydrology (CIROH).  
- **Purpose:** Provide educational materials and practical examples for using PINNs in hydrological research and modeling.  

## Input / Output  
**Input:** Jupyter notebooks and configuration files for training PINN models on hydrological PDEs.  
**Output:** Trained PINN models and results visualizing solutions to heat and shallow water equations.  
