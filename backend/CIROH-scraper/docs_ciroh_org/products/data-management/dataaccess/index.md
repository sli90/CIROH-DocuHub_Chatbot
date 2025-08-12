# Data Access

[Skip to main content](https://docs.ciroh.org/docs/products/data-management/dataaccess/#__docusaurus_skipToContent_fallback)

On this page

Within the CIROH projects, we encounter a wide range of data resources and data access inquiries. One of the most frequently asked questions is, "How can I obtain access to xyz-resource?". To help with answering that question, we have documented some of the most common data access methods and resources here, with links to additional sites to dive deeper.

## Input and Output Data of the National Water Model [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#input-and-output-data-of-the-national-water-model "Direct link to Input and Output Data of the National Water Model")

Here, you will find resources that grant access to the input data used and the output data produced by the operational national water model.

### Official NOMADS Resource [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#official-nomads-resource "Direct link to Official NOMADS Resource")

The official NWM meteorological inputs and hydrology and routing outputs are accessible through both HTTP and FTP. These resources are provided by the National Center for Environmental Prediction (NCEP) at the following locations:

- NOMADS - NOAA Operational Model Archive and Distribution System
  - [HTTP](https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm)
  - [FTP](ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/nwm)

As of October 24, 2023, these resources include the following directories:

```codeBlockLines_e6Vv
para_post-processed/    22-Sep-2023 20:37    -
post-processed/         02-Nov-2020 14:31    -
prod/                   24-Oct-2023 00:18    -
v3.0/                   24-Oct-2023 00:18    -

```

The `para_post-processed` directory lacks specific documentation, although the "para" designation suggests it is a "parallel" execution, indicating a candidate production run under testing for operational use. In the post-processed dataset, you will find the following subdirectories:

- [NOMADS post-processed](https://nomads.ncep.noaa.gov/pub/data/nccf/com/nwm/post-processed/)
  - RFC: Outputs filtered down to RFC locations.
  - WMS: Contains re-indexed/reformatted outputs in per-forecast netCDFs suitable for rapid querying and responsive for graph visualizations on the water.noaa.gov/map site.
  - IMAGES: .png-formatted renderings of NWM output for various domains and variables.
  - logs: Logs. :)

### NODD - NOAA Open Data Dissemination Program [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#nodd---noaa-open-data-dissemination-program "Direct link to NODD - NOAA Open Data Dissemination Program")

"The NOAA Open Data Dissemination (NODD) Program provides public access to NOAA's open data on commercial cloud platforms through public-private partnerships. These partnerships remove obstacles to public use of NOAA data, help avoid costs and risks associated with federal data access services, and leverage operational public-private partnerships with the cloud computing and information services industries."
(For more information, visit [NODD](https://www.noaa.gov/information-technology/open-data-dissemination))

The NODD datasets made available through several public cloud vendors are an incredible resource for accessing NWM data for research and evaluative purposes. The NWS NODD datasets are listed on [this page](https://www.noaa.gov/nodd/datasets) and include the following:

#### AWS [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#aws "Direct link to AWS")

AWS hosts two repositories as part of their sustainability data initiative.

The first repository contains the operational data (now hosts 4 week rolling collection of all output; it used to only be short range and the registry entry retains the description only for the short\_range data [here](https://registry.opendata.aws/noaa-nwm-pds/); alternatively, the same resource is described under the sustainability initiative page [here](https://aws.amazon.com/marketplace/pp/prodview-73iwu7dcfuge2).)

- The catalog of AWS-hosted operational NWM data can be browsed [here](https://noaa-nwm-pds.s3.amazonaws.com/index.html).

The second (and more useful) AWS repository contains several versions of the retrospective dataset each described on the main page under the open data registry [here](https://registry.opendata.aws/nwm-archive/).
(The same information is also on the AWS sustainability initiative webpage [here](https://aws.amazon.com/marketplace/pp/prodview-g6lcchc7brshwa) )

The different catalogs of those \[currently\] five versions of that resource are linked below:

- Two versions of NWM v2.1 retrospective
  - netCDF, [here](https://noaa-nwm-retrospective-2-1-pds.s3.amazonaws.com/index.html)
  - zarr, [here](https://noaa-nwm-retrospective-2-1-zarr-pds.s3.amazonaws.com/index.html)
- Two versions of NWM v2.0 retrospective
  - netCDF, [here](https://noaa-nwm-retro-v2-0-pds.s3.amazonaws.com/index.html)
  - zarr, [here](https://noaa-nwm-retro-v2-zarr-pds.s3.amazonaws.com/index.html)
- NWM v1.2 retrospective data
  - netCDF, [here](https://nwm-archive.s3.amazonaws.com/index.html)

The AWS retrospective resource is the primary publicly available source for the version 1.0 of the "AORC" Analysis of Record for Calibration dataset, which is a 40-year best-available estimate of most common meteorological parameters required for hydrological modeling. Version 1.1 of the dataset will accompany the release of the NWM model version 3.0 retrospective (or 2.2 version??), hopefully in the next few weeks.

Jupyter notebook instructions for processing NWM Zarr and NetCDF output formats [here](https://github.com/CIROH-UA/data_access_example/)

An example of pulling data from the channel output zarr 2.1 archive and writing the results to csv follows:

```codeBlockLines_e6Vv
'''
#install these libraries if they aren't already installed
!pip install zarr
!pip install xarray
!pip install s3fs
!pip install numpy
'''
# Import needed libraries

import xarray as xr
import numpy as np
import s3fs
from datetime import datetime, timedelta

# open the zarr store
url = "s3://noaa-nwm-retrospective-2-1-zarr-pds/chrtout.zarr"
fs = s3fs.S3FileSystem(anon=True)
store = xr.open_zarr(s3fs.S3Map(url, s3=fs))

# Function to get the time series for a specified reach id and and time range
# then write it out to a csv file.
def GetAndWriteTimeSeriesAtReach(reach_id, start_time_index, end_time_index):
    flows = streamflow_array.where(feature_id_array==reach_id, drop=True)
    df_flows = flows[start_time_index:end_time_index].to_dataframe()
    df_flows.to_csv(f'flows_{reach_id}.csv')

# get an xarray array of the various values
time_array = store['time']
feature_id_array = store['feature_id']
streamflow_array = store['streamflow']

# Define the feature IDs to check for
feature_ids = [5781221, 5781223, 5781703]

# Specify the start and end times of interest
start_time = datetime(2015, 5, 23, 0, 0, 0)
end_time = datetime(2015, 6, 24, 0, 0, 0)

# Get the indices for the needed dates
zero_start_time = start_date = datetime(1979, 2, 1, 0, 0, 0)
start_time_index = int((start_time - zero_start_time).total_seconds() / 3600)
end_time_index = int((end_time - zero_start_time).total_seconds() / 3600)

for reach_id in feature_ids:
    GetAndWriteTimeSeriesAtReach(reach_id, start_time_index, end_time_index)

'''
Simple Script for Retrieving Retrospective NWM Data from AWS Store
Dan Ames, 11/17/2023
dan.ames@byu.edu
'''

```

#### Google – Operational NWM Data [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#google--operational-nwm-data "Direct link to Google – Operational NWM Data")

Google hosts the most complete operational data archive of inputs and outputs from the National Water Model, with nearly every file since August 2018. The Google open data registry provides additional explanations [here](https://console.cloud.google.com/marketplace/product/noaa-public/national-water-model?project=explore-ai-387703).

- Operational data can be browsed [here](https://console.cloud.google.com/storage/browser/national-water-model).
- Google also hosts a copy of the NWM v1.2 retrospective [here](https://console.cloud.google.com/storage/browser/national-water-model-reanalysis).

Coming soon: Big Query

Efforts are underway to make some of the datasets from the NWM operational and retrospective simulations available on BigQuery for ultra-high-bandwidth access. Stay tuned...

#### Azure/Planetary Computer [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#azureplanetary-computer "Direct link to Azure/Planetary Computer")

Microsoft hosts the NWM input and output datasets in Azure Blob Storage, associated with the Microsoft Planetary Computer.
[Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/dataset/storage/noaa-nwm)
Tom Augspurger of Microsoft has a series of notebooks providing examples of how to use this data from his workshop at the first CIROH developers conference.
[Tom Augspurger's Notebooks](https://github.com/TomAugspurger/noaa-nwm)

### CIROH Resources [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#ciroh-resources "Direct link to CIROH Resources")

More detailed information and example usage will be available soon.

- Kerchunk Retro (points to AWS 2.1 NetCDF Retro)
  - [Kerchunk Retro](https://ciroh-nwm-zarr-retrospective-data-copy.s3.amazonaws.com/index.html) \- Forcing complete; model output 2011-2020
- Kerchunk Operational (points to Google assets – a simple text change can point to AWS short range, if desired)
  - [Kerchunk Operational](https://ciroh-nwm-zarr-copy.s3.amazonaws.com/index.html)

### Other resources [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#other-resources "Direct link to Other resources")

#### ESRI Living Atlas [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#esri-living-atlas "Direct link to ESRI Living Atlas")

ESRI Living Atlas provides a map-enabled version of the NWM output, which can be accessed [here](https://www.esri.com/arcgis-blog/products/analytics/analytics/esri-visualizes-noaas-national-water-model/).

#### Description of WRF-Hydro code: [​](https://docs.ciroh.org/docs/products/data-management/dataaccess/\#description-of-wrf-hydro-code "Direct link to Description of WRF-Hydro code:")

A detailed description of various aspects of the WRF-Hydro code, which produces the current NWM, can be found [here](https://ral.ucar.edu/sites/default/files/public/projects/wrf_hydro/technical-description-user-guide/wrf-hydro-v5.1.1-technical-description.pdf).

* * *

[**📄️nwmurl** \\
nwmurl is a Python library developed by CIROH 2023. It provides utility functions specifically designed to subset and generate National Water Model (NWM) data URLs. This library simplifies the process of accessing NWM data for various purposes such as analysis, modeling, and visualization.](https://docs.ciroh.org/docs/products/data-management/dataaccess/NWMURL%20Library)

- [Input and Output Data of the National Water Model](https://docs.ciroh.org/docs/products/data-management/dataaccess/#input-and-output-data-of-the-national-water-model)
  - [Official NOMADS Resource](https://docs.ciroh.org/docs/products/data-management/dataaccess/#official-nomads-resource)
  - [NODD - NOAA Open Data Dissemination Program](https://docs.ciroh.org/docs/products/data-management/dataaccess/#nodd---noaa-open-data-dissemination-program)
  - [CIROH Resources](https://docs.ciroh.org/docs/products/data-management/dataaccess/#ciroh-resources)
  - [Other resources](https://docs.ciroh.org/docs/products/data-management/dataaccess/#other-resources)