# CIROH Documentation Scraper

A comprehensive tool for scraping and organizing CIROH (Cooperative Institute for Research to Operations in Hydrology) documentation from docs.ciroh.org into local Markdown files.

## 🎯 Purpose

This project automates the process of:
1. Discovering all documentation links from CIROH's product and service pages
2. Scraping content from each page
3. Saving content as organized Markdown files maintaining the original site structure

This enables offline access, version control, and integration with other documentation systems.

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Firecrawl API key (free tier available at [firecrawl.dev](https://www.firecrawl.dev))

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/ciroh-docs-scraper.git
cd ciroh-docs-scraper
```

### 2. Set up Python environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API credentials
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Firecrawl API key
# FIRECRAWL_API_KEY=your_api_key_here
```

### 4. Run the complete scraping workflow
```bash
# Option 1: Run all steps automatically (scrapes both products and services)
./batch_scrape.sh

# Option 2: Scrape specific sections
./batch_scrape.sh --section products   # Scrape only products
./batch_scrape.sh --section services   # Scrape only services

# Option 3: Run steps individually
python scripts/discover_links.py                    # Discover all links (products + services)
python scripts/discover_links.py --section products # Discover only product links
python scripts/discover_links.py --section services # Discover only service links
python scripts/scrape_with_firecrawl.py            # Scrape content from all links
python scripts/validate_results.py                 # Validate scraping results
```

## 📁 Project Structure

```
ciroh-docs-scraper/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
├── batch_scrape.sh             # Automated workflow script
│
├── scripts/                    # Main scripts
│   ├── setup_environment.py    # Environment setup helper
│   ├── discover_links.py       # Link discovery script
│   ├── scrape_with_firecrawl.py # Content scraping script
│   └── validate_results.py     # Results validation script
│
├── docs/                       # Additional documentation
│   ├── API_SETUP.md           # Detailed API setup guide
│   ├── CONTRIBUTING.md        # Contribution guidelines
│   └── EXAMPLES.md            # Usage examples
│
└── docs_ciroh_org/            # Output directory (created automatically)
    ├── products/              # Scraped product documentation
    │   ├── community-fim/
    │   ├── data-management/
    │   ├── evaluation/
    │   └── ...
    └── services/              # Scraped service documentation
        ├── cloudservices/
        ├── on-prem/
        ├── external-resources/
        └── ...
```

## 🔧 Detailed Usage

### Step 1: Discover Documentation Links

The `discover_links.py` script automatically discovers all documentation links from CIROH's product categories:

```bash
python scripts/discover_links.py

# This will create:
# - links_inventory.json: Complete link inventory with metadata
# - links_summary.txt: Human-readable summary
# - Individual category files (e.g., community-fim_links.txt)
```

### Step 2: Scrape Content

The `scrape_with_firecrawl.py` script reads the discovered links and scrapes content:

```bash
python scripts/scrape_with_firecrawl.py

# Options:
# --input links_inventory.json   # Specify input file (default: links_inventory.json)
# --output docs_ciroh_org       # Specify output directory (default: docs_ciroh_org)
# --max-retries 3               # Maximum retry attempts for failed requests
# --delay 1                     # Delay between requests in seconds
```

### Step 3: Validate Results

Check that all expected files were created successfully:

```bash
python scripts/validate_results.py

# This will generate:
# - validation_report.txt: Detailed validation results
# - Lists any missing files or issues
```

## 📊 What Gets Scraped

The scraper covers all CIROH documentation including:

### Products (~68 pages total)
- **Community Flood Inundation Mapping** (4 pages)
- **Data Management Tools** (8 pages)
- **Evaluation Tools** (3 pages)
- **Hydrofabric** (1 page)
- **Machine Learning & AI** (3 pages)
- **Mobile Apps** (2 pages)
- **NextGen Framework** (4 pages)
- **Portal** (1 page)
- **Research DataStream** (5 pages)
- **Snow Tools** (5 pages)
- **Visualization Tools** (2 pages)
- **NextGen In A Box (NGIAB)** (30 pages)

### Services (31 pages total)
- **Main Services Pages** (6 pages)
- **Cloud Services** (13 pages)
- **On-Premise Services** (8 pages)
- **External Resources** (4 pages)

Total: ~99 documentation pages

## 🛠️ Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - The scraper includes automatic retry logic with exponential backoff
   - If you hit rate limits, increase the delay between requests

2. **Failed Scrapes**
   - Check `scraping_errors.log` for detailed error messages
   - The scraper will automatically retry failed pages
   - Use `--max-retries` to increase retry attempts

3. **Missing Content**
   - Some pages may require JavaScript rendering
   - The scraper will note these in the validation report
   - Consider using alternative scraping methods for problematic pages

### Environment Variables

Create a `.env` file with:
```
FIRECRAWL_API_KEY=your_api_key_here
SCRAPE_DELAY=1.0               # Delay between requests (seconds)
MAX_RETRIES=3                  # Maximum retry attempts
OUTPUT_DIR=docs_ciroh_org      # Output directory
```

## 🤝 Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on how to contribute to this project.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- CIROH for providing comprehensive water resources documentation
- Firecrawl for the powerful web scraping API
- The open source community for various tools and libraries used

## 📧 Contact

For questions or issues, please:
1. Check the [troubleshooting section](#-troubleshooting)
2. Open an issue on GitHub
3. Contact the maintainers

---

**Note**: This tool is for educational and research purposes. Always respect website terms of service and rate limits when scraping content.# CIROH-scraper
# CIROH-scraper
# CIROH-scraper
