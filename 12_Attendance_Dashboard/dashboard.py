import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. HACKER THEME SETUP ---
st.set_page_config(page_title="SYSTEM // ATTENDANCE", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Dark Matrix Aesthetics */
    .stApp { background-color: #0d1117; }
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New', Courier, monospace; text-transform: uppercase; }
    p, span, div { font-family: 'Courier New', Courier, monospace; }
    div[data-testid="stMetricValue"] { color: #00FF41; font-weight: bold; }
    .status-warning { color: #FF003C; font-size: 1.2rem; border: 1px solid #FF003C; padding: 10px; border-radius: 5px; background: rgba(255, 0, 60, 0.1); }
    hr { border-color: #00FF41; opacity: 0.3; }
    </style>
""", unsafe_allow_html=True)

st.title("/> COMMAND_CENTER_UI")
st.markdown("---")

FILE_NAME = "Automated_Master_Attendance002.xlsx"

# Check if the scraper has done its job yet
if not os.path.exists(FILE_NAME):
    st.markdown(f'<div class="status-warning">⚠️ SYSTEM ERROR: [{FILE_NAME}] not found.<br><br>Action Required: Open your terminal and run <b>python scraper.py</b> to initialize data extraction.</div>', unsafe_allow_html=True)
else:
    # --- 2. LOAD & FILTER DATA ---
    df = pd.read_excel(FILE_NAME)
    
    st.sidebar.title("/> FILTERS")
    subject_list = ["ALL SUBJECTS"] + list(df['Subject'].unique())
    selected_subject = st.sidebar.selectbox("TARGET_SUBJECT", subject_list)

    if selected_subject == "ALL SUBJECTS":
        display_df = df
    else:
        display_df = df[df['Subject'] == selected_subject]

    # --- 3. CORE METRICS ---
    total_classes = len(display_df)
    total_present = len(display_df[display_df['Status'] == 'Present'])
    total_absent = len(display_df[display_df['Status'] == 'Absent'])
    percentage = (total_present / total_classes) * 100 if total_classes > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("TOTAL RECORDS", total_classes)
    col2.metric("PRESENT", total_present)
    col3.metric("ABSENT", total_absent)
    
    # Red percentage if below 75%
    if percentage >= 75:
        col4.metric("PERCENTAGE", f"{percentage:.2f}%", "Safe")
    else:
        col4.metric("PERCENTAGE", f"{percentage:.2f}%", "-Danger", delta_color="inverse")

    st.markdown("---")

    # --- 4. VISUALIZATIONS ---
    left_column, right_column = st.columns([2, 1])

    with left_column:
        st.subheader("/> Data_Stream")
        
        # Color coding for the table
        def highlight_status(val):
            if val == 'Present': return 'background-color: rgba(34, 197, 94, 0.15); color: #00FF41;'
            elif val == 'Absent': return 'background-color: rgba(239, 68, 68, 0.15); color: #FF003C;'
            return ''
            
        st.dataframe(display_df.style.map(highlight_status, subset=['Status']), use_container_width=True, height=450)

    with right_column:
        st.subheader("/> Status_Ratio")
        if total_classes > 0:
            fig = px.pie(names=['Present', 'Absent'], values=[total_present, total_absent], hole=0.75, color_discrete_sequence=['#00FF41', '#FF003C'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, font=dict(family="Courier New", color="#00FF41"))
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    # --- 5. SYSTEM OVERVIEW (Only shows if 'All Subjects' is selected) ---
    if selected_subject == "ALL SUBJECTS":
        st.markdown("---")
        st.subheader("/> Sub-System_Analysis")
        
        summary_df = df.groupby('Subject').apply(lambda x: pd.Series({'Percentage': ((x['Status'] == 'Present').sum() / len(x) * 100).round(2)})).reset_index()
        
        bar_fig = px.bar(summary_df, x='Percentage', y='Subject', orientation='h', color='Percentage', color_continuous_scale=['#FF003C', '#00FF41'], range_color=[50, 100])
        bar_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(family="Courier New", color="#00FF41"))
        st.plotly_chart(bar_fig, use_container_width=True)