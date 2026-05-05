# National Water Model Data Access Example

## Overview

This repository showcases a Python code example that demonstrates how to efficiently access data from the National Water Model (NWM) for various configurations. The code generates JSON header URLs for accessing specific NWM data, retrieves the data in parallel, and then processes and plots the results. 

The provided Jupyter Notebook, "DataAccessExample.ipynb," walks you through the entire process, and the accompanying "urlgennwm.py" contains utility functions to generate NWM URLs.

## Getting Started

### Prerequisites

Before running the code, make sure you have the following prerequisites installed:

- Python 3.x
- Jupyter Notebook
- Required Python packages (install with `pip` if not already installed):
  - `numpy`
  - `xarray`
  - `fsspec`
  - `ujson`
  - `matplotlib`
  - `psutil`
  - `concurrent.futures`
  - `multiprocessing`
  - `joblib`
  - `tqdm`

### Installation

1. Clone the repository to your local machine:

git clone https://github.com/CIROH-UA/data_access_example.git


2. Navigate to the repository folder:


3. Launch the Jupyter Notebook to execute the example:


## Usage

1. In the Jupyter Notebook, you can modify the input parameters, such as `start_date`, `end_date`, `fcst_cycle`, `lead_time`, `varinput`, `geoinput`, and `runinput`, to customize the NWM data retrieval.

2. The code will generate a list of JSON header URLs tailored to your specified parameters using the `urlgennwm.generate_urls` function.

3. The code efficiently retrieves the NWM data in parallel, processes it, and creates separate plots for each feature ID.

4. You can view the resulting time series plots of the extracted streamflow values in the Jupyter Notebook.

## Customize Your Data Retrieval

To retrieve specific NWM data, you can customize the following parameters:

- `start_date`: The starting date for data retrieval in the format "YYYYMMDDHHMM."

- `end_date`: The ending date in the same format.

- `fcst_cycle`: A list of forecast cycle numbers.

- `lead_time`: A list of lead times in hours for forecasts.

- `varinput`: An integer representing the variable of interest.

- `geoinput`: An integer representing the geographic region of interest.

- `runinput`: An integer representing the NWM run configuration.

## Contributing

Contributions to improve and expand this example are welcome. Feel free to submit pull requests, report issues, or suggest enhancements.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

