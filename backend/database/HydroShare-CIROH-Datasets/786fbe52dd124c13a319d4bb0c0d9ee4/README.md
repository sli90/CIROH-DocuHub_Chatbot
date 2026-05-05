## Using HydroShare Buckets to Access Resource Files

This resource includes the following files:

* **hydroshare_s3_bucket_access_examples.ipynb**: Examples for working directly with HydroShare S3 buckets to access and manage resource files, without the need to download them locally first.
* **hs_bucket_access_gdal_example.ipynb**: Examples for reading raster and shapefile directly from HydroShare S3 buckets using `gdal`, without the need to download them locally first.
* **hs_bucket_access_non_gdal_example.ipynb**: Examples of using 1- `h5netcdf` and `xarray` for reading netcdf files, 2- `rioxarray` to read raster files, and 3- `pandas` to read CSV files, all directly from HydroShare S3 buckets, without the need to download them locally first.
* **user_account.py**: A utility for reading cached HydroShare account information in any JupyterHub instance accessible by HydroShare. The example notebooks use this utility so that users do not have to enter their hydroshare account information manually to access hydroshare buckets.
* **conda\_env**: A folder containing the **CondaEnvironmentSetup.ipynb** notebook with instructions and scripts for setting up a custom Conda environment.
* **README.md**: Explains the contents of this resource.

To use this resource in HydroShare, select ***Open With*** on one of the available application servers to launch the corresponding JupyterHub environment. Then, open the desired Jupyter Notebook and follow the instructions.