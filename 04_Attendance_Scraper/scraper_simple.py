import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_my_attendance():
    # --- 1. SETTINGS & CREDENTIALS ---
    EMAIL = "Panchasarapoojan2004@gmail.com"
    PASSWORD = "YOUR_PASSWORD_HERE" # Put your real password here
    
    LOGIN_URL = "https://attendence-system-1910.vercel.app/users/login"
    DATA_URL = "https://attendence-system-1910.vercel.app/students/current/attendances"

    # --- 2. START THE ROBOT BROWSER ---
    print("Starting the browser...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        # --- 3. GO TO LOGIN PAGE & TYPE CREDENTIALS ---
        print("Going to login page...")
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 15) # We will wait up to 15 seconds for pages to load

        # Find the email and password boxes by their 'type'
        email_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        password_box = driver.find_element(By.XPATH, "//input[@type='password']")
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")

        print("Typing email and password...")
        email_box.send_keys(EMAIL)
        password_box.send_keys(PASSWORD)
        
        print("Clicking login...")
        login_button.click()

        # Wait 5 seconds to let the server process the login
        time.sleep(5) 

        # --- 4. GO TO ATTENDANCE PAGE ---
        print("Moving to attendance page...")
        driver.get(DATA_URL)
        
        # Wait until a table appears on the screen
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(3) # Give it 3 extra seconds just to be fully loaded

        # --- 5. GRAB DATA AND SAVE TO EXCEL ---
        print("Reading the table...")
        page_source_code = driver.page_source
        
        # Pandas finds all tables in the source code
        found_tables = pd.read_html(page_source_code)
        
        if len(found_tables) > 0:
            # We take the first table it found
            attendance_data = found_tables[0] 
            
            # Save it as an Excel file
            attendance_data.to_excel("My_Attendance.xlsx", index=False)
            print("✅ SUCCESS! Data saved to 'My_Attendance.xlsx'")
        else:
            print("❌ Could not find a table on the page.")

    except Exception as error:
        print(f"❌ An error stopped the script: {error}")
        
    finally:
        # --- 6. CLEAN UP ---
        print("Closing the browser...")
        driver.quit()

# This tells Python to run the function above
if __name__ == "__main__":
    scrape_my_attendance()