# Project Title: **ciroh-portal**

## Project Objective
The **CIROH Portal** is a static website built using **Docusaurus**, designed to serve as a documentation or informational hub. Its main goal is to provide a modern, easily maintainable platform for hosting CIROH-related content and resources. It simplifies content creation, organization, and deployment for developers and contributors maintaining the CIROH ecosystem.

## Core Functionalities  
- Uses **Docusaurus** for generating a modern, responsive static website.  
- Provides **live local development** with hot-reloading for rapid content updates.  
- Supports **automated build and deployment** to GitHub Pages or other static hosting services.  
- Allows **SSH and non-SSH deployment options** for flexibility in publishing.  

## Technical Stack  
- **Language:** JavaScript  
- **Framework:** [Docusaurus](https://docusaurus.io/)  
- **Package Manager:** Yarn  
- **Deployment Options:** GitHub Pages, SSH-based deployment  

## Setup and Usage  
1. **Install dependencies:** Run `yarn`.  
2. **Local development:** Use `yarn start` to launch a development server with live reload.  
3. **Build static site:** Execute `yarn build` to generate static files in the `build` directory.  
4. **Deploy:**  
   - With SSH: `USE_SSH=true yarn deploy`  
   - Without SSH: `GIT_USER=<Your GitHub username> yarn deploy`  

## Project Context & Domain  
- **Domain:** Web development / Documentation portal.  
- **Affiliation:** CIROH (Consortium of Universities for the Advancement of Hydrologic Science, Inc.).  
- **Purpose:** Serve as a centralized online portal for CIROH’s documentation, community resources, or related content.  

## Input / Output  
**Input:**  
- Markdown documentation files and Docusaurus configuration settings.  

**Output:**  
- A fully built static website generated in the `build` directory, ready for deployment to web hosting platforms.  
