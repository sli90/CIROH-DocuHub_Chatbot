## Content of this resource:
- **readme.md**: This file explains the content of this HydroShare resource.
- **retrieve-nwm-v3-retrospective-streamflow-data.ipynb**: Code to retrieve the NWM streamflow data from retrospective simulations for the stream reach of interest.
- **create-inundation-maps-using-FIM-xarray.ipynb**: Code to create the flood inundation map based on the FIM method for a given discharge and reach ID.
- **rem_zeroed_masked_0.tif**: A GeoTIFF containing Height Above Nearest Drainage values.
- **gw_catchments_reaches_filtered_addedAttributes_crosswalked_0.gpkg**: Vector data and attributes for river reaches.
- **demDerived_reaches_split_filtered_addedAttributes_crosswalked_0.gpkg**: DEM-derived reach geometries that will be used for visualization.
- **hydroTable_0.csv**: A comma-separated file containing pre-computed stage-discharge values for every reach in the demDerived dataset.
- **nwm_utils**: This folder contains supplementary code.
- **21117CV000B.pdf**: FEMA Flood Insurance Study report for Kenton County, Kentucky.
- **21117C_20150619.zip**: FEMA flood maps.
- **Figure**: This folder contains an image of the case study location as well as images comparing flood inundation maps generated based on the FIM approach against FEMA.


## Case Study: Fowler Creek Watershed, Kentucky

Our case study focuses on the Fowler Creek watershed, part of the Licking River watershed (HUC 05100101) in Kentucky. Water in the Fowler Creek watershed flows from south to north, draining into Banklick Creek and eventually into the Licking River, which in turn feeds into the Ohio River. The dark green polygon in the figure below represents the watershed boundary of Fowler Creek. The green point indicates the outlet, which is located downstream of a USGS gage (shown as a white point) on Banklick Creek.

<div style="display: flex; flex-direction: row; justify-content: center; align-items: center;">
    <img src="https://www.hydroshare.org/resource/0ef4366e7711478fa2637f5049b4881a/data/contents/Figure/domain-study.png" width="1000" height="500" style="margin-right: 20px;">
</div>

This creek is identified by the feature_id 2087827 in the National Water Model (NWM). This feature_id corresponds to the `Permament_Identifier` of the NHDPlus (National Hydrography Dataset Plus). We will first use the `retrieve-nwm-v3-retrospective-streamflow-data.ipynb` code to retrieve NWM retrospective streamflow data from 1979-2023 for this particular reach and estimate the **maximum peak flow** based on the model results, which is about **66.42 cms**. The most recent retrospective simulations are available in the form of Zarr and NetCDF files at <a href="https://noaa-nwm-retrospective-3-0-pds.s3.amazonaws.com/index.html" style="color: blue; background-color: snow;">https://noaa-nwm-retrospective-3-0-pds.s3.amazonaws.com/index.html</a>. We will use `xarray` and `Dask` to work with the Zarr data.

Secondly, we will use the 66.42 cms value as input for the `create-inundation-maps-using-FIM-xarray.ipynb` code to apply the basic Flood Inundation Mapping (FIM) approach and create the inundation extent for this watershed. The FIM process has been developed by the NOAA Office of Water Prediction. For more information, see the [inundation-mapping project](https://github.com/NOAA-OWP/inundation-mapping). There are two approaches to using the data provided by NOAA OWP to compute FIM: basic (simplified) mapping and mosaic mapping. The latter represents the state of practice in this domain; however, for simplicity, this notebook will demonstrate the former. 

Next, we will use the peak discharge of 1% annual chance (corresponding to a 100-year recurrence interval) from FEMA as input for the `create-inundation-maps-using-FIM-xarray.ipynb` code to apply the basic Flood Inundation Mapping (FIM) approach and create the inundation extent for this watershed. For convenience, we have included these data in this HydroShare resource. However, if you want to try obtaining it yourself, follow the steps in the green box below. In the PDF file (Flood Insurance Study report within this HydroShare resource), under Section 3.1 (Hydrologic Analysis), Table 3 summarizes the discharges. On page 16, the value for Fowler Creek at the confluence with Banklick Creek is **5220 cfs**. The associated flood map for this discharge can be viewed in the zipped folder, which contains the National Flood Hazard Layer (NFHL) for the region of interest. Among the different shapefiles within this file, we use `S_Fld_Haz_Ar.shp`, which contains information about the flood hazards within the Flood Risk Project area.

<div style="border:2px solid limegreen; padding: 10px; background-color: honeydew; border-radius: 10px;">
    <p style="font-size:16px; font-family: Arial, sans-serif; color: darkgreen;">
        To access the FEMA Flood Insurance Study Report and National Flood Hazard Layer, follow the steps below:
    </p>
    <ul style="font-size:16px; font-family: Arial, sans-serif; color: darkgreen; list-style-type: decimal; padding-left: 20px;">
        <li>Visit <a href="https://www.fema.gov/flood-maps/products-tools" style="blue: #C70039;"> the FEMA Products and Tools</a>.</li>
        <li>Click on the "View All MSC (Map Service Center) Tools" button, which will take you to another webpage. </li>
        <li>Select the state, county, and community of your interest.</li>
        <li>Expand the "Effective Products" section to see a list of regulatory products authorized by law for making determinations under the NFIP. The Flood Insurance Study (FIS) Reports provide information about 1% annual chance discharge values. The NFHL-Datas-County section contains GIS data related to FEMA flood maps. </li>
    </ul>
</div>

Finally, we will use the discharge value of **5220 cfs** as input for the `create-inundation-maps-using-FIM-v3-xarray.ipynb` code to generate a FIM-based map for this flow. Note that this value should be converted to cubic meters per second (cms) (~147.8 cms) for use in the Jupyter Notebook, as the FIM methodology is based on cms. The main goal of this test is to reduce uncertainties associated with potential errors in the simulated NWM discharge by using the FEMA-provided discharge value. 


The following shows the comparison between the FEMA map, flood inundation extent created based on the FIM approach using the 100-year flood from the FEMA FIS report, and flood inundation extent created based on the FIM approach using the maximum peak flow from the NWM retrospective data.

<div style="display: flex; flex-direction: column; justify-content: center; align-items: center;">
    <img src="https://www.hydroshare.org/resource/0ef4366e7711478fa2637f5049b4881a/data/contents/Figure/FEMA_FEMAFIM_NWMFIM_comparison.png" width="1000" height="500" style="margin-top: 20px;">
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












