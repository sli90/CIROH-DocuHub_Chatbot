---
title: CIROH Blog
source: https://docs.ciroh.org/blog
scraped_date: 2025-01-31
---

![Screenshot of Hydroshare Resource](https://docs.ciroh.org/assets/images/aorc-data-retrieval-hydroshare-8cf1d0e0ef2e88fd3e47058cf2fae473.png)

> _A screenshot of the HydroShare resource page for [Jupyter Notebooks for the Retrieval of AORC Data for Hydrologic Analysis](https://www.hydroshare.org/resource/72ea9726187e43d7b50a624f2acf591f/)._

The Analysis of Record for Calibration (AORC) dataset is recognized as a high-value resource for the CUAHSI and CIROH community.
This dataset is hosted by NOAA via Amazon Web Services (AWS) and is available in two primary formats:
a [latitude-longitude gridded dataset](https://registry.opendata.aws/noaa-nws-aorc/)
and the [National Water Model (NWM) projected dataset, part of the NWM Retrospective archive](https://registry.opendata.aws/nwm-archive/).
To enhance accessibility and illustrate analysis capabilities, we developed four user-friendly Jupyter Notebooks that enable data retrieval for both specific points of interest and spatial domains defined by shapefiles:

- **AORC\_LL\_PointRetrieval.ipynb**: For retrieving and aggregating data from the latitude-longitude gridded dataset for a specific point using geographic coordinates.
- **AORC\_LL\_ZoneRetrieval.ipynb**: For retrieving and aggregating data from the latitude-longitude gridded dataset for an area defined by a polygon shapefile.
- **AORC\_NWMProj\_PointRetrieval.ipynb**: For retrieving and aggregating data from the NWM projected dataset for a specific point using geographic coordinates.
- **AORC\_NWMProj\_ZoneRetrieval.ipynb**: For retrieving and aggregating data from the NWM projected dataset for an area defined by a polygon shapefile.

These Jupyter Notebooks, containing instructions and Python code to access the data, enable researchers to retrieve AORC data from AWS.
From there, the notebooks offer options to subset and aggregate the data over user-defined time intervals (beyond the original hourly resolution) and spatial area.
These serve as examples for how you could write or modify code to access AORC data in your work.
The notebooks are publicly [available on HydroShare](https://www.hydroshare.org/resource/72ea9726187e43d7b50a624f2acf591f/)
and are compatible with JupyterHub computing platforms such as [CIROH 2i2c JupyterHub linked to HydroShare](https://www.hydroshare.org/resource/2dd1ac86e8854d4fb9fe5fbafaec2b98/).

To use these notebooks, go to the [HydroShare resource](https://www.hydroshare.org/resource/72ea9726187e43d7b50a624f2acf591f/),
select "Open With" at the top right, and choose "CIROH 2i2c JupyterHub".
This will copy the resource contents (notebooks and data) into the CIROH JupyterHub environment,
where you can open and work through them to access the data.
Note that you will need a [CUAHSI HydroShare account](https://www.hydroshare.org/) to access "Open With" in HydroShare,
and you will also need to [request CIROH-2i2c JupyterHub access](https://docs.ciroh.org/docs/services/access/#accessing-ciroh-2i2c-jupyterhub) using a GitHub account.

Our work also includes a comparative analysis of the two AORC datasets with a summary of findings.
While we mostly observed small differences, mainly due to projections, users should be aware of potential discrepancies between the datasets.

By providing these user-friendly tools and highlighting the characteristics of both AORC datasets,
our work aims to support and facilitate more efficient hydrological and climate-related research within the CUAHSI and CIROH community.

### References:

- Salehabadi, H., D. Tarboton, A. Nassar, A. M. Castronova, P. Dash (2025). Jupyter Notebooks for the Retrieval of AORC Data for Hydrologic Analysis, HydroShare, [http://www.hydroshare.org/resource/72ea9726187e43d7b50a624f2acf591f](http://www.hydroshare.org/resource/72ea9726187e43d7b50a624f2acf591f)
- The development versions of these notebooks are available on GitHub: [https://github.com/CUAHSI/notebooks](https://github.com/CUAHSI/notebooks) in the Data Access Examples / AORC - Retrieval of AORC Data for Hydrologic Analysis folder.
- Patel, A., A. Castronova (2025). CIROH 2i2c JupyterHub, HydroShare, [http://www.hydroshare.org/resource/2dd1ac86e8854d4fb9fe5fbafaec2b98](http://www.hydroshare.org/resource/2dd1ac86e8854d4fb9fe5fbafaec2b98)

![A poster, titled &quot;Assessing streamflow forecast over the Hackensack River Watershed using physics- and AI-driven weather prediction models&quot;.](https://docs.ciroh.org/assets/images/blog_CIROH_DevCon-bd5de4e3ca6192611aadd30bb47b1586.png)

> _A poster presented by the I-SMART team at the CIROH Developers Conference, held at the University of Vermont in Burlington from May 28 to 30, 2025._

The densely populated Hackensack River watershed lies within the New York City Metropolitan Area, which spans northern New Jersey and southern New York.
Accurate streamflow forecasting within this region is therefore essential to enable effective water resource management, flood prediction, and disaster preparedness.

Precipitation data is critical for effective hydrological modeling, making the identification of reliable data sources a key priority.
This is why the Integrated Spatial Modeling and Remote Sensing Technologies Laboratory (I-SMART),
an interdisciplinary research unit within the Davidson Laboratory at Stevens Institute of Technology in Hoboken, New Jersey,
uses the latest developments in both atmospheric and hydrological modeling to address flood risks in the Hackensack Watershed
with solutions that could be expanded to the entire New York City Metropolitan Area.

In the past, this work has included key early applications of the Next Generation Water Resources Modeling Framework (NextGen).
Notably, the I-SMART group was among the first to force the NextGen framework with multiple atmospheric models for comparative analysis during a real-world event:
the passage of Superstorm Ida over the New York metropolitan area in September 2021.
The recent advent of NextGen In a Box (NGIAB) has provided an opportunity to accelerate these applications even further
by taking full advantage of NGIAB's containerized, user-friendly, and easily deployed environment.

Recently, the I-SMART team has been testing various regional atmospheric models grounded in physical equations,
including traditional models like WRF and next-generation atmospheric models such as MPAS.
Additionally, given the increasing popularity and adoption of AI/ML-based approaches,
the team has also begun exploring their potential.
The goal of this work is to assess the performance of these approaches in the Hackensack Watershed,
along with investigating the sensitivity of the model to various meteorological forcings, including forcings based on the National Water Model.
_(The initial and/or boundary conditions for all the models were determined using the Global Forecast System.)_

This investigation required handling a large volume of precipitation data from various models,
each with different spatial resolutions and in some cases, such as MPAS, using unstructured grids.
As such, one of the key challenges was finding a hydrological modeling framework flexible enough to accommodate such diversity.
This made the NextGen framework a natural choice, allowing them to integrate precipitation forcings from various sources
with the appropriate pre-processing to align them with the model requirements in terms of spatial and temporal scales.

The complex implementation and execution of these models was faciliated by NextGen In A Box (NGIAB),
which successfully enabled the integration of diverse precipitation sources.
By simplifying local deployment and providing full control over model inputs, configurations, and runtime operations,
NGIAB has given the I-SMART team the tools to conduct their groundbreaking research with even greater efficiency.

The recent DevCon 2025 event showcased not just cutting-edge development practices, but also demonstrated how modern DevOps principles and cloud infrastructure can seamlessly support large-scale technical workshops. Our team had the privilege of providing IT infrastructure and support for over 200 attendees, creating a robust learning environment through an exemplary public-private partnership.

![Image of CIROH&#39;s Research Cyberinfrastructure and DevOps team. On the left, two graphs are shown depicting usage for the Google Cloud-2i2c and Jetstream2 environments.](https://docs.ciroh.org/assets/images/it_team-224ec60c3871a16d47ce478c486fe8c2.png)

> _CIROH's Research Cyberinfrastructure and DevOps team._
>
> _Left to right, top to bottom:_
>
> _Manjila Singh, Arpita Patel, Nia Minor, Trupesh Patel, James Halgren; Benjamin Lee._

Last week, I had the incredible opportunity to co-present a keynote at the CIROH
Developers Conference (DevCon 2025), which attracted over 200 attendees. This
presentation, which I presented alongside Dan Ames, focused on "CIROH HydroInformatics
and Research Cyberinfrastructure." It was a fantastic experience to share insights
into the powerful tools and technologies that CIROH engineers, students, researchers
have been developing to advance hydrological research and operations.

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_7.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_0.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_1.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_2.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_3.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_4.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_5.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_6.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_7.jpeg)

- ![Arpita Patel and Dan Ames presenting their plenary keynote at CIROH DevCon 2025.](https://docs.ciroh.org/img/blog/2025-06-devcon25/keynote_0.jpeg)


![AWI Science and Technology Team @ CIROH DevCon2025](https://docs.ciroh.org/assets/images/DevCon_AWI_Team-c9f08b48601493edf8e47d7478fdcfff.png)

> _CIROH-AWI Science and Technology Team._
>
> _Left to right: Sagy Cohen, Steven Burian, Manjila Singh, Saide Zand, Savalan N. Neisary, Arpita Patel, Nia Minor, Trupesh Patel, Sifan A. Koriche, Jonathan Frame, Reza S. Alipour, Hari T. Jajula, Chad Perry; Josh Cunningham._

May was a pivotal month for representing the [Cooperative Institute for Research to Operations in Hydrology (CIROH)](https://ciroh.ua.edu/) and our collective work in advancing water science. As one of CIROH's Ambassadors, I had the privilege of connecting with the broader scientific community at two key events: the [Environmental and Water Resources Institute (EWRI) Congress](https://www.ewricongress.org/) in Anchorage, Alaska, and the [2025 CIROH Developers Conference](https://ciroh.ua.edu/devconference/2025-ciroh-developers-conference/) in Burlington, Vermont.

![Image of graphical outputs from the δHBV2.0 model](https://docs.ciroh.org/assets/images/img-e699e9df162042eda9a4a1b4a242ffb1.jpg)

Predicting water flow with precision across the vast U.S. landscape is a complex challenge. That's why Song et al. 2024 developed δHBV2.0, a cutting-edge hydrologic model. It's built with high-resolution modeling of physics to deliver seamless, highly accurate streamflow simulations, even down to individual sub-basins. It's already proven to be a major improvement, performing better than older tools at about 4,000 measurement sites. We also provide a comprehensive 40-year water dataset for ~180,000 river reaches to support this.

Penn State research group pushed δHBV2.0 further, training it with even more detailed river data and integrating other trusted models, aiming to make it a key part of the NextGen national water modeling system (as a potential NWM3.0 successor). But here's a common hurdle: making powerful scientific tools like this easy and reliable for everyone to use within a larger framework can be tough. Setup issues, runtime errors, and inconsistent results can frustrate users.

NGIAB stepped in to solve exactly this problem. Team has taken the complexity out of using the operations-ready models within NextGen by creating one unified, reliable package. Thanks to NGIAB, users don't have to worry about tricky setups or whether the model will run correctly. NGIAB ensures that our models are compatible everywhere and, most importantly, that they run exactly as designed, consistently and faithfully, every single time, no babysitting required. This means users get the full power of our advanced modeling, without the headaches.

Last week at Google Cloud Next representing our CIROH cloud-based computing efforts! With more than 30,000 participants, Google Next always amazes me! It's huge, engaging on so many levels! Engaging booths, networking opportunities, great presentations, workshops, AI coach for basketball, incredible keynote from an amazing team! Event was not just a conference, but a celebration of innovation and a glimpse into the future of cloud computing!
Great to see how Gemini is transforming data manipulation in BigQuery. The ability to use natural language to query, transform, and visualize data is revolutionizing how we interact with massive datasets. Gabe Weiss's demo particularly showcased the potential for non-specialists to derive insights from complex data.

If you missed the keynote, I highly recommend watching the recording here: [GCN25 Keynote Video](https://www.youtube.com/live/VABwMpL3JCo?t=3564s)

- ![BigQuery and Earth Engine demo at Google Cloud Next conference](https://docs.ciroh.org/img/blog/2025-04-gcp/gcp-6.jpg)

- ![Arpita Patel at the Google Cloud Next conference](https://docs.ciroh.org/img/blog/2025-04-gcp/gcp-1.jpg)

- ![Title slide from the Google Cloud Next conference](https://docs.ciroh.org/img/blog/2025-04-gcp/gcp-2.jpg)

- ![Slide depicting Google's AI stack](https://docs.ciroh.org/img/blog/2025-04-gcp/gcp-3.jpg)

- ![Slide announcing Gemini for Google Distributed Cloud](https://docs.ciroh.org/img/blog/2025-04-gcp/gcp-4.jpg)

- ![Slide announcing Google Agentspace](https://docs.ciroh.org/img/blog/2025-04-gcp/gcp-5.jpg)

- ![BigQuery and Earth Engine demo at Google Cloud Next conference](https://docs.ciroh.org/img/blog/2025-04-gcp/gcp-6.jpg)

- ![Arpita Patel at the Google Cloud Next conference](https://docs.ciroh.org/img/blog/2025-04-gcp/gcp-1.jpg)


## 🌍 AWI News

The Alabama Water Institute (AWI) at the University of Alabama (UA) recently published an article highlighting how NextGen In A Box (NGIAB) could transform hydrological modeling. This article provides great insight into NGIAB's real-world impact:

- 🚀 **30-minute setup** vs days/weeks of configuration
- 📖 **Provo River Basin Case Study** demonstrating rapid deployment

![ngiab image](https://docs.ciroh.org/img/logos/ngiab.png)

[➡️ Read the full press release here!](https://awi.ua.edu/news/nextgen-in-a-box-ngiab-revolutionizing-hydrological-modeling-with-a-30-minute-setup/)

Pennsylvania State University (PSU) researchers have been leveraging CIROH Cyberinfrastructure to tackle complex hydrological modeling challenges. This post highlights their innovative approach using the [Wukong computing platform](https://docs.ciroh.org/docs/services/on-prem/Wukong/) in conjunction with Amazon S3 bucket storage to efficiently process and analyze large-scale environmental datasets. 🚀

AGU24 brought together the world's leading minds in Earth and space sciences. CIROH participated actively, showcasing advances in water prediction, modeling techniques and many more technologies.

## **Presentations and Posters** 📊

The conference provided an excellent platform for CIROH researchers to present their groundbreaking work. Our team delivered impactful presentations and poster sessions highlighting CIROH's innovative work, including advancements in water prediction systems
and community water modeling.

These sessions sparked thought-provoking discussions and fostered collaborations with other researchers. For those who missed it, **posters and presentation slides are now available** [here](https://github.com/CIROH-UA/Conferences/tree/main/AGU24). Feel free to explore these materials and share your thoughts. 📝

The Community NextGen framework has seen significant advancements in November 2024, with major updates across multiple components and exciting new resources for users. Let's dive into the key developments that are making hydrologic modeling more accessible and powerful than ever.

The 2024 CIROH Science Meeting was a huge success, bringing together researchers, federal partners, and consortium members both in person and virtually. We're excited to share the valuable resources from this year's meeting with the wider CIROH community.

Slides and pictures from the various sessions, keynotes, and the Federal Town Hall have all been uploaded to a shared drive for easy access. You can find links to these materials here: [Access the Shared Drive with Presentation Slides](https://drive.google.com/drive/folders/1NsJEWHQBD92ndc3FD_bFEKgqTUqTxVM3)

![gcp architectrure diagram](https://docs.ciroh.org/img/gcp_architecture_diagram.png)_Image Source: [https://github.com/BYU-Hydroinformatics/api-nwm-gcp](https://github.com/BYU-Hydroinformatics/api-nwm-gcp)_

Several important historical and ongoing National Water Model (NWM) datasets are now available on Google Cloud BigQuery, which makes them queryable through SQL using Google Cloud console. Some of these data sets are also accessible through an API (e.g. using Python). These datasets and their current status are as follows:

|     |     |     |     |     |
| --- | --- | --- | --- | --- |
| Product | Cloud Console SQL | CIROH API | Historical | Daily Updates |
| Medium-range forecasts | X | X | X | X |
| Long-range forecasts | X | X | X | X |
| Analysis and Assimilation | X | X | X | X |
| Retrospective Data (NWM v3) | X |  | X |  |
| Return Periods | X |  | X |  |

This month, we are excited to showcase two case studies that utilized our cyberinfrastructure tools and services. These case studies demonstrate how CIROH's cyberinfrastructure is being utilized to support hydrological research and operational advancements.

## 1\. ngen-datastream and NGIAB

![ngen-datastream image](https://docs.ciroh.org/img/blog/2024-08-case-studies/ngen-datastream-august-blog.jpg)

We're excited to share some recent developments and updates from CIROH's Research CyberInfrastructure team:

### Cloud Infrastructure

- CIROH's Google Cloud Account is now fully operational and managed by our team. You can find more information [here.](https://docs.ciroh.org/docs/services/cloudservices/google-cloud/)
- We're in the process of migrating our 2i2c JupyterHub to CIROH's Google Cloud account.
- We've successfully deployed the Google BigQuery API (developed by BYU and Google) for NWM data in our cloud. To access this API, please contact us at [ciroh-it-admin@ua.edu](mailto:ciroh-it-admin@ua.edu). Please refer to [NWM BigQuery API](https://docs.ciroh.org/docs/products/data-management/bigqeury-api/) to learn more.

**CIROH Developers Conference 2024**

![DevCon2024](https://docs.ciroh.org/img/blog/2024-05-devcon24/devcon24_01.jpeg)

The CIROH team recently participated in the **2nd Annual CIROH Developers Conference (DevCon24)**, held from May 29th to June 1st,2024. The conference brought together a diverse group of water professionals to exchange knowledge and explore cutting-edge research in the field of hydrological forecasting.

**AWRA 2024 Spring Conference**

The **CIROH CyberInfrastructure team** recently participated in the **AWRA 2024 Spring Conference**, co-hosted by **the Alabama Water Institute at the University of Alabama.**

Themed "Water Risk and Resilience: Research and Sustainable Solutions," the conference brought together a diverse group of water professionals to exchange knowledge and explore cutting-edge research in the field.

**Google Cloud Next '24**

Hello everyone, and thanks for stopping by!

I recently had the incredible opportunity to attend Google Cloud Next 2024 in person for the first time, and it was truly an **amazing experience**. From **insightful keynote presentations and workshops to vibrant booths** buzzing with connections, the event was a whirlwind of innovation and inspiration.

**Accelerating Innovation: CIROH's March 2024 Update**

The CIROH team has been diligently accelerating research cyberinfrastructure capabilities this month. We're thrilled to share key milestones achieved in enhancing the Community NextGen project and our cloud/on-premises platforms.

Welcome to the February edition of the CIROH DocuHub blog, where we bring you the latest updates and news about the Community NextGen project and CIROH's Cloud and on-premise Infrastructure.

Our team has been hard at work enhancing CIROH's Infrastructure and Community NextGen tools. Here are some highlights from February 2024:

1. We successfully launched our new On-premises Infrastructure, which is now fully operational. You can find documentation for it [here](https://docs.ciroh.org/docs/services/on-prem/).

Welcome to the January edition of the CIROH DocuHub blog, where we share the latest updates and news about the Community NextGen project monthly. NextGen is a cutting-edge hydrologic modeling framework that aims to advance the science and practice of hydrology and water resources management. In this month's blog, we will highlight some of the recent achievements and developments of the Community NextGen team.

Happy New Year!!! We are back from SFO after attending AGU last month. We are excited to share the latest updates for NGIAB, NextGen, T-route, Hydrofabric, NextGen forcings, and Community Support from December 2023.

[Visit NGIAB News](https://docs.ciroh.org/news)

We've released NGIAB v1.1.0! This release fixes issues:

- [#21](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/21)
- [#67](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/67)
- [#44](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/44)

More info: [https://github.com/CIROH-UA/NGIAB-CloudInfra/releases/tag/v1.1.0](https://github.com/CIROH-UA/NGIAB-CloudInfra/releases/tag/v1.1.0)

[Visit NGIAB News](https://docs.ciroh.org/news)

We are excited to share the latest updates for NGIAB, NextGen, T-route, Hydrofabric, NextGen forcings and Community Support.

[Visit NGIAB News](https://docs.ciroh.org/news)

We've introduced a fresh addition within DocuHub, offering the most up-to-date insights on NGIAB and NextGen monthly updates.

[Visit NGIAB Release Notes Page](https://docs.ciroh.org/news)

## NextGen Framework Forcings

A new [forcing processor](https://github.com/CIROH-UA/ngen-datastream/tree/main/forcingprocessor) tool has been made public. This tool converts any National Water Model based forcing files into ngen forcing files. This process can be an intensive operation in compute, memory, and IO, so this tool facilitates generating ngen input and ultimately makes running ngen more accessible.