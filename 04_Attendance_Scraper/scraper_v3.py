import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

def scrape_attendmate_by_subject():
    # ==========================================
    # 1. CREDENTIALS & SETTINGS
    # ==========================================
    USERNAME = "dev"
    PASSWORD = "123456"
    
    LOGIN_URL = "https://attendmateweb.vercel.app/login"
    ATTENDANCE_URL = "https://attendmateweb.vercel.app/attendance"
    # ==========================================

    print("🚀 Waking up the Bot...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 15) 
    master_data = [] 

    try:
        # --- 2. LOG IN ---
        print("\n🔒 Logging in to AttendMate...")
        driver.get(LOGIN_URL)
        
        # Wait for the page to hydrate
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Email or Username']"))).send_keys(USERNAME)
        driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(PASSWORD)
        
        sign_in_btn = driver.find_element(By.XPATH, "//button[contains(., 'Sign In')]")
        driver.execute_script("arguments[0].click();", sign_in_btn)

        wait.until(EC.url_contains("/dashboard"))
        print("✅ Login successful!")
        time.sleep(2)

        # --- 3. NAVIGATE TO ATTENDANCE ---
        print("\n⚙️ Navigating to Attendance History...")
        driver.get(ATTENDANCE_URL)
        
        # CRITICAL FIX: Wait for the Next.js spinning loader to disappear
        print("   -> Waiting for page data to load...")
        try:
            wait.until_not(EC.presence_of_element_located((By.CLASS_NAME, "animate-spin")))
        except TimeoutException:
            pass # Continue if the spinner doesn't exist or is already gone
            
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Attendance History')]")))
        time.sleep(2) 

        # --- 4. EXTRACT SUBJECT LIST FROM DROPDOWN ---
        print("\n🔎 Finding available subjects...")
        
        # Robust Dropdown Trigger Locator
        # Looks for the container next to the label, or the text "All Subjects"
        try:
            # First attempt: Target the box displaying the current selection
            dropdown_trigger = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'All Subjects')]/ancestor::button | //*[contains(text(), 'All Subjects')]/parent::div")))
        except TimeoutException:
            # Fallback: Just look for the text anywhere
            dropdown_trigger = driver.find_element(By.XPATH, "//*[contains(text(), 'All Subjects')]")

        # Click to open menu
        driver.execute_script("arguments[0].click();", dropdown_trigger)
        time.sleep(1.5) 

        # Grab all options in the opened menu (React usually uses role='option' or standard list items)
        dropdown_options = driver.find_elements(By.XPATH, "//*[@role='option'] | //li | //div[contains(@class, 'option')]") 
        subject_names = []
        
        for option in dropdown_options:
            text = option.text.strip()
            # Ignore the default "All" option and empty elements
            if text and "All Subjects" not in text and "FILTER" not in text:
                subject_names.append(text)
                
        print(f"✅ Found {len(subject_names)} subjects: {', '.join(subject_names)}")
        
        # Close the dropdown by sending the ESCAPE key
        webdriver.ActionChains(driver).send_keys('\x1b').perform() 
        time.sleep(1)

        # --- 5. LOOP THROUGH EACH SUBJECT ---
        for subject in subject_names:
            print(f"\n" + "="*40)
            print(f"📖 Processing Subject: {subject}")
            print("="*40)
            
            # Re-open the dropdown
            try:
                # Target whatever the currently selected subject text is
                current_selection = driver.find_element(By.XPATH, f"//*[contains(text(), 'FILTER BY SUBJECT')]/following-sibling::* | //button[contains(@aria-haspopup, 'listbox')]")
                driver.execute_script("arguments[0].click();", current_selection)
            except:
                # If we can't find it dynamically, click near the Filter label
                fallback_trigger = driver.find_element(By.XPATH, "//*[contains(text(), 'FILTER BY SUBJECT')]")
                driver.execute_script("arguments[0].click();", fallback_trigger)
                
            time.sleep(1.5)
            
            # Click the target subject from the menu
            subject_option = wait.until(EC.presence_of_element_located((By.XPATH, f"//*[text()='{subject}'] | //span[text()='{subject}']")))
            driver.execute_script("arguments[0].click();", subject_option)
            
            # Wait for the spinner to finish filtering the records
            try:
                wait.until_not(EC.presence_of_element_located((By.CLASS_NAME, "animate-spin")))
            except:
                pass
            time.sleep(2) 

            # --- SCROLL AND EXTRACT FOR THIS SUBJECT ---
            last_record_count = 0
            scroll_attempts = 0
            current_date = "Unknown Date"
            
            while True:
                # Extract headers and cards
                elements = driver.find_elements(By.XPATH, "//*[contains(text(), '202') or contains(text(), 'PRESENT') or contains(text(), 'ABSENT')]")
                valid_elements = [el for el in elements if len(el.text) > 3 and len(el.text) < 150]

                for el in valid_elements:
                    try:
                        text = el.text.strip()
                        
                        # 1. Update the running Date
                        # e.g., "TUE, MAR 17, 2026"
                        if re.search(r'202\d', text) and "PRESENT" not in text and "ABSENT" not in text:
                            current_date = text 
                            continue
                            
                        # 2. Extract the record Card
                        if "PRESENT" in text or "ABSENT" in text:
                            status = "Present" if "PRESENT" in text else "Absent"
                            
                            record = {
                                "Subject": subject,
                                "Date": current_date, # Date only, no time
                                "Status": status
                            }
                            
                            if record not in master_data:
                                master_data.append(record)
                                
                    except StaleElementReferenceException:
                        continue

                # SCROLLING LOGIC
                cards_only = driver.find_elements(By.XPATH, "//div[contains(., 'PRESENT') or contains(., 'ABSENT')]")
                valid_cards = [c for c in cards_only if 10 < len(c.text) < 150]
                
                if len(valid_cards) > 0:
                    driver.execute_script("arguments[0].scrollIntoView();", valid_cards[-1])
                
                time.sleep(2.5)
                
                current_count = len(driver.find_elements(By.XPATH, "//div[contains(., 'PRESENT') or contains(., 'ABSENT')]"))
                if current_count == last_record_count:
                    scroll_attempts += 1
                    if scroll_attempts >= 3:
                        print(f"   🛑 Finished scraping '{subject}'.")
                        break
                else:
                    last_record_count = current_count
                    scroll_attempts = 0

        # --- 6. EXPORT TO EXCEL ---
        print("\n" + "="*50)
        total_scraped = len(master_data)
        if total_scraped > 0:
            df = pd.DataFrame(master_data)
            excel_name = "AttendMate_Filtered_Subjects.xlsx"
            df.to_excel(excel_name, index=False)
            print(f"🎉 100% COMPLETE! {total_scraped} records saved to: {excel_name}")
        else:
            print("⚠️ No data was collected.")
        print("="*50)

    except Exception as e:
        print(f"\n❌ A critical error stopped the bot: {e}")

    finally:
        time.sleep(2)
        driver.quit()

if __name__ == "__main__":
    scrape_attendmate_by_subject()