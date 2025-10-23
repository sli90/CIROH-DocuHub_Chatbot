# Project Title: **hf_pmtiles**

## Project Objective  
The **hf_pmtiles** repository provides a Docker-based workflow to convert GeoPackage files into Protomaps PMTiles format. It utilizes the Lynker Spatial Hydrofabric dataset under the OBDL license. The repository aims to streamline the generation of PMTiles for hydrologic or geospatial visualization and distribution.

## Core Functionalities  
- Converts GeoPackages into Protomaps PMTiles using a Dockerized process.  
- Provides an example style and usage guide in the `map` folder.  
- Enables serving of generated tiles using compatible tools such as Martin Tiles or the PMTiles utility.  

## Technical Stack  
- **Languages/Tools:** Docker.  
- **Data Sources:** Lynker Spatial Hydrofabric under OBDL license.  
- **Tile Format:** Protomaps PMTiles.  

## Setup and Usage  
1. **Build the Docker image:**  
   ```bash
   docker build -t pmtiles .
   ```  
2. **Wait for processing:** The build process downloads and processes the required data.  
3. **Run the Docker container:**  
   ```bash
   docker run --name hfmap --rm -it pmtiles /bin/bash
   ```  
4. **Copy the PMTiles file from the container:**  
   ```bash
   docker cp hfmap:/mbtiles/merged/merged.pmtiles .
   ```  
5. **Serve the tiles locally:** Use a tile-serving tool like [Martin Tiles](https://martin.maplibre.org/) or the PMTiles command-line utility.  

## Project Context & Domain  
- **Domain:** Geospatial Data Processing / Hydrology.  
- **Affiliation:** Lynker Spatial.  
- **Purpose:** Simplify the conversion of GeoPackages to PMTiles for efficient mapping and visualization workflows.  

## Input / Output  
**Input:**  
- GeoPackage (.gpkg) files containing spatial or hydrologic data.  

**Output:**  
- Protomaps PMTiles (.pmtiles) files suitable for web-based tile serving or visualization.  
