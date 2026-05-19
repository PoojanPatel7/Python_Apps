import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# --- HELPER FUNCTION: DROPDOWN SELECTOR ---
def select_dropdown(driver, wait, label_text, option_text):
    print(f"   -> Setting {label_text} to '{option_text}'")
    try:
        label = wait.until(EC.presence_of_element_located((By.XPATH, f"//label[contains(text(), '{label_text}')]")))
        dropdown_box = label.find_element(By.XPATH, "./following-sibling::div//div[contains(@class, 'dropdown-selected-option')]")
        driver.execute_script("arguments[0].click();", dropdown_box)
        time.sleep(1) 
        
        option = wait.until(EC.presence_of_element_located((By.XPATH, f"//*[text()='{option_text}']")))
        driver.execute_script("arguments[0].click();", option)
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Failed to set {label_text}: {e}")

def fully_automated_scraper():
    # ==========================================
    # 1. YOUR SETTINGS
    # ==========================================
    EMAIL = "panchasarapoojan2004@gmail.com"
    PASSWORD = "Dcs@2023" # Put your real password here
    
    LOGIN_URL = "https://attendence-system-1910.vercel.app/users/login"
    ATTENDANCE_URL = "https://attendence-system-1910.vercel.app/students/current/attendances"
    # ==========================================

    print("🚀 Waking up the Ghost Bot...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 15) 
    master_data = [] 

    try:
        # --- 2. LOG IN ---
        print("\n🔒 Logging in...")
        driver.get(LOGIN_URL)
        email_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        password_box = driver.find_element(By.XPATH, "//input[@type='password']")
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")

        email_box.send_keys(EMAIL)
        password_box.send_keys(PASSWORD)
        driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(4) 

        # --- 3. GO TO ATTENDANCE PAGE ---
        print("\n⚙️ Loading attendance page (using default selections)...")
        driver.get(ATTENDANCE_URL)
        wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Select Subjects')]")))
        
        # Give the site an extra moment to load its default state data natively
        time.sleep(2) 
        
        # --- 4. GET ALL SUBJECTS ---
        subject_label = driver.find_element(By.XPATH, "//label[contains(text(), 'Select Subjects')]")
        subject_dropdown_box = subject_label.find_element(By.XPATH, "./following-sibling::div//div[contains(@class, 'dropdown-selected-option')]")
        driver.execute_script("arguments[0].click();", subject_dropdown_box)
        time.sleep(1) 
        
        raw_options = subject_label.find_element(By.XPATH, "./following-sibling::div").text.split('\n')
        all_subjects = [sub.strip() for sub in raw_options if sub.strip() and sub.strip().lower() != 'none']
        driver.execute_script("arguments[0].click();", subject_dropdown_box) 
        time.sleep(1)

        print(f"✅ Found {len(all_subjects)} subjects based on default selections.")

        # --- 5. THE MASTER LOOP ---
        for subject in all_subjects:
            if "web" in subject.lower():
                print(f"\n⏭️ Skipping Web Subject: {subject}")
                continue
                
            print(f"\n" + "-"*50)
            print(f"📖 Processing: {subject}")
            print("-"*50)
            
            # Select Subject and Click View
            select_dropdown(driver, wait, "Select Subjects", subject)
            view_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'View Attendance')]")
            driver.execute_script("arguments[0].click();", view_btn)
            
            # Wait for Loading Spinner to disappear
            try:
                wait.until_not(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Loading...')]")))
            except TimeoutException:
                pass
            time.sleep(2) # Give the rows a moment to paint on screen
            
            # Check for completely empty subjects
            try:
                empty_message = driver.find_elements(By.XPATH, "//*[contains(text(), 'There is no attendances found for you')]")
                if len(empty_message) > 0:
                    print("   ⚠️ Subject is empty. Skipping to next.")
                    go_back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Go Back')]")
                    driver.execute_script("arguments[0].click();", go_back_btn)
                    time.sleep(1.5)
                    continue
            except:
                pass

            # Parse Expected Total
            try:
                total_text_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Total Attendances:')]")
                expected_total = int(re.search(r'\d+', total_text_element.text).group())
            except (NoSuchElementException, AttributeError):
                expected_total = 0
                
            print(f"   🎯 TARGET TO FIND: {expected_total} records")

            if expected_total > 0:
                page_number = 1
                subject_records_scraped = 0
                
                # --- 6. PAGINATION LOOP ---
                while subject_records_scraped < expected_total:
                    print(f"   📄 Scanning Page {page_number}...")
                    
                    rows = driver.find_elements(By.XPATH, "//*[contains(@class, 'bg-green') or contains(@class, 'bg-red')]")
                    
                    if len(rows) == 0:
                        break # Break if page is broken/empty
                        
                    # 🔴 MEMORIZE THE TOP ROW DATA SO WE KNOW WHEN IT CHANGES
                    top_row_text_before_click = rows[0].text
                    
                    for row in rows:
                        try:
                            row_html = row.get_attribute("outerHTML").lower()
                            row_text = row.text
                            
                            if "/" in row_text and ":" in row_text:
                                text_lines = [line.strip() for line in row_text.replace('\r', '').split('\n') if line.strip()]
                                
                                if len(text_lines) >= 4:
                                    is_present = "bg-green" in row_html or "rgb(34, 197, 94" in row_html
                                    
                                    record = {
                                        "Subject": subject,
                                        "Date": text_lines[0],
                                        "From Time": text_lines[1],
                                        "To Time": text_lines[2],
                                        "Topic": " ".join(text_lines[3:]), 
                                        "Status": "Present" if is_present else "Absent"
                                    }
                                    
                                    # Anti-Duplicate Check
                                    if record not in master_data:
                                        master_data.append(record)
                                        subject_records_scraped += 1
                                        
                        except StaleElementReferenceException:
                            continue
                    
                    print(f"      ✔️ Scraped {subject_records_scraped} / {expected_total} records.")

                    if subject_records_scraped >= expected_total:
                        print(f"   ✅ Target Reached! All records collected.")
                        break

                    # --- CLICK NEXT AND WAIT FOR PAGE TO FLIP ---
                    try:
                        all_buttons = driver.find_elements(By.TAG_NAME, "button")
                        nav_buttons = [b for b in all_buttons if b.text.strip().lower() not in ['log in', 'go back', 'view attendance']]
                        
                        if len(nav_buttons) > 0:
                            next_btn = nav_buttons[-1] # Target the > arrow
                            
                            is_disabled = next_btn.get_attribute("disabled") or "opacity" in next_btn.get_attribute("class")
                            
                            if is_disabled:
                                print("   🛑 Next button is disabled. End of pages.")
                                break
                            else:
                                print("   ➡️ Clicking next page arrow...")
                                driver.execute_script("arguments[0].click();", next_btn)
                                page_number += 1
                                
                                # 🔴 THE SPEED FIX: WAIT FOR THE DATA TO PHYSICALLY CHANGE
                                wait_time = 0
                                while wait_time < 10: # Wait up to 10 seconds for the new page to load
                                    time.sleep(0.5)
                                    try:
                                        new_rows = driver.find_elements(By.XPATH, "//*[contains(@class, 'bg-green') or contains(@class, 'bg-red')]")
                                        if len(new_rows) > 0 and new_rows[0].text != top_row_text_before_click:
                                            # The text has changed! The new page is ready.
                                            break 
                                    except StaleElementReferenceException:
                                        pass
                                    wait_time += 0.5
                                    
                        else:
                            break
                    except Exception as e:
                        print(f"   🛑 Pagination error: {e}")
                        break 

            # --- 7. GO BACK TO MENU ---
            print(f"Going back to menu...")
            go_back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Go Back')]")
            driver.execute_script("arguments[0].click();", go_back_btn)
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Select Subject For Attendance')]")))
            time.sleep(1.5)

        # --- 8. FINAL EXPORT ---
        print("\n" + "="*50)
        print(f"🎉 100% COMPLETE! Total Master Records Scraped: {len(master_data)}")
        if len(master_data) > 0:
            df = pd.DataFrame(master_data)
            excel_name = "Automated_Master_Attendance002.xlsx"
            df.to_excel(excel_name, index=False)
            print(f"✅ Your data file is saved to: {excel_name}")
        print("="*50)

    except Exception as e:
        print(f"\n❌ A critical error stopped the bot: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    fully_automated_scraper()