
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

def microsoft_print_to_pdf(page, file_name):
    """Simulate Microsoft Print to PDF using a pre-configured virtual printer."""
    try:
        page.keyboard.press("Control+P")  # Open the print dialog
        print("Triggered print dialog for Microsoft Print to PDF")
        # Add a delay for the system to process the print dialog
        page.wait_for_timeout(2000)
        page.keyboard.press("Enter")  # Confirm the print
        print(f"Simulated saving to Microsoft Print to PDF: {file_name}")
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

        # Simulate Microsoft Print to PDF
        microsoft_print_to_pdf(page, file_name_microsoft_print_to_pdf)

        browser.close()

def load_links_from_json(file_path):
    """Load links from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        if not isinstance(data, dict) or 'links' not in data or not isinstance(data['links'], list):
            raise ValueError("JSON must contain a 'links' key with a list of URLs.")
        return data['links']

def main():
    json_file_path = "cat.json"
    output_dir = "output_pdfs"  # Directory to save PDFs
    os.makedirs(output_dir, exist_ok=True)

    links = load_links_from_json(json_file_path)
    print(f"Loaded links: {links}")

    for link in links:
        process_link(link, output_dir)

if __name__ == "__main__":
    main()
