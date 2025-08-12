# FIM Evaluation Framework

[Skip to main content](https://docs.ciroh.org/docs/products/community-fim/fimeval/#__docusaurus_skipToContent_fallback)

> **NOTE**
>
>  Below content is rendered from [https://github.com/sdmlua/fimpef/blob/main/README.md](https://github.com/sdmlua/fimpef/blob/main/README.md).

## Flood Inundation Mapping Predictions Evaluation Framework (FIMeval)

* * *

[![Version](https://camo.githubusercontent.com/fd548941d0e6fc60ef94d90961b7ab3226c4cc417f86352983c6f88fd2dd1386/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f762f72656c656173652f73646d6c75612f66696d6576616c)](https://github.com/sdmlua/fimeval/releases)[![Issues](https://camo.githubusercontent.com/78e06e2e4da2ed256fae169b620d15eebe4812b910755f48f3b9d0feb8d9897b/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6973737565732f73646d6c75612f66696d6576616c)](https://github.com/sdmlua/fimeval/issues)[![License: GPL v3](https://camo.githubusercontent.com/8a398fc9fbf479a323d2d91b9fcb6fb9c6b4d08e96dbb544488ccbed312115fc/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f4c6963656e73652d47504c76332d626c75652e737667)](https://opensource.org/licenses/GPL-3.0)[![PyPI version](https://camo.githubusercontent.com/a38932411d3c588776c3685b1f3dbbbddd6121534ea298e8528f3ec400308b10/68747470733a2f2f62616467652e667572792e696f2f70792f66696d6576616c2e7376673f69636f6e3d7369253341707974686f6e)](https://badge.fury.io/py/fimeval)[![PyPI Downloads](https://camo.githubusercontent.com/475d8ab2e84af2d7000ba608972d473683c68f1988e68bd44ae667a4debe4bc0/68747470733a2f2f7374617469632e706570792e746563682f62616467652f66696d6576616c)](https://pepy.tech/projects/fimeval)

|  |  |
| --- | --- |
| [![SDML Logo](https://camo.githubusercontent.com/3144a76016c24b3f32281f151c46857601e5662e7e593013f3cb8024ff33af46/68747470733a2f2f73646d6c2e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032332f30312f53444d4c5f6c6f676f5f53715f677265792e706e67)](https://sdml.ua.edu/) | This repository provides a user-friendly Python package and source code for the automatic evaluation of flood inundation maps. It is developed under Surface Dynamics Modeling Lab (SDML), Department of Geography and the Environment at The University of Alabama, United States. |

### **Background**

* * *

The accuracy of the flood inundation mapping (FIM) is critical for model development and disaster preparedness. The evaluation of flood maps from different sources using geospatial platforms can be tedious and requires repeated processing and analysis for each map. These preprocessing steps include extracting the correct flood extent, assigning the same projection system to all the maps, categorizing the maps as binary flood maps, removal of permanent water bodies, etc. This manual data processing is cumbersome and prone to human error.

To address these issues, we developed Flood Inundation Mapping Prediction Evaluation Framework (FIMeval), a Python-based FIM evaluation framework capable of automatically evaluating flood maps from different sources. FIMeval takes the advantage of comparing multiple target datasets with large benchmark datasets. It includes an option to incorporate permanent waterbodies as non-flood pixels with a user input file or pre-set dataset. In addition to traditional evaluation metrics, it can also compare the number of buildings inundated using a user input file or a pre-set dataset.

### **Repository structure**

* * *

The architecture of the `fimeval` integrates different modules to which helps the automation of flood evaluation. All those modules codes are in source ( `src` ) folder.

```
fimeval/
├── docs/                       # Documentation (contains 'FIMserv' Tool usage sample codes)
│   └── sampledata/              # Contains the sample data to demonstrate how this frameworks works
│   └── fimeval_usage.ipynb            #Sample code usage of the Evaluation framework
├── Images/                       # have sample images for documentation
├── src/
│   └── fimeval/
│       ├──BuildingFootprint/ # Contains the evaluation of model predicted FIM with microsoft building footprint
│       │   └── evaluationwithBF.py
│       └── ContingencyMap/      # Contains all the metrics calculation and contingency map generation
│       │   ├── evaluationFIM.py # main evaluation moodule
│       │   └── methods.py  # Contains 3 different methods of evaluation
│       │   └── metrics.py  # metrics calculation module
│       │   └── plotevaluationmetrics.py  # use to vizualize the different performance metrics
│       │   └── printcontingency.py  # prints the contingency map to quickly generate the Map layout
│       │   └── PWBs3.py  # module which helps to get permanent water bodies from s3 bucket
│       └── utilis.py   #Includes the resampling and reprojection of FIMs
└── tests/                  # Includes test cases for different functionality
```

The graphical representation of fimeval pipeline can be summarized as follows in **`Figure 1`**. Here, it will show all the steps incorporated within the `fimeval` during packaging and all functionality are interconnected to each other, resulting the automation of the framework.

[![image](https://github.com/sdmlua/fimpef/raw/main/Images/flowchart.jpg)](https://github.com/sdmlua/fimpef/blob/main/Images/flowchart.jpg)

Figure 1: Flowchart showing the entire framework pipeline.

### **Framework Installation and Usage**

* * *

This framework is published as a python package in PyPI ( [https://pypi.org/project/fimeval/).For](https://pypi.org/project/fimeval/).For) directly using the package, the user can install this package using python package installer 'pip' and can import on their workflows:

```
#Install to use this framework
pip install fimeval

#Use this framework in your workflows using poetry
poetry add fimeval
```

Import the package to the jupyter notebook or any python IDE.

```
#Import the package
import fimeval as fp
```

**Note: The framework usage provided in detailed in [Here (docs/fimeval\_usage.ipynb)](https://github.com/sdmlua/fimpef/blob/main/docs/fimeval_usage.ipynb)**. It has detail documentation from installation, setup, running- until results.

#### **Main Directory Structure**

The main directory contains the primary folder for storing the case studies. If there is one case study, user can directly pass the case study folder as the main directory. Each case study folder must include a Benchmark FIM (B-FIM) with a 'benchmark' word assigned within the B-FIM file and different Model Predicted FIM (M-FIM)
in tif format.
For mutilple case studies,the main directory could be structure in such a way that contain the seperate folders for individual case studies.For example, if a user has two case studies they should create two seperate folders as shown in the Figure below.

[![image](https://github.com/sdmlua/fimpef/raw/main/Images/directorystructure.png)](https://github.com/sdmlua/fimpef/blob/main/Images/directorystructure.png)

Figure 2: Main directory structure for one and multiple case study.

This directory can be defined as follows while running framework.

```
main_dir = Path('./path/to/main/dir')
```

#### **Permanent Water Bodies (PWB)**

This framework uses PWB to first to delineate the PWB in the FIM and assign into different class so that the evaluation will be more fair. For the Contiguous United States (CONUS), the PWB is already integrated within the framework however, if user have more accurate PWB or using fimeval for outside US they can initialize and use PWB within fimeval framework. Currently it is using PWB publicly hosted by ESRI: [https://hub.arcgis.com/datasets/esri::usa-detailed-water-bodies/about](https://hub.arcgis.com/datasets/esri::usa-detailed-water-bodies/about)

If user have more precise PWB, they can input their own PWB boundary as .shp and .gpkg format and need to assign the shapefile of the PWB and define directory as,

```
PWD_dir = Path('./path/to/PWB/vector/file')
```

#### **Methods for Extracting Flood Extents**

1. **`smallest_extent`**


The framework will first check all the raster extents (benchmark and FIMs). It will then determine the smallest among all the rasters. A shape file will then be created to mask all the rasters.

2. **`convex_hull`**


Another provision of determining flood extent is the generation of the minimum bounding polygon along the valid shapes. The framework will select the smallest raster extent followed by the generation of the valid vector shapes from the raster. It will then generate the convex hull (minimum bounding polygon along the valid shapes).

3. **`AOI`**


User can give input an already pre-defined flood extent vector file. This method will only be valid if user is working with their own evaluation boundary,


Depending upon user preference, they need to pass those method name as a argument while running the evaluation.

The FIM evaluation extent for `smallest_extent` and `convex_hull` can be seen in below **Figure 3** which is GIS layout version of an contengency map output of `EvaluateFIM` module defined in Table 1.

[![image](https://github.com/sdmlua/fimpef/raw/main/Images/methodslayout.jpg)](https://github.com/sdmlua/fimpef/blob/main/Images/methodslayout.jpg)

Figure 3: Layout showing the difference between smallest extent and convex hull FIM extent and evaluation result.

Methods can be defined as follows.

```
method_name = "smallest_extent"
```

For the method 'AOI', user also need to pass the shapefile of the AOI along with method name as AOI.

```
#For AOI based FIM evaluation
method_name = "AOI"
AOI  = Path('./path/to/AOI/vectorfile')
```

#### **Executing the Evaluation framework**

The complete description of different modules, what they are meant for, arguments taken to run that module and what will be the end results from each is described in below **Table 1**. If user import `fimeval` framework as `fp` into workflows, they can call each module mentioned in **Table 1** as `fp.Module_Name(args)`. Here arguments in italic represents the optional field, depending upon the user requirement.

Table 1: Modules in `fimeval` are in order of execution.

| Module Name | Objective | Arguments | Outputs |
| --- | --- | --- | --- |
| `EvaluateFIM` | It runs all the evaluation of FIM between B-FIM and M-FIMs. | `main_dir`: Main directory containing the case study folders, <br>`method_name`: How users wants to evaluate their FIM, <br>`outpur_dir`: Output directory where all the results and the intermidiate files will be saved for further calculation, <br>_`PWB_dir`_: The permanenet water bodies vectory file directory if user wants to user their own boundary, <br>_`target_crs`_: this fimeval framework needs the floodmaps to be in projected CRS so define the projected CRS in epsg code format, <br>_`target_resolution`_: sometime if the benchmark is very high resolution than candidate FIMs, it needs heavy computational time, so user can define the resolution if there FIMs are in different spatial resolution, else it will use the coarser resolution among all FIMS within that case. | The outputs includes generated files in TIFF, SHP, CSV, and PNG formats, all stored within the output folder. Users can visualize the TIFF files using any geospatial platform. The TIFF files consist of the binary Benchmark-FIM (Benchmark.tif), Model-FIM (Candidate.tif), and Agreement-FIM (Contingency.tif). The shp files contain the boundary of the generated flood extent. |
| `PlotContingencyMap` | For better understanding, It will print the agreement maps derived in first step. | `main_dir`, `method_name`, `output_dir` : Based on the those arguments, once all the evaluation is done, it will dynamically get the corresponding contingency raster for printing. | This prints the contingency map showing different class of evaluation (TP, FP, no data, PWB etc). The outputs look like- Figure 4 first row. |
| `PlotEvaluationMetrics` | For quick understanding of the evaluation metrics, to plot bar of evaluation scores. | `main_dir`, `method_name`, `output_dir` : Based on the those arguments, once all the evaluation is done, it will dynamically get the corresponding file for printing based on all those info. | This prints the bar plots which includes different performance metrics calculated by EvaluateFIM module. The outputs look like- Figure 4 second row. |
| `EvaluationWithBuildingFootprint` | For Building Footprint Analysis, user can specify shapefile of building footprints as .shp or .gpkg format. By default it consider global Microsoft building footprint dataset. Those data are hosted in Google Earth Engine (GEE) so, It pops up to authenticate the GEE account, please allow it and it will download the data based on evaluation boundary and evaluation is done. | `main_dir`, `method_name`, `output_dir`: Those arguments are as it is, same as all other modules. <br>_`building_footprint`_: If user wants to use their own building footprint file then pass the directory here, _`country`_: It is the 3 letter based country ISO code (eg. 'USA', NEP' etc), for the building data automation using GEE based on the evaluation extent, _`shapefile_dir`_: this is the directory of user defined AOI if user is working with their own boundary and automatic Building footprint download and evaluation. | It will calculate the different metrics (e.g. TP, FP, CSI, F1, Accuracy etc) based on hit and miss of building on different M-FIM and B-FIM. Those all metrics will be saved as CSV format in `output_dir` and finally using that info it prints the counts of building foorpint in each FIMs as well as scenario on the evaluation end via bar plot. |

[![](https://github.com/sdmlua/fimpef/raw/main/Images/methodsresults_combined.jpg)](https://github.com/sdmlua/fimpef/blob/main/Images/methodsresults_combined.jpg)

Figure 4: Combined raw output from framework for different two method. First row (subplot a and b) and second row (subplot c and d) is contingency maps and evaluation metrics of FIM derived using `PrintContingencyMaP` and `PlotEvaluationMetrics` module. Third row (subplot e and f) is the output after processing and calculating of evaluation with BF by unsing `EvaluateWithBuildingFoorprint` module.

## 🔧 Installation Instructions

### 1\. ✅ Prerequisites

Before installing `fimeval`, ensure the following software are installed:

- **Python**: Version 3.10 or higher
- **Anaconda**: For managing environments and dependencies
- **GIS Software**: For Visulalisation

  - [ArcGIS](https://www.esri.com/en-us/arcgis/products/index) or [QGIS](https://qgis.org/en/site/)
- **Optional**:

  - [Google Earth Engine](https://earthengine.google.com/) account
  - Java Runtime Environment (for using GEE API)

* * *

### 2\. Install Anaconda

If Anaconda is not installed, download and install it from the [official website](https://www.anaconda.com/products/distribution).

* * *

### 3\. 🌐 Set Up Virtual Environment

#### 💻 For Mac Users

Open **Terminal** and run:

```
# Create a new environment named 'fimeval'
conda create --name fimeval python=3.10

# Activate the environment
conda activate fimeval

# Install Jupyter Notebook
pip install notebook

# Install fimeval package
pip install fimeval

```

### ☁️ Google Colab Version

To use fimeval in Google Colab, follow the steps below:

## Upload Files

Upload all necessary input files (e.g., raster, shapefiles, model outputs) to your Google Drive.

## Open Google Colab

Go to Google Colab and sign in with a valid Google account.

## Mount Google Drive

In a new Colab notebook, mount the Google Drive

```
pip install fimeval
```

### **Acknowledgements**

|  |  |
| --- | --- |
| [![alt text](https://camo.githubusercontent.com/f1425ea9a6a4492162f5ff3a63a5d0827fc95442381ae96e095095c7afd57152/68747470733a2f2f6369726f682e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032322f30382f4349524f484c6f676f5f323030783230302e706e67)](https://camo.githubusercontent.com/f1425ea9a6a4492162f5ff3a63a5d0827fc95442381ae96e095095c7afd57152/68747470733a2f2f6369726f682e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032322f30382f4349524f484c6f676f5f323030783230302e706e67) | Funding for this project was provided by the National Oceanic & Atmospheric Administration (NOAA), awarded to the Cooperative Institute for Research to Operations in Hydrology (CIROH) through the NOAA Cooperative Agreement with The University of Alabama. |

### **For More Information**

Contact [Sagy Cohen](https://geography.ua.edu/people/sagy-cohen/)
( [sagy.cohen@ua.edu](https://github.com/sdmlua/fimpef/blob/main/mailto:sagy.cohen@ua.edu))
Dipsikha Devi, ( [ddevi@ua.edu](https://github.com/sdmlua/fimpef/blob/main/mailto:ddevi@ua.edu))
Supath Dhital, ( [sdhital@crimson.ua.edu](https://github.com/sdmlua/fimpef/blob/main/mailto:sdhital@crimson.ua.edu))