#!/usr/bin/env python3
"""
Setup script to verify environment and dependencies for CIROH documentation scraper
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """Check if Python version meets requirements"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. You have {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True


def check_package(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name.split('>=')[0])
    return spec is not None


def install_requirements():
    """Install required packages from requirements.txt"""
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    print("\nInstalling required packages...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False


def check_env_file():
    """Check if .env file exists and has required keys"""
    env_file = Path(__file__).parent.parent / ".env"
    env_example = Path(__file__).parent.parent / ".env.example"
    
    if not env_file.exists():
        print("\n⚠️  .env file not found")
        if env_example.exists():
            print("Creating .env from .env.example...")
            env_example.rename(env_file)
            print("✅ .env file created. Please edit it and add your API keys.")
            return False
        else:
            print("❌ .env.example not found either!")
            return False
    
    # Check for required keys
    required_keys = ["FIRECRAWL_API_KEY"]
    missing_keys = []
    
    with open(env_file, 'r') as f:
        content = f.read()
        for key in required_keys:
            if key not in content:
                missing_keys.append(key)
    
    if missing_keys:
        print(f"⚠️  Missing required environment variables: {', '.join(missing_keys)}")
        print("Please edit .env file and add the missing values.")
        return False
    
    # Check if API key is still the placeholder
    if "your_firecrawl_api_key_here" in content:
        print("⚠️  Please replace 'your_firecrawl_api_key_here' with your actual API key")
        return False
    
    print("✅ .env file configured")
    return True


def create_directories():
    """Create necessary directories"""
    directories = [
        Path(__file__).parent.parent / "docs_ciroh_org",
        Path(__file__).parent.parent / "logs",
        Path(__file__).parent.parent / "output"
    ]
    
    print("\nCreating directories...")
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ {directory}")
    
    return True


def main():
    """Main setup function"""
    print("=== CIROH Documentation Scraper Setup ===\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("\n⚠️  Some packages failed to install. You may need to install them manually.")
    
    # Check environment file
    env_ready = check_env_file()
    
    # Create directories
    create_directories()
    
    # Final status
    print("\n=== Setup Summary ===")
    if env_ready:
        print("✅ Environment is ready!")
        print("\nNext steps:")
        print("1. Run: python scripts/discover_links.py")
        print("2. Run: python scripts/scrape_with_firecrawl.py")
        print("3. Run: python scripts/validate_results.py")
    else:
        print("⚠️  Environment setup incomplete!")
        print("\nPlease:")
        print("1. Edit .env file and add your Firecrawl API key")
        print("2. Re-run this setup script")
        print("\nTo get a Firecrawl API key:")
        print("- Visit: https://www.firecrawl.dev")
        print("- Sign up for a free account")
        print("- Copy your API key from the dashboard")


if __name__ == "__main__":
    main()