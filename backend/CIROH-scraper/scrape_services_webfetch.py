#!/usr/bin/env python3
"""
Scrape CIROH services documentation using WebFetch
"""

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime

# List of all services URLs
services_urls = [
    "https://docs.ciroh.org/docs/services",
    "https://docs.ciroh.org/docs/services/intro",
    "https://docs.ciroh.org/docs/services/access",
    "https://docs.ciroh.org/docs/services/subdomain",
    "https://docs.ciroh.org/docs/services/on-prem",
    "https://docs.ciroh.org/docs/services/external-resources",
    "https://docs.ciroh.org/docs/services/cloudservices/cloudserviceblogs",
    "https://docs.ciroh.org/docs/services/cloudservices/2i2c",
    "https://docs.ciroh.org/docs/services/cloudservices/2i2c/documentation/custom-images",
    "https://docs.ciroh.org/docs/services/cloudservices/cuahsi",
    "https://docs.ciroh.org/docs/services/cloudservices/HydroShare",
    "https://docs.ciroh.org/docs/services/cloudservices/ciroh%20jupyterhub",
    "https://docs.ciroh.org/docs/services/cloudservices/ciroh%20jupyterhub/documentation",
    "https://docs.ciroh.org/docs/services/cloudservices/ciroh%20jupyterhub/documentation/conda",
    "https://docs.ciroh.org/docs/services/cloudservices/ciroh%20jupyterhub/documentation/python-package-conflicts",
    "https://docs.ciroh.org/docs/services/cloudservices/ciroh%20jupyterhub/documentation/gcp-object-storage",
    "https://docs.ciroh.org/docs/services/cloudservices/aws",
    "https://docs.ciroh.org/docs/services/cloudservices/aws/documentation/aws-best-practice",
    "https://docs.ciroh.org/docs/services/cloudservices/google-cloud",
    "https://docs.ciroh.org/docs/services/on-prem/Wukong",
    "https://docs.ciroh.org/docs/services/on-prem/Wukong/access",
    "https://docs.ciroh.org/docs/services/on-prem/Wukong/sysinfo",
    "https://docs.ciroh.org/docs/services/on-prem/Pantarhei",
    "https://docs.ciroh.org/docs/services/on-prem/Pantarhei/access",
    "https://docs.ciroh.org/docs/services/on-prem/Pantarhei/obtain",
    "https://docs.ciroh.org/docs/services/on-prem/Pantarhei/sysinfo",
    "https://docs.ciroh.org/docs/services/on-prem/Pantarhei/RunningJobs",
    "https://docs.ciroh.org/docs/services/external-resources/nsf-access",
    "https://docs.ciroh.org/docs/services/external-resources/nsf-access/derecho",
    "https://docs.ciroh.org/docs/services/external-resources/nsf-access/jetstream",
    "https://docs.ciroh.org/docs/services/external-resources/nsf-access/anvil"
]

print(f"=== CIROH Services Documentation Scraping ===")
print(f"Total links to scrape: {len(services_urls)}")
print("Note: This script will create the file structure.")
print("Use WebFetch tool to get actual content for each URL.")
print()

# Process first 5 URLs as example
for i, url in enumerate(services_urls[:5]):
    print(f"\n[{i+1}/5] Processing: {url}")
    
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
    
    print(f"  File path: {file_path}")
    print(f"  Status: Ready for WebFetch")

print(f"\n\nRemaining {len(services_urls) - 5} URLs need to be processed...")
print("\nTo complete scraping:")
print("1. Use WebFetch tool with prompt: 'Extract the main content as clean markdown'")
print("2. Save the extracted content to the corresponding file paths")
print("3. Add metadata header to each file")