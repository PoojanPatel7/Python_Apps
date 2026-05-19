from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd

def advanced_universal_scraper():
    url = input("Enter the website link (e.g., https://example.com): ")
    
    # 1. Spin up a hidden browser to render JavaScript
    print(f"\nLaunching hidden browser to render {url}...")
    
    with sync_playwright() as p:
        # Launch Chromium (headless=True means it runs invisibly in the background)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Go to the URL and wait until all network activity stops (fully loaded)
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Grab the fully rendered HTML
            html_content = page.content()
            print("Successfully rendered and captured the website code!")
        except Exception as e:
            print(f"Error loading the website: {e}")
            browser.close()
            return
            
        browser.close()

    # 2. Parse the rendered code
    soup = BeautifulSoup(html_content, 'html.parser')

    # 3. Give the user extraction options
    print("\nWebsite analyzed! What kind of data do you want to extract?")
    print("1. All Links (URLs and text)")
    print("2. All Headings (H1 to H4)")
    print("3. All Paragraphs (Text content)")
    print("4. All Images (Image sources and alt text)")
    
    choice = input("Enter your choice (1, 2, 3, or 4): ")
    data = []

    # 4. Extract based on choice
    if choice == '1':
        print("Extracting links...")
        for a in soup.find_all('a', href=True):
            text = a.text.strip()
            if text:
                data.append({'Text': text, 'URL': a['href']})
                
    elif choice == '2':
        print("Extracting headings...")
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = h.text.strip()
            if text:
                data.append({'Level': h.name, 'Text': text})
                
    elif choice == '3':
        print("Extracting paragraphs...")
        for p in soup.find_all('p'):
            text = p.text.strip()
            if text:
                data.append({'Paragraph': text})
                
    elif choice == '4':
        print("Extracting images...")
        for img in soup.find_all('img', src=True):
            data.append({'Image Source': img['src'], 'Alt Text': img.get('alt', 'No alt text')})
    else:
        print("Invalid choice. Exiting.")
        return

    if not data:
        print("No data found for your selection.")
        return

    # 5. Save to Excel
    df = pd.DataFrame(data)
    filename = input("\nEnter the name for your Excel file (without .xlsx): ")
    filename = f"{filename}.xlsx"

    try:
        df.to_excel(filename, index=False)
        print(f"\nBoom! Extracted {len(data)} rows of data.")
        print(f"Data has been saved to '{filename}'.")
    except Exception as e:
        print(f"Error saving to Excel: {e}")

if __name__ == "__main__":
    advanced_universal_scraper()