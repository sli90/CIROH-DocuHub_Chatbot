# NextGen on 2i2c JupyterHub

[Skip to main content](https://docs.ciroh.org/docs/products/ngiab/distributions/nextgen-2i2c/#__docusaurus_skipToContent_fallback)

On this page

New CIROH JupyterHub image named "NextGen National Water Model (NWM)" has both NGIAB Data Preprocess and NextGen packages installed.

> You can access 2i2c JupyterHub here: [https://ciroh.awi.2i2c.cloud/hub/login](https://ciroh.awi.2i2c.cloud/hub/login).

![JupyterHub](https://docs.ciroh.org/assets/images/jupyterhub-464abfe07a594a5289edeb4c59857754.png)

## Working with HydroShare, AORC data, HydroFabric and NextGen on CIROH JupyterHub Tutorial [​](https://docs.ciroh.org/docs/products/ngiab/distributions/nextgen-2i2c/\#working-with-hydroshare-aorc-data-hydrofabric-and-nextgen-on-ciroh-jupyterhub-tutorial "Direct link to Working with HydroShare, AORC data, HydroFabric and NextGen on CIROH JupyterHub Tutorial")

This HydroShare resource provides a tutorial on the use of the Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI) HydroShare repository and linked CIROH JupyterHub computing platform on 2i2c in support of CIROH collaborative research and NextGen modeling. It introduces use of Jupyter Notebooks for retrieval of NOAA Analysis of Record for Calibration (AORC) datasets and setting up and executing NextGen for a small test watershed as a starting point for research with NextGen.

You can find the resource here: [https://www.hydroshare.org/resource/fc8539358fe64ca6a47468728a0687a1/](https://www.hydroshare.org/resource/fc8539358fe64ca6a47468728a0687a1/)

To open the resource in CIROH JupyterHub, click the "Open with..." button on the HydroShare page and select "CIROH JupyterHub":

![Opening with CIROH JupyterHub](https://docs.ciroh.org/assets/images/resource-43b2106555301063f9d29113976d7d36.png)

## Command Line Examples [​](https://docs.ciroh.org/docs/products/ngiab/distributions/nextgen-2i2c/\#command-line-examples "Direct link to Command Line Examples")

Here are some command-line examples related to working with the data:

```codeBlockLines_e6Vv
# Virtual environment
source /ngen/.venv/bin/activate
python -m ngiab_data_cli -i "gage-10109001" -s
# Hydrofabric
python -m ngiab_data_cli -i "cat-2861446" -s
# Forcing
python -m ngiab_data_cli -i "cat-2861446" -f --start "2021-10-01" --end "2022-09-30"
# Configuration
python -m ngiab_data_cli -i "cat-2861446" -r --start "2021-10-01" --end "2022-09-30"
# Run
/dmod/bin/ngen-serial config/cat-2861446_subset.gpkg all config/cat-2861446_subset.gpkg all config/realization.json

```

* * *

## Visualizations [​](https://docs.ciroh.org/docs/products/ngiab/distributions/nextgen-2i2c/\#visualizations "Direct link to Visualizations")

Shown below is a sample visualization based on the above command-line example:

![Graph](https://docs.ciroh.org/assets/images/graph-618fe46ba8f67fb53c6fd3644b167381.png)

- [Working with HydroShare, AORC data, HydroFabric and NextGen on CIROH JupyterHub Tutorial](https://docs.ciroh.org/docs/products/ngiab/distributions/nextgen-2i2c/#working-with-hydroshare-aorc-data-hydrofabric-and-nextgen-on-ciroh-jupyterhub-tutorial)
- [Command Line Examples](https://docs.ciroh.org/docs/products/ngiab/distributions/nextgen-2i2c/#command-line-examples)
- [Visualizations](https://docs.ciroh.org/docs/products/ngiab/distributions/nextgen-2i2c/#visualizations)