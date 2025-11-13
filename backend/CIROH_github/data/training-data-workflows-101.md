# Project Title: **training-data-workflows-101**

## Project Objective  
The **Training Data Workflows 101** workshop introduces a software engineering approach to hydrological data science. It teaches participants to build reproducible, modular, and maintainable data workflows while transitioning from exploratory notebooks to production-ready Python modules. The focus is not on specific tools, but on design principles that enable efficient, scalable, and frustration-free research workflows.

---

## Workshop Philosophy  
This workshop emphasizes **software engineering principles** over tool-specific training. Participants learn to:
- Treat workflows as modular, version-controlled systems.
- Use Git for reproducibility.
- Implement standardized data interfaces using `pandas.Series`.
- Focus on readability, maintainability, and code reuse.

| Principle        | Definition                                  | Implementation Example                                  |
|------------------|---------------------------------------------|----------------------------------------------------------|
| Reproducibility  | Same inputs produce same outputs            | Git version control, standardized interfaces             |
| Readability      | Clear and self-documenting code             | Descriptive naming, modular functions                    |
| Maintainability  | Easy to modify and extend                   | Clean interfaces between workflow stages                 |
| Code Reuse       | Avoid duplicating functionality             | DRY principle, shared modules                            |

---

## Learning Objectives  
Participants will learn to:
1. Decompose workflows into discrete, modular stages.  
2. Transition from exploratory Jupyter notebooks to production Python modules.  
3. Design clean interfaces using standardized `pandas.Series` objects.  
4. Acquire data efficiently from multiple sources (USGS NWIS API, NOAA NWM archives).  
5. Build CLI tools for reproducible, parameterized execution.  
6. Apply iterative development — starting simple, then adding complexity.  

---

## Curriculum Architecture  

The workshop is structured into **three phases** across nine Jupyter notebooks and supporting Python modules:

| Phase | Focus | Description |
|-------|--------|-------------|
| **Phase 1 – Foundation** | Conceptual workflow design | Introduces abstract workflow decomposition before coding. |
| **Phase 2 – Core Technical Skills** | Acquire / Manipulate / Visualize pattern | Refactors notebook code into reusable modules with standardized interfaces. |
| **Phase 3 – Production Practices** | Deployment and CLI workflows | Moves from interactive development to reproducible, command-line execution. |

**Notebooks:**  
00-Welcome • 01-Workflows • 02-BaselineWorkflow • 03-Functions • 04-Interfaces • 05-Acquire • 06-PythonFromTerminal • 07-Visualize • 08-VisualizationExample • 09-WrapUp  

**Modules:**  
`python/modules.py`, `pythonv2/workflowCLI.py`

---

## Core Workflow Pattern  
The workshop teaches a three-stage workflow pattern with a **standardized `pandas.Series` interface**:

1. **Acquire** → `acquire_streamflow_nwis_iv()`, `acquire_streamflow_nwm_re()`
2. **Manipulate** → `resample_to_daily()`, `cubicftsec_to_cubicmsec()`
3. **Visualize** → `visualize_matplotlib()`, `visualize_seaborn()`, `visualize_holoviews()`, `visualize_plotly()`

### Interface Contract  
Each stage consumes and produces a `pandas.Series` object with:
- **DatetimeIndex** for temporal alignment  
- **Named units** (e.g., “streamflow (m³/s)”)  
- **Float64 dtype** for numerical consistency  

This enables plug-and-play modularity across all workflow stages.

---

## Development Philosophy  

| Stage | Tool | Purpose | Strengths | Limitations |
|--------|------|----------|------------|--------------|
| **Exploration** | Jupyter Notebook | Rapid prototyping, visualization | Interactive, immediate feedback | Poor reproducibility and version control |
| **Modularization** | `.py` modules | Reusable libraries | Testable, maintainable, clean interfaces | Requires structured design |
| **Production** | CLI scripts | Automated execution | Reproducible, parameterized | Limited interactivity |

---

## Data Sources and Technology Stack  

### Data Sources
- **USGS NWIS API** (`waterdata.usgs.gov`) – Instantaneous streamflow data  
- **NOAA NWM Retrospective (S3 Zarr Archive)** – Model outputs via S3  

### Technology Stack
| Category | Libraries | Purpose |
|-----------|------------|----------|
| Data Structures | `pandas`, `NumPy` | Core data manipulation |
| Multidimensional Data | `xarray` | NetCDF/Zarr handling |
| Domain Acquisition | `dataretrieval` | USGS NWIS API wrapper |
| Cloud Data | `s3fs` | S3 filesystem interface |
| Visualization | `matplotlib`, `seaborn`, `holoviews`, `plotly` | Diverse visualization methods |
| Development | `Python 3.11`, `JupyterHub` | Interactive + CLI environments |

---

## Key Design Principles  
1. **Modularity Through Interfaces** — Consistent `pandas.Series` design allows swapping data sources and visualization methods seamlessly.  
2. **Start Simple, Iterate** — Build minimal viable workflows, then scale incrementally.  
3. **Efficient Data Acquisition** — Filter at the source to reduce data transfer and memory overhead.  
4. **Version Control with Git** — Use branches, pull requests, and commit hashes for reproducibility.  

---

## Target Audience  
- Hydrological researchers writing data analysis scripts.  
- Environmental data scientists seeking maintainable workflows.  
- Graduate students developing computational research pipelines.  
- CIROH members using National Water Model outputs.  

**Prerequisites:**  
Basic Python, Jupyter familiarity, and fundamental hydrology concepts. No prior software engineering experience required.

---

## Workshop Environment  
Accessible through **CIROH’s cloud JupyterHub**:  
`https://ciroh.awi.2i2c.cloud`

---

## License  
Licensed under the **Apache License 2.0**.  
© 2025 CIROH – The University of Alabama.  
Permits use, modification, distribution, and commercial application with proper attribution.
