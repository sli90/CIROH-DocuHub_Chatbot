#!/usr/bin/env python3
"""
Scrape CIROH services documentation using Firecrawl MCP
"""

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime

# Load services links from inventory
with open('links_inventory.json', 'r') as f:
    inventory = json.load(f)

# Track progress
total_links = inventory['metadata']['total_links']
scraped = 0
failed_urls = []

print(f"=== CIROH Services Documentation Scraping ===")
print(f"Total links to scrape: {total_links}")
print()

# Process each category
for category_key, category_data in inventory['categories'].items():
    print(f"\n{category_data['name']}:")
    
    for url in category_data['links']:
        # Convert URL to file path
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        # Remove /docs/ prefix
        if path.startswith("/docs/"):
            path = path[6:]
        
        # Create file path
        file_path = os.path.join("docs_ciroh_org", path.strip("/"))
        if file_path.endswith("/") or not os.path.splitext(file_path)[1]:
            file_path = os.path.join(file_path, "index.md")
        else:
            file_path += ".md"
        
        # Create directory
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        print(f"  Scraping: {url}")
        print(f"  Saving to: {file_path}")
        
        # Create placeholder content for now
        content = f"""---
title: {os.path.basename(path) or 'Index'}
source: {url}
scraped: {datetime.now().isoformat()}
status: pending_scrape
---

# {os.path.basename(path) or 'Services'}

This page will be scraped from: {url}

Please run the full scraping process to get the actual content.
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        scraped += 1
        print(f"  ✓ Created placeholder ({scraped}/{total_links})")
        
        # Small delay
        time.sleep(0.1)

print(f"\n=== Summary ===")
print(f"Total files created: {scraped}")
print(f"Failed: {len(failed_urls)}")
print("\nPlaceholder files have been created.")
print("To get actual content, use the firecrawl_scrape MCP tool for each URL.")