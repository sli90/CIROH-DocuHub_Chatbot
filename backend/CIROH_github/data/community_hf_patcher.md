# Project Title: **community_hf_patcher**

## Project Objective  
The **community_hf_patcher** repository provides scripts and Docker configurations to apply patches to the **CIROH Community Hydrofabric**, a temporary fork of Lynker Spatial's **NextGen Hydrofabric v2.2**.  
These patches improve compatibility with CIROH projects, including the **NextGen In A Box** ecosystem. The repository generates patched hydrofabric datasets that can be published to the **Community Hydrofabric bucket** on AWS S3.

## Core Functionalities  
- Applies patches to the CIROH Community Hydrofabric.  
- Publishes processed hydrofabric data to AWS S3.  
- Corrects gage-to-flowpath mappings (~4500 gages).  
- Reformats hydrolocation tables to be GPKG compliant for GIS compatibility.  
- Adds database indices for faster query performance.  
- Subsets the hydrofabric into individual VPUs.  
- Uses Docker for building, processing, and compressing hydrofabric data.  

## Technical Stack  
- **Languages/Tools:** Python, Shell.  
- **Containerization:** Docker (multi-stage builds).  
- **Data Sources:** Lynker Spatial’s NextGen Hydrofabric v2.2 (ODbL licensed).  
- **Storage:** AWS S3 for output publication.  
- **Dependencies:** Docker, AWS CLI (for upload).  

## Setup and Usage  
### Prerequisites  
- Docker  
- AWS CLI (if uploading to S3)  

### Running the Patcher  
Run the build process using:  
```bash
./generate_hydrofabric.sh
```  
To upload outputs to an S3 bucket, uncomment AWS commands in the shell scripts.

### Repository Structure  
- **`generate_hydrofabric.sh`** – Main entrypoint for building and running the Docker container, extracting outputs, and optionally uploading results.  
- **`generate_vpus.sh`** – Secondary script that subsets the hydrofabric into individual VPUs.  
- **`Dockerfile`** – Defines stages for downloading, processing, and compressing hydrofabric data.  
- **`scripts/`** – Contains Python and shell scripts for data processing tasks.  
  - **`scripts/formatting`** – Handles data formatting and storage structure.  
  - **`scripts/hydro`** – Modifies hydrologic data affecting simulation outputs.  

### Workflow Overview  
1. **Build and Run the Docker Container:**  
   - Downloads raw hydrofabric data.  
   - Adds indices and updates gages.  
   - Converts hydrolocations and subsets VPUs.  
   - Compresses processed outputs.  

2. **Extract Processed Files:**  
   - `conus_nextgen.gpkg`: Complete patched hydrofabric.  
   - `conus_nextgen.tar.gz`: Compressed version of the above.  
   - `gage_replacements.csv`: Catalog of gage corrections.  
   - `VPU/`: Folder with individual VPU hydrofabrics.  
   - `VPU/compressed/`: Folder with compressed tarballs of each VPU hydrofabric.  

3. **Upload to S3 (Optional):**  
   Uncomment upload commands in the scripts and ensure valid AWS credentials are configured.  

## Project Context & Domain  
- **Domain:** Hydrology / Geospatial Data Processing.  
- **Affiliation:** CIROH (Cooperative Institute for Research to Operations in Hydrology).  
- **Purpose:** Apply compatibility patches to the NextGen Hydrofabric v2.2 for CIROH projects and publish updated versions to AWS S3.  

## Input / Output  
**Input:**  
- Lynker Spatial’s NextGen Hydrofabric v2.2 source data.  
- Configuration and patch scripts.  

**Output:**  
- Patched hydrofabric files (`.gpkg`, `.tar.gz`).  
- Updated gage mapping CSV.  
- Subset VPU hydrofabric folders (optional).  
- Uploaded datasets in the Community Hydrofabric S3 bucket (optional).  
