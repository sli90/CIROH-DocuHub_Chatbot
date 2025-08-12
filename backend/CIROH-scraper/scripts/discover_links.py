#!/usr/bin/env python3
"""
Discover all documentation links from CIROH product and service pages
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import time
from tqdm import tqdm
import argparse

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Base URL for CIROH documentation
BASE_URL = "https://docs.ciroh.org"
PRODUCTS_URL = f"{BASE_URL}/docs/products"
SERVICES_URL = f"{BASE_URL}/docs/services"

# Known product categories (from manual exploration)
PRODUCT_CATEGORIES = {
    "community-fim": "Community Flood Inundation Mapping",
    "data-management": "Data Management and Access Tools",
    "evaluation": "Evaluation Tools",
    "Hydrofabric": "Hydrofabric",
    "ml-ai": "Machine Learning and AI Tools",
    "mobile-apps": "Mobile Apps",
    "nextgen-framework": "NextGen Framework",
    "portal": "CIROH Research Portal",
    "research-datastream": "Research DataStream",
    "snow-tools": "Snow Sensing and Modeling Tools",
    "visualization": "Visualization and Analysis Tools",
    "ngiab": "NextGen In A Box (NGIAB)"
}

# Known service categories (from manual exploration)
SERVICE_CATEGORIES = {
    "main": "Main Services Pages",
    "cloudservices": "Cloud Services",
    "on-prem": "On-Premise Services",
    "external-resources": "External Resources"
}

# Pre-discovered links for each category (based on manual exploration)
PREDISCOVERED_LINKS = {
    "community-fim": [
        "/docs/products/community-fim",
        "/docs/products/community-fim/fim-database",
        "/docs/products/community-fim/fimeval",
        "/docs/products/community-fim/fimserv"
    ],
    "data-management": [
        "/docs/products/data-management",
        "/docs/products/data-management/hydroshare",
        "/docs/products/data-management/hydroserver",
        "/docs/products/data-management/dataaccess",
        "/docs/products/data-management/dataaccess/NWMURL%20Library",
        "/docs/products/data-management/waternode",
        "/docs/products/data-management/bigquery-api",
        "/docs/products/data-management/netwa"
    ],
    "evaluation": [
        "/docs/products/evaluation",
        "/docs/products/evaluation/cses",
        "/docs/products/evaluation/rtiteehr"
    ],
    "Hydrofabric": [
        "/docs/products/Hydrofabric"
    ],
    "ml-ai": [
        "/docs/products/ml-ai",
        "/docs/products/ml-ai/sweml",
        "/docs/products/ml-ai/nwm_ml"
    ],
    "mobile-apps": [
        "/docs/products/mobile-apps",
        "/docs/products/mobile-apps/RIVR"
    ],
    "nextgen-framework": [
        "/docs/products/nextgen-framework",
        "/docs/products/nextgen-framework/ngen",
        "/docs/products/nextgen-framework/troute",
        "/docs/products/nextgen-framework/nextgen"
    ],
    "portal": [
        "/docs/products/portal"
    ],
    "research-datastream": [
        "/docs/products/research-datastream",
        "/docs/products/research-datastream/cli",
        "/docs/products/research-datastream/components",
        "/docs/products/research-datastream/api",
        "/docs/products/research-datastream/status"
    ],
    "snow-tools": [
        "/docs/products/snow-tools",
        "/docs/products/snow-tools/snow-intro",
        "/docs/products/snow-tools/sweml-v2-0",
        "/docs/products/snow-tools/snow-sensing",
        "/docs/products/snow-tools/optimize-sensors"
    ],
    "visualization": [
        "/docs/products/visualization",
        "/docs/products/visualization/tethys-cses"
    ],
    "ngiab": [
        "/docs/products/ngiab",
        "/docs/products/ngiab/intro",
        "/docs/products/ngiab/intro/at-a-glance",
        "/docs/products/ngiab/intro/directories",
        "/docs/products/ngiab/intro/glossary",
        "/docs/products/ngiab/intro/install",
        "/docs/products/ngiab/intro/what-is",
        "/docs/products/ngiab/components",
        "/docs/products/ngiab/components/community-hydrofabric",
        "/docs/products/ngiab/components/ngiab-calibration",
        "/docs/products/ngiab/components/ngiab-preprocessor",
        "/docs/products/ngiab/components/ngiab-teehr",
        "/docs/products/ngiab/components/ngiab-visualizer",
        "/docs/products/ngiab/distributions",
        "/docs/products/ngiab/distributions/nextgen-2i2c",
        "/docs/products/ngiab/distributions/ngiab-docker",
        "/docs/products/ngiab/distributions/ngiab-singularity",
        "/docs/products/ngiab/dashboard",
        "/docs/products/ngiab/office-hours"
    ]
}

# Pre-discovered links for services (based on manual exploration)
PREDISCOVERED_SERVICE_LINKS = {
    "main": [
        "/docs/services",
        "/docs/services/intro",
        "/docs/services/access",
        "/docs/services/subdomain",
        "/docs/services/on-prem",
        "/docs/services/external-resources"
    ],
    "cloudservices": [
        "/docs/services/cloudservices/cloudserviceblogs",
        "/docs/services/cloudservices/2i2c",
        "/docs/services/cloudservices/2i2c/documentation/custom-images",
        "/docs/services/cloudservices/cuahsi",
        "/docs/services/cloudservices/HydroShare",
        "/docs/services/cloudservices/ciroh%20jupyterhub",
        "/docs/services/cloudservices/ciroh%20jupyterhub/documentation",
        "/docs/services/cloudservices/ciroh%20jupyterhub/documentation/conda",
        "/docs/services/cloudservices/ciroh%20jupyterhub/documentation/python-package-conflicts",
        "/docs/services/cloudservices/ciroh%20jupyterhub/documentation/gcp-object-storage",
        "/docs/services/cloudservices/aws",
        "/docs/services/cloudservices/aws/documentation/aws-best-practice",
        "/docs/services/cloudservices/google-cloud"
    ],
    "on-prem": [
        "/docs/services/on-prem/Wukong",
        "/docs/services/on-prem/Wukong/access",
        "/docs/services/on-prem/Wukong/sysinfo",
        "/docs/services/on-prem/Pantarhei",
        "/docs/services/on-prem/Pantarhei/access",
        "/docs/services/on-prem/Pantarhei/obtain",
        "/docs/services/on-prem/Pantarhei/sysinfo",
        "/docs/services/on-prem/Pantarhei/RunningJobs"
    ],
    "external-resources": [
        "/docs/services/external-resources/nsf-access",
        "/docs/services/external-resources/nsf-access/derecho",
        "/docs/services/external-resources/nsf-access/jetstream",
        "/docs/services/external-resources/nsf-access/anvil"
    ]
}


def discover_links_from_page(url, visited=None, max_depth=3, current_depth=0):
    """
    Discover links from a given page by parsing HTML
    
    Args:
        url: URL to scrape
        visited: Set of already visited URLs
        max_depth: Maximum depth to follow links
        current_depth: Current recursion depth
    
    Returns:
        List of discovered links
    """
    if visited is None:
        visited = set()
    
    if current_depth >= max_depth or url in visited:
        return []
    
    visited.add(url)
    discovered_links = []
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Only process CIROH docs links
            if absolute_url.startswith(BASE_URL) and ('/docs/products/' in absolute_url or '/docs/services/' in absolute_url):
                parsed = urlparse(absolute_url)
                clean_path = parsed.path
                
                if clean_path not in discovered_links and clean_path not in visited:
                    discovered_links.append(clean_path)
                    
                    # Recursively discover links from this page
                    if current_depth < max_depth - 1:
                        time.sleep(0.5)  # Be polite
                        sub_links = discover_links_from_page(
                            absolute_url, visited, max_depth, current_depth + 1
                        )
                        discovered_links.extend(sub_links)
        
    except Exception as e:
        print(f"Error discovering links from {url}: {e}")
    
    return list(set(discovered_links))


def create_link_inventory(section="both"):
    """Create comprehensive link inventory
    
    Args:
        section: 'products', 'services', or 'both'
    """
    inventory = {
        "metadata": {
            "created": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "section": section,
            "total_categories": 0,
            "total_links": 0
        },
        "categories": {}
    }
    
    all_links = []
    
    print("=== CIROH Documentation Link Discovery ===")
    print(f"Section: {section.upper()}")
    print()
    
    # Determine which sections to process
    sections_to_process = []
    if section in ["products", "both"]:
        sections_to_process.append(("products", PRODUCT_CATEGORIES, PREDISCOVERED_LINKS))
    if section in ["services", "both"]:
        sections_to_process.append(("services", SERVICE_CATEGORIES, PREDISCOVERED_SERVICE_LINKS))
    
    # Process each section
    for section_name, categories, prediscovered in sections_to_process:
        print(f"\n=== Processing {section_name.upper()} ===")
        
        # Process each category
        for category, description in tqdm(categories.items(), desc=f"Processing {section_name} categories"):
            print(f"\n{category.upper()}: {description}")
            
            # Use prediscovered links
            category_links = prediscovered.get(category, [])
            
            # Convert to full URLs
            full_urls = [BASE_URL + link for link in category_links]
            
            # Create section-prefixed category name for inventory
            inv_category = f"{section_name}_{category}"
            
            inventory["categories"][inv_category] = {
                "name": f"[{section_name.title()}] {description}",
                "links": full_urls,
                "count": len(full_urls),
                "section": section_name
            }
            
            all_links.extend(full_urls)
            
            # Save category-specific file
            category_file = Path(f"link_lists/{section_name}_{category}_links.txt")
            category_file.parent.mkdir(exist_ok=True)
            with open(category_file, 'w') as f:
                f.write(f"# {description}\n")
                f.write(f"# Section: {section_name}\n")
                f.write(f"# Total links: {len(full_urls)}\n\n")
                for url in full_urls:
                    f.write(f"{url}\n")
            
            print(f"  - Found {len(full_urls)} links")
            print(f"  - Saved to {category_file}")
    
    # Update metadata
    inventory["metadata"]["total_links"] = len(all_links)
    inventory["metadata"]["total_categories"] = len(inventory["categories"])
    
    # Save complete inventory as JSON
    inventory_file = Path("links_inventory.json")
    with open(inventory_file, 'w') as f:
        json.dump(inventory, f, indent=2)
    
    print(f"\n✅ Complete inventory saved to {inventory_file}")
    
    # Save human-readable summary
    summary_file = Path("links_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("# CIROH Documentation Links Summary\n")
        f.write(f"# Generated: {inventory['metadata']['created']}\n")
        f.write(f"# Total Categories: {inventory['metadata']['total_categories']}\n")
        f.write(f"# Total Links: {inventory['metadata']['total_links']}\n\n")
        
        for category, data in inventory["categories"].items():
            f.write(f"\n## {data['name']} ({data['count']} links)\n")
            for link in data["links"]:
                f.write(f"{link}\n")
    
    print(f"✅ Summary saved to {summary_file}")
    
    # Save all links in a single file
    all_links_file = Path("all_links.txt")
    with open(all_links_file, 'w') as f:
        for link in sorted(set(all_links)):
            f.write(f"{link}\n")
    
    print(f"✅ All links saved to {all_links_file}")
    
    return inventory


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Discover CIROH documentation links")
    parser.add_argument(
        "--section",
        choices=["products", "services", "both"],
        default="both",
        help="Which section to discover links for (default: both)"
    )
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(Path(__file__).parent.parent)
    
    # Create link inventory
    inventory = create_link_inventory(args.section)
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Total categories: {inventory['metadata']['total_categories']}")
    print(f"Total links discovered: {inventory['metadata']['total_links']}")
    
    print("\nLinks per category:")
    for category, data in inventory["categories"].items():
        print(f"  - {category}: {data['count']} links")
    
    print("\n✅ Link discovery complete!")
    print("\nNext step: Run 'python scripts/scrape_with_firecrawl.py' to scrape content")


if __name__ == "__main__":
    main()