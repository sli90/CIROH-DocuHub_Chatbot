# Project Title: **nwmurl**

## Project Objective  
**nwmurl** is a Python library developed by CIROH (2023). It provides utility functions designed to subset and generate National Water Model (NWM) data URLs.  
The tool simplifies the process of accessing NWM data for purposes such as analysis, modeling, and visualization.

## Core Functionalities  
- Generates NWM data URLs for operational and retrospective datasets.  
- Allows users to customize data retrieval parameters such as date ranges, forecast cycles, variables, geographic regions, and run configurations.  
- Supports URL generation from multiple data sources including NOAA and CIROH-hosted storage locations.  
- Offers Boolean options to save generated URLs to a text file.  
- Provides detailed parameter options for operational and retrospective datasets.  

## Technical Stack  
- **Language:** Python  
- **Dependencies:** Not specified.  
- **Installation:**  
  ```bash
  pip install nwmurl
  ```

## Setup and Usage  
1. **Operational Dataset Example:**  
   ```python
   import nwmurl

   start_date = "202201120000"
   end_date   = "202201130000"
   fcst_cycle = [0,8]
   lead_time = [1,18]
   varinput = 1
   geoinput = 1
   runinput = 1
   urlbaseinput = 2
   meminput = 1
   write_to_file = False

   file_list = nwmurl.generate_urls_operational(
       start_date,
       end_date,
       fcst_cycle,
       lead_time,
       varinput,
       geoinput,
       runinput,
       urlbaseinput,
       meminput,
       write_to_file
   )
   ```  

2. **Retrospective Dataset Example:**  
   ```python
   import nwmurl

   start_date = "200701010000"
   end_date = "200701030800"
   urlbaseinput = 2
   selected_var_types = [1, 2]
   selected_object_types = [1]  
   write_to_file = True

   file_list = nwmurl.generate_urls_retro(
       start_date,
       end_date,
       urlbaseinput,
       selected_object_types,
       selected_var_types,
       write_to_file
   )
   ```  

## Project Context & Domain  
- **Domain:** Hydrology / Data Access / Water Modeling.  
- **Affiliation:** CIROH (2023).  
- **Purpose:** Streamline generation of NWM data URLs for modeling, analysis, and visualization tasks.

## Input / Output  
**Input:**  
- Parameters for date range, forecast cycle, variable type, geographic region, and run configuration.  
- Dataset selection (operational or retrospective).  

**Output:**  
- List of generated NWM data URLs.  
- Optional text file containing URLs if `write_to_file` is set to `True`.  

## Contribution Guidelines  
1. Fork the repository.  
2. Clone your fork:  
   ```bash
   git clone https://github.com/CIROH-UA/nwmurl.git
   ```  
3. Create a new branch for your feature:  
   ```bash
   git checkout -b feature/your-feature-name
   ```  
4. Implement changes and update the package version in `setup.py` if needed.  
5. Commit with descriptive messages and push changes.  
6. Open a pull request describing your changes for review.  

## License  
Not specified.  
