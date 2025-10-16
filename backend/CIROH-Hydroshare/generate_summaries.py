#!/usr/bin/env python3
"""
Script to generate summaries for HydroShare markdown files using Gemini 2.5 API.
Reads markdown files from data/ folder, generates summaries, and saves to CSV.
"""

import os
import csv
import time
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini 2.5 model
model = genai.GenerativeModel('gemini-2.5-pro')

# File paths
CSV_FILE = 'hydroshare_links_list.csv'
PROMPT_FILE = 'dataset_summarization_prompt.txt'
DATA_DIR = 'data'


def read_prompt():
    """Read the summarization prompt from file."""
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def read_markdown_file(filename):
    """Read markdown file from data directory."""
    file_path = os.path.join(DATA_DIR, f"{filename}.md")
    if not os.path.exists(file_path):
        print(f"Warning: File not found: {file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_summary(markdown_content, prompt, max_retries=3):
    """Generate summary using Gemini API with retry logic."""
    for attempt in range(max_retries):
        try:
            # Combine prompt and markdown content
            full_prompt = f"{prompt}\n\n---\n\nMARKDOWN FILE CONTENT:\n\n{markdown_content}"

            # Generate summary
            response = model.generate_content(full_prompt)
            return response.text.strip()

        except Exception as e:
            error_str = str(e)

            # Check if it's a rate limit error
            if "429" in error_str or "quota" in error_str.lower():
                # Extract retry delay if available
                import re
                retry_match = re.search(r'retry in (\d+(?:\.\d+)?)\s*s', error_str)
                wait_time = float(retry_match.group(1)) if retry_match else 15

                print(f"  Rate limit hit. Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time + 1)  # Add 1 second buffer

                if attempt < max_retries - 1:
                    continue

            print(f"Error generating summary: {e}")
            return f"Error: {str(e)}"

    return "Error: Max retries exceeded"


def process_csv():
    """Process CSV file and generate summaries for all entries."""
    # Read the prompt
    prompt = read_prompt()
    print(f"Loaded prompt from {PROMPT_FILE}")

    # Read CSV
    rows = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from {CSV_FILE}")

    # Process each row
    for i, row in enumerate(rows, 1):
        md_file_name = row['md_file_name'].strip()  # Remove leading/trailing spaces
        print(f"\n[{i}/{len(rows)}] Processing: {md_file_name}")

        # Check if summary already exists and is not an error
        if 'Summary' in row and row['Summary'] and not row['Summary'].startswith('Error:'):
            print(f"  ✓ Summary already exists, skipping...")
            continue

        # Read markdown file
        markdown_content = read_markdown_file(md_file_name)
        if markdown_content is None:
            row['Summary'] = "Error: Markdown file not found"
            continue

        # Generate summary
        print(f"  Generating summary...")
        summary = generate_summary(markdown_content, prompt)
        row['Summary'] = summary

        print(f"  ✓ Summary generated ({len(summary)} characters)")

        # Add delay to respect rate limits (10 requests/minute = 6 seconds between requests)
        if i < len(rows):
            time.sleep(7)  # 7 seconds to be safe

    # Write updated CSV
    fieldnames = list(rows[0].keys())
    if 'Summary' not in fieldnames:
        fieldnames.append('Summary')

    with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ All summaries generated and saved to {CSV_FILE}")


if __name__ == "__main__":
    print("=== HydroShare Dataset Summary Generator ===\n")
    process_csv()
