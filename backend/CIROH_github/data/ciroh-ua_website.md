# Project Title: **ciroh-ua_website**

## Project Objective  
The **CIROH DocuHub** serves as a centralized documentation and communication portal for CIROH projects, built using [Docusaurus](https://docusaurus.io/).  
It provides a structured platform to host technical documentation, blog content, and product information related to CIROH and its NextGen initiatives.  
The project aims to enhance collaboration, transparency, and accessibility across CIROH’s distributed teams and contributors.

## Core Functionalities  
- **Static site generation:** Built using Docusaurus for efficient, responsive documentation websites.  
- **Multi-environment deployment:**  
  - **Production:** [https://docs.ciroh.org/](https://docs.ciroh.org/)  
  - **Staging:** [https://docs.ciroh.org/docuhub-staging/](https://docs.ciroh.org/docuhub-staging/) (for testing and validation).  
- **Contributor workflows:**  
  - Edit content directly via GitHub (“Edit page” button).  
  - Submit pull requests for review and merge.  
  - Contribute to the Products tab by sharing repository links.  
  - Add blog posts following official guidelines.  
- **Local development support:** Step-by-step setup guide for cloning, installing dependencies, and running the development server.  
- **Support channels:** Direct contact via CIROH IT Admin and Arpita Patel for contributor assistance.  

## Technical Stack  
- **Framework:** [Docusaurus](https://docusaurus.io/)  
- **Language:** JavaScript  
- **Runtime:** Node.js (LTS version)  
- **Package Manager:** npm  
- **Hosting:** docs.ciroh.org (production) and docs.ciroh.org/docuhub-staging (staging)  
- **Version Control:** GitHub  
- **Continuous Integration:** GitHub Actions (used for PR validation and local build testing).  

## Setup and Usage  
1. **Clone Repository:**  
   ```bash
   git clone https://github.com/CIROH-UA/ciroh-ua_website.git
   cd ciroh-ua_website
   ```  
2. **Install Node.js (LTS):** Obtain from [nodejs.org](https://nodejs.org/en).  
3. **Install Dependencies:**  
   ```bash
   npm install
   ```  
4. **Run Locally:**  
   ```bash
   npm run start
   ```  
   Opens the local server at http://localhost:3000  
5. **Build for Production (optional):**  
   ```bash
   npm run build
   ```  
   Generates static files in the `build/` directory.  
6. **Validate PR Locally:**  
   Download the build folder from GitHub Actions PR validation, unzip, then run:  
   ```bash
   npx http-server
   ```  

## Project Context & Domain  
- **Domain:** Web development / Documentation management.  
- **Affiliation:** Cooperative Institute for Research to Operations in Hydrology (**CIROH**), hosted by **The University of Alabama**.  
- **Purpose:** Facilitate the sharing and maintenance of CIROH’s documentation, blogs, and project resources through a unified web portal.  

## Input / Output  
**Input:**  
- Markdown-based documentation files, configuration files, and static assets.  

**Output:**  
- A compiled static documentation website served via docs.ciroh.org and its staging environment.  
