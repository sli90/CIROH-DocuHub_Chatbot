#!/usr/bin/env python3
"""
Validate scraped documentation results
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote
from typing import Dict, List, Tuple
import logging
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configuration
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "docs_ciroh_org")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def url_to_filepath(url: str, base_dir: str = OUTPUT_DIR) -> str:
    """Convert URL to expected local file path"""
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


def check_file_validity(file_path: str) -> Dict:
    """Check if a scraped file is valid"""
    result = {
        "exists": False,
        "size": 0,
        "has_content": False,
        "has_metadata": False,
        "word_count": 0,
        "issues": []
    }
    
    if not os.path.exists(file_path):
        result["issues"].append("File does not exist")
        return result
    
    result["exists"] = True
    result["size"] = os.path.getsize(file_path)
    
    if result["size"] == 0:
        result["issues"].append("File is empty")
        return result
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for metadata header
            if content.startswith("---"):
                result["has_metadata"] = True
                # Find end of metadata
                end_marker = content.find("---", 3)
                if end_marker > 0:
                    content_body = content[end_marker + 3:]
                else:
                    content_body = content
            else:
                content_body = content
                result["issues"].append("Missing metadata header")
            
            # Check content
            content_body = content_body.strip()
            if len(content_body) > 50:  # Minimum content threshold
                result["has_content"] = True
                result["word_count"] = len(content_body.split())
            else:
                result["issues"].append(f"Insufficient content (only {len(content_body)} characters)")
            
            # Check for common scraping failures
            error_indicators = [
                "404 Not Found",
                "403 Forbidden",
                "Error loading page",
                "Page not found",
                "Access denied"
            ]
            
            for indicator in error_indicators:
                if indicator.lower() in content.lower():
                    result["issues"].append(f"Content indicates error: '{indicator}'")
                    break
    
    except Exception as e:
        result["issues"].append(f"Error reading file: {str(e)}")
    
    return result


def validate_category(category: str, links: List[str]) -> Dict:
    """Validate all files in a category"""
    category_result = {
        "total_links": len(links),
        "files_found": 0,
        "files_valid": 0,
        "files_missing": [],
        "files_invalid": [],
        "total_word_count": 0,
        "issues_by_file": {}
    }
    
    for url in links:
        file_path = url_to_filepath(url)
        validation = check_file_validity(file_path)
        
        if validation["exists"]:
            category_result["files_found"] += 1
            
            if not validation["issues"]:
                category_result["files_valid"] += 1
                category_result["total_word_count"] += validation["word_count"]
            else:
                category_result["files_invalid"].append(url)
                category_result["issues_by_file"][url] = validation["issues"]
        else:
            category_result["files_missing"].append(url)
    
    return category_result


def generate_report(validation_results: Dict) -> str:
    """Generate human-readable validation report"""
    report_lines = [
        "# CIROH Documentation Scraping Validation Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        f"- Total categories: {validation_results['total_categories']}",
        f"- Total expected files: {validation_results['total_expected']}",
        f"- Total files found: {validation_results['total_found']}",
        f"- Total valid files: {validation_results['total_valid']}",
        f"- Total missing files: {validation_results['total_missing']}",
        f"- Total invalid files: {validation_results['total_invalid']}",
        f"- Success rate: {validation_results['success_rate']:.1f}%",
        f"- Total word count: {validation_results['total_words']:,}",
        "",
        "## Category Breakdown"
    ]
    
    for category, results in validation_results["categories"].items():
        report_lines.extend([
            "",
            f"### {category}",
            f"- Expected: {results['total_links']} files",
            f"- Found: {results['files_found']} files",
            f"- Valid: {results['files_valid']} files",
            f"- Word count: {results['total_word_count']:,}"
        ])
        
        if results["files_missing"]:
            report_lines.append(f"- **Missing files ({len(results['files_missing'])}):**")
            for url in results["files_missing"]:
                report_lines.append(f"  - {url}")
        
        if results["files_invalid"]:
            report_lines.append(f"- **Invalid files ({len(results['files_invalid'])}):**")
            for url in results["files_invalid"]:
                issues = results["issues_by_file"][url]
                report_lines.append(f"  - {url}")
                for issue in issues:
                    report_lines.append(f"    - {issue}")
    
    # Add recommendations
    if validation_results["total_missing"] > 0 or validation_results["total_invalid"] > 0:
        report_lines.extend([
            "",
            "## Recommendations",
            ""
        ])
        
        if validation_results["total_missing"] > 0:
            report_lines.extend([
                "### For Missing Files:",
                "1. Re-run the scraper with resume option: `python scripts/scrape_with_firecrawl.py --resume`",
                "2. Check if the URLs are still valid on the source website",
                "3. Review failed_urls.txt for specific errors",
                ""
            ])
        
        if validation_results["total_invalid"] > 0:
            report_lines.extend([
                "### For Invalid Files:",
                "1. Check scraping_errors.json for detailed error information",
                "2. Try increasing retry attempts: `--max-retries 5`",
                "3. Consider using fallback scraping for problematic pages",
                "4. Manually verify and fix files with insufficient content"
            ])
    
    return "\n".join(report_lines)


def main():
    """Main validation function"""
    logger.info("=== CIROH Documentation Validation ===")
    
    # Load links inventory
    inventory_file = "links_inventory.json"
    if not os.path.exists(inventory_file):
        logger.error(f"Links inventory not found: {inventory_file}")
        logger.info("Please run 'python scripts/discover_links.py' first")
        sys.exit(1)
    
    with open(inventory_file, 'r') as f:
        inventory = json.load(f)
    
    # Validate each category
    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "total_categories": 0,
        "total_expected": 0,
        "total_found": 0,
        "total_valid": 0,
        "total_missing": 0,
        "total_invalid": 0,
        "total_words": 0,
        "categories": {}
    }
    
    logger.info(f"Validating {len(inventory['categories'])} categories...")
    
    for category, data in inventory["categories"].items():
        logger.info(f"\nValidating {category}...")
        category_results = validate_category(category, data["links"])
        validation_results["categories"][category] = category_results
        
        # Update totals
        validation_results["total_categories"] += 1
        validation_results["total_expected"] += category_results["total_links"]
        validation_results["total_found"] += category_results["files_found"]
        validation_results["total_valid"] += category_results["files_valid"]
        validation_results["total_missing"] += len(category_results["files_missing"])
        validation_results["total_invalid"] += len(category_results["files_invalid"])
        validation_results["total_words"] += category_results["total_word_count"]
        
        # Log category summary
        logger.info(f"  - Found: {category_results['files_found']}/{category_results['total_links']}")
        logger.info(f"  - Valid: {category_results['files_valid']}")
        if category_results["files_missing"]:
            logger.warning(f"  - Missing: {len(category_results['files_missing'])}")
        if category_results["files_invalid"]:
            logger.warning(f"  - Invalid: {len(category_results['files_invalid'])}")
    
    # Calculate success rate
    if validation_results["total_expected"] > 0:
        validation_results["success_rate"] = (
            validation_results["total_valid"] / validation_results["total_expected"] * 100
        )
    else:
        validation_results["success_rate"] = 0
    
    # Generate report
    report = generate_report(validation_results)
    
    # Save report
    report_file = "validation_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save detailed JSON results
    json_file = "validation_results.json"
    with open(json_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    # Print summary
    logger.info("\n=== Validation Summary ===")
    logger.info(f"Total files expected: {validation_results['total_expected']}")
    logger.info(f"Total files found: {validation_results['total_found']}")
    logger.info(f"Total valid files: {validation_results['total_valid']}")
    logger.info(f"Success rate: {validation_results['success_rate']:.1f}%")
    logger.info(f"Total content: {validation_results['total_words']:,} words")
    
    if validation_results["total_missing"] > 0:
        logger.warning(f"\n⚠️  Missing files: {validation_results['total_missing']}")
    
    if validation_results["total_invalid"] > 0:
        logger.warning(f"⚠️  Invalid files: {validation_results['total_invalid']}")
    
    logger.info(f"\n✅ Validation complete!")
    logger.info(f"Detailed report saved to: {report_file}")
    logger.info(f"JSON results saved to: {json_file}")
    
    # Exit with appropriate code
    if validation_results["success_rate"] >= 95:
        logger.info("\n🎉 Excellent! Over 95% of files successfully scraped.")
        sys.exit(0)
    elif validation_results["success_rate"] >= 80:
        logger.info("\n✅ Good! Over 80% of files successfully scraped.")
        logger.info("Consider re-running scraper for missing files.")
        sys.exit(0)
    else:
        logger.warning("\n⚠️  Success rate below 80%. Please review issues and re-run scraper.")
        sys.exit(1)


if __name__ == "__main__":
    main()