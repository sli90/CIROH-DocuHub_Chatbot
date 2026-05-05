## Content of this resource:
- **readme.md**: This file explains the content of this HydroShare resource.
- **retrieve-nwm-v3-retrospective-streamflow-data.ipynb**: Code to retrieve the NWM streamflow data from retrospective simulations for the stream reach of interest.
- **flow-duration-analysis.ipynb**: Code to access, compute, and analyze the flow statistics, including flow duration and peak flow statistics. These statistics could be used as inputs to the following Jupyter Notebook to create corresponding flood maps using the Flood Inundation Mapping (FIM) approach.  
- **create-inundation-maps-using-FIM-xarray.ipynb**: Code to create the flood inundation map based on the FIM method for a given discharge and reach ID.
- **rem_zeroed_masked_0.tif**: A GeoTIFF containing Height Above Nearest Drainage values.
- **gw_catchments_reaches_filtered_addedAttributes_crosswalked_0.gpkg**: Vector data and attributes for river reaches.
- **demDerived_reaches_split_filtered_addedAttributes_crosswalked_0.gpkg**: DEM-derived reach geometries that will be used for visualization.
- **hydroTable_0.csv**: A comma-separated file containing pre-computed stage-discharge values for every reach in the demDerived dataset.
- **nwm_utils**: This folder contains supplementary code.
- **27041CV000A.pdf**: FEMA Flood Insurance Study report for Douglas County, Minnesota.
- **27041C_20091118.zip**: FEMA flood maps for Spruce Creek basin.
- **27153CV000A.pdf**: FEMA Flood Insurance Study report for Todd County, Minnesota..
- **27153C_20110204.zip**: FEMA flood maps for Long River Prairie basin.
- **Figure**: This folder contains an image of the case study location as well as images comparing flood inundation maps generated based on the FIM approach against FEMA.
- **Video**: This folder contains videos showing how to access StreamStats data.
- **StreamStats_Report**: This folder contains catchment and flow statistics reports (in both PDF and CSV formats) obtained from the USGS StreamStats web application for both gaged and ungaged basins. 
- **fema-map-styles**: Style that has been used for the visualization of FEMA maps in QGIS. To load the style in QGIS, right-click on the layer and select Properties. Then, go to the Symbology tab, click on the Style button, and choose Load Style from File. Navigate to this QML file and open it.


## Case Study: Long Prairie Watershed, Minnesota

Our case study focuses on two basins within the Spruce Creek-Long Prairie River (HUC10/0701010802) watershed, which is part of the larger Long Prairie (HUC8/07010108) watershed. This region predominantly covers Douglas County and Todd County in Minnesota. The Long Prairie River flows east to west, confluencing with Spruce Creek, which drains from north to south into the Long Prairie River. The river continues westward until it reaches the USGS stream gage (05245100) located on the Long Prairie River near Long Prairie City, where it intersects with US Highway 71. From there, it flows northward, ultimately draining into the Crow Wing River. In Figure (a) below, the light-shaded green polygon represents the watershed boundary of the Spruce Creek-Long Prairie River watershed, and the white points indicate the locations of USGS stream gages. 

The selected two subcatchments are highlighted in Figure (b). These subcatchments were chosen to show how the developed codes can be used to obtain National Water Model streamflow data and create flood maps for both an ungaged basin (Spruce Creek, Figure c) and a gaged basin (part of the Long Prairie River, Figure d). 

<div style="display: flex; flex-direction: row; justify-content: center; align-items: center;">
    <img src="https://www.hydroshare.org/resource/3200bab682ec4c3287147cbe40e768ee/data/contents/Figure/domain-study.png" width="1000" height="500" style="margin-right: 20px;">
</div>

### The gaged basin

The selected basin of the Long Prairie River contains several sub-basins, among which we chose a sub-basin with the associated feature_id 4966267 as defined in the National Water Model (NWM) input data. This feature_id corresponds to the `COMID` of the NHDPlus (National Hydrography Dataset). This sub-basin is the most upstream within the selected basin and is closest to the USGS gage is located, making it ideal for our study. Please note that our code accepts the USGS gage ID as input and finds the corresponding feature_id. By running our code in `retrieve-nwm-v3-retrospective-streamflow-data.ipynb`, this ID will be printed out. 

### The ungaged basin

Same as for the gaged basin, our selected ungaged basin, encompassing Spruce Creek, has several sub-basins. For the purpose of this study, we chose the most downstream segment of this stream with the feature_id 4965159.

## Methodology

We will first use the `retrieve-nwm-v3-retrospective-streamflow-data.ipynb` code to retrieve NWM retrospective streamflow data from 1979-2023 for both gaged and ungaged reaches and then estimate the **maximum peak flow** based on the NWM results. The most recent retrospective simulations are available in the form of Zarr and NetCDF files at <a href="https://noaa-nwm-retrospective-3-0-pds.s3.amazonaws.com/index.html" style="color: blue; background-color: snow;">https://noaa-nwm-retrospective-3-0-pds.s3.amazonaws.com/index.html</a>. We will use `xarray` and `Dask` to work with the Zarr data. 

> The maximum peak flow for the gaged (Long Prairie River) and ungaged (Spruce Creek) basins, are <strong>51.12 cms</strong> and <strong>9.5 cms</strong>, respectively. These are computed in Section 4 of the notebook. Note that the maximum peak flow from the observed dataset is about **92.6 cms**, which corresponds to the year 1972 and is beyond the NWM retrospective period. If we only focus on the period that both observed and the NWM data overlpas, the maximum peak flow from the observed dataset is about <strong>82.13 cms</strong> corresponding to the year 2001, which is more than 1.5 times larger than the maximum peak flow from the NWM data. A comparison of the modeled versus observed data is provided in the last section of this jupyter notebook. 

The last section of the `retrieve-nwm-v3-retrospective-streamflow-data.ipynb` code offers a basic peak flow analysis. However, the `flow-duration-analysis.ipynb` code provides a more comprehensive peak flow frequency analysis. The main focus of this code is to obtain **Flow-Duration Statistics** and **Peak-Flow Statistics** for both gaged and ungaged basins from the [USGS StreamStats application](https://streamstats.usgs.gov/ss/). Note that the USGS StreamStats application provides these information for both gaged and ungaged basins based on a combination of historical data, regional regression equations, and hydrologic models to estimate these characteristics. Additionally, it computes flow duration statistics for the NWM streamflow data for both basins. Below is a short video demonstrating how to generate a report on peak flow and flow duration statistics from StreamStats. You can also find the report files we obtained and made available in this resource within the folder called StreamStats_Report. 

<div style="display: flex; flex-direction: row; justify-content: center; align-items: center;">
    <video width="600" controls>
      <source src="https://www.hydroshare.org/resource/3200bab682ec4c3287147cbe40e768ee/data/contents/Video/StreamStats_LongPrairieRiver_HowTo.mp4" type="video/mp4">
    </video>
</div>

> Section 5 of the <strong>flow-duration-analysis</strong> code plots the different flow duration curves for both basins and estimates the corresponding discharge value for a flow with a 1% probability of being exceeded. There are significant discrepencies between the StreamStats flow duration curves and the computed curves based on the USGS and NWM data. One source of the discrepancies between these lines could be the different approaches used to compute the flow duration curves. Additionally, differences in the data periods may also contribute to these discrepancies.

> For the selected reach of the <span style="color:blue">Long Prairie River</span>, the code reports values of <strong>30.02, 22.63, and 69.7 cms</strong>, corresponding to observed data obtained from the USGS gage, modeled data obtained from the NWM retrospective version 3, and data obtained from the StreamStats report, respectively. For the selected reach of the <span style="color:blue">Spruce Creek</span>, the code reports values of <strong>2.86 and 7.14 cms</strong>, corresponding to modeled data obtained from the NWM retrospective version 3 and data obtained from the StreamStats report, respectively. 

> Section 6 focuses on <strong>Peak-Flow Statistics</strong>, also known as Annual Exceedance Probability (AEP). These statistics are only available for the data obtained from the StreamStats report. Future work can apply the same approach to create AEP for the NWM data. However, in this project, we wanted to understand how these values differ from those derived from the flow duration curves. For the selected reach of the <span style="color:blue">Long Prairie River</span>, the code reports a flow value of <strong>55.8 cms</strong> assoricated with a 1% annual chance of being exceeded. For the selected reach of the <span style="color:blue">Spruce Creek</span>, the code reports values of <strong>19.6 cms</strong> for the same 1% annual chance.  

In addition to the peak flows mentioned above, we also obtained the flow values corresponding to a 100-year recurrance interval from **FEMA** for both basins. For convenience, we have included these data in this HydroShare resource. However, if you want to try obtaining it yourself, follow the steps in the green box below. 

<div style="border:2px solid limegreen; padding: 10px; background-color: honeydew; border-radius: 10px;">
    <p style="font-size:16px; font-family: Arial, sans-serif; color: darkgreen;">
        To access the FEMA Flood Insurance Study Report and National Flood Hazard Layer, follow the steps below:
    </p>
    <ul style="font-size:16px; font-family: Arial, sans-serif; color: darkgreen; list-style-type: decimal; padding-left: 20px;">
        <li>Visit <a href="https://www.fema.gov/flood-maps/products-tools" style="blue: #C70039;"> the FEMA Products and Tools</a>.</li>
        <li>Click on the "View All MSC (Map Service Center) Tools" button, which will take you to another webpage. </li>
        <li>Select the state, county, and community of your interest.</li>
        <li>Expand the "Effective Products" section to see a list of regulatory products authorized by law for making determinations under the NFIP. The Flood Insurance Study (FIS) Reports provide information about 1% annual chance discharge values. The NFHL-Data-County section contains GIS data related to FEMA flood maps. </li>
    </ul>
</div>

> In the Flood Insurance Study (FIS) report of the Todd County, under Section 3.1 (Hydrologic Analysis), Table 1 on page 7 summarizes the discharges. The 1% annual chance flow for Long Prairie River at US Highway 71 is <strong>2860 cfs (81 cms)</strong>. The associated flood map for this discharge can be viewed in the zipped folder containing the National Flood Hazard Layer (NFHL) for the region of interest. Among the different shapefiles within this file, we use `S_Fld_Haz_Ar.shp`, which contains information about the flood hazards within the Flood Risk Project area. For Douglas County, we could not find any discharge values in the FIS report. Section 3.1 of the Douglas County report only provides the regional regression equation, and we did not have enough information to compute Q100 (the 1-percent-annual-chance flow). Similar to Todd County, the shapefile of the FEMA maps for Douglas County can be found in the county's associated folder.

### Summary of Peak Flow Values
All values are in cubic meters per second.

- **Long Prairie River (gaged basin, feature_id: 4966267):**
  - NWM: maximum daily flow: 51.11
  - USGS: maximum daily flow: 82.13
  - NWM: Flow-Duration Statistic (1% probability): 22.63
  - USGS: Flow-Duration Statistic (1% probability): 30.02
  - StreamStats: Flow-Duration Statistics (1% probability): 69.7
  - StreamStats: Peak-Flow Statistics (1% AEP): 55.8
  - FEMA (1% annual chance): 81

- **Spruce Creek (ungaged basin, feature_id: 4965159):**
  - NWM: maximum daily flow: 9.5
  - USGS: maximum daily flow: Not available
  - NWM: Flow-Duration Statistic (1% probability): 2.86
  - USGS: Flow-Duration Statistic (1% probability): Not available
  - StreamStats: Flow-Duration Statistics (1% probability): 7.14
  - StreamStats: Peak-Flow Statistics (1% AEP): 19.6
  - FEMA (1% annual chance): Not available

Next, we will use some of the peak flow discharges from the summary table above as an input for the `create-inundation-maps-using-FIM-xarray.ipynb` code to apply the basic Flood Inundation Mapping (FIM) approach and create the inundation extent for both sub-basins. The FIM process has been developed by the NOAA Office of Water Prediction. For more information, see the [inundation-mapping project](https://github.com/NOAA-OWP/inundation-mapping). There are two approaches to using the data provided by NOAA OWP to compute FIM: basic (simplified) mapping and mosaic mapping. The latter represents the state of practice in this domain; however, for simplicity, this notebook will demonstrate the former. 

> For the <strong>gaged basin (Long Prairie River, feature_id 4966267)</strong>, we used the FEMA 1% annual chance discharge (81 cms) and the maximum daily flow from the NWM results (51.11 cms) to run the `create-inundation-maps-using-FIM-v3-xarray.ipynb` code twice and created flood maps. The main goal of using the FEMA 1% annual chance discharge in addition to the NWM maximum daily flow is to reduce uncertainties associated with potential errors in the simulated NWM discharge by incorporating the FEMA-provided discharge value. For the <strong>ungaged basin (Spruce Creek, feature_id 4965159)</strong>, we used the 1% AEP discharge from StreamStats (19.6 cms) and the maximum daily flow from the NWM results (9.5 cms) to run the flood inundation mapping code. 

The following shows the comparison between the FEMA map, the flood inundation extent created using the FIM approach with a non-NWM dataset, and the flood inundation extent created using the FIM approach with the maximum peak flow from the NWM retrospective data for both basins.

<div style="display: flex; flex-direction: column; justify-content: center; align-items: center;">
    <img src="https://www.hydroshare.org/resource/3200bab682ec4c3287147cbe40e768ee/data/contents/Figure/FEMA_nonNWMFIM_NWMFIM_comparison.png" width="1000" height="500" style="margin-top: 20px;">
</div>

## How to run computational notebooks in this resource:
You can run these notebooks locally or use cloud computing services. To access the CIROH JupyterHub, you have two options. First, you can right-click on any of the Jupyter Notebooks within this resource and choose the `CIROH Production JupyterHub` option. Alternatively, you can open the entire resource by clicking on the `Open with` button located at the top right corner of the landing page. Once you're in the resource, make sure to select the `Medium` server, and then follow the steps provided in the notebook. 

<div style="border:2px solid #0000FF; padding: 10px; background-color: #E0F7FA; border-radius: 10px;">
    <p style="font-size:16px; font-family: Arial, sans-serif; color: #000080;">
        To successfully run the notebooks on CIROH cloud services, please ensure that:
    </p>
    <ul style="font-size:16px; font-family: Arial, sans-serif; color: #000080;">
        <li>✅ You have a HydroShare account to authorize the CIROH platform to access your resource content. If you haven’t already, <a href="https://help.hydroshare.org/introduction-to-hydroshare/getting-started/create-an-account/">create an account on HydroShare</a> and sign in. </li>
        <li>✅ You have already added the CIROH JupyterHub WebApp to your “Open With” list menu. Head to HydroShare and navigate to the "CIROH Production Jupyterhub" resource at this <a href="https://www.hydroshare.org/resource/2dd1ac86e8854d4fb9fe5fbafaec2b98/">URL</a>. This resource is an "app connector" allowing you to add the CIROH production JupyterHub to your list of apps available via your "Open with" menu in HydroShare. Ensure that the square icon labeled "Add Web App to Open with list" in HydroShare is green. If it appears red, a single click will change it to green. </li>
        <li>✅ You have access to the CIROH JupyterHub environments. If not, follow the <a href="https://docs.ciroh.org/docs/services/cloudservices/ciroh%20jupyterhub/#how-to-get-access-to-these-environments">steps</a>. Click on “Open with …” -> CIROH JupyterHub. Once you select this option from the drop-down in HydroShare, a new browser tab will open for the CIROH JupyterHub. The first time you do this, you may need to agree to the Terms of Use and “sign in with HydroShare” to authorize the platform to access your resource content. Use “Medium” and then click the orange “Start” button at the bottom of the page. It will take a few moments for your server to start up.  </li>
    </ul>
</div>












