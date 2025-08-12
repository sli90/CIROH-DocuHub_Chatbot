# Usage Examples

This document provides detailed examples of using the CIROH Documentation Scraper in various scenarios.

## Basic Usage

### Complete Workflow
```bash
# Run everything automatically
./batch_scrape.sh
```

### Step-by-Step Workflow
```bash
# Step 1: Set up environment
python scripts/setup_environment.py

# Step 2: Discover all links
python scripts/discover_links.py

# Step 3: Scrape all content
python scripts/scrape_with_firecrawl.py

# Step 4: Validate results
python scripts/validate_results.py
```

## Advanced Usage

### Scraping Specific Categories

#### Single Category
```bash
# Scrape only the "community-fim" category
python scripts/scrape_with_firecrawl.py --category community-fim

# Scrape only "data-management" category
python scripts/scrape_with_firecrawl.py --category data-management
```

#### Multiple Categories (Sequential)
```bash
# Create a script to scrape specific categories
for category in community-fim evaluation ml-ai; do
    python scripts/scrape_with_firecrawl.py --category $category
done
```

### Custom Output Directory
```bash
# Save to a different directory
python scripts/scrape_with_firecrawl.py --output /path/to/custom/output

# Example: Organize by date
OUTPUT_DIR="scraped_$(date +%Y%m%d)"
python scripts/scrape_with_firecrawl.py --output "$OUTPUT_DIR"
```

### Adjusting Rate Limits
```bash
# Slower scraping (more polite)
python scripts/scrape_with_firecrawl.py --delay 3.0

# Faster scraping (if API allows)
python scripts/scrape_with_firecrawl.py --delay 0.5

# More retries for unstable connections
python scripts/scrape_with_firecrawl.py --max-retries 5
```

### Resume Failed Scraping
```bash
# First attempt
python scripts/scrape_with_firecrawl.py

# If some URLs failed, resume
python scripts/scrape_with_firecrawl.py --resume

# Resume with more retries
python scripts/scrape_with_firecrawl.py --resume --max-retries 5 --delay 2.0
```

## Environment Configuration

### Basic .env Setup
```env
# Minimum required configuration
FIRECRAWL_API_KEY=fc-your-api-key-here
```

### Advanced .env Setup
```env
# API Configuration
FIRECRAWL_API_KEY=fc-your-api-key-here

# Scraping behavior
SCRAPE_DELAY=2.0               # Slower for stability
MAX_RETRIES=5                  # More retries
CONCURRENT_REQUESTS=3          # Fewer concurrent requests

# Output settings
OUTPUT_DIR=my_docs             # Custom output directory
CREATE_BACKUPS=true            # Backup before overwriting

# Logging
LOG_LEVEL=DEBUG                # More detailed logs
LOG_FILE=detailed_scraping.log # Custom log file

# Fallback options
ENABLE_FALLBACK_SCRAPING=true  # Use BeautifulSoup if Firecrawl fails
USER_AGENT=MyCustomBot/1.0     # Custom user agent
```

## Scripting Examples

### Automated Daily Scraping
```bash
#!/bin/bash
# daily_scrape.sh - Run via cron

# Set up environment
cd /path/to/ciroh-docs-scraper
source venv/bin/activate

# Create dated output directory
OUTPUT_DIR="docs_$(date +%Y%m%d)"

# Run scraping
python scripts/discover_links.py
python scripts/scrape_with_firecrawl.py --output "$OUTPUT_DIR"

# Validate and report
python scripts/validate_results.py > "report_$(date +%Y%m%d).txt"

# Email results (optional)
mail -s "CIROH Docs Scraping Report" admin@example.com < "report_$(date +%Y%m%d).txt"
```

### Selective Category Updates
```python
#!/usr/bin/env python3
# selective_update.py - Update only changed categories

import subprocess
import json
from datetime import datetime, timedelta

# Categories to check
CATEGORIES_TO_UPDATE = ["community-fim", "data-management", "evaluation"]

# Check last update time (implement your logic)
def should_update_category(category):
    # Example: Update if older than 7 days
    # Implement your own logic here
    return True

# Update selected categories
for category in CATEGORIES_TO_UPDATE:
    if should_update_category(category):
        print(f"Updating {category}...")
        subprocess.run([
            "python", "scripts/scrape_with_firecrawl.py",
            "--category", category,
            "--resume"
        ])
```

### Error Handling and Retry
```bash
#!/bin/bash
# robust_scrape.sh - Scrape with automatic retry on failure

MAX_ATTEMPTS=3
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT of $MAX_ATTEMPTS"
    
    # Try scraping
    if python scripts/scrape_with_firecrawl.py; then
        echo "Scraping successful!"
        break
    else
        echo "Scraping failed, checking for partial success..."
        
        # Check if any files were scraped
        if [ -d "docs_ciroh_org" ] && [ "$(ls -A docs_ciroh_org)" ]; then
            echo "Partial success, attempting to resume..."
            python scripts/scrape_with_firecrawl.py --resume --delay 3.0
        else
            echo "Complete failure, waiting before retry..."
            sleep 60
        fi
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
done

# Final validation
python scripts/validate_results.py
```

## Integration Examples

### Git Integration
```bash
#!/bin/bash
# git_integrated_scrape.sh - Scrape and commit changes

# Scrape content
./batch_scrape.sh

# Check for changes
if [ -n "$(git status --porcelain docs_ciroh_org/)" ]; then
    # Changes detected
    git add docs_ciroh_org/
    git commit -m "Update CIROH documentation $(date +%Y-%m-%d)"
    
    # Optional: Create a pull request
    git checkout -b "docs-update-$(date +%Y%m%d)"
    git push origin "docs-update-$(date +%Y%m%d)"
    
    echo "Changes committed and pushed!"
else
    echo "No changes detected"
fi
```

### Python Integration
```python
#!/usr/bin/env python3
# integrate_scraper.py - Use scraper as a library

import sys
sys.path.append('scripts')

from discover_links import create_link_inventory
from scrape_with_firecrawl import FirecrawlScraper, url_to_filepath

# Discover links
print("Discovering links...")
inventory = create_link_inventory()

# Initialize scraper
scraper = FirecrawlScraper(api_key="your-api-key")

# Scrape specific URLs
urls_to_scrape = [
    "https://docs.ciroh.org/docs/products/community-fim",
    "https://docs.ciroh.org/docs/products/evaluation"
]

for url in urls_to_scrape:
    print(f"Scraping {url}...")
    content = scraper.scrape_with_fallback(url)
    if content:
        scraper.save_content(url, content)
```

### Docker Integration
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run scraper
CMD ["python", "scripts/scrape_with_firecrawl.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  scraper:
    build: .
    environment:
      - FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY}
      - SCRAPE_DELAY=2.0
      - OUTPUT_DIR=/output
    volumes:
      - ./output:/output
      - ./logs:/app/logs
```

## Monitoring and Reporting

### Progress Monitoring
```python
#!/usr/bin/env python3
# monitor_progress.py - Real-time progress monitoring

import json
import time
from pathlib import Path

def monitor_scraping():
    """Monitor scraping progress in real-time"""
    
    # Load expected URLs
    with open("links_inventory.json") as f:
        inventory = json.load(f)
    
    total_expected = inventory["metadata"]["total_links"]
    
    while True:
        # Count scraped files
        scraped_files = list(Path("docs_ciroh_org").glob("**/*.md"))
        scraped_count = len(scraped_files)
        
        # Calculate progress
        progress = (scraped_count / total_expected) * 100
        
        # Display progress
        print(f"\rProgress: {scraped_count}/{total_expected} ({progress:.1f}%)", end="")
        
        if scraped_count >= total_expected:
            print("\nScraping complete!")
            break
        
        time.sleep(5)

if __name__ == "__main__":
    monitor_scraping()
```

### Custom Validation
```python
#!/usr/bin/env python3
# custom_validation.py - Advanced content validation

import os
from pathlib import Path

def validate_content_quality(file_path):
    """Validate content quality metrics"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check various quality metrics
    checks = {
        "has_title": "# " in content,
        "min_length": len(content) > 500,
        "has_metadata": content.startswith("---"),
        "no_errors": "404" not in content.lower(),
        "has_sections": "## " in content
    }
    
    return all(checks.values()), checks

# Validate all files
for md_file in Path("docs_ciroh_org").glob("**/*.md"):
    is_valid, checks = validate_content_quality(md_file)
    if not is_valid:
        print(f"Quality issues in {md_file}:")
        for check, passed in checks.items():
            if not passed:
                print(f"  - Failed: {check}")
```

## Troubleshooting Examples

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python scripts/scrape_with_firecrawl.py

# Or in .env file
echo "LOG_LEVEL=DEBUG" >> .env
```

### Test Single URL
```python
#!/usr/bin/env python3
# test_single_url.py - Test scraping a single URL

from scripts.scrape_with_firecrawl import FirecrawlScraper
import os

# Test URL
test_url = "https://docs.ciroh.org/docs/products/community-fim"

# Initialize scraper
scraper = FirecrawlScraper(os.getenv("FIRECRAWL_API_KEY"))

# Try scraping
print(f"Testing: {test_url}")
result = scraper.scrape_with_fallback(test_url)

if result:
    print("Success! Content preview:")
    print(result.get("markdown", "")[:500])
else:
    print("Failed to scrape URL")
```

These examples should help you use the CIROH Documentation Scraper effectively in various scenarios. Adjust the examples to fit your specific needs!