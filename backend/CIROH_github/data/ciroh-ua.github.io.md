# Project Title: **ciroh-ua.github.io**

## Project Objective  
The **CIROH DocuHub** serves as the centralized documentation portal for the Cooperative Institute for Research to Operations in Hydrology (CIROH). Built using **Docusaurus v3.8.1**, it provides technical, organizational, and community-focused documentation for CIROH’s hydrological research ecosystem. The platform acts as the public-facing hub for CIROH’s cloud services, software tools, and research infrastructure.

---

## Core Functions  
- **Technical Documentation Repository:** Hosts detailed documentation for major CIROH products, including NextGen Framework, NGIAB (NextGen In A Box), National Water Model, and related data tools.  
- **Service Directory:** Provides access guides for CIROH’s computing infrastructure (AWS, Google Cloud, 2i2c JupyterHub, Pantarhei HPC, Wukong HPC).  
- **Community Hub:** Features news, blog posts, and community impact stories.  
- **Resource Gateway:** Links to CIROH’s GitHub repositories, data portals, and feedback forms.  

Maintained by the **DocuHub Team at the University of Alabama** and funded by **NOAA under award NA22NWS4320003**.  

---

## System Architecture  
- **Framework:** Docusaurus v3.8.1  
- **Build Process:** Compiles Markdown/MDX documentation into optimized static HTML, CSS, and JS bundles for hosting via web server or CDN.  
- **Frontend Stack:**  
  - CSS: `styles.21de081a.css`  
  - JS Bundles: `runtime~main.c258ff69.js`, `main.aa1c79d7.js`  
- **Search:** Implemented via Algolia DocSearch integration.  
- **Analytics:** Google Tag Manager + Google Analytics (ID: `G-7KD31X6H62`) with anonymized IP tracking.  
- **Diagram Support:** Integrated using `docusaurus-plugin-drawio` via CDN.  

---

## Content Organization  

### Documentation Hierarchy  
| Category | Root Path | Purpose |
|-----------|------------|----------|
| **Products** | `/docs/products/intro` | Documentation for CIROH hydrological products |
| **Services** | `/docs/services/intro` | Guides for computing and data access |
| **Policies** | `/docs/policies/intro` | Research practices and policy documentation |
| **Contribute** | `/docs/contribute/` | Contributor guidelines and workflows |

### Dynamic Content Streams  
| Stream | Path | RSS/Atom Feeds |
|---------|------|----------------|
| Blog | `/blog` | `/blog/rss.xml`, `/blog/atom.xml` |
| News | `/news` | No |
| Release Notes | `/release-notes` | `/release-notes/rss.xml`, `/release-notes/atom.xml` |

### Tag-Based Discovery  
Cross-tagging enables thematic content exploration across documentation and posts.  
Common tags:  
- **NGIAB** (47+ documents)  
- **National Water Model** (46+)  
- **NextGen Framework** (13+)  
- **NextGen Datastream** (14+)  

---

## User Interface and Navigation  

- **Navbar:** Top navigation includes Products, Services, Policies, and CIROH Portal links with external link indicators.  
- **Footer:** Three-column layout with Quick Links, About CIROH, and Social Media (GitHub, LinkedIn, YouTube, Instagram, Facebook, Twitter/X).  
- **Theme System:** Supports light, dark, and system modes via dynamic data attributes.  
- **Hero Banner:** Displays the CIROH logo, tagline “Documenting Water Research in the Digital Age,” and a community-oriented message.  
- **Carousel:** Highlights CIROH services and products (e.g., JupyterHub, NGIAB, AWS, Google Cloud).  
- **Feature Grid:** Presents six core themes — Knowledge Hub, Research & Growth, Blog & News, Education & Training, CyberInfrastructure, and Global Collaboration.  

---

## Homepage Features  

- **Team Section:** Lists CIROH DocuHub developers and contributors:  
  - Arpita Patel – DevOps Manager & Enterprise Architect  
  - Benjamin Lee – DevOps Engineer  
  - Trupesh Patel – Research Software Engineer  
  - Manjila Singh – Graduate Research Assistant  
  - Nia Minor – Graduate Research Assistant  
  - Zimuzo Ernest-Eze – Undergraduate Student Assistant  
- **Testimonials:** Features statements from community members including Patrick Clemins, James Halgren, and Supath Dhital.  
- **Consortium Display:**  
  - **Sponsors:** NOAA, USGS, 2i2c, Lynker  
  - **Members:** 14 academic institutions (e.g., UAH, UCSD, Hawaii, Iowa, Alabama, BYU, etc.)  
  - **Partners:** 14 organizations (e.g., ORNL, Jupiter Intelligence, RTI, CUAHSI, Penn State, UC Davis)  

---

## SEO and Performance  

- **Meta & OG Tags:** Configured for language, locale, and social media previews.  
- **Canonical URLs:** Defined for SEO consistency.  
- **Sitemap:** Contains 300+ URLs with `changefreq="weekly"` and `priority="0.5"`.  
- **Asset Hashing:** Uses content hashes (e.g., `styles.21de081a.css`) for efficient caching and invalidation.  
- **Preconnect Optimization:** DNS preconnects for Google Analytics and Tag Manager reduce latency.  
- **Hydration Strategy:** Uses a hydration placeholder (`data-has-hydrated=false`) to avoid layout shifts pre-render.  

---

## Error Handling  
The custom **404 page** maintains full site navigation and styling consistency.  
Includes:  
- Hero title: “Page Not Found”  
- Message: “We could not find what you were looking for.”  
- Contact and feedback links for user support.  
- Analytics tracking to log broken links for future improvements.  

---

## Integrations  

| Integration | Description |
|--------------|-------------|
| **CIROH Portal** | Linked throughout the navbar, footer, and carousel — provides access to datasets and applications. |
| **GitHub** | Linked from footer — source code repository at [github.com/CIROH-UA/ciroh-ua_website](https://github.com/CIROH-UA/ciroh-ua_website). |
| **Feedback** | Integrated Microsoft Forms (`forms.office.com/r/5ww7qRWwwf`) for community feedback. |

---

## License  
Licensed under the **Apache License 2.0**.  
© 2025 Cooperative Institute for Research to Operations in Hydrology (CIROH).  
Maintained by the University of Alabama DocuHub Team.
