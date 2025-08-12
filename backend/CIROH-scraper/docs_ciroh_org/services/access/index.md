---
title: Infrastructure Access
source: https://docs.ciroh.org/docs/services/access
scraped_date: 2025-01-31
---

CIROH provides access to public cloud services, HPC, and on-premises infrastructure to support the research projects of CIROH's members and partners.

* * *

## Selecting a platform

Click the buttons below to open/close their panels.

**What is your primary requirement?**

High Performance Computing

**Which HPC platform are you planning to use?**

Pantarhei HPC

Pantarhei offers CPU, GPU, and FPGA nodes.

[Get started with Pantarhei](https://docs.ciroh.org/docs/services/on-prem/Pantarhei/)

Wukong HPC

Wukong offers CPU and GPU nodes.

[Get started with Wukong](https://docs.ciroh.org/docs/services/on-prem/Wukong/)

* * *

Cloud Computing

**What kind of computing environment are you looking for?**

General Purpose

CIROH provides researchers with access to enterprise-level AWS cloud services.

[CIROH AWS Account info](https://docs.ciroh.org/docs/services/cloudservices/aws/)

Google-Specific Services

CIROH Google VM Link
CIROH provides researchers with access to enterprise-level Google Cloud services.

[CIROH Google Account info](https://docs.ciroh.org/docs/services/cloudservices/google-cloud/)

Interactive Computing Environment

In collaboration with 2i2c, CIROH offers a dedicated JupyterHub environment on Google Cloud specifically designed for hydrological research. Both CPU and GPU options are available.

[CIROH-2i2c JupyterHub info](https://docs.ciroh.org/docs/services/cloudservices/2i2c/)

* * *

Data Storage and Archival

Hydroshare is a collaborative, general-purpose repository for data, models, and other research products.

[HydroShare info](https://docs.ciroh.org/docs/services/cloudservices/HydroShare/)

Additionally, CIROH provides researchers with access to data buckets for use with AWS and Google Cloud services.

[CIROH AWS Account info](https://docs.ciroh.org/docs/services/cloudservices/aws/) [CIROH Google Account info](https://docs.ciroh.org/docs/services/cloudservices/google-cloud/)

* * *

Data-Intensive Computing

CIROH's AWS instance and Google VMs both offer solid options for data-intensive processes.

[CIROH AWS Account info](https://docs.ciroh.org/docs/services/cloudservices/aws/) [CIROH Google Account info](https://docs.ciroh.org/docs/services/cloudservices/google-cloud/)

* * *

## Accessing Public Cloud Services

CIROH has partnered with [**AWS**](https://docs.ciroh.org/docs/services/cloudservices/aws/) and [**Google Cloud**](https://docs.ciroh.org/docs/services/cloudservices/google-cloud/) to provide access to their cloud computing services.

note

If using CIROH-2i2c services, please see the "Accessing CIROH JupyterHub" section below for additional steps.

### Requesting Project Access

PIs or Workshops Lead leading CIROH projects or workshops may use this form to request cloud computing resources on AWS or Google Cloud. Access is available to all consortium members and partners.

1. Submit a GitHub template request detailing your project requirements and specifications.
2. Our team will review your request and assist you in obtaining the necessary access.

[Cloud Infrastructure Request Form](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/new?assignees=&labels=infrastructure&projects=&template=case_studies_call.md&title=)

note

Please refer to [this link](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues?q=is%3Aissue%20is%3Aclosed%20label%3Agoogle%2C%222i2c%20JupyterHub%22%2Caws%20) for references to submitted forms.

CIROH Consortium members or partners are responsible for:

- Management of CIROH subaccounts assigned to them.
- Project-specific software and environment configuration.
- Handling account creation and/or access for project contacts.

### Cost of Use

- Use of CIROH JupyterHub is free for all consortium projects.
- Individual projects are allotted $500 monthly for use of AWS and Google Cloud services.
- CIROH projects that anticipate exceeding the monthly budget for cloud services may request additional funds via the form below.

[Exceeding Budget Request Form](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/new?assignees=&labels=infrastructure&projects=&template=exceeding_budget_request.md&title=)

* * *

## Accessing CIROH-2i2c JupyterHub

In partnership with [**2i2c**](https://2i2c.org/), CIROH provides [**JupyterHub**](https://docs.ciroh.org/docs/services/cloudservices/2i2c) with both CPU and GPU capabilities.

### Requesting Project Access

PIs or Workshop Leads leading CIROH projects or workshops may use this form to request cloud computing resources (CIROH-2i2c JupyterHub). Access is available to all consortium members and partners.

1. Submit a GitHub template request detailing your project requirements and specifications.
2. Our team will review your request and assist you in obtaining the necessary access.

[Cloud Infrastructure Request Form](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/new?assignees=&labels=infrastructure&projects=&template=case_studies_call.md&title=)

### Requesting Individual Access

Submit one of the following forms to get access to CIROH JupyterHub environments:

[CIROH-2i2c JupyterHub CPU Access Request Form](https://forms.office.com/Pages/ResponsePage.aspx?id=jnIAKtDwtECk6M5DPz-8p4IIpHdEnmhNgjOa9FjrwGtUNUoyV1UxNFIzV1AyTDhTNzdOT1Q5NVlLTC4u) [CIROH-2i2c JupyterHub GPU Access Request Form](https://forms.office.com/r/mkrVJzyg9u)

note

You will need to submit your GitHub username for this request.
If you do not currently have a GitHub account, follow the instructions at [GitHub](https://docs.github.com/en/get-started/start-your-journey/creating-an-account-on-github).

### Requesting Custom Images

To request custom images:

1. Create an `environment.yml` file by exporting your conda environment.
2. Fill out the CIROH-2i2c JupyterHub Software Install form.

[CIROH-2i2c JupyterHub Software Install Form](https://forms.office.com/Pages/ResponsePage.aspx?id=jnIAKtDwtECk6M5DPz-8p4IIpHdEnmhNgjOa9FjrwGtUNUoyV1UxNFIzV1AyTDhTNzdOT1Q5NVlLTC4u)

* * *

## Accessing On-Premises Infrastructure

CIROH operates an on-premises infrastructure that includes high-performance computing (HPC) resources and specialized software via the [**Pantarhei**](https://docs.ciroh.org/docs/services/on-prem/Pantarhei/) and [**Wukong**](https://docs.ciroh.org/docs/services/on-prem/Wukong/) systems.

### Requesting Project Access

Principle Investigators (PIs) leading CIROH projects may use this form to request CIROH on-premise resources for their teams, including Pantarhei and Wukong. Access is available to all consortium members and partners.

1. Submit a GitHub template request detailing your project requirements and specifications.
2. Our team will review your request and assist you in obtaining the necessary access.

> **Note**: The On-Premises Infrastructure Request Form must be submitted by the PI of the project.

[On-premises Infrastructure Request Form](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/new?assignees=&labels=on-prem&projects=&template=onprem-request.md&title=)

### Requesting Individual Access

> **Note**: Before requesting individual access, the On-Premises Infrastructure Request Form above **must** be completed by your PI.

Non-UA users should complete the VPN Access Request section of the form below before proceeding.

From there, please complete the On-Premise Access Request section of the form below to request individual access to Pantarhei or Wukong.

[On-Premise Access Request Form](https://forms.office.com/Pages/ResponsePage.aspx?id=jnIAKtDwtECk6M5DPz-8p4IIpHdEnmhNgjOa9FjrwGtUMzdTOUpKVU5UWFNCU0ZQUlowS0cxV0xFRy4u)

* * *

## Accessing JetStream2 through CIROH

In collaboration with [NSF Access](https://docs.ciroh.org/docs/services/external-resources/nsf-access/), CIROH offers access to an allocation on the [JetStream2](https://docs.ciroh.org/docs/services/external-resources/nsf-access/jetstream) computing platform.

**Step 1:** The PI for your project must submit the Infrastructure Request Form below to request team-wide access to JetStream2.

[Infrastructure Request Form](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/new?assignees=&labels=on-prem&projects=&template=onprem-request.md&title=)

**Step 2:** If you don't already have an NSF Access account, register for one using the link below.

[NSF Access New User Registration](https://operations.access-ci.org/identity/new-user)

**Step 3:** Using your NSF Access ID, submit the JetStream2 Access Request form for individual user accounts on JetStream2.

[JetStream2 Access Request Form](https://forms.office.com/r/ERyKyHbdaC)

info

If you are unable to access the JetStream2 forms, please contact the CIROH team at [ciroh-it-admin@ua.edu](mailto:ciroh-it-admin@ua.edu) for assistance.

Once you're granted access, you're ready to begin using JetStream2! Visit the [logging in to JetStream2 page](https://docs.jetstream-cloud.org/getting-started/login/) to get started.

* * *

## Accessing NWM BigQuery API

To access CIROH's [**NWM BigQuery API**](https://docs.ciroh.org/docs/products/data-management/bigquery-api/), please submit the form below.

[NWM BigQuery API Access Request Form](https://forms.office.com/r/FeNpjZstkr)

* * *

## Requesting Infrastructure Support for Conferences and Programs

CIROH Project Leads can request computing resources for workshops using this process. Available infrastructure includes NSF Access VMs, CIROH-2i2c JupyterHub, AWS, and Google Cloud - accessible to all consortium members and partners.

1. Complete our GitHub template with your workshop's technical requirements.
2. Our team will process your request and ensure participants have necessary access before your workshop begins.

[Workshop IT Request Form](https://github.com/CIROH-UA/NGIAB-CloudInfra/issues/new?assignees=&projects=&template=workshop_IT_request.md)

- [Selecting a platform](https://docs.ciroh.org/docs/services/access/#selecting-a-platform)
- [Accessing Public Cloud Services](https://docs.ciroh.org/docs/services/access/#accessing-public-cloud-services)
  - [Requesting Project Access](https://docs.ciroh.org/docs/services/access/#requesting-project-access)
  - [Cost of Use](https://docs.ciroh.org/docs/services/access/#cost-of-use)
- [Accessing CIROH-2i2c JupyterHub](https://docs.ciroh.org/docs/services/access/#accessing-ciroh-2i2c-jupyterhub)
  - [Requesting Project Access](https://docs.ciroh.org/docs/services/access/#requesting-project-access-1)
  - [Requesting Individual Access](https://docs.ciroh.org/docs/services/access/#requesting-individual-access)
  - [Requesting Custom Images](https://docs.ciroh.org/docs/services/access/#requesting-custom-images)
- [Accessing On-Premises Infrastructure](https://docs.ciroh.org/docs/services/access/#accessing-on-premises-infrastructure)
  - [Requesting Project Access](https://docs.ciroh.org/docs/services/access/#requesting-project-access-2)
  - [Requesting Individual Access](https://docs.ciroh.org/docs/services/access/#requesting-individual-access-1)
- [Accessing JetStream2 through CIROH](https://docs.ciroh.org/docs/services/access/#accessing-jetstream2-through-ciroh)
- [Accessing NWM BigQuery API](https://docs.ciroh.org/docs/services/access/#accessing-nwm-bigquery-api)
- [Requesting Infrastructure Support for Conferences and Programs](https://docs.ciroh.org/docs/services/access/#requesting-infrastructure-support-for-conferences-and-programs)