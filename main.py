import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from datetime import datetime

# Configuration
HEADLESS = True  # Set to True to run browser in headless mode
BASE_URL = "https://www.uedayagi.com/dailysignal"

def setup_driver():
    """Initialize and configure Chrome driver with download settings"""
    # Set up download directory
    download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"Created download directory: {download_dir}")
    else:
        print(f"Using download directory: {download_dir}")

    # Configure Chrome options
    options = uc.ChromeOptions()
    
    # Download settings
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    # Headless configuration
    if HEADLESS:
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
    else:
        options.add_argument('--start-maximized')

    # Initialize driver
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=140)

    return driver, download_dir

def get_most_recent_report_link(driver, wait):
    """Find and return the most recent report link from the archive page"""
    print("Looking for the most recent report...")
    
    try:
        # Wait for the report list to load
        report_list = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "article.report-archive-article ul")
        ))
        
        # Find the first <li> element (most recent report)
        first_report = report_list.find_element(By.TAG_NAME, "li")
        
        # Get the link element
        link = first_report.find_element(By.TAG_NAME, "a")
        
        # Extract date and title for logging
        date_span = link.find_element(By.CLASS_NAME, "date")
        title_span = link.find_element(By.CLASS_NAME, "ttl")
        
        report_url = link.get_attribute("href")
        report_date = date_span.text
        report_title = title_span.text
        
        print(f"Found most recent report:")
        print(f"  Date: {report_date}")
        print(f"  Title: {report_title}")
        print(f"  URL: {report_url}")
        
        return link, report_url, report_date
        
    except Exception as e:
        print(f"Error finding report link: {e}")
        raise

def click_pdf_download_button(driver, wait):
    """Find and click the PDF download button on the report page"""
    print("\nLooking for PDF download button...")
    
    try:
        # Wait for the PDF button to be present
        # Using multiple strategies to find the button
        pdf_button = None
        
        # Strategy 1: Find by class name
        try:
            pdf_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "a.report-dl-button.green-button")
            ))
            print("Found PDF button using CSS selector")
        except:
            pass
        
        # Strategy 2: Find by text content
        if not pdf_button:
            try:
                pdf_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(@class, 'report-dl-button') and contains(text(), 'PDF')]")
                ))
                print("Found PDF button using XPath")
            except:
                pass
        
        # Strategy 3: Find by href pattern
        if not pdf_button:
            try:
                pdf_button = driver.find_element(By.XPATH, "//a[contains(@href, '.pdf')]")
                print("Found PDF button by href pattern")
            except:
                pass
        
        if pdf_button:
            pdf_url = pdf_button.get_attribute("href")
            print(f"PDF URL: {pdf_url}")
            
            # Scroll to button
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", pdf_button)
            time.sleep(1)
            
            # Highlight the button (optional, for visibility)
            driver.execute_script("""
                arguments[0].style.border = '3px solid red';
                arguments[0].style.backgroundColor = 'yellow';
            """, pdf_button)
            
            print("Clicking PDF download button...")
            pdf_button.click()
            print("PDF download initiated!")
            
            return pdf_url
        else:
            raise Exception("Could not find PDF download button")
            
    except Exception as e:
        print(f"Error clicking PDF button: {e}")
        raise

def wait_for_download(download_dir, timeout=30):
    """Wait for the PDF download to complete"""
    print("\nWaiting for download to complete...")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check for PDF files in download directory
        files = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
        
        # Check if there are any .crdownload files (Chrome's temporary download files)
        temp_files = [f for f in os.listdir(download_dir) if f.endswith('.crdownload')]
        
        if files and not temp_files:
            print(f"Download complete! File: {files[-1]}")
            return os.path.join(download_dir, files[-1])
        
        time.sleep(1)
    
    print("Download timeout reached")
    return None

def main():
    driver = None
    
    try:
        # Initialize driver
        driver, download_dir = setup_driver()
        wait = WebDriverWait(driver, 15)
        
        # Navigate to main page
        print(f"Navigating to {BASE_URL}...")
        driver.get(BASE_URL)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(3)
        
        # Get the most recent report link
        report_link, report_url, report_date = get_most_recent_report_link(driver, wait)
        
        # Click the report link
        print(f"\nNavigating to report page...")
        report_link.click()
        
        # Wait for report page to load
        print("Waiting for report page to load...")
        time.sleep(3)
        
        # Click the PDF download button
        pdf_url = click_pdf_download_button(driver, wait)
        
        # Wait for download to complete
        time.sleep(5)
        downloaded_file = wait_for_download(download_dir)
        
        if downloaded_file:
            print(f"\n✓ Successfully downloaded: {downloaded_file}")
            print(f"✓ Report date: {report_date}")
        else:
            print("\n✗ Download may not have completed within timeout")
        
        print("\nScript completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\nClosing browser...")
            time.sleep(2)  # Brief pause to see final state
            driver.quit()
            print("Browser closed.")

if __name__ == "__main__":
    main()