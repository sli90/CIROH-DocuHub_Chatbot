# Reference

Last updated on 2025-04-22

## Glossary

### Modeling Terms

#### National Water Model (NWM)
Hydrologic model used operationally by NOAA's National Weather Service to provide hydrologic predictions for over 3.4 million rivers and streams across the United States

#### Next Generation Water Resources Modeling Framework (NextGen)
An advancement of the NWM, a standards-based and model-agnostic modular set of software tools that applies the Basic Model Interface

#### NextGen in a Box (NGIAB)
An open-source, containerized solution that encapsulates the NextGen framework and essential modeling components into a self-contained, reproducible application

#### Data Preprocess
A tool to streamline data preparation for NextGen runs

#### Tools for Exploratory Evaluation in Hydrologic Research (TEEHR)
A Python-based package enabling iterative and explorative analysis of hydrologic model performance

#### Data Visualizer
A tool that provides a robust environment for geospatial and time series visualization of catchments and nexus points

#### Forcings
External inputs that drive a model

#### t-route
Channel routing model used in the NWM. t-route is used in NextGen.

#### Channel routing
Predicts the magnitude and shape of a hydrograph as water moves through waterways.

#### ngen
The NextGen model engine

#### Realization file
A file that configures models and the variables exchanged between them. For example, our realization files define which hydrologic model we are using, over what time period, and over which regions.

#### Hydrofabric
See [the hydrofabric documentation](https://noaa-owp.github.io/hydrofabric/articles/01-intro-deep-dive.html)

#### Conceptual Functional Equivalent (CFE) Model
A simplified conceptual rainfall-runoff model designed to be functionally equivalent to the NWM. This is an available model in NGIAB.

#### Rainfall-runoff model
Describes how rainfall is converted into runoff in a catchment, producing a hydrograph in response to a rainfall event

#### NoahOWP
Version of the Noah-MP land surface model used by NOAA's Office of Water Prediction. This is an available model in NGIAB.

#### Land surface model
Describes the exchange of water and energy between the land surface and the atmosphere

#### Long short-term memory (LSTM) model
A type of recurrent neural network that excels at learning long-term dependencies in sequential data. This is an available model in NGIAB.

#### Error statistics
The difference between the true value and the modeled variable

#### Skill score
The accuracy of a model relative to a reference approach, like random chance or persistence

#### Persistence
A forecast that the future condition will be the same as the present condition

#### Uncertainty quantification
Estimation of uncertainty and errors in models

### Computing Terms

#### Containerization
Encapsulating applications, their dependencies, and runtime environments into a single, portable unit to address compatibility issues and hardware variation challenges

#### Docker
A widely used containerization platform that provides a lightweight, portable, and scalable solution for software deployment

#### Singularity
A containerization platform for HPC environments

#### Basic Model Interface (BMI)
A standardized system designed to enhance interoperability between models and datasets

#### Tethys Platform
Platform for geospatial web app development

#### High-Performance Computing (HPC)
Systems with clusters of parallel processors that process data and perform calculations at high speeds

#### Job scheduler (e.g. SLURM/PBS/LSF)
A software that manages which tasks run where and when on an HPC system

#### Open-source
Software or data that is publicly accessible and can be redistributed or modified

#### Secure Shell (SSH)
Network protocol that provides secure remote access with encrypted connections

### Hydrologic Terms

#### Catchment
Area from which precipitation collects and drains into an output point like a river or water body. Also known as a watershed

#### Streamflow
The flow of water in a channel, measured in units of volume/time (e.g. cubic meters per second (CMS), cubic feet per second (CFS)). Also known as discharge

#### Hydrologic model
A computer-based replication of the natural water cycle

#### CONUS (Continental United States)
Refers to the 48 contiguous states and D.C.

#### Surface runoff
Unconfined flow of water over the ground surface

#### Hydrologic signature
Quantitative metrics that define streamflow, such as maximum flow, baseflow, mean flow, or slope

#### Hydrograph
Graph that depicts streamflow at a specific location over time