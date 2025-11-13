# Project Title: **LSTM (Basic Model Interface for Streamflow Prediction)**

## Project Objective  
This project provides a **Long Short-Term Memory (LSTM)** deep learning model designed for use within the **Next Generation Water Resources Modeling Framework (NextGen)**.  
The goal is to enable **streamflow prediction** using trained LSTM networks through a standardized **Basic Model Interface (BMI)**, improving model interoperability and accuracy in hydrologic forecasting.  
It allows integration with NextGen and supports model testing, training, and validation for multiple basins using open hydrologic datasets.

## Core Functionalities  
- **BMI Integration:** Wraps an LSTM model with a Basic Model Interface (BMI) to standardize how models interact within NextGen.  
- **NeuralHydrology adaptation:** Uses a modified version of NeuralHydrology’s `CudaLSTM` for forward passes (`nextgen_cuda_lstm.py`).  
- **Flexible configurations:** Supports multiple trained LSTM models with varying input attributes and forcings.  
- **Example datasets:** Includes forcing and observation data for four USGS gauges (e.g., Falling River, Marsh Creek, Brokenstraw Creek, Narraguagus River).  
- **Training & testing setup:** Offers examples for model setup, configuration, and execution using Python or Jupyter Notebooks.  
- **Unit tests:** Implements automated tests for BMI model control, variable getters/setters, and grid functions.  
- **Environment setup:** Uses `environment.yml` for dependency management via Anaconda or standard Python environments.  

## Technical Stack  
- **Language:** Python  
- **Frameworks & Tools:**  
  - [PyTorch](https://pytorch.org/) (for model training/inference)  
  - [NeuralHydrology](https://neuralhydrology.readthedocs.io/) (adapted model structure)  
  - [BMI](https://bmi.readthedocs.io/en/latest/) (interface standard)  
  - [Anaconda](https://www.anaconda.com/) (environment management)  
- **Dependencies:** Defined in `environment.yml` (includes `xarray==0.14.0` and `llvm-openmp==10.0.0`).  
- **Data Formats:** NetCDF (`.nc`), YAML (`.yml`), and PyTorch model weights (`.pt`).  

## Setup and Usage  
### Environment Setup  
1. Create a conda environment:  
   ```bash
   conda env create -f environment.yml
   conda activate bmi_lstm
   ```  
2. Install the LSTM library:  
   ```bash
   pip install lstm
   ```  

### Running the Model  
1. Configure the LSTM run by editing or creating a YAML config file in `bmi_config_files/`.  
2. Run the LSTM BMI module:  
   ```bash
   python -m lstm
   ```  
3. Example workflow:  
   - Initialize the model: `model.initialize()`  
   - Run one or multiple timesteps: `model.update()` or `model.update_until(model.iend)`  
   - Finalize: `model.finalize()`  

### Unit Testing  
Run the BMI test suite:  
```bash
python ./lstm/run_bmi_unit_test.py
```  

## Project Context & Domain  
- **Domain:** Hydrology / Machine Learning / Streamflow prediction.  
- **Affiliation:** Developed for integration with the **NOAA Office of Water Prediction’s NextGen framework**.  
- **Purpose:** Advance hydrologic modeling by coupling deep learning models with standardized interfaces for operational and research applications.  

## Input / Output  
**Input:**  
- Atmospheric forcing data (e.g., NLDAS-based NetCDF files).  
- Catchment static attributes from the CAMELS dataset.  
- Configuration files (`.yml`) defining parameters, forcings, and runtime periods.  
- Trained model weights (`.pt` files).  

**Output:**  
- Simulated streamflow predictions for target basins.  
- Comparison datasets for model evaluation.  
- Logs and unit test results verifying BMI functionality.  
