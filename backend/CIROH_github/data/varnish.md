# Project Title: **varnish**

## Project Objective  
The **varnish** package serves as a template for The Carpentries Workbench. It provides HTML, CSS, and JavaScript templates for Carpentries lessons, adapted from the `{pkgdown}` package, and is automatically installed and used by `{sandpaper}` to render lesson websites.

## Core Functionalities  
- Supplies HTML templates for Carpentries lessons.  
- Uses the mustache templating language for rendering.  
- Compiles and minifies CSS and JavaScript via GitHub Actions.  
- Provides templates for lesson structure components, including:  
  - content-chapter  
  - content-syllabus  
  - content-extra  
  - content-overview  
  - head, navbar, header, footer, and layout.  
- Supports YAML-based global and page-specific parameters.  
- Compatible with `{pkgdown}` and `{sandpaper}` for automated site rendering.  

## Technical Stack  
- **Languages/Frameworks:** R, mustache, HTML, CSS, JavaScript.  
- **Tools:** SASS, uglifyjs, Node.js (version 16), npm, GitHub Actions.  
- **Dependencies:** Node, npm, nvm, pkgdown, sandpaper.  

## Setup and Usage  
### Installation  
Install the package via The Carpentries R-universe repository:  
```r
install.packages("varnish", repos = "https://carpentries.r-universe.dev")
```  
It is automatically detected and used by `{sandpaper}` to apply styles and templates to lesson websites.

### Building CSS and JavaScript Locally  
1. Install Node.js (via `nvm`):  
   ```sh
   nvm install 16
   npm install
   ```  
2. Minify assets:  
   ```sh
   bash squash-sass.sh     # compile CSS using sass
   bash squash-a-script.sh # compile JS using uglifyjs
   ```  

### Template Parameters  
- Defined in `site/_pkgdown.yaml` or provided via `{pkgdown}`.  
- Includes parameters such as `title`, `time`, `source`, `branch`, `contact`, `license`, and lesson metadata.  
- Page-specific parameters include:  
  - `{{ instructor }}` – instructor view toggle.  
  - `{{ aio }}` – include all-in-one page.  
  - `{{ this_page }}` – current HTML file name.  
  - `{{{ schedule }}}`, `{{{ resources }}}` – sidebar content.  

## Project Context & Domain  
- **Domain:** Educational Web Development / R Package Templates.  
- **Affiliation:** The Carpentries.  
- **Purpose:** Provide standardized lesson templates and styling for The Carpentries Workbench.  

## Input / Output  
**Input:**  
- Source HTML templates, YAML configuration, and Node-based CSS/JS files.  

**Output:**  
- Compiled and minified CSS and JS files.  
- Rendered lesson websites styled using the Varnish template.  
