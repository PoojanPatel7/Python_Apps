import streamlit as st
import pandas as pd
import plotly.express as px
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# 1. UI SETUP & CSS
# ==========================================
st.set_page_config(page_title="SYSTEM // ATTENDANCE", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New', Courier, monospace; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { color: #00FF41; }
    .stButton>button { border: 1px solid #00FF41; color: #00FF41; background-color: transparent; width: 100%; font-family: 'Courier New', Courier, monospace;}
    .stButton>button:hover { background-color: #00FF41; color: black; }
    .terminal-box { background-color: #0a0a0a; color: #00FF41; padding: 15px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; height: 300px; overflow-y: auto; border: 1px solid #333;}
    </style>
""", unsafe_allow_html=True)

st.title("/> COMMAND_CENTER_V2.0")
st.markdown("---")

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def log_update(message, log_list, log_container):
    """Pushes a live update to the Streamlit Terminal Box"""
    log_list.append(f"> {message}")
    # Keep only the last 15 lines so it doesn't get infinitely long
    display_logs = "\n".join(log_list[-15:])
    log_container.markdown(f'<div class="terminal-box">{display_logs}</div>', unsafe_allow_html=True)

def select_dropdown(driver, wait, label_text, option_text):
    try:
        label = wait.until(EC.presence_of_element_located((By.XPATH, f"//label[contains(text(), '{label_text}')]")))
        dropdown = label.find_element(By.XPATH, "./following-sibling::div//div[contains(@class, 'dropdown-selected-option')]")
        driver.execute_script("arguments[0].click();", dropdown)
        time.sleep(0.3) # Minimized sleep for speed
        option = wait.until(EC.presence_of_element_located((By.XPATH, f"//*[text()='{option_text}']")))
        driver.execute_script("arguments[0].click();", option)
        time.sleep(0.3)
    except:
        pass

def should_skip_subject(subject_name, selected_track):
    """Filters subjects based on your chosen track"""
    sub = subject_name.lower()
    if selected_track == "AI Track":
        if "web" in sub: return True
    elif selected_track == "Web Track":
        if "machine learning" in sub or "deep learning" in sub: return True
    return False

# ==========================================
# 3. THE HIGH-SPEED GHOST BOT
# ==========================================
def deploy_fast_scraper(email, password, track, filename, terminal_container):
    log_history = []
    log_update("INITIALIZING HIGH-SPEED HEADLESS BOT...", log_history, terminal_container)
    
    # SPEED HACK 1: Headless Mode & Disable Images
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") # Run invisibly!
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    prefs = {"profile.managed_default_content_settings.images": 2} # Block images
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10) # Reduced max wait time
    master_data = []

    try:
        log_update("Authenticating...", log_history, terminal_container)
        driver.get("https://attendence-system-1910.vercel.app/users/login")
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))).send_keys(email)
        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(password)
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[@type='submit']"))
        
        # SPEED HACK 2: Dynamic wait instead of time.sleep(4)
        wait.until(EC.url_changes("https://attendence-system-1910.vercel.app/users/login"))
        log_update("Auth Success. Navigating to database...", log_history, terminal_container)

        driver.get("https://attendence-system-1910.vercel.app/students/current/attendances")
        wait.until(EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Select Subjects')]")))
        
        select_dropdown(driver, wait, "Select Course", "Msc Cs")
        select_dropdown(driver, wait, "Select Batch", "MSC CS BATCH 2022-2027")
        select_dropdown(driver, wait, "Select Division", "MSC CS BATCH 2022-2027 Div-2")
        select_dropdown(driver, wait, "Select Semester", "Sem8")
        
        subject_label = driver.find_element(By.XPATH, "//label[contains(text(), 'Select Subjects')]")
        dropdown_box = subject_label.find_element(By.XPATH, "./following-sibling::div//div[contains(@class, 'dropdown-selected-option')]")
        driver.execute_script("arguments[0].click();", dropdown_box)
        time.sleep(0.5) 
        raw_options = subject_label.find_element(By.XPATH, "./following-sibling::div").text.split('\n')
        all_subjects = [sub.strip() for sub in raw_options if sub.strip() and sub.strip().lower() != 'none']
        driver.execute_script("arguments[0].click();", dropdown_box) 
        
        log_update(f"Found {len(all_subjects)} subjects total. Applying {track} filter...", log_history, terminal_container)

        for subject in all_subjects:
            if should_skip_subject(subject, track):
                log_update(f"Skipping: {subject}", log_history, terminal_container)
                continue
                
            log_update(f"Extracting: {subject}", log_history, terminal_container)
            select_dropdown(driver, wait, "Select Subjects", subject)
            driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(text(), 'View Attendance')]"))
            
            # Dynamic Wait for API
            try: wait.until_not(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Loading...')]")))
            except: pass
            
            try:
                if len(driver.find_elements(By.XPATH, "//*[contains(text(), 'There is no attendances found')]")) > 0:
                    driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(text(), 'Go Back')]"))
                    time.sleep(0.5)
                    continue
            except: pass

            try:
                total_text = driver.find_element(By.XPATH, "//*[contains(text(), 'Total Attendances:')]").text
                expected_total = int(re.search(r'\d+', total_text).group())
            except: expected_total = 0

            if expected_total > 0:
                scraped = 0
                while scraped < expected_total:
                    rows = driver.find_elements(By.XPATH, "//*[contains(@class, 'bg-green') or contains(@class, 'bg-red')]")
                    if not rows: break
                    first_row_element = rows[0] 
                    
                    for row in rows:
                        try:
                            row_html, row_text = row.get_attribute("outerHTML").lower(), row.text
                            if "/" in row_text and ":" in row_text:
                                lines = [line.strip() for line in row_text.replace('\r', '').split('\n') if line.strip()]
                                if len(lines) >= 4:
                                    is_present = "bg-green" in row_html or "rgb(34, 197, 94" in row_html
                                    record = {"Subject": subject, "Date": lines[0], "From Time": lines[1], "To Time": lines[2], "Topic": " ".join(lines[3:]), "Status": "Present" if is_present else "Absent"}
                                    if record not in master_data:
                                        master_data.append(record)
                                        scraped += 1
                        except: continue

                    if scraped >= expected_total: break

                    # SPEED HACK 3: Staleness check instead of hard sleep
                    try:
                        nav_buttons = [b for b in driver.find_elements(By.TAG_NAME, "button") if b.text.strip().lower() not in ['log in', 'go back', 'view attendance']]
                        if len(nav_buttons) > 0:
                            next_btn = nav_buttons[-1]
                            if next_btn.get_attribute("disabled"): break
                            
                            driver.execute_script("arguments[0].click();", next_btn)
                            # Waits ONLY exactly as long as it takes the row to vanish
                            try: wait.until(EC.staleness_of(first_row_element))
                            except: pass
                        else: break
                    except: break 

            driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(text(), 'Go Back')]"))
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Select Subject For Attendance')]")))
            time.sleep(0.5)

        if len(master_data) > 0:
            file_path = f"{filename}.xlsx"
            pd.DataFrame(master_data).to_excel(file_path, index=False)
            log_update(f"SUCCESS! {len(master_data)} records saved to {file_path}", log_history, terminal_container)
            time.sleep(2)
            st.rerun() 
        else:
            log_update("WARNING: Bot finished, but found zero records.", log_history, terminal_container)

    except Exception as e:
        log_update(f"FATAL ERROR: {str(e)}", log_history, terminal_container)
    finally:
        driver.quit()

# ==========================================
# 4. SIDEBAR SETTINGS (TRACK & FILENAME)
# ==========================================
st.sidebar.title("/> SYS_CONFIG")

track_choice = st.sidebar.radio("SELECT_TRACK", ["All Subjects", "AI Track", "Web Track"])
file_name_input = st.sidebar.text_input("OUTPUT_FILE_NAME", value="Master_Attendance")
target_file = f"{file_name_input}.xlsx"

if not os.path.exists(target_file):
    st.sidebar.warning("SYSTEM OFFLINE: Data required.")
    
    email_input = st.sidebar.text_input("EMAIL")
    pass_input = st.sidebar.text_input("PASSWORD", type="password")
    
    if st.sidebar.button("DEPLOY FAST BOT"):
        if email_input and pass_input:
            # Create the terminal box in the main UI
            st.subheader("/> Live_Terminal_Stream")
            terminal_box = st.empty()
            deploy_fast_scraper(email_input, pass_input, track_choice, file_name_input, terminal_box)
        else:
            st.sidebar.error("Credentials required.")
else:
    st.sidebar.success(f"SYSTEM ONLINE: {target_file} loaded.")
    if st.sidebar.button("PURGE DATA & RESYNC"):
        os.remove(target_file)
        st.rerun()

# ==========================================
# 5. DASHBOARD RENDERER
# ==========================================
if os.path.exists(target_file):
    df = pd.read_excel(target_file)
    
    subject_list = ["ALL"] + list(df['Subject'].unique())
    selected_subject = st.sidebar.selectbox("FILTER_SUBJECT", subject_list)

    display_df = df if selected_subject == "ALL" else df[df['Subject'] == selected_subject]

    total_classes = len(display_df)
    total_present = len(display_df[display_df['Status'] == 'Present'])
    total_absent = len(display_df[display_df['Status'] == 'Absent'])
    percentage = (total_present / total_classes) * 100 if total_classes > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL RECORDS", total_classes)
    col2.metric("PRESENT", total_present)
    col3.metric("ABSENT", total_absent)
    col4.metric("PERCENTAGE", f"{percentage:.2f}%", "Safe" if percentage >= 75 else "-Danger", delta_color="inverse")

    st.markdown("---")
    left_column, right_column = st.columns([2, 1])

    with left_column:
        st.subheader("/> Data_Stream")
        def highlight_status(val):
            if val == 'Present': return 'background-color: rgba(34, 197, 94, 0.2); color: #00FF41;'
            elif val == 'Absent': return 'background-color: rgba(239, 68, 68, 0.2); color: #FF003C;'
            return ''
        st.dataframe(display_df.style.map(highlight_status, subset=['Status']), use_container_width=True, height=400)

    with right_column:
        st.subheader("/> Status_Ratio")
        if total_classes > 0:
            fig = px.pie(names=['Present', 'Absent'], values=[total_present, total_absent], hole=0.7, color_discrete_sequence=['#00FF41', '#FF003C'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Awaiting deployment command. Set your parameters in the sidebar.")