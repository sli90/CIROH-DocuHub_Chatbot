# Project Title: **docuhub-staging**

## Project Objective  
**docuhub-staging** is a static documentation portal built on **Docusaurus v3.9.1**, serving as the centralized knowledge base for the **Cooperative Institute for Research to Operations in Hydrology (CIROH)**. It hosts technical documentation, organizational policies, data governance frameworks, and CIROH project resources in a structured and accessible format. This repository represents the **staging environment** for DocuHub, supporting continuous content updates and validation before production deployment.

## Core Functionalities  
- Implements a **three-tier architecture** with a static frontend, content management layer, and external integrations.  
- Built on **Docusaurus** with modular React components for navigation, search, and theming.  
- Organizes content across key documentation categories:
  - `/docs/products` – Technical documentation for CIROH products.  
  - `/docs/services` – Service guides and system documentation.  
  - `/docs/policies` – Governance, compliance, and data management documents.  
  - `/blog`, `/news`, `/release-notes` – Updates, announcements, and version tracking.  
  - `/impact`, `/contact`, `/docs/contribute` – Community and contribution sections.  
- Integrates **Google Analytics (G-7KD31X6H62)** for user metrics and **jsDelivr CDN** for asset delivery.  
- Maintains **26+ image assets**, PDF policy documents, and dynamically hashed static files for caching efficiency.  
- Features custom 404 error handling and metadata-driven SEO optimization.

## Technical Stack  
- **Languages/Frameworks:** Docusaurus v3.9.1 (React-based static site generator).  
- **Tools/Dependencies:** `@docusaurus/core`, `@docusaurus/theme-classic`, `docusaurus-plugin-drawio`, Webpack, Infima CSS system, pdfTeX for PDF generation.  
- **Hosting/Runtime:** Deployed to a staging subdirectory under `http://ciroh.org/docuhub-staging/`.  

## Setup and Usage  
1. Clone the repository and install dependencies using `npm install` or `yarn install`.  
2. To build locally, run `npm run build` to generate the static site output.  
3. Preview with `npm run start` or deploy to staging with the configured base path `/docuhub-staging/`.  
4. All absolute URLs are automatically prefixed with the base path for staging compatibility.  
5. Content is located under the `/docs`, `/blog`, and `/assets` directories, following CIROH’s documentation taxonomy.

## Project Context & Domain  
- **Domain:** Documentation / Knowledge Management / Hydrology Research Infrastructure.  
- **Affiliation:** CIROH (Cooperative Institute for Research to Operations in Hydrology), University of Alabama.  
- **Purpose:** To provide a unified, well-structured knowledge portal for CIROH researchers, partners, and stakeholders, ensuring discoverability, transparency, and compliance in research communication.  

## Input / Output  
**Input:**  
- Markdown files, PDF documents, images, and metadata (Dublin Core, Adobe XMP).  
- Configuration files for Docusaurus theme and navigation.  

**Output:**  
- A fully built static site with searchable documentation, versioned policies, and linked CIROH resources.  
- Gen
