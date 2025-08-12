#!/usr/bin/env python3
"""
Scrape content from CIROH documentation links using Firecrawl API
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import argparse

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Configuration
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1"
SCRAPE_DELAY = float(os.getenv("SCRAPE_DELAY", "1.0"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "5"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "docs_ciroh_org")
ENABLE_FALLBACK = os.getenv("ENABLE_FALLBACK_SCRAPING", "true").lower() == "true"
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (compatible; CIROH-Docs-Scraper/1.0)")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def url_to_filepath(url: str, base_dir: str = OUTPUT_DIR) -> str:
    """Convert URL to local file path"""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    
    # Remove /docs/ prefix
    if path.startswith("/docs/"):
        path = path[6:]  # Remove "/docs/"
    
    # Create full path
    full_path = os.path.join(base_dir, path.strip("/"))
    
    # Add index.md for directories
    if full_path.endswith("/") or not os.path.splitext(full_path)[1]:
        full_path = os.path.join(full_path, "index.md")
    else:
        full_path += ".md"
    
    return full_path


class FirecrawlScraper:
    """Firecrawl API scraper with retry logic and fallback"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        self.scraped_count = 0
        self.failed_urls = []
        self.error_log = []
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    def scrape_url(self, url: str) -> Optional[Dict]:
        """Scrape a single URL using Firecrawl API"""
        try:
            payload = {
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "waitFor": 2000,
                "timeout": 30000
            }
            
            response = self.session.post(
                f"{FIRECRAWL_API_URL}/scrape",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    return data["data"]
                else:
                    logger.warning(f"Firecrawl returned no data for {url}")
                    return None
            else:
                logger.error(f"Firecrawl API error for {url}: {response.status_code} - {response.text}")
                if response.status_code == 429:
                    # Rate limit - wait longer
                    time.sleep(10)
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            raise
    
    def fallback_scrape(self, url: str) -> Optional[Dict]:
        """Fallback scraping method using BeautifulSoup"""
        if not ENABLE_FALLBACK:
            return None
            
        try:
            headers = {"User-Agent": USER_AGENT}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find main content area
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_='content') or
                soup.find('div', class_='docs-content') or
                soup.body
            )
            
            if main_content:
                # Convert to markdown-like format
                text_content = []
                
                # Extract title
                title = soup.find('h1')
                if title:
                    text_content.append(f"# {title.get_text().strip()}\n")
                
                # Extract paragraphs and headers
                for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code', 'ul', 'ol']):
                    if element.name.startswith('h'):
                        level = int(element.name[1])
                        text_content.append(f"\n{'#' * level} {element.get_text().strip()}\n")
                    elif element.name == 'p':
                        text_content.append(f"\n{element.get_text().strip()}\n")
                    elif element.name in ['pre', 'code']:
                        text_content.append(f"\n```\n{element.get_text().strip()}\n```\n")
                    elif element.name in ['ul', 'ol']:
                        for li in element.find_all('li'):
                            prefix = "- " if element.name == 'ul' else "1. "
                            text_content.append(f"{prefix}{li.get_text().strip()}\n")
                
                markdown_content = "\n".join(text_content)
                
                return {
                    "markdown": markdown_content,
                    "url": url,
                    "metadata": {
                        "title": title.get_text().strip() if title else "Untitled",
                        "sourceURL": url,
                        "statusCode": response.status_code
                    }
                }
            
            logger.warning(f"Fallback scraping found no main content for {url}")
            return None
            
        except Exception as e:
            logger.error(f"Fallback scraping failed for {url}: {str(e)}")
            return None
    
    def scrape_with_fallback(self, url: str) -> Optional[Dict]:
        """Try Firecrawl first, then fallback if needed"""
        try:
            # Try Firecrawl API first
            result = self.scrape_url(url)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Firecrawl failed for {url}, trying fallback: {str(e)}")
        
        # Try fallback method
        result = self.fallback_scrape(url)
        if result:
            logger.info(f"Successfully used fallback for {url}")
            return result
        
        # Both methods failed
        self.failed_urls.append(url)
        self.error_log.append({
            "url": url,
            "error": "Both Firecrawl and fallback methods failed",
            "timestamp": datetime.now().isoformat()
        })
        return None
    
    def save_content(self, url: str, content_data: Dict) -> bool:
        """Save scraped content to file"""
        try:
            # Get the markdown content
            markdown_content = content_data.get("markdown", "")
            if not markdown_content:
                logger.warning(f"No markdown content for {url}")
                return False
            
            # Determine file path
            file_path = url_to_filepath(url)
            
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Add metadata header
            metadata = content_data.get("metadata", {})
            header = f"""---
title: {metadata.get('title', 'Untitled')}
source: {url}
scraped: {datetime.now().isoformat()}
---

"""
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(header + markdown_content)
            
            logger.info(f"Saved: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving content for {url}: {str(e)}")
            return False
    
    def scrape_batch(self, urls: List[str], progress_bar: bool = True) -> Dict:
        """Scrape multiple URLs with progress tracking"""
        results = {
            "success": [],
            "failed": [],
            "total": len(urls)
        }
        
        # Progress bar
        pbar = tqdm(total=len(urls), desc="Scraping pages") if progress_bar else None
        
        # Process URLs with rate limiting
        for i, url in enumerate(urls):
            try:
                # Rate limiting
                if i > 0:
                    time.sleep(SCRAPE_DELAY)
                
                # Scrape content
                content_data = self.scrape_with_fallback(url)
                
                if content_data:
                    # Save content
                    if self.save_content(url, content_data):
                        results["success"].append(url)
                        self.scraped_count += 1
                    else:
                        results["failed"].append(url)
                else:
                    results["failed"].append(url)
                
            except KeyboardInterrupt:
                logger.info("Scraping interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {str(e)}")
                results["failed"].append(url)
            
            if pbar:
                pbar.update(1)
        
        if pbar:
            pbar.close()
        
        return results


def load_links_inventory(file_path: str = "links_inventory.json") -> Dict:
    """Load links from inventory file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Links inventory not found: {file_path}")
        logger.info("Please run 'python scripts/discover_links.py' first")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing links inventory: {e}")
        sys.exit(1)


def main():
    """Main scraping function"""
    global OUTPUT_DIR, SCRAPE_DELAY, MAX_RETRIES
    
    parser = argparse.ArgumentParser(description="Scrape CIROH documentation using Firecrawl API")
    parser.add_argument("--input", default="links_inventory.json", help="Input links inventory file")
    parser.add_argument("--output", default=OUTPUT_DIR, help="Output directory for scraped content")
    parser.add_argument("--category", help="Scrape only specific category")
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES, help="Maximum retry attempts")
    parser.add_argument("--delay", type=float, default=SCRAPE_DELAY, help="Delay between requests")
    parser.add_argument("--resume", action="store_true", help="Resume from previous scraping session")
    
    args = parser.parse_args()
    
    # Check API key
    if not FIRECRAWL_API_KEY:
        logger.error("FIRECRAWL_API_KEY not found in environment variables!")
        logger.info("Please set up your .env file with your Firecrawl API key")
        sys.exit(1)
    
    # Update global settings
    OUTPUT_DIR = args.output
    SCRAPE_DELAY = args.delay
    MAX_RETRIES = args.max_retries
    
    # Load links inventory
    inventory = load_links_inventory(args.input)
    
    # Collect all URLs to scrape
    all_urls = []
    categories_to_scrape = []
    
    if args.category:
        # Scrape specific category
        if args.category in inventory["categories"]:
            category_data = inventory["categories"][args.category]
            all_urls.extend(category_data["links"])
            categories_to_scrape.append(args.category)
        else:
            logger.error(f"Category '{args.category}' not found in inventory")
            sys.exit(1)
    else:
        # Scrape all categories
        for category, data in inventory["categories"].items():
            all_urls.extend(data["links"])
            categories_to_scrape.append(category)
    
    # Check for existing files if resuming
    if args.resume:
        existing_urls = []
        for url in all_urls[:]:
            file_path = url_to_filepath(url)
            if os.path.exists(file_path):
                existing_urls.append(url)
                all_urls.remove(url)
        
        if existing_urls:
            logger.info(f"Skipping {len(existing_urls)} already scraped URLs")
    
    # Initialize scraper
    logger.info("=== CIROH Documentation Scraper ===")
    logger.info(f"Categories to scrape: {', '.join(categories_to_scrape)}")
    logger.info(f"Total URLs to scrape: {len(all_urls)}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Rate limit delay: {SCRAPE_DELAY}s")
    logger.info("")
    
    scraper = FirecrawlScraper(FIRECRAWL_API_KEY)
    
    # Start scraping
    start_time = time.time()
    results = scraper.scrape_batch(all_urls)
    elapsed_time = time.time() - start_time
    
    # Summary
    logger.info("\n=== Scraping Summary ===")
    logger.info(f"Total URLs processed: {results['total']}")
    logger.info(f"Successfully scraped: {len(results['success'])}")
    logger.info(f"Failed: {len(results['failed'])}")
    logger.info(f"Time elapsed: {elapsed_time:.2f} seconds")
    logger.info(f"Average time per URL: {elapsed_time/results['total']:.2f} seconds")
    
    # Save failed URLs for retry
    if results["failed"]:
        failed_file = "failed_urls.txt"
        with open(failed_file, 'w') as f:
            f.write(f"# Failed URLs - {datetime.now().isoformat()}\n")
            for url in results["failed"]:
                f.write(f"{url}\n")
        logger.info(f"\nFailed URLs saved to: {failed_file}")
    
    # Save error log
    if scraper.error_log:
        error_file = "scraping_errors.json"
        with open(error_file, 'w') as f:
            json.dump(scraper.error_log, f, indent=2)
        logger.info(f"Error details saved to: {error_file}")
    
    logger.info("\n✅ Scraping complete!")
    logger.info(f"Content saved to: {OUTPUT_DIR}/")
    
    if len(results['success']) > 0:
        logger.info("\nNext step: Run 'python scripts/validate_results.py' to validate results")


if __name__ == "__main__":
    main()