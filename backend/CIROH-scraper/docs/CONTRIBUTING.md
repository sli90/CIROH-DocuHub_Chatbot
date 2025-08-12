# Contributing to CIROH Documentation Scraper

Thank you for your interest in contributing to the CIROH Documentation Scraper! This guide will help you get started.

## Ways to Contribute

### 1. Report Issues
- Use GitHub Issues to report bugs
- Include detailed information:
  - Python version
  - Error messages
  - Steps to reproduce
  - Expected vs actual behavior

### 2. Suggest Enhancements
- Open an issue with "Enhancement" label
- Describe the feature and use case
- Discuss before implementing major changes

### 3. Submit Pull Requests
- Fix bugs
- Add features
- Improve documentation
- Optimize performance

## Development Setup

### 1. Fork and Clone
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/yourusername/ciroh-docs-scraper.git
cd ciroh-docs-scraper
```

### 2. Create Branch
```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or bugfix branch
git checkout -b bugfix/issue-description
```

### 3. Set Up Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8 mypy
```

### 4. Make Changes
- Follow existing code style
- Add tests for new features
- Update documentation as needed

### 5. Test Your Changes
```bash
# Run tests
pytest tests/

# Check code style
black --check scripts/
flake8 scripts/

# Type checking
mypy scripts/
```

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use Black for formatting
- Maximum line length: 100 characters
- Use type hints where appropriate

### Docstrings
```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When validation fails
    """
    pass
```

### Imports
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import requests
from bs4 import BeautifulSoup

# Local
from .utils import helper_function
```

## Testing Guidelines

### Unit Tests
```python
# tests/test_scraper.py
import pytest
from scripts.scrape_with_firecrawl import url_to_filepath

def test_url_to_filepath():
    """Test URL to filepath conversion"""
    url = "https://docs.ciroh.org/docs/products/ngiab/intro"
    expected = "docs_ciroh_org/products/ngiab/intro.md"
    assert url_to_filepath(url) == expected
```

### Integration Tests
- Test actual API calls (with mocks)
- Test file I/O operations
- Test error handling

## Pull Request Process

### 1. Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up-to-date with main

### 2. PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### 3. Review Process
- Maintainers will review within 48 hours
- Address feedback promptly
- Be patient and respectful

## Project Structure

```
ciroh-docs-scraper/
├── scripts/              # Main application code
│   ├── __init__.py
│   ├── discover_links.py
│   ├── scrape_with_firecrawl.py
│   └── validate_results.py
├── tests/               # Test files
│   ├── __init__.py
│   ├── test_discovery.py
│   ├── test_scraper.py
│   └── test_validation.py
├── docs/                # Documentation
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
└── README.md
```

## Adding New Features

### 1. New Scraping Method
```python
# scripts/scrapers/new_scraper.py
class NewScraper(BaseScraper):
    """Implementation of new scraping method"""
    
    def scrape(self, url: str) -> Dict:
        """Scrape content from URL"""
        # Implementation
        pass
```

### 2. New Output Format
```python
# scripts/formatters/new_formatter.py
class NewFormatter(BaseFormatter):
    """Format scraped content in new way"""
    
    def format(self, content: Dict) -> str:
        """Format content"""
        # Implementation
        pass
```

## Common Tasks

### Adding a New Product Category
1. Update `PRODUCT_CATEGORIES` in `discover_links.py`
2. Add category to `PREDISCOVERED_LINKS`
3. Test discovery and scraping
4. Update documentation

### Improving Error Handling
1. Identify error scenarios
2. Add specific exception handling
3. Log errors appropriately
4. Add retry logic if needed
5. Update tests

### Performance Optimization
1. Profile code to find bottlenecks
2. Consider async/parallel processing
3. Optimize API calls
4. Add caching where appropriate
5. Benchmark improvements

## Release Process

### Version Numbering
- Follow Semantic Versioning (X.Y.Z)
- X: Major (breaking changes)
- Y: Minor (new features)
- Z: Patch (bug fixes)

### Release Checklist
1. Update version in `__version__`
2. Update CHANGELOG.md
3. Run full test suite
4. Create release branch
5. Tag release
6. Update documentation

## Getting Help

### Resources
- Project README
- API documentation
- GitHub Discussions
- Stack Overflow

### Communication
- Be respectful and patient
- Provide context and examples
- Search existing issues first
- Follow up on your issues/PRs

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- CONTRIBUTORS.md file
- Release notes

Thank you for contributing!