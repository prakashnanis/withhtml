
import subprocess
import json
import os
import urllib.parse
from playwright.sync_api import sync_playwright

def save_as_pdf(page, file_name):
    """Generate PDF using Playwright's built-in method."""
    try:
        page.pdf(path=file_name, format="A4", print_background=True)
        print(f"Saved PDF using Playwright: {file_name}")
    except Exception as e:
        print(f"Failed to save PDF using Playwright: {e}")

def microsoft_print_to_pdf(page, temp_html, file_name):
    """Simulate Microsoft Print to PDF using a pre-configured virtual printer."""
    try:
        # Save the page content to a temporary HTML file
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(page.content())
        
        # Windows-specific printing to 'Microsoft Print to PDF'
        printer_name = "Microsoft Print to PDF"
        command = [
            "powershell",
            "-Command",
            f"Start-Process -FilePath '{temp_html}' -Verb PrintTo -ArgumentList '{printer_name}', '{file_name}'"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Saved PDF using Microsoft Print to PDF: {file_name}")
        else:
            print(f"Failed to print to PDF: {result.stderr}")
    except Exception as e:
        print(f"Failed to simulate Microsoft Print to PDF: {e}")

def process_link(link, output_dir):
    """Process a single link to generate PDFs."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless mode enabled
        page = browser.new_page()
        page.goto(link, wait_until="domcontentloaded")

        # Extract the filename from the URL (remove https:// and replace slashes with underscores)
        parsed_url = urllib.parse.urlparse(link)
        filename = parsed_url.path.strip("/").replace("/", "_") + ".pdf"
        
        # Generate filenames
        file_name_save_as_pdf = os.path.join(output_dir, f"{filename}_save_as_pdf.pdf")
        file_name_microsoft_print_to_pdf = os.path.join(output_dir, f"{filename}_microsoft_print_to_pdf.pdf")

        # Save as PDF
        save_as_pdf(page, file_name_save_as_pdf)

        # Simulate Microsoft Print to PDF (use HTML)
        temp_html = os.path.join(output_dir, f"{filename}_temp.html")
        microsoft_print_to_pdf(page, temp_html, file_name_microsoft_print_to_pdf)

        browser.close()

def load_links_from_json(file_path):
    """Load links from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("JSON must be an object with categories as keys, each having a list of URLs.")
        return data

def main():
    json_file_path = "cat.json"
    output_dir = "output_pdfs"  # Directory to save PDFs
    os.makedirs(output_dir, exist_ok=True)

    # Load the JSON data and process each link from all categories
    data = load_links_from_json(json_file_path)

    # Prepare a dictionary to store results, where keys are categories
    result_data = {}

    # Iterate over each category in the JSON file, regardless of its name
    for category, links in data.items():
        print(f"Processing category: {category}")
        for link in links:
            process_link(link, output_dir)

    # Save the result data as a new JSON file with categories
    result_json_path = "output_results.json"
    with open(result_json_path, 'w') as f:
        json.dump(result_data, f, indent=4)

    print(f"Results have been saved to: {result_json_path}")

if __name__ == "__main__":
    main()
