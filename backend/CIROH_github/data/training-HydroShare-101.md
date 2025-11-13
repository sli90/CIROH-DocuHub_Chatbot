# Project Title: **training-HydroShare-101**

## Project Objective  
This repository provides a **template lesson** built with [The Carpentries Workbench](https://carpentries.github.io/sandpaper-docs/). It is designed to help educators, trainers, and researchers create and publish structured training materials or workshops—such as the **HydroShare 101** lesson—using the Carpentries framework.  
The project’s goal is to support reproducible, version-controlled, and collaboratively maintained educational content for technical and scientific training.

## Core Functionalities  
- **Template-based lesson creation:** Provides a complete framework for building new lesson repositories from a Carpentries template.  
- **GitHub Pages integration:** Automatically builds and hosts lesson websites through GitHub Pages.  
- **Configuration guidance:** Step-by-step setup for the `config.yaml` file, which controls lesson metadata and lifecycle stage.  
- **Lesson lifecycle management:** Includes configurable life cycle stages such as “pre-alpha” to indicate lesson maturity.  
- **Citation and metadata setup:** Offers instructions for updating citation, license, contribution, and conduct documentation (`CITATION.cff`, `LICENSE.md`, `CONTRIBUTING.md`, etc.).  
- **Contributor onboarding:** Provides guidelines for community collaboration, tagging, and repository annotation (topics, lesson language, etc.).  
- **Automated build and workflow setup:** Uses GitHub Actions to automate lesson deployment.  

## Technical Stack  
- **Framework:** [The Carpentries Workbench](https://github.com/carpentries/workbench-template-md)  
- **Language:** Markdown (with YAML configuration)  
- **Hosting:** GitHub Pages  
- **Automation:** GitHub Actions  
- **License:** CC-BY (Creative Commons Attribution)  

## Setup and Usage  
1. **Create a new repository:**  
   Use the template at [carpentries/workbench-template-md](https://github.com/carpentries/workbench-template-md/generate) and include all branches.  
2. **Activate GitHub Pages:**  
   Enable the `gh-pages` branch under repository settings to host the lesson site.  
3. **Edit `config.yaml`:**  
   Update fields such as `title`, `created`, `keywords`, `life_cycle`, and `contact`.  
4. **Update documentation files:**  
   Modify `CITATION.cff`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and `LICENSE.md` as needed.  
5. **Annotate the repository:**  
   Add lesson-related tags (e.g., `lesson`, `pre-alpha`, `english`) under repository topics.  
6. **Customize the README:**  
   Replace the template’s placeholder instructions with lesson-specific content.  

## Project Context & Domain  
- **Domain:** Educational content / Training framework.  
- **Affiliation:** Based on **The Carpentries** teaching framework, used widely across data science and research computing communities.  
- **Intended Use:** Serves as the foundation for HydroShare or hydrology-related training materials developed within the Carpentries ecosystem.  

## Input / Output  
**Input:**  
- Markdown lesson content, configuration files (`config.yaml`, metadata docs), and associated assets.  

**Output:**  
- A fully rendered static website (via GitHub Pages) hosting the educational lesson.  
