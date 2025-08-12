---
title: CIROH News
source: https://docs.ciroh.org/news
scraped_date: 2025-01-31
---

* * *

**Stay connected with the latest developments in NextGen water modeling!** This news hub brings you updates, breakthroughs, and opportunities from across our community of practice.

Discover how researchers and practitioners are applying NextGen frameworks to solve pressing water challenges, learn about upcoming training events, and explore new resources to enhance your modeling workflow. Our community-driven approach ensures you'll always be informed about the innovations that matter most.

* * *

## June 2025 Updates

### NGIAB-data-preprocess

A new release of ngiab_data_preprocess, version **v4.3.0**, is now available. This update primarily includes small improvements and bug fixes. Among the more noticeable changes, the map application can now display data source chunking. Additionally, missing values in the AORC forcing data will now be filled using interpolation.

Beyond these changes, an **'alias'** for ngiab_data_preprocess has been created. This allows users to execute the command-line interface (CLI) more concisely, for example, using `uvx ngiab-prep -i cat-123` instead of the longer `uvx --from ngiab_data_preprocess cli -i cat-123`. This alias functions as a separate pip package that simply depends on ngiab_data_preprocess.

[Read more...](https://github.com/CIROH-UA/NGIAB_data_preprocess/releases/tag/v4.3.0)

### ngen-datastream

For this month, we primarily focused on cleaning up the code and updating to the **latest Python version, 3.12**. In terms of system operations, we have scaled back to **VPU16** and are now exclusively running only VPU16.

It's been observed that the NWM analysis_assim_extend forcings are intermittent, which is causing similar intermittent behavior in the analogous datastream runs.

[Read more...](https://github.com/CIROH-UA/ngen-datastream/commits/main/?since=2025-06-01&until=2025-06-30)

* * *

## May 2025 Updates

### CIROH Developer's Conference 2025: NextGen Workshops

📚 Content from many of DevCon2025's workshops has been made publicly available! Links to several of them are provided below.

> _Note that some workshops made use of resources that were deployed specifically during DevCon. However, their steps should still work when adapted for local installations._

- [Navigating the NextGen Ecosystem and NextGen In A Box (NGIAB)](https://github.com/CIROH-UA/Conferences/blob/main/CIROHDevCon2025/CIROH%20Community%20NextGen%202025_Final.pdf)
- [BMI Basics for NGIAB](https://github.com/CIROH-UA/Conferences/blob/main/CIROHDevCon2025/BMI%20Basics%20Workshop.md)
- [Output visualization through Tethys and evaluation customization using TEEHR](https://github.com/CIROH-UA/Conferences/blob/main/CIROHDevCon2025/OutputVisualizationThroughTethysAndTEEHREvaluation_DevCon2025_IntroSlides.pdf)
- [NextGen Calibration Workshop](https://github.com/skoriche/NGIAB-Calibration-DevCon25/blob/main/README.md)
- [NextGen Research Datastream: How to Contribute to Improving NextGen Forecasts](https://github.com/CIROH-UA/Conferences/blob/main/CIROHDevCon2025/ResearchDataStream_workshop.md) ( [Slides](https://github.com/CIROH-UA/Conferences/blob/main/CIROHDevCon2025/ResearchDataStream_presentation.pdf))
- [Working with HydroShare, AORC data, HydroFabric and NextGen on CIROH JupyterHub](https://www.hydroshare.org/resource/fc8539358fe64ca6a47468728a0687a1/)

### CIROH-2i2c JupyterHub: New NextGen National Water Model Image

🚀 The NextGen In A Box ecosystem is now available for use on CIROH-2i2c JupyterHub! Select the "NextGen National Water Model (NWM)" image to get started.

[Read more...](https://ciroh.awi.2i2c.cloud/)

* * *

## April 2025 Updates

### New NGIAB-Calibration Feature🎉

⚙️ Major update to NextGen In A Box! It now supports extended calibration for CFE and NOAA OWP modules. The new calibration framework provides more flexible parameter tuning and improved model performance.

👨‍💻 Uses ngen-cal branch: [https://github.com/CIROH-UA/ngen-cal/tree/ngiab_cal](https://github.com/CIROH-UA/ngen-cal/tree/ngiab_cal)

📖 For detailed instructions on how to use the new calibration capabilities, please check out: [https://github.com/CIROH-UA/ngen-cal/tree/ngiab_cal#how-to-use-this](https://github.com/CIROH-UA/ngen-cal/tree/ngiab_cal#how-to-use-this)

![A snaphot of the NGIAB CLI's "guide.sh" script.](https://docs.ciroh.org/img/news/April-2025-ngiab-cli.png)

[Read more...](https://github.com/CIROH-UA/ngiab_cal)

### New NextGen In A Box Product Website

🎉 We're excited to announce the launch of our new NGIAB dedicated website! Visit our NGIAB webiste at [https://ngiab.ciroh.org/](https://ngiab.ciroh.org/) to explore all NGIAB tools, documentation, and resources all in one place.

![NGIAB Website Image](https://docs.ciroh.org/img/news/April-2025-ngiab-website.png)

[Read more...](https://ngiab.ciroh.org/)

### NGIAB 101 Training Module Now Available

📚 The new NGIAB 101 training module is now available with comprehensive documentation, installation guides, and step-by-step instructions for the complete NGIAB end-to-end workflow. It is perfect for new users and those looking to deepen their understanding of the platform.

![NGIAB 101 Image](https://docs.ciroh.org/img/news/April-2025-ngiab-101.png)

[Read more...](https://docs.ciroh.org/training-NGIAB-101)

### Datastream Visualization: NGIAB-client (Visualizer) v0.1.3 released

🚀 The visualizer now includes DataStream S3 bucket visualization, which allows users to download data from DataStream S3 bucket and visualize data directly. The new update improves time series data handling, fixes some graph display issues and ensures proper datastream-ensemble associations.

![Datastream Visualization](https://docs.ciroh.org/img/news/April-2025-datastream-vis.png)

[Read more...](https://github.com/CIROH-UA/ngiab-client/commits/main/?since=2025-04-01&until=2025-04-30)

### NGIAB-CloudInfra: New and improved shell scripts

✨ The shell scripts in NGIAB have gotten a new look! The entire NGIAB workflow has been polished for a clean, intuitive experience.

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra/commits/main/?since=2025-04-01&until=2025-04-30)

* * *

## March 2025 Updates

### NGIAB-data-preprocess

#### 🚀 New Release v4.0.5!

This month's update focuses on speed and reliability! We've improved initial setup times by switching to `boto3` for slightly faster S3 hydrofabric downloads. Plus, we've resolved map display issues by updating our JavaScript dependencies.

🔥A new image of NGIAB-data-preprocess is now available in the [CIROH 2i2c JupyterHub](https://ciroh.awi.2i2c.cloud/hub/login) production environment.

![NGIAB-Preprocess Image](https://docs.ciroh.org/img/news/March-2025-ngiab-preprocess-jupyterhub-image.png)

[Read more...](https://github.com/CIROH-UA/NGIAB_data_preprocess/commits/main/?since=2025-03-01&until=2025-04-02)

### NGIAB-CloudInfra: NGIAB Docker Image

#### ⚡New Release v1.4.3!

New calibrated dataset added for Provo River near Woodland, UT AWI_16_10154200_009.tar.gz in README at the link below. Also available in HydroShare!!!

The new script - runTeehr.sh now available to run NGIAB-TEEHR Evaluation on both ARM64 and AMD64 platforms.

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra/blob/main/README.md)

### Updated Community NextGen Documentation Page

📢 We've new updates under Community NextGen products tab. 📚 This comprehensive resource includes an overview of NGIAB and its extensions.

- 🔍 Learn more about Data Preprocess, TEEHR Evaluation, Data Visualizer, and DataStreamCLI.

- 🛠️ Key features, Capabilities and Access Method are included.


🔗 Visit the new Community Hydrologic Modeling Framework documentation page [here](https://docs.ciroh.org/docs/products/ngiab/):

[Read more...](https://docs.ciroh.org/docs/products/ngiab/)

### ngen-datastream

✨ Added CIROH Community Hydrofabric Testing! Automated CI tests are added for each VPU to ensure the geopackage is compatible with DataStreamCLI, NextGen and NGIAB.

[Read more...](https://github.com/CIROH-UA/ngen-datastream/commits/main/?since=2025-03-01&until=2025-04-02)

### NGIAB-HPCInfra: NGIAB Singularity Image for HPC!

✨ March updates include 2 PRs:

- New calibrated dataset added for Provo River near Woodland, UT AWI_16_10154200_009.tar.gz in README at the link below.
- Synced the NGIAB HPC singularity image with the latest features from NGIAB docker image .

[Read more...](https://github.com/CIROH-UA/NGIAB-HPCInfra/commits/main/?since=2025-03-01&until=2025-04-02)

### Community FIM Documentation on DocuHub

📢 Both FIM as a service (FIMserv) and FIM Evaluation Framework (FIMPEF) documentation now available on DocuHub!! Go to Products tab -> Community Flood Inundation Mapping

[Read more...](https://docs.ciroh.org/docs/products/Community%20Flood%20Inundation%20Mapping/FIM%20as%20a%20Service/)

### CIROH Portal New Look!!

📢 BYU Team released newer version of CIROH Portal using docusaurus framework. This brings consistency with CIROH DocuHub!

[Read more...](https://portal.ciroh.org/)

### DocuHub Contribute page Updated

📢 For more ways to contribute to DocuHub. Read below

[Read more...](https://docs.ciroh.org/docs/contribute)

* * *

## February 2025 Updates

### NGIAB-data-preprocess

🚀 New Release v4.0.3! February brings exciting enhancements to our data preprocessing tool! We've now integrated AORC as an additional data source option for forcings. The codebase has been thoroughly refactored to simplify future integration of new gridded data sources. This architectural improvement makes the tool more extensible and easier to maintain going forward.

[Read more...](https://github.com/CIROH-UA/NGIAB_data_preprocess/commits/main/?since=2025-01-01&until=2025-02-28)

### NGIAB-CloudInfra: NGIAB Docker Image

🔥 New Release v1.4.2! Our February update delivers significant improvements to the NGIAB Docker image! The container now incorporates the latest code from CIROH-UA/ngen:ngiab and CIROH-UA/t-route:ngiab branches. We've updated CFE and Noah-OWP-Modular to their latest versions, removed the GDAL dependency to streamline the image, and implemented remoteless partitioning for enhanced parallel performance.

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra/commits/main/?since=2025-01-01&until=2025-02-28)

### ngen-datastream

✨ Community Research Tools Now Public! The terraform configurations and executions for the community Research Datastream in AWS are now publicly available in the ngen-datastream repository (path: research_datastream/terraform_community). We've also added an interactive text-based graphical interface script to guide new users through the Datastream CLI tool (path: scripts/datastream_guide), making the onboarding experience more intuitive.

[Read more...](https://github.com/CIROH-UA/ngen-datastream/commits/main/?since=2025-01-01&until=2025-02-28)

### NGIAB-HPCInfra: NGIAB Singularity Image

⚡ Critical HPC Fix Deployed! The NGIAB Singularity Image now leverages the latest code from CIROH-UA/ngen:ngiab and CIROH-UA/t-route:ngiab branches. A critical pull request was merged to resolve the 'srun permission denied' issue on HPC compute nodes by transitioning to OpenMPI. This fix has been successfully validated on both the Pantarhei and Anvil clusters, ensuring smooth operation in HPC environments.

[Read more...](https://github.com/CIROH-UA/NGIAB-HPCInfra/commits/main/?since=2025-01-01&until=2025-02-28)

### CIROH-UA/ngen:ngiab

✨ Performance Optimization Update! The NGIAB-CloudInfra and NGIAB-HPCInfra containers now utilize our optimized ngiab branch of CIROH-UA/ngen. T-route performance has been significantly enhanced for parallel execution with an alternative partitioning scheme specifically optimized for single-machine parallel runs. Additionally, we've introduced new configuration options that allow users to disable netCDF forcing caching and catchment output writing for more flexible deployment scenarios.

[Read more...](https://github.com/CIROH-UA/ngen/commits/ngiab/?since=2025-01-01&until=2025-02-28)

### CIROH-UA/t-route:ngiab

✨ 3x Faster Performance! The NGIAB-CloudInfra and NGIAB-HPCInfra containers now incorporate our optimized ngiab branch of CIROH-UA/t-route. We've drastically improved t-route output writing efficiency, resulting in approximately three times faster performance. This enhancement significantly reduces processing time for hydrological simulations.

[Read more...](https://github.com/CIROH-UA/t-route/commits/ngiab/?since=2025-01-01&until=2025-02-28)

* * *

## December 2024 Updates

### NGIAB-data-preprocess

Pro Tip: The data-preprocess tool offers VPU subsetting capabilities and can generate configuration files for empirical models like the 'Demonstration LSTM'. Check out these and other new features in the latest release! Discover more updates here.

[Read more...](https://github.com/CIROH-UA/NGIAB_data_preprocess/commits/main/?since=2024-12-01&until=2024-12-20)

### NGIAB-CloudInfra: NGIAB Docker Image

Version 1.4.0 is now available! This release introduces the "demonstration LSTM" within NGIAB, along with sample AWI-008 input data. The LSTM model serves as an educational example to help users get started, though it's not optimized for maximum prediction accuracy." Explore more updates here.

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra/releases/tag/v1.4.0)

### ngen-datastream

Important Update: Datastream has been upgraded to v2.2 hydrofabric and now generates both NextGen outputs and forcings for VPUs 02, 03W, and 16. For more details, visit the Datastream portal at https://datastream.ciroh.org/index.html

[Read more...](https://github.com/CIROH-UA/ngen-datastream/blob/main/docs/AGU_2024_Poster_FINAL.jpg)

### NGIAB-HPCInfra: NGIAB Singularity Image

December updates include 4 PRs adding 'Demostration LSTM' in NGIAB-HPCInfra. Learn more about the updates here.

[Read more...](https://github.com/CIROH-UA/NGIAB-HPCInfra/commits/main/?since=2024-12-01&until=2024-12-20)

### NWM BigQuery API Update

Access NWM streamflow prediction data directly through BigQuery instead of downloading netCDF files. Learn more about this efficient data access method in our documentation here:

[Read more...](https://docs.ciroh.org/docs/products/data-management/bigquery-api/)

* * *

## November 2024 Updates

### NGIAB-CloudInfra: NGIAB Docker Image

Release v1.3.0 has been released with several significant improvements: * Integration of forked ngen and t-route repositories from CIROH-UA's GitHub. * Updated sample input data based on hydrofabric v2.2 * 15 PRs merged * TEEHR integration * CI pipeline improvements with unified Dockerfile * Enhanced NGIAB Visualizer. Explore more updates here.

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra/releases/tag/v1.3.0)

### NGIAB-HPCInfra: NGIAB Singularity Image

November updates include: * 4 PRs updating singularity image to use CIROH-UA repositories * Updated README with new sample input data for hydrofabric v2.2 * Alignment with Docker image modifications

[Read more...](https://github.com/CIROH-UA/NGIAB-HPCInfra/commits/main/?since=2024-11-01&until=2024-11-25)

### ngen-datastream

22 new commits pushed to the main repository

[Read more...](https://github.com/CIROH-UA/ngen-datastream/commits/main/?since=2024-11-01&until=2024-11-25)

### NGIAB-data-preprocess

Version 3.1.2 released featuring: * 7 PRs merged * Major update for compatibility with hydrofabric v2.2. Discover more updates here.

[Read more...](https://github.com/CIROH-UA/NGIAB_data_preprocess/commits/main/?since=2024-11-01&until=2024-11-25)

### Hydrofabric v2.2

The latest Hydrofabric v2.2 data model is now available.

[Read more...](https://lynker-spatial.s3-us-west-2.amazonaws.com/hydrofabric/v2.2/hfv2.2-data_model.html)

### NextGen Model Framework (CIROH-UA/ngen) - fork of NOAA-OWP/ngen

NGIAB-CloudInfra and NGIAB-HPCInfra now utilize the main branch of CIROH-UA/ngen.

[Read more...](https://github.com/CIROH-UA/ngen)

### T-route (CIROH-UA/t-route) - fork of NOAA-OWP/t-route

NGIAB-CloudInfra and NGIAB-HPCInfra now utilize the datastream branch of CIROH-UA/t-route. Main branch is in sync with NOAA-OWP/t-route

[Read more...](https://github.com/CIROH-UA/t-route)

* * *

## September 2024 Updates

### Best Practice Guide for NextGen Framework

Technical guidance for the inclusion of models/modules in the NextGen Water Resources Modeling Framework is now available in DocuHub.

[Read more...](https://docs.ciroh.org/docs/policies/NextGen/)

### NextGen Model Framework (NOAA-OWP/ngen)

2 PRs merged in September. Explore more updates here.

[Read more...](https://github.com/NOAA-OWP/ngen/commits/master/?since=2024-09-01&until=2024-09-26)

### T-route (NOAA-OWP/t-route)

4 PRs were merged in September.

[Read more...](https://github.com/NOAA-OWP/t-route/commits/master/?since=2024-09-01&until=2024-09-26)

### NextGen Community Office Hours

We are excited to invite you to join our NextGen Community Office Hours. It is an excellent opportunity for everyone to stay up to date with the latest developments in hydrologic modeling at CIROH. Join us to engage with the team and learn more about ongoing projects and advancements.

[Read more...](https://docs.ciroh.org/docs/products/ngiab/office-hours)

### NGIAB-CloudInfra : NGIAB Docker Image

We are happy to announce that NGIAB version 1.2.1 has been released, available for both ARM and x86 architectures. This release is up to date with the latest ngen commit ID: f321889 and t-route commit ID: d0982a5. Learn more about the updates here.

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra/releases/tag/v1.2.1)

### ngen-datastream

In September, 10 pull requests were merged.

[Read more...](https://github.com/CIROH-UA/ngen-datastream/commits/main/?since=2024-09-01&until=2024-09-26)

### NGIAB-data-preprocess

5 PRs were merged in September.

[Read more...](https://github.com/CIROH-UA/NGIAB_data_preprocess/commits/main/?since=2024-09-01&until=2024-09-26)

* * *

## August 2024 Updates

### NextGen Model Framework (NOAA-OWP/ngen)

Five PRs merged in August. Explore more updates here.

[Read more...](https://github.com/NOAA-OWP/ngen/commits/master/?since=2024-08-01&until=2024-08-29)

### T-route (NOAA-OWP/t-route)

Eight PRs were merged in August.

[Read more...](https://github.com/NOAA-OWP/t-route/commits/master/?since=2024-08-01&until=2024-08-29)

### NGIAB-CloudInfra : NGIAB Docker Image

NGIAB version 1.2.0 has been released, available for both ARM and X86 architectures. This release is up to date with the latest ngen commit ID: 2ffedf8 and t-route commit ID: 9d9d711

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra/commits/main/?since=2024-08-01&until=2024-08-29)

### NGIAB-HPCInfra: NGIAB Singularity Image

In August, a new Singularity image was released for NGIAB-HPCInfra. Learn more about the updates here.

[Read more...](https://github.com/CIROH-UA/NGIAB-HPCInfra/commits/main/?since=2024-08-01&until=2024-08-29)

### ngen-datastream

In August, nine pull requests were merged. These include the addition of the forcingprocessor feature, increased test coverage, updates to the research datastream Terraform, and new documentation.

[Read more...](https://github.com/CIROH-UA/ngen-datastream/commits/main/?since=2024-08-01&until=2024-08-29)

### NGIAB-data-preprocess

Five PRs were merged in August. We are excited to announce the new release v2.0.0! This release uses catchment ids in place of waterbody ids.

[Read more...](https://github.com/CIROH-UA/NGIAB_data_preprocess/commits/main/?since=2024-08-01&until=2024-08-29)

* * *

## July 2024 Updates

### NextGen Model Framework (ngen)

Four PRs merged in July. Explore more updates here.

[Read more...](https://github.com/NOAA-OWP/ngen)

### NGIAB-CloudInfra

In July, one PR was merged. We are preparing to present "Advancing Hydrological Modeling: CIROH's NextGen In A Box (NGIAB) and Enhanced Tools for Community-Driven Research" at AGU24. You can find more updates here.

[Read more...](https://agu.confex.com/agu/agu24/prelim.cgi/Paper/1697622)

### ngen-DataStream

In July, 6 PRs were merged. We are also presenting "NextGen National Water Model Framework Datastream" paper at AGU24. More updates can be found here.

[Read more...](https://agu.confex.com/agu/agu24/prelim.cgi/Paper/1589746)

### NGIAB-data-preprocessor

Nine PRs were merged in July.

[Read more...](https://github.com/AlabamaWaterInstitute/NGIAB_data_preprocess)

### T-route

Five PRs were merged in July.

[Read more...](https://github.com/NOAA-OWP/t-route)

* * *

## June 2024 Updates

### ngen-DataStream

In June, 9 PRs were merged. Ngen-datastream was updated to be compatible with the new hydrofabric data format provided by hfsubset version 2.1.1.

[Read more...](https://github.com/CIROH-UA/ngen-datastream)

### NGIAB-data-preprocessor

Four PRs were merged in June. We are happy to announce the new release v1.0.1. This release includes various improvements and bug fixes.

[Read more...](https://github.com/AlabamaWaterInstitute/NGIAB_data_preprocess)

### NextGen Model Framework (ngen)

Eleven PRs merged in June. Explore more updates here.

[Read more...](https://github.com/NOAA-OWP/ngen)

### CIROH DevCon24 Conference Slides

Access the slides from the 8 NextGen Track workshops held at CIROH DevCon24. Slides can be found here.

[Read more...](https://hydroshare.org/resource/99a1bdcc97af4d159f1116e2573a12ba/)

* * *

## May 2024 Updates

### NGIAB-CloudInfra

The NextGen In A Box (NGIAB) workshop last week at CIROH DevCon24 was a huge success. New sample dataset is created "AWI-006". We had 50+ attendees and most of them were successfully able to run NGIAB on their local machine. For those without the admin access, we provided them the AWS instances for the workshop. This workshop introduced a new geospatial visualization tool for visualizing outputs from NGIAB runs. During May, 16 PRs were merged. Slides can be found at:

[Read more...](https://github.com/CIROH-UA/Conferences/tree/main/CIROHDevCon2024/NextGenTrack)

### NGIAB-HPCInfra

Run NGIAB on HPC using NGIAB-HPCInfra. This repo is upgraded to use AWI-006 dataset. For more details, please refer README at

[Read more...](https://github.com/CIROH-UA/NGIAB-HPCInfra)

### ngen-DataStream

NextGen Simulation Development Tools workshop was a huge success. It provided attendees with a hands-on experience using the ngen-datastream tool. In May, 21 PRs were merged. Explore the updates. Slides for the DevCon can be found at:

[Read more...](https://github.com/CIROH-UA/ngen-datastream)

### NGIAB-data-preprocessor

The NextGen Simulation Development Tools workshop at CIROH DevCon24 showcased the tool's capabilites of simplifying data preparation for next-gen simulations.

[Read more...](https://github.com/AlabamaWaterInstitute/NGIAB_data_preprocess)

### NextGen Model Framework (ngen)

3 PRs merged in May. Explore more updates here.

[Read more...](https://github.com/NOAA-OWP/ngen)

* * *

## April 2024 Updates

### NGIAB-data-preprocessor

Introducing a tool for NGIAB data preparation. A workshop is planned for CIROH DevCon24 under NextGen Simulation Development Tools.

[Read more...](https://github.com/AlabamaWaterInstitute/NGIAB_data_preprocess)

### NGIAB-CloudInfra

In April, we are gearing up to present the NextGen In A Box (NGIAB) workshop at CIROH DevCon24

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra)

### NGIAB-HPCInfra

Here is the updated link to NGIAB-HPCInfra

[Read more...](https://github.com/CIROH-UA/NGIAB-HPCInfra)

### ngen-DataStream

In April, we are getting ready to present NextGen DataStream at CIROH DevCon24. A workshop is planned under NextGen Simulation Development Tools

[Read more...](https://github.com/CIROH-UA/ngen-datastream)

### NextGen Model Framework (ngen)

Thirteen PRs merged in April. Explore the updates.

[Read more...](https://github.com/NOAA-OWP/ngen)

* * *

## March 2024 Updates

### Improvement of NGIAB HPCInfra Repositories

Automating build of NGIAB HPCInfra using GitHub Actions

[Read more...](https://github.com/CIROH-UA/NGIAB-HPCInfra)

### ngen-DataStream

In March, the python internal to the datastream was containerized. This included implementing catchment-specific configuration for PET, CFE, and Noah OWP (https://github.com/CIROH-UA/ngen-datastream/pull/46). The scripts and plotting tools were developed to perform benchmarking and preliminary results have been collected.

[Read more...](https://github.com/CIROH-UA/ngen-datastream)

### NextGen Model Framework (ngen)

Seven PRs merged in March.

[Read more...](https://github.com/NOAA-OWP/ngen)

* * *

## Feb 2024 Updates

### Improvement of NGIAB CI Pipeline for Pull Requests from Forked Repositories

Three pull requests have been successfully merged. Pull requests submitted using forked repositories are now automatically tested in the CI Pipeline. Upon merging changes to the main repository, another CI pipeline is triggered to retest the build and push the image to DockerHub. Additionally, new AWI_004 sample data is now available for 09 VPU for unit testing.

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra)

### ngen-DataStream

In February, two pull requests were merged. For small runs, you can access ngen-DataStream at: https://github.com/CIROH-UA/ngen-datastream/tree/main/examples

[Read more...](https://github.com/CIROH-UA/ngen-datastream)

### NextGen Model Framework (ngen)

Nine PRs merged in February.

[Read more...](https://github.com/NOAA-OWP/ngen)

### T-route

Twelve PRs merged in February.

[Read more...](https://github.com/NOAA-OWP/t-route)

* * *

## Jan 2024 Updates

### Run NextGen In A Box(NGIAB) with Singularity on HPC without docker support!!!

If you want to use NGIAB on HPC that does not support docker, we have a solution for you. Please follow the steps at this link.

[Read more...](https://github.com/CIROH-UA/Ngen-Singularity)

### NextGen In A Box (NGIAB)

We have made some improvements to NGIAB: 10 PRs merged. Sample input data updated to use AWI_003(with new data provider names). Boost upgraded to v1.79. Self-hosted Runner can start and stop automatically with GitHub Actions. NGIAB image can run in auto mode. Geopackage support added. Documentation available at CIROH DocuHub

[Read more...](https://docs.ciroh.org/docs/products/ngiab/distributions/ngiab-docker)

### ngen-DataStream

3 PRs merged in January. Documentation available at: /products/Hydrologic%20Modeling%20Framework/nextgenDatastream/

[Read more...](https://github.com/CIROH-UA/ngen-datastream)

### NextGen Model Framework (ngen)

6 PRs merged in January.

[Read more...](https://github.com/NOAA-OWP/ngen)

### T-route

3 PRs merged in January.

[Read more...](https://github.com/NOAA-OWP/t-route)

* * *

## Dec 2023 Updates

### NGIAB presentation at AGU!!!

NextGen In A Box: Advancing Collaborative Modeling for Enhanced Water Resource Management presented by Arpita. We had a full house!

[Read more...](https://docs.ciroh.org/news/Conference%20Material#agu-2023)

### NextGen In A Box

NGIAB Updates: Merged CI pipeline changes PR#74 by Benjamin Lee, Added case study map and a plot with output results PR#72 by Shahab Alam, PR#70 by Josh Cu

### NextGen Model Framework

5 PRs merged in December.

### T-route

12 PRs merged in December.

### Hydrofabric

Lynker is proud to support CIROH with a freely accessable resource for geospatial data: https://www.lynker-spatial.com/. Updated transects/cross section runners

### NextGen Framework Forcings

December updates include an (almost) complete stream script that will produce daily ngen outputs. Documentation (readme) included. ngen-datastream/subsetting has been deprecated and hfsubset integrated into the stream. Benchmarking has begun.

### Community Support

December is always an AGU Month! San Francisco (the traditional home of AGU) brings us to the season where we reflect on our own work for the year and finally learn what our coworkers have been doing all this time! Checkout the presentation slides from CIROH at below link.

[Read more...](https://github.com/CIROH-UA/Conferences)

### NOAA-OWP AGU Presentations

NOAA-OWP AGU Presentations

[Read more...](https://github.com/NOAA-OWP/OWP-Presentations/tree/main/AGU/AGU_2023)

* * *

## Nov 2023 Updates

### NGIAB Updates

NGIAB v1.1.0 Release!

[Read more...](https://github.com/CIROH-UA/NGIAB-CloudInfra/releases/tag/v1.1.0)

### NextGen Research Lightning Talk

Presented at CIROH NextGen Research Lightning Talk Webinar

[Read more...](https://docs.ciroh.org/news/Conference%20Material#community-nextgen-advancement-lightning-talk---nov-2023)

### NextGen Model Framework

14 PRs merged in November. Adding new tests for sqlite and new geopackage-based hydrofabric support.

### T-route

13 PRs merged in November. Added additional json/geojson support

### Hydrofabric

Lynker is proud to support CIROH with a freely accessable resource for geospatial data: https://www.lynker-spatial.com/. Updated hfsubset to support using the v2.0 hydrofabric by default. Added Cross-section support to the hydrofabric. 13 PRs merged in November. Added additional json/geojson support

### NextGen Framework Forcings

14 PRs merged towards the Research Data Stream. Fixed lingering pyarrow issues. Added new support for all segments to be dockerized. Added S3 support with regards to the control flow design, to support one reusable, configurable sequence

### Community Support

Singularity support is coming to AWI for HPC users that are able to run Singularity builds. Work on serialization (passing from one run to the next with model states still in memory or imported from a file) is ongoing, relative temporal configurations of NextGen with consideration to model configuration changes between timesteps, and better general support for framework polymorphism.

* * *

## Oct 2023 Updates

### NGIAB Updates

15 runs of the whole build process, 7 successful, and 2 pending. Over 550 pulls of the container image, number of 'canonical' runs (uploading their metadata and results) is coming in a future version.

### NextGen Model Framework

Updates to SUMMA candidate model, performance improvements for memory usage and spatial domain tooling to decouple the currently used geojson Feature and geometry classes into their own simple features interface. This is an abstract interface, with a coupled Boost.Geometry backend that will be used as the default backend.

### T-route

22 Pull Requests were worked on in October with 11 merged, and a focus on testing and getting the compiling process to be tested and reliable particularly for downstream NGIAB and HPC usage of t-route