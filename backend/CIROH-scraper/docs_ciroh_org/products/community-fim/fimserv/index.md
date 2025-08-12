# FIM as a Service

[Skip to main content](https://docs.ciroh.org/docs/products/community-fim/fimserv/#__docusaurus_skipToContent_fallback)

> **NOTE**
>
>  Below content is rendered from [https://github.com/sdmlua/FIMserv/blob/main/README.md](https://github.com/sdmlua/FIMserv/blob/main/README.md).

# Flood Inundation Mapping Tool using the OWP HAND-FIM operational framework

* * *

[![Version](https://camo.githubusercontent.com/a28c0a6266df7e69f0f0a5f66d805a319e238cc1ef4d1b5ee60c46b49a7afbdd/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f762f72656c656173652f73646d6c75612f46494d73657276)](https://github.com/sdmlua/FIMserv/releases)[![Issues](https://camo.githubusercontent.com/3a15bac30ecb1e628dfbe92a7a94a2189f1c5903f70f35d69015f0af39ce92d1/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732f73646d6c75612f46494d73657276)](https://github.com/sdmlua/FIMserv/issues)[![License: GPL v3](https://camo.githubusercontent.com/8a398fc9fbf479a323d2d91b9fcb6fb9c6b4d08e96dbb544488ccbed312115fc/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f4c6963656e73652d47504c76332d626c75652e737667)](https://opensource.org/licenses/GPL-3.0)[![PyPI version](https://camo.githubusercontent.com/8b0eb4a232f183926054ab0c52152c326c9d71fc2f7971f0e099ef843d0afef0/68747470733a2f2f62616467652e667572792e696f2f70792f66696d73657276652e7376673f69636f6e3d7369253341707974686f6e)](https://badge.fury.io/py/fimserve)[![PyPI Downloads](https://camo.githubusercontent.com/f6d38c557f7f19082ce6ed31890bb2d233717fe6a2eda30f72682e8ad0737904/68747470733a2f2f7374617469632e706570792e746563682f62616467652f66696d7365727665)](https://pepy.tech/projects/fimserve)[![Publish Status](https://github.com/sdmlua/FIMserv/actions/workflows/python-publish.yml/badge.svg)](https://github.com/sdmlua/FIMserv/actions/workflows/python-publish.yml)

### **OWP HAND-FIM 'as a service' (FIMserv)**

* * *

|  |  |
| --- | --- |
| [![SDML Logo](https://camo.githubusercontent.com/3144a76016c24b3f32281f151c46857601e5662e7e593013f3cb8024ff33af46/68747470733a2f2f73646d6c2e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032332f30312f53444d4c5f6c6f676f5f53715f677265792e706e67)](https://sdml.ua.edu/) | This package presents a streamlined, user-friendly and cloud-enabled pipeline to generate Operational flood inundation map using the NOAA Office of Water Prediction (OWP) Height Above Nearest Drainage (HAND) Flood Inundation Mapping (FIM) framework using the National Water Model retrospective and forecasted streamflow. It is developed under the Surface Dynamics Modeling Lab (SDML) as part of a project funded by the Cooperative Institute for Research to Operations in Hydrology (CIROH). |

### **Background**

* * *

OWP HAND-FIM is a national-scale operational flood forecasting framework ( [https://github.com/NOAA-OWP/inundation-mapping](https://github.com/NOAA-OWP/inundation-mapping)). It is a terrain-based fluvial flooding model that uses model-predicted streamflow and reach-averaged Synthetic Rating Curves (SRCs) to generate inundation extent and depth rasters at HUC-8 scale (Hydrologic Unit Code-8). The model can produce FIMs for all order streams within the watershed at a very low computational cost. This notebook streamline the FIM generation process or the OWP HAND-FIM framework on the cloud. It allow users to run over mutiple HUC-8s simultaneously. This model can run using any temporal resolution available from the input streamflow data (hourly, daily, monthly etc). ### **Currently we are hosting the FIM-4.4, 4.5 and 4.8 version for Inundation Mapping.**

### **Package structures**

* * *

This FIMserv framework is published as python package and published on [PyPI](https://pypi.org/project/fimserve/0.1.62/) [![PyPI version](https://camo.githubusercontent.com/8b0eb4a232f183926054ab0c52152c326c9d71fc2f7971f0e099ef843d0afef0/68747470733a2f2f62616467652e667572792e696f2f70792f66696d73657276652e7376673f69636f6e3d7369253341707974686f6e)](https://badge.fury.io/py/fimserve). It contains multiple modules to perform different functionalities which are structured into the fimserve folder while development of python packaging.

```
FIMserv/
├── docs/                   # Documentation (contains 'FIMserv' Tool usage sample codes)
│     ├── source/           #Contains  sphinx documentation (under development)
│     ├──code_usage.ipynb  #Contains the detailed documentation
│     └── FIMin3Steps.ipynb  #Focusing only on FIM generation within 3 steps
├── GeoGLOWS/               # Streamflow download using GeoGLOWS hydrofabrics
├── src/
│   └── fimserve/
│       ├── streamflowdata/ # Handles streamflow data
│       │   ├── nwmretrospectivedata.py   # Processes NWM retrospective data
│       │   ├── geoglows.py   # Module to retrieve geoglows streamflow data
│       │   ├── usgsdata.py   # Retrieve USGS gauge station data
│       │   └── forecasteddata.py        # Processes all range forecasted streamflow data
│       ├── plots/          # Vizualization functionalities
│       ├── FIMsubset/      # Subsetting functionalities for FIM
│       │   ├── xycoord.py  # Subset using Lat, Lon
│       │   └── shpsubset.py # Subset using boundary
│       ├── statistics/     # Statistical analysis
│       │   └── calculatestatistics.py  # Statistical analysis between NWM and USGS gauge data
│       ├── datadownload.py # Includes HUC8 data retrival and folder management module
│       ├── runFIM.py       # OWPHAND model execution
│       ├── vizualization.py # Interactive visualization of user-defined inundation files (in Jupyter Notebook)
└── tests/                  # Includes test cases for different functionality

```

**The structure of the framework consisting its applications and connection between different functionalities.** The right figure, **b)**, is the directory structure used in this package (for e.g. after using this code by following [docs/code\_usage.ipynb](https://github.com/sdmlua/FIMserv/blob/main/docs/code_usage.ipynb)) to download and process one or multiple hucs.

[![Flowchart](https://github.com/sdmlua/FIMserv/raw/main/images/flowchart.jpg)](https://github.com/sdmlua/FIMserv/blob/main/images/flowchart.jpg)

_Fig. (a)A complete workflow demonstrating the framework architecture, and (b) directory structure as it appears on the user's system after using the FIMserv for FIM generation._

### **Tool Usage**

* * *

Although not mandatory,
**we strongly recommend users create a virtual environment and install this package on that virtual environment to avoid the conflict between system dependencies and package dependencies.**

**‼️ If your system doesnot have git, install it first. Download link of git for windows or MacOS: [https://git-scm.com/downloads](https://git-scm.com/downloads)**

**For conda users**

```
#creating a virtual environment using conda
conda create --name fimserve python==3.10

#Activate environment
conda activate fimserve
```

**If you don't have conda**

```
#create a virtual env using 'venv'
python -m venv fimserve python==3.10

#activate environment
#For MAC Users
source fimserve/bin/activate

#For WINDOW Users
fimserve\Scripts\activate
```

**Once Virtual env is ready, install or add fimserve into your workflows**

```
#Using pip
pip install uv
uv pip install fimserve
'OR'
pip install fimserve

#OR add using poetry to your framework development for quick FIM generation
poetry add fimserve
```

**FIM generation only in 3 steps using fimserve framework**

This framework have multiple other funtionalities, but the most important is to generate the FIM. The following step is the standard way to generate FIM using OWP Operation FIM framework with FIMserv. This is just a quick 3 steps for one huc and one event, user can use this framework as many case and event as per thier requirement. The google colab version of **FIMin3Steps is here**\- [![Google Colab](https://camo.githubusercontent.com/96889048f8a9014fdeba2a891f97150c6aac6e723f5190236b10215a97ed41f3/68747470733a2f2f636f6c61622e72657365617263682e676f6f676c652e636f6d2f6173736574732f636f6c61622d62616467652e737667)](https://colab.research.google.com/drive/1LLagzuLKTDu3WzwjqRoIgnn2iiAveU2f?usp=sharing)

```
#Import framework once it is installed in your workflows
import fimserve as fm

# Initialize necessary variables
huc = "03020202"        #HUC8 ID
start_date = "2016-10-08"   #Start date of the streamflow data
end_date = "2016-10-10"     #End date of the streamflow data

value_time = ["2016-10-09 03:00:00"]   #Time of the streamflow data user want to generate FIM within start_date and end_date
```

**Step 1. Download HUC8 data**

OWP HAND FIM model runs at HUC-8 watershed scale. User need to identify the HUC8 ID for their specific region of interest. In this example we are using the Neuse River Flooding in North Carolina from Hurricane Mathhew,2016. The HUC8 id is 03020202. The locations and informations about the HUC8 IDs are available here in: **[ArcGIS Instant App](https://ualabama.maps.arcgis.com/apps/instant/basic/index.html?appid=88789b151b50430d8e840d573225b36b)**.

```
fm.DownloadHUC8(huc)    #Download the HUC8 data
```

**Step 2. Get the NWM Streamflow data**

Users can retrieve NWM forecasted and retrospective data for a specified date range (start date to end date). Additionally, they can store streamflow data for a specific date, as defined by value\_times, during the initialization process to generate FIM.

```
fm.getNWMretrospectivedata(start_date, end_date, huc, value_time)
```

**Step 3. Generate the Flood Inundation Mapping**

This functionality automatically uses the recently downloaded and stored streamflow to generate FIM. This automation is based on the HUCID.

```
fm.runOWPHANDFIM(huc)       #Run the OWP-HAND FIM with the NWM retrospective streamflow data
```

Then there are a lot of different modules/funtionalities related to Syntetic Rating Curve (SRCs) analysis, NWM and USGS streamflow Evaluation, Subsetting of FIM, Domain filtering etc. For reference to run, [Here (docs/code\_usage.ipynb)](https://github.com/sdmlua/FIMserv/blob/main/docs/code_usage.ipynb) is the sample usage of this FIMserv tool and which covers all modules in detailed and to generate FIM only, follow this shorter, FIM in 3 steps version [Here (docs/FIMin3steps.ipynb)](https://github.com/sdmlua/FIMserv/blob/main/docs/FIMin3steps.ipynb).

Use Google Colab. Here is **Detailed code Usage of FIMserv in Google Colab**: [![Google Colab](https://camo.githubusercontent.com/96889048f8a9014fdeba2a891f97150c6aac6e723f5190236b10215a97ed41f3/68747470733a2f2f636f6c61622e72657365617263682e676f6f676c652e636f6d2f6173736574732f636f6c61622d62616467652e737667)](https://colab.research.google.com/drive/1mAjgkkCvR3Tcbdz48SwlkHmEo1GZvsh7?usp=sharing)

**Different HUC8 IDs, USGS gauge stations and flowline information that might be required to further understand/running this framework can be found in this [ArcGIS Instant App](https://ualabama.maps.arcgis.com/apps/instant/basic/index.html?appid=88789b151b50430d8e840d573225b36b).**

### **Citing This Tool**

Anupal Baruah, Supath Dhital, Sagy Cohen, et al. **FIMserv v.1.0: A Tool for Streamlining Flood Inundation Mapping (FIM) Using the United States Operational Hydrological Forecasting Framework**. _Environmental Modelling & Software_, **Volume 192**, 2025, 106581. [https://doi.org/10.1016/j.envsoft.2025.106581](https://doi.org/10.1016/j.envsoft.2025.106581)

### **Acknowledgements**

* * *

|  |  |
| --- | --- |
| [![alt text](https://camo.githubusercontent.com/f1425ea9a6a4492162f5ff3a63a5d0827fc95442381ae96e095095c7afd57152/68747470733a2f2f6369726f682e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032322f30382f4349524f484c6f676f5f323030783230302e706e67)](https://camo.githubusercontent.com/f1425ea9a6a4492162f5ff3a63a5d0827fc95442381ae96e095095c7afd57152/68747470733a2f2f6369726f682e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032322f30382f4349524f484c6f676f5f323030783230302e706e67) | Funding for this project was provided by the National Oceanic & Atmospheric Administration (NOAA), awarded to the Cooperative Institute for Research to Operations in Hydrology (CIROH) through the NOAA Cooperative Agreement with The University of Alabama (NA22NWS4320003). |
|  | We would like to acknowledge the TEEHR script developed by RTI International ( [https://github.com/RTIInternational/teehr](https://github.com/RTIInternational/teehr)). We use this script to get NWM discharge quickly. |

### **For More Information**

* * *

#### **Contact**

[Dr. Sagy Cohen](https://geography.ua.edu/people/sagy-cohen/)
( [sagy.cohen@ua.edu](https://github.com/sdmlua/FIMserv/blob/main/mailto:sagy.cohen@ua.edu)),
Dr Anupal Baruah,( [abaruah@ua.edu](https://github.com/sdmlua/FIMserv/blob/main/mailto:abaruah@ua.edu)), Supath Dhital ( [sdhital@crimson.ua.edu](https://github.com/sdmlua/FIMserv/blob/main/mailto:sdhital@crimson.ua.edu))