# Project Title: **ngen-cal**

## Project Objective  
**ngen-cal** provides supporting code and workflows for automated calibration of [NGen](https://github.com/noaa-owp/ngen) Formulations using **Dynamic Dimensioned Search (DDS)**. It enables the generation of NGen parameter formulation permutations and executes them through the NGen framework driver.

## Core Functionalities  
- Automated calibration of NGen Formulations using DDS.  
- Python-based workflow for generating parameter permutations.  
- Executes runs through the NGen framework driver.  
- Includes unit testing using pytest.  
- Provides issue tracking and contribution guidelines for user support.  

## Technical Stack  
- **Language:** Python.  
- **Testing Framework:** pytest.  
- **Dependencies:** Listed in `requirements.txt`.  
- **Status:** Pre-release development (see CHANGELOG.md).  

## Setup and Usage  
- **Installation:** `TODO` (INSTALL.md referenced but not completed).  
- **Configuration:** `TODO`.  
- **Usage:** `TODO`.  

### Testing Instructions  
1. Install dependencies:  
   ```bash
   pip install -r python/requirements.txt
   ```  
   Or create and activate a virtual environment:  
   ```bash
   mkdir venv
   virtualenv ./venv
   source ./venv/bin/activate
   pip install -r python/requirements.txt
   ```  
2. Run tests using pytest:  
   ```bash
   pytest --log-cli-level 0 python/ngen-cal/test/
   ```  

## Project Context & Domain  
- **Domain:** Hydrology / Model Calibration.  
- **Affiliation:** Not specified.  
- **Purpose:** Support automated calibration workflows for NGen Formulations using DDS.  

## Input / Output  
**Input:**  
- NGen parameter formulations.  
- Python dependencies listed in `requirements.txt`.  

**Output:**  
- Calibration results from DDS-based workflow runs.  
