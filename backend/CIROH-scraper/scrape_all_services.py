#!/usr/bin/env python3
"""
Script to scrape all services pages using Firecrawl MCP
"""

import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote

# All services URLs to scrape
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

# URLs that have already been scraped
scraped_urls = [
    "https://docs.ciroh.org/docs/services/intro",
    "https://docs.ciroh.org/docs/services/access",
    "https://docs.ciroh.org/docs/services/cloudservices/aws"
]

# Filter out already scraped URLs
urls_to_scrape = [url for url in services_urls if url not in scraped_urls]

print(f"=== CIROH Services Documentation Scraping ===")
print(f"Total URLs: {len(services_urls)}")
print(f"Already scraped: {len(scraped_urls)}")
print(f"URLs to scrape: {len(urls_to_scrape)}")
print()

# Function to convert URL to file path
def url_to_filepath(url, base_dir="docs_ciroh_org"):
    parsed = urlparse(url)
    path = unquote(parsed.path)
    
    # Remove /docs/ prefix
    if path.startswith("/docs/"):
        path = path[6:]
    
    # Create file path
    file_path = os.path.join(base_dir, path.strip("/"))
    if file_path.endswith("/") or not os.path.splitext(file_path)[1]:
        file_path = os.path.join(file_path, "index.md")
    else:
        file_path += ".md"
    
    return file_path

# Create list of scraping commands
print("URLs to scrape:")
for i, url in enumerate(urls_to_scrape, 1):
    file_path = url_to_filepath(url)
    print(f"{i}. {url}")
    print(f"   -> {file_path}")
    print()

print("\nTo scrape these URLs, use the firecrawl_scrape MCP tool for each URL.")
print("Each URL should be scraped with:")
print('- formats: ["markdown"]')
print("- onlyMainContent: true")
print("\nThe content should be saved to the corresponding file paths shown above.")