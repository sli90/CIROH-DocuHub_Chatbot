## Enabling Community Research with the Next Generation National Water Modeling Framework on HydroShare-Linked Computing Platforms

Presentatiohn at AWRA 2025 Annual Water Resources Conference, Westminster, Colorado, November 10, 2025

Tarboton, D., A. Nassar, A. Castronova, A. Patel, F. Baig, H. Salehabadi, M. Abualqumboz, P. Dash and J. Horsburgh, (2025), "Enabling Community Research with the Next Generation National Water Modeling Framework on HydroShare-Linked Computing Platforms," AWRA 2025 Annual Water Resources Conference, Westminster, Colorado, November 10, 2025

## 📦 Contents  

- Powerpoint Presentation: Tarboton-Hydroshare-AWRA-11-10-25.pptx
- Tutorial folder with Python code and Jupyter Notebooks to set up, run, and analyze the results from a NextGEN model configured for research over a small watershed using the CIROH-2i2c Jupyterhub Community NextGen hub.

---

### 🌊 NextGen Hydrologic Modeling Tutorial
The Tutorial folder holds Python code and Jupyter Notebooks with step-by-step instructions to set up, run, and analyze the results from a NextGEN model configured for research over a small watershed using the CIROH-2i2c Jupyterhub Community NextGen hub. 

#### Jupyter Notebooks

##### 🧭 `NextGen_Data_Preparation.ipynb`  
- Subsets the hydrofabric dataset, AORC forcings, and sets up the model configuration and realization for CFE and Noah-OWP.  

##### 🚀 `NextGen_Run.ipynb`  
- Executes the NextGen hydrologic model using the default configuration and parameter values.

##### 📊 `NextGen_Output_Analysis.ipynb`  
- Analyzes and evaluates model output using water balance components.  
- Enables post-processing and visualization of results for interpretation and reporting.  

---

#### Python Utility Files

| Utility File | Purpose |
|--------------|---------|
| `forcings_visualization_utils.py` | Visualization of meteorological forcing data |
| `hydrofabric_visualization_utils.py` | Visualization of hydrofabric data |
| `ngen_outputs_utils.py` | Analysis and visualization of model outputs |

---

#### 📘 Steps

1. Use "Open With" on this resource to Launch the CIROH JupyterHub platform using the CIROH-2i2c Jupyterhub Community NextGen hub configuration. This copies the content of this resource into CIROH JupyterHub.   
2. In the Tutorial folder open and execute (cell by cell) the cells in  `NextGen_Data_Preparation.ipynb` to prepare inputs. This defined the area of interest, subsets the hydrofabric, and generates AORC forcings for the model. 
3. Proceed to `NextGen_Run.ipynb` to execute the model. This executes the NextGen model using the prepared inputs and default parameters and model formulation.  
4. Finish with `NextGen_Output_Analysis.ipynb` to analyze and visualize results.  

---

#### 👥 Intended Audience
 
- **Researchers** interested in getting started with NextGen to model watershed behavior and hydrologic processes  
- **Practitioners** interested in NextGen modeling workflows and their potential operational applications  
- **Educators** teaching hydrologic modeling and reproducible workflows

#### 🛠️ Preparation
To access CIROH-2i2c JupyterHub you need to request Individual CIROH-2i2c JupyterHub CPU Access at https://docs.ciroh.org/docs/services/access#accessing-ciroh-jupyterhub.  This requires a github account.  

#### 📦 Dependencies
This resource is set up to work with the CIROH-2i2c JupyterHub CIROH Community NextGen hub configuration. This has the content from [NextGen in a Box](https://github.com/CIROH-UA/NGIAB-CloudInfra) and [NGIAB data preprocess]( https://github.com/CIROH-UA/NGIAB_data_preprocess)

---
### 🙏 Acknowledgments
This research was supported by the Cooperative Institute for Research to Operations in Hydrology (CIROH) with funding under award NA22NWS4320003 from the NOAA Cooperative Institute Program. The statements, findings, conclusions, and recommendations are those of the authors and do not necessarily reflect the opinions of NOAA.

