# NGIAB Singularity Distribution

[Skip to main content](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-singularity/#__docusaurus_skipToContent_fallback)

> **NOTE**
>
>  Below content is rendered from [https://github.com/CIROH-UA/NGIAB-HPCInfra/blob/main/README.md](https://github.com/CIROH-UA/NGIAB-HPCInfra/blob/main/README.md).

# **NextGen In A Box (NGIAB)**

**Run the NextGen National Water Resources Modeling Framework locally with ease.**

NGIAB provides a containerized and user-friendly solution for running the NextGen framework, allowing you to control inputs, configurations, and execution on your local machine.

[![](https://github.com/CIROH-UA/NGIAB-CloudInfra/raw/main/image/README/ngiab.png)](https://github.com/CIROH-UA/NGIAB-CloudInfra/blob/main/image/README/ngiab.png)

|  |  |
| --- | --- |
| [![alt text](https://camo.githubusercontent.com/f1425ea9a6a4492162f5ff3a63a5d0827fc95442381ae96e095095c7afd57152/68747470733a2f2f6369726f682e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032322f30382f4349524f484c6f676f5f323030783230302e706e67)](https://camo.githubusercontent.com/f1425ea9a6a4492162f5ff3a63a5d0827fc95442381ae96e095095c7afd57152/68747470733a2f2f6369726f682e75612e6564752f77702d636f6e74656e742f75706c6f6164732f323032322f30382f4349524f484c6f676f5f323030783230302e706e67) | Funding for this project was provided by the National Oceanic & Atmospheric Administration (NOAA), awarded to the Cooperative Institute for Research to Operations in Hydrology (CIROH) through the NOAA Cooperative Agreement with The University of Alabama (NA22NWS4320003). |

**Why NextGen In A Box?**

- **Run NextGen Locally:** Experiment with the framework and customize configurations on your local machine.
- **Control Over Inputs:** Choose specific regions or basins for analysis and modify input data as needed.
- **Simplified Setup:** Utilize Docker containers for effortless deployment, avoiding complex software installations.
- **Open Research Practices:** Promote transparency and reproducibility through open-source tools like Git and GitHub.

## Repository Information

- This branch specifically for the users of Singularity container image to run simulation on NextGen Framework
- The file structure and brife information of each file:



```
.
├── guide.sh
├── README.md
└── singularity
      ├── singularity_ngen.def
      └── templates
          ├── guide
              └── HelloNGEN.sh

```


1. [`guilde.sh`](https://github.com/CIROH-UA/NGIAB-HPCInfra/blob/main/guide.sh) : The guide script to run the simulations on the singularity image
2. [`README.md`](https://github.com/CIROH-UA/NGIAB-HPCInfra/blob/main/README.md) : Documentation of how to run the model and contribute in development on NGIAB
3. [`singularity_ngen.def`](https://github.com/CIROH-UA/NGIAB-HPCInfra/blob/main/singularity/singularity_ngen.def) : The singularity definition file to build image
4. [`HelloNGEN.sh`](https://github.com/CIROH-UA/NGIAB-HPCInfra/blob/main/singularity/templates/guide/HelloNGEN.sh) : This is NGen execution script, which runs when the image is being executed by users.

## Prerequisites

### 1\. Access a compute node

On your HPC system, request an interactive session on a compute node using your scheduler (e.g., SLURM):

```
srun --partition=<partition_name> --nodes=1 --ntasks=1 --time=<hh:mm:ss> --pty bash
```

Replace `<partition_name>` and `<hh:mm:ss>` with the appropriate partition and time limits for your HPC system.

### 2\. Install SingularityCE on HPC

Ensure SingularityCE is installed and validated on your HPC system. All operations, including data preparation and running the simulation, should be performed on a compute node, not the login node. Consult your system administrator or follow these steps:

**i. Check Singularity Availability**:

Verify that SingularityCE is installed on your HPC environment by running:

```
singularity --version
```

**ii. Install SingularityCE (if necessary)**:

Refer to the [official SingularityCE installation guide](https://docs.sylabs.io/guides/4.0/admin-guide/installation.html#installation-on-linux) for instructions tailored to Linux environments.

### Input Data

- **Download Sample Data:** Use the provided commands to download sample data for the Sipsey Fork case study.
- **To generate your own data:** Refer to the [NGIAB-datapreprocessor](https://github.com/AlabamaWaterInstitute/NGIAB_data_preprocess) for instructions on generating custom input data.
- **To generate your own data and run using NGIAB:** Refer to the [ngen-datastream repository](https://github.com/CIROH-UA/ngen-datastream/tree/main) for instructions on generating custom input data.

This section guides you through downloading and preparing the sample input data for the NextGen In A Box project.

**Step 1: Create Project Directory**

On the HPC system, create a directory for the project and data using the following commands:

```
mkdir -p NextGen/ngen-data
```

```
cd NextGen/ngen-data
```

**Step 2: Download Sample Data**

Use wget to download the compressed data file:

**Option 1: AWI-009 input data (realization file includes - SLOTH, NoahOWP, CFE) - calibrated realization file for Provo River near Woodland, UT**

```
wget --no-parent https://ciroh-ua-ngen-data.s3.us-east-2.amazonaws.com/AWI-009/AWI_16_10154200_009.tar.gz
```

**Option 2: AWI-007 input data (relization file includes - SLOTH, NoahOWP, CFE)**

```
wget --no-parent https://ciroh-ua-ngen-data.s3.us-east-2.amazonaws.com/AWI-007/AWI_16_2863657_007.tar.gz
```

**Option 3: AWI-008 input data (realization file includes - SLOTH, Demostration LSTM)**

```
wget --no-parent https://ciroh-ua-ngen-data.s3.us-east-2.amazonaws.com/AWI-008/AWI_16_2863806_008.tar.gz
```

**Step 3: Extract and Rename**

Extract the downloaded file and optionally rename the folder:

**Option 1**

```
tar -xf AWI_16_10154200_009.tar.gz
```

**Option 2:**

```
tar -xf AWI_16_2863657_007.tar.gz
```

**Option 3:**

```
tar -xf AWI_16_2863806_008.tar.gz
```

Now you have successfully downloaded and prepared the sample input data in the NextGen/ngen-data directory.

**Step 4: Clone and Run**
Navigate to the NextGen directory, clone the repository, and execute the guide script:

```
cd ../../NextGen
```

```
git clone https://github.com/CIROH-UA/NGIAB-HPCInfra.git
```

```
cd NGIAB-HPCInfra
```

```
./guide.sh
```

## Run NextGen In A Box

To run NextGen framework, hydrologist only have to execute the [guide script](https://github.com/CIROH-UA/Ngen-Singularity/blob/main/guide.sh) to run simulations on self-contained NextGen framework container image.

- The guide script feature:
  - Determine architecher of the underling system (ARM or x86)
  - Automaticlly download latest Singularity NextGen image from Docker Hub
  - Allow to attach input data by providing relative path of it
  - The options of running image:
    1. Run simulation in **Serial** mode
    2. Run simulation in **Parallel** mode
    3. Run image in **Interactive shell** mode