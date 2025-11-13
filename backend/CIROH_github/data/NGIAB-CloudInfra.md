# Project Title: **NGIAB-CloudInfra**

## Project Objective
Provide a containerized, user-friendly way to run the **NextGen** National Water Resources Modeling Framework locally. The project focuses on simplifying setup and execution, giving users control over inputs, configurations, and runs while supporting open research, evaluation, and visualization workflows.

## Core Functionalities
- **Run NextGen locally:** Experiment with the framework on a personal machine.
- **Control over inputs:** Choose regions/basins and adjust input data as needed.
- **Simplified setup:** Deploy using Docker containers and provided guide scripts.
- **Open research:** Encourage transparency with open-source tooling.
- **Evaluation tools:** Integrated **TEEHR** capabilities for model evaluation.
- **Visualization:** Built-in support to visualize outputs via the **Tethys Platform**.
- **Guide scripts & docs:** `guide.sh`, `runTeehr.sh`, `viewOnTethys.sh` and a comprehensive `docs/` tree to navigate usage and options.

## Technical Stack
- **Containerization:** Docker
- **Evaluation/Visualization:** TEEHR; Tethys Platform
- **Orchestrations/CI:** GitHub Actions workflows (for image build/push)
- **Models/Ecosystem:** NextGen framework
- **Languages:** Not specified.

## Setup and Usage
- **Recommended entrypoints:** Use the guide scripts (`guide.sh`, `runTeehr.sh`, `viewOnTethys.sh`); pass `-h` to see flags.
- **Documentation:** See the `docs/` folder for details; broader docs mirrored at docs.ciroh.org/products/ngiab.
- **Container image:** Releases are published to Docker Hub (`awiciroh/ciroh-ngen-image`).

## Project Context & Domain
- **Domain:** Hydrology / Water resources modeling.
- **Funding & Affiliation:** Sponsored by **NOAA**, awarded to **CIROH** through the NOAA Cooperative Agreement with **The University of Alabama** (NA22NWS4320003).
- **Related resources:** Case-study assets and setup details are available via the linked HydroShare resource for the Provo River NGIAB case study.

## Input / Output
**Input:** User-selected regions/basins and corresponding NextGen input datasets/configurations (high-level control via scripts and container).  
**Output:** NextGen model outputs suitable for **TEEHR** evaluation and **Tethys** visualization (plots, metrics, and geospatial visualizations). Specific file formats/paths: Not specified.
