# Running NGIAB, TEEHR Evaluation and Tethys Visualizer

## Installation and Setup Instructions

Follow these steps to set up and run the NGIAB, TEEHR Evaluation and Tethys Visualizer:

1. Download the provided zip folder
2. Extract the zip folder to your preferred location
3. Clone the NGIAB-CloudInfra Infrastructure repository:
   `git clone https://github.com/CIROH-UA/NGIAB-CloudInfra.git`
4. Navigate to the cloned repository:
   `cd NGIAB-CloudInfra`
5. Run the setup guide script:
   `./guide.sh`
6. When prompted, provide the absolute path to the folder extracted in step 2

After completing these steps, follow the prompts to get the output plot shown below:

![gage-10154200 Output Plot showing TEEHR metrics](https://www.hydroshare.org/resource/88e0ebf2719c492381efcb27fba71032/data/contents/gage_10154200_output_plot.png)

---

## How We Generated the Input Data (gage-10154200) on Jetstream2

### Versions Used
- **NGIAB Data Preprocess:** [v4.3.3](https://github.com/CIROH-UA/NGIAB_data_preprocess/releases/tag/v4.3.3)
- **NGIAB CloudInfra:** [v1.4.3](https://github.com/CIROH-UA/NGIAB-CloudInfra/releases/tag/v1.4.3)

### Jetstream2 Instance Configuration

- **Flavor:** m3.2xl
- **vCPUs:** 64
- **RAM:** 250 GB
- **Local Storage:** 60 GB

---

## Data Preparation Commands

To obtain the necessary data (the "zip folder" referenced in step 2), we executed the following commands on a Jetstream2 instance:

### Step 1: Data Preprocessing
`uvx ngiab-prep -i gage-10154200 -sfr --start 2017-01-01 --end 2023-01-02`

This command prepares the input data for the workflow. 

📚 **Learn more:** [NGIAB Data Preprocess Repository](https://github.com/CIROH-UA/NGIAB_data_preprocess)

#### Command Arguments Explained:
- `-i INPUT_FEATURE` - ID of feature to subset (supports prefixes like `cat-5173`, `gage-01646500`, or `wb-1234`)
- `-s, --subset` - Subset the hydrofabric to the given feature
- `-f, --forcings` - Generate forcings for the given feature  
- `-r, --realization` - Create a realization for the given feature
- `--start` - Start date for forcings/realization (format: YYYY-MM-DD)
- `--end` - End date for forcings/realization (format: YYYY-MM-DD)
- `-g, --gage` - Use gage ID instead of catid

### Step 2: Model Calibration
`uvx ngiab-cal ~/ngiab_preprocess_output/gage-10154200 -i 200 -g 10154200 --run -f --cr 0.8`

This command performs model calibration using the prepared data.

📚 **Learn more:** [NGIAB Calibration Repository](https://github.com/CIROH-UA/ngiab-cal)

#### Calibration Arguments:
- `data_folder` - Path to the folder you wish to calibrate
- `-g GAGE` - Gage ID to use for calibration
- `-f, --force` - Overwrite existing configuration
- `--run` - Automatically run the calibration (may be unstable)
- `-i ITERATIONS` - Number of iterations to calibrate for (default: 100)
- `--calibration_ratio` - Split ratio for calibration vs validation data
  - `1.0` = 100% calibration, 0% validation
  - `0.8` = 80% calibration, 20% validation  
  - `0.5` = 50% calibration, 50% validation (default)

---

## Output Location

Once these commands finish running, the output folder containing the necessary data will be located at:

`~/ngiab_preprocess_output/gage-10154200`
