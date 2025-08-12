#!/bin/bash
# CIROH Documentation Batch Scraping Script
# This script automates the entire scraping workflow

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Functions
print_header() {
    echo -e "${BLUE}====================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}====================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.8"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION found"
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env file not found. Creating from .env.example..."
            cp .env.example .env
            print_error "Please edit .env and add your Firecrawl API key"
            exit 1
        else
            print_error ".env.example not found"
            exit 1
        fi
    fi
    
    # Check for API key
    if grep -q "your_firecrawl_api_key_here" .env; then
        print_error "Please update your Firecrawl API key in .env file"
        exit 1
    fi
    
    print_success "Environment file configured"
}

setup_environment() {
    print_header "Setting Up Environment"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_warning "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install/update dependencies
    print_warning "Installing dependencies..."
    pip install -q -r requirements.txt
    
    print_success "Environment ready"
}

run_step() {
    local step_name=$1
    local script_path=$2
    local description=$3
    
    print_header "$step_name: $description"
    
    if python "$script_path"; then
        print_success "$step_name completed successfully"
        return 0
    else
        print_error "$step_name failed"
        return 1
    fi
}

cleanup_previous_run() {
    print_header "Cleanup Previous Run (Optional)"
    
    if [ -f "failed_urls.txt" ] || [ -f "scraping_errors.json" ]; then
        read -p "Remove previous error logs? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f failed_urls.txt scraping_errors.json
            print_success "Previous error logs removed"
        fi
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --section SECTION    Scrape specific section: products, services, or both (default: both)"
    echo "  --help              Show this help message"
    echo
    echo "Examples:"
    echo "  $0                   # Scrape both products and services"
    echo "  $0 --section products  # Scrape only products"
    echo "  $0 --section services  # Scrape only services"
}

main() {
    # Parse command line arguments
    SECTION="both"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --section)
                SECTION="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate section argument
    if [[ ! "$SECTION" =~ ^(products|services|both)$ ]]; then
        print_error "Invalid section: $SECTION"
        echo "Valid options: products, services, both"
        exit 1
    fi
    
    clear
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║   CIROH Documentation Scraper v1.0        ║"
    echo "║   Automated Batch Processing              ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo "Section to scrape: $(echo $SECTION | tr '[:lower:]' '[:upper:]')"
    echo
    
    # Start timestamp
    START_TIME=$(date +%s)
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Optional cleanup
    cleanup_previous_run
    
    # Step 1: Setup check
    if ! run_step "Step 1" "scripts/setup_environment.py" "Environment Setup & Verification"; then
        exit 1
    fi
    
    # Step 2: Discover links
    if ! run_step "Step 2" "scripts/discover_links.py --section $SECTION" "Discovering Documentation Links"; then
        exit 1
    fi
    
    # Step 3: Scrape content
    echo
    print_warning "Step 3 may take 10-30 minutes depending on rate limits..."
    if ! run_step "Step 3" "scripts/scrape_with_firecrawl.py" "Scraping Documentation Content"; then
        print_warning "Some pages may have failed. Check failed_urls.txt"
        # Don't exit - continue to validation
    fi
    
    # Step 4: Validate results
    if ! run_step "Step 4" "scripts/validate_results.py" "Validating Scraped Content"; then
        print_warning "Validation found issues. Check validation_report.txt"
    fi
    
    # Calculate elapsed time
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))
    
    # Final summary
    print_header "Scraping Complete!"
    
    echo -e "${GREEN}Time elapsed: ${MINUTES}m ${SECONDS}s${NC}"
    echo
    echo "📁 Output locations:"
    echo "   - Scraped content: docs_ciroh_org/"
    echo "   - Links inventory: links_inventory.json"
    echo "   - Validation report: validation_report.txt"
    
    if [ -f "failed_urls.txt" ]; then
        echo
        print_warning "Some URLs failed to scrape. See: failed_urls.txt"
        echo "To retry failed URLs:"
        echo "   python scripts/scrape_with_firecrawl.py --resume"
    fi
    
    echo
    print_success "All done! 🎉"
    echo
    echo "Next steps:"
    echo "1. Review validation_report.txt for any issues"
    echo "2. Browse scraped content in docs_ciroh_org/"
    echo "3. Commit changes to git if satisfied"
}

# Run main function with all arguments
main "$@"