import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import random  # For motivational quotes
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# --- Google Sheets Configuration ---
DATA_SHEET_NAME = "timetable"  # Your Google Sheet name
CREDENTIALS_FILE = "productivity-450902-c3aafad7c158.json"  # Your downloaded JSON file

# --- Utility Functions for Persistence with Google Sheets ---
def serialize_data(data):
    """Convert datetime objects to ISO strings for JSON."""
    def default(o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    return json.dumps(data, default=default)

def deserialize_data(json_str):
    """Convert ISO datetime strings back to datetime objects."""
    def object_hook(dct):
        if 'entry_datetime' in dct:
            try:
                dct['entry_datetime'] = datetime.datetime.fromisoformat(dct['entry_datetime'])
            except Exception:
                pass
        if 'time' in dct:
            try:
                dct['time'] = datetime.datetime.fromisoformat(dct['time'])
            except Exception:
                pass
        return dct
    return json.loads(json_str, object_hook=object_hook)

def load_data_from_file():
    """Loads subject chapter data from Google Sheets."""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
        client = gspread.authorize(creds)
        sheet = client.open(DATA_SHEET_NAME).sheet1
        data_str = sheet.acell('A1').value
        if data_str:
            return deserialize_data(data_str)
        else:
            # If A1 is empty, return default structure.
            return {
                "Botany": [],
                "Zoology": [],
                "Physics": [],
                "Chemistry": []
            }
    except Exception as e:
        st.error("Error loading data from Google Sheets: " + str(e))
        return {
            "Botany": [],
            "Zoology": [],
            "Physics": [],
            "Chemistry": []
        }

def save_data_to_file():
    """Saves the current subject chapter data to Google Sheets."""
    data = st.session_state['subject_chapters_data']
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
        client = gspread.authorize(creds)
        sheet = client.open(DATA_SHEET_NAME).sheet1
        json_str = serialize_data(data)
        sheet.update('A1', json_str)
    except Exception as e:
        st.error("Error saving data to Google Sheets: " + str(e))

# --- Color Palette & Button Styles ---
PRIMARY_COLOR = "#007BFF"
SECONDARY_COLOR = "#66B2FF"
BACKGROUND_COLOR_LIGHT = "#F8F9FA"
BACKGROUND_COLOR_SECTION = "#E9ECEF"
TEXT_COLOR_PRIMARY = "#212529"
TEXT_COLOR_SECONDARY = "#6C757D"
COLOR_SUCCESS = "#28A745"
COLOR_WARNING = "#DC3545"
TAB_HIGHLIGHT_COLOR = "#D1E7DD"

BUTTON_COLOR_LIGHT = PRIMARY_COLOR
BUTTON_TEXT_COLOR_LIGHT = "white"
BUTTON_BORDER_COLOR_LIGHT = PRIMARY_COLOR

BUTTON_COLOR_DARK = PRIMARY_COLOR
BUTTON_TEXT_COLOR_DARK = "white"
BUTTON_BORDER_COLOR_DARK = PRIMARY_COLOR

BUTTON_COLOR_COLORFUL = "#4dd0e1"
BUTTON_TEXT_COLOR_COLORFUL = "black"
BUTTON_BORDER_COLOR_COLORFUL = "#4dd0e1"

# --- Application Configuration ---
st.set_page_config(
    page_title="NEET Exam Prep - Subject-wise Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if 'subject_chapters_data' not in st.session_state:
    st.session_state['subject_chapters_data'] = load_data_from_file()
if 'app_theme' not in st.session_state:
    st.session_state['app_theme'] = "Light Mode"  # Default theme

SUBJECT_CHOICES = ["Botany", "Zoology", "Physics", "Chemistry"]
THEME_OPTIONS = ["Light Mode", "Dark Mode", "Colorful Mode"]

# Motivational Quotes and Study Tips
motivational_quotes = [
    "The expert in anything was once a beginner.",
    "Believe you can and you're halfway there.",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "The only way to do great work is to love what you do.",
    "Your future is created by what you do today, not tomorrow."
]
study_tips = [
    "Plan your study schedule and stick to it.",
    "Use active recall and spaced repetition techniques.",
    "Practice with past papers regularly.",
    "Take short breaks to avoid burnout.",
    "Stay hydrated and get enough sleep.",
    "Focus on understanding concepts rather than rote memorization.",
    "Join study groups or online forums for discussions.",
    "Use different learning resources like textbooks, videos, and online materials.",
    "Regularly test yourself to track progress.",
    "Stay positive and believe in your preparation."
]

# -------------------- Helper Functions --------------------
def _create_default_reminders(entry_datetime):
    """Creates a list of default revision reminders."""
    return [
        {"reminder_id": 1, "type": "1st Reminder (12 hours)", "time": entry_datetime + datetime.timedelta(hours=12), "status": "Pending"},
        {"reminder_id": 2, "type": "2nd Reminder (3 days)", "time": entry_datetime + datetime.timedelta(days=3), "status": "Pending"},
        {"reminder_id": 3, "type": "3rd Reminder (5 days)", "time": entry_datetime + datetime.timedelta(days=5), "status": "Pending"},
    ]

def _prepare_csv_data(subject_chapters_data):
    """Prepares CSV data from subject chapters data."""
    all_data = []
    for subject, chapters in subject_chapters_data.items():
        for chapter in chapters:
            for reminder in chapter['reminders']:
                all_data.append({
                    "Subject": subject,
                    "Chapter Name": chapter['chapter_name'],
                    "Entry Date": chapter['entry_datetime'].strftime("%Y-%m-%d %H:%M:%S"),
                    "Reminder Type": reminder['type'],
                    "Reminder Time": reminder['time'].strftime("%Y-%m-%d %H:%M:%S"),
                    "Status": reminder['status'],
                    "Exams Appeared": chapter['exams_appeared'],
                    "Exam Status": chapter['exam_status'],
                    "Time Spent (minutes)": chapter['time_spent']
                })
    return pd.DataFrame(all_data).to_csv(index=False).encode('utf-8')

def _aggregate_productivity_data(subject_chapters_data, start_date=None):
    """Aggregates revision data for productivity tracking."""
    aggregated = {}
    for subject, chapters in subject_chapters_data.items():
        for chapter in chapters:
            for reminder in chapter["reminders"]:
                reminder_date = reminder["time"].date()
                if start_date and reminder_date < start_date:
                    continue
                if reminder_date not in aggregated:
                    aggregated[reminder_date] = {"total": 0, "revised": 0}
                aggregated[reminder_date]["total"] += 1
                if reminder["status"] == "Revised":
                    aggregated[reminder_date]["revised"] += 1
    return aggregated

# -------------------- Core Functions --------------------
def add_chapter_and_reminders(subject, chapter_name, entry_datetime, custom_reminders=None):
    """Adds a new chapter with revision reminders."""
    reminders = custom_reminders if custom_reminders else _create_default_reminders(entry_datetime)
    st.session_state['subject_chapters_data'][subject].append({
        "chapter_name": chapter_name,
        "entry_datetime": entry_datetime,
        "reminders": reminders,
        "exams_appeared": 0,
        "exam_status": "Not Appeared",
        "time_spent": 0
    })
    save_data_to_file()
    st.success(f"Chapter '{chapter_name}' ({subject}) added with revision reminders scheduled from {entry_datetime.strftime('%Y-%m-%d %H:%M')}.")

def mark_reminder_revised(subject, chapter_index, reminder_index):
    """Marks a reminder as 'Revised' and saves data."""
    st.session_state['subject_chapters_data'][subject][chapter_index]['reminders'][reminder_index]['status'] = "Revised"
    save_data_to_file()
    st.experimental_rerun()

def mark_reminder_pending(subject, chapter_index, reminder_index):
    """Marks a reminder as 'Pending' and saves data."""
    st.session_state['subject_chapters_data'][subject][chapter_index]['reminders'][reminder_index]['status'] = "Pending"
    save_data_to_file()
    st.experimental_rerun()

def calculate_subject_progress(subject):
    """Calculates overall progress percentage for a subject."""
    subject_data = st.session_state['subject_chapters_data'][subject]
    if not subject_data:
        return 0
    total_reminders = sum(len(chapter['reminders']) for chapter in subject_data)
    revised_reminders = sum(1 for chapter in subject_data for reminder in chapter['reminders'] if reminder['status'] == "Revised")
    return (revised_reminders / total_reminders) * 100 if total_reminders else 0

def display_reminders_section(subject, chapter, chapter_index):
    """Displays revision reminders with checkboxes."""
    reminders_list = []
    for reminder_index, reminder in enumerate(chapter["reminders"]):
        current_status = reminder["status"] == "Revised"
        checkbox_key = f"checkbox_{subject}_{chapter_index}_{reminder_index}"
        checkbox_value = st.checkbox(reminder["type"], value=current_status, key=checkbox_key)
        if checkbox_value != current_status:
            if checkbox_value:
                mark_reminder_revised(subject, chapter_index, reminder_index)
            else:
                mark_reminder_pending(subject, chapter_index, reminder_index)
        reminders_list.append({
            "Reminder Type": reminder["type"],
            "Reminder Time": reminder["time"].strftime("%Y-%m-%d %H:%M"),
            "Status": "Revised" if reminder["status"] == "Revised" else "Pending"
        })
    df_reminders = pd.DataFrame(reminders_list)
    st.dataframe(df_reminders[["Reminder Type", "Reminder Time", "Status"]], hide_index=True)

def display_time_spent_section(subject, chapter):
    """Displays and updates time spent tracking."""
    time_spent_key = f"time_spent_{subject}_{chapter['chapter_name']}"
    time_spent = st.number_input("Time Spent Studying (minutes):",
                                 value=chapter.get("time_spent", 0),
                                 min_value=0,
                                 step=5,
                                 key=time_spent_key)
    if time_spent != chapter.get("time_spent", 0):
        chapter["time_spent"] = time_spent
        save_data_to_file()
        st.success("Time spent updated!")

def display_exam_tracking_section(subject, chapter, chapter_index):
    """Displays and updates exam tracking information."""
    st.subheader(f"{subject} Exam Tracking - {chapter['chapter_name']}")
    exam_count_key = f"exam_count_{subject}_{chapter_index}"
    exam_status_key = f"exam_status_{subject}_{chapter_index}"
    exam_appeared = st.number_input("Exams Appeared",
                                    min_value=0,
                                    value=chapter.get("exams_appeared", 0),
                                    key=exam_count_key)
    exam_status_text = st.text_input("Exam Status",
                                     value=chapter.get("exam_status", "Not Appeared"),
                                     key=exam_status_key,
                                     placeholder="e.g., Score, Performance")
    if st.button("Update Exam Info", key=f"update_exam_btn_{subject}_{chapter_index}"):
        chapter["exams_appeared"] = exam_appeared
        chapter["exam_status"] = exam_status_text
        save_data_to_file()
        st.success("Exam information updated!")

def _get_chapter_item(subject_data, chapter_name):
    """Helper function to find a chapter and its index by name."""
    for idx, chapter in enumerate(subject_data):
        if chapter["chapter_name"] == chapter_name:
            return chapter, idx
    return None, -1

def display_subject_tab_content(subject):
    """Displays chapter selection, reminders, time spent, and exam tracking for a subject."""
    st.subheader(f"{subject} Revision Progress")
    progress_percent = calculate_subject_progress(subject)
    st.progress(int(min(progress_percent, 100)))
    st.write(f"Overall Revision Completion: {progress_percent:.2f}%")

    subject_data = st.session_state['subject_chapters_data'][subject]
    chapter_names = [chapter["chapter_name"] for chapter in subject_data]

    if not chapter_names:
        st.info(f"No chapters added in {subject} yet. Add chapters to schedule reminders.")
        return

    selected_chapter_name = st.selectbox(f"Select {subject} Chapter:", ["Select Chapter"] + chapter_names, index=0)
    if selected_chapter_name != "Select Chapter":
        chapter, chapter_index = _get_chapter_item(subject_data, selected_chapter_name)
        if chapter:
            display_reminders_section(subject, chapter, chapter_index)
            display_time_spent_section(subject, chapter)
            display_exam_tracking_section(subject, chapter, chapter_index)

def download_csv_data():
    """Prepares and returns CSV data of all chapters and reminders."""
    return _prepare_csv_data(st.session_state['subject_chapters_data'])

# -------------------- Productivity Tracking --------------------
def display_productivity_tracking():
    """Displays productivity tracking with a line chart and data table."""
    st.header("Productivity Tracking")
    tracking_period = st.selectbox("Select Tracking Period:", ["Last 1 Week", "Last 1 Month", "All Time"])
    start_date = _get_start_date_for_tracking(tracking_period)
    aggregated_data = _aggregate_productivity_data(st.session_state['subject_chapters_data'], start_date)
    df_productivity = _create_productivity_dataframe(aggregated_data)
    if df_productivity.empty:
        st.info("No productivity data available for the selected period.")
    else:
        _display_productivity_chart(df_productivity)
        st.dataframe(df_productivity)

def _get_start_date_for_tracking(tracking_period):
    """Determines the start date based on the tracking period."""
    today = datetime.date.today()
    if tracking_period == "Last 1 Week":
        return today - datetime.timedelta(days=7)
    elif tracking_period == "Last 1 Month":
        return today - datetime.timedelta(days=30)
    return None  # All Time

def _create_productivity_dataframe(aggregated_data):
    """Creates a DataFrame from aggregated productivity data."""
    data = [
        {
            "Date": date_key,
            "Total Reminders": stats["total"],
            "Revised": stats["revised"],
            "Productivity (%)": (stats["revised"] / stats["total"] * 100) if stats["total"] else 0
        }
        for date_key, stats in aggregated_data.items()
    ]
    df = pd.DataFrame(data)
    return df.sort_values("Date") if not df.empty else df

def _display_productivity_chart(df_productivity):
    """Displays the productivity line chart."""
    fig = px.line(df_productivity, x="Date", y="Productivity (%)", markers=True,
                  title="Daily Productivity Over Time")
    st.plotly_chart(fig, use_container_width=True)

# -------------------- Theme CSS Functions --------------------
def apply_light_theme_css():
    """Applies CSS for Light Mode."""
    css = f"""
        <style>
        body {{
            color: {TEXT_COLOR_PRIMARY};
            background-color: {BACKGROUND_COLOR_LIGHT};
        }}
        .stApp {{
            background-color: {BACKGROUND_COLOR_LIGHT};
        }}
        .css-1lcbmhc {{
            background-color: {BACKGROUND_COLOR_SECTION} !important;
        }}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def apply_dark_theme_css():
    """Applies CSS for Dark Mode."""
    css = f"""
        <style>
        body {{
            color: {TEXT_COLOR_PRIMARY};
            background-color: #222;
        }}
        .stApp {{
            background-color: #222;
        }}
        .css-1lcbmhc {{
            background-color: #444 !important;
            color: white !important;
        }}
        .css-keje6i {{
            background-color: #333 !important;
            color: white;
        }}
        div.stButton > button:first-child {{
            background-color: {BUTTON_COLOR_DARK}; color: {BUTTON_TEXT_COLOR_DARK}; border-color: {BUTTON_BORDER_COLOR_DARK};
        }}
        div.stDownloadButton > button:first-child {{
            background-color: {SECONDARY_COLOR}; color: {TEXT_COLOR_PRIMARY}; border-color: {SECONDARY_COLOR};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: white;
        }}
        .stProgress > div > div > div > div {{
            background-color: {SECONDARY_COLOR};
        }}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def apply_colorful_theme_css():
    """Applies CSS for Colorful Mode."""
    css = f"""
        <style>
        .stApp {{
            background-color: #e0f7fa;
        }}
        .css-1lcbmhc {{
            background-color: #b2ebf2 !important;
        }}
        .css-keje6i {{
            background-color: #80deea !important;
        }}
        div.stButton > button:first-child {{
            background-color: {BUTTON_COLOR_COLORFUL}; color: {BUTTON_TEXT_COLOR_COLORFUL}; border-color: {BUTTON_BORDER_COLOR_COLORFUL};
        }}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# -------------------- Sidebar --------------------
with st.sidebar:
    st.title("📚 NEET Prep App")
    with st.expander("App Theme", expanded=False):
        st.session_state['app_theme'] = st.selectbox("Choose Theme:", THEME_OPTIONS,
                                                     index=THEME_OPTIONS.index(st.session_state['app_theme']))
    with st.expander("Add New Chapter", expanded=True):
        subject = st.selectbox("Subject:", SUBJECT_CHOICES)
        chapter_name = st.text_input("Chapter Name:", placeholder="e.g., Structure of Atom")
        entry_date = st.date_input("Entry Date:", value=datetime.date.today())
        entry_time = st.time_input("Entry Time:", value=datetime.time(datetime.datetime.now().hour, datetime.datetime.now().minute))
        st.subheader("Customize Revision Schedule (Optional)")
        custom_12hr = st.checkbox("Use 12-hour Reminder?", value=True)
        custom_3day = st.checkbox("Use 3-day Reminder?", value=True)
        custom_5day = st.checkbox("Use 5-day Reminder?", value=True)
        if st.button("Add Chapter"):
            if chapter_name and subject:
                entry_datetime = datetime.datetime.combine(entry_date, entry_time)
                custom_reminders_list = []
                if custom_12hr:
                    custom_reminders_list.append({
                        "reminder_id": 1,
                        "type": "1st Reminder (Custom)",
                        "time": entry_datetime + datetime.timedelta(hours=12),
                        "status": "Pending"
                    })
                if custom_3day:
                    custom_reminders_list.append({
                        "reminder_id": 2,
                        "type": "2nd Reminder (Custom)",
                        "time": entry_datetime + datetime.timedelta(days=3),
                        "status": "Pending"
                    })
                if custom_5day:
                    custom_reminders_list.append({
                        "reminder_id": 3,
                        "type": "3rd Reminder (Custom)",
                        "time": entry_datetime + datetime.timedelta(days=5),
                        "status": "Pending"
                    })
                add_chapter_and_reminders(subject, chapter_name, entry_datetime, custom_reminders_list or None)
            else:
                st.warning("Please enter chapter name and select subject.")
    with st.expander("Data Options", expanded=False):
        st.header("Download Data")
        csv_data = download_csv_data()
        st.download_button(label="Download All Data as CSV",
                           data=csv_data,
                           file_name="neet_prep_data.csv",
                           mime='text/csv')
    st.header("Motivation")
    quote = random.choice(motivational_quotes)
    st.markdown(f"> *\"{quote}\"*")
    st.header("Study Tips")
    with st.expander("See Study Tips"):
        for tip in study_tips:
            st.markdown(f"- {tip}")

# -------------------- Main Panel and Tabs --------------------
st.title("Revision & Exam Tracker Dashboard")

# --- Apply Theme CSS ---
if st.session_state['app_theme'] == "Dark Mode":
    apply_dark_theme_css()
elif st.session_state['app_theme'] == "Colorful Mode":
    apply_colorful_theme_css()
else:
    apply_light_theme_css()

# Create tabs for subjects, Today's Revisions, and Productivity Tracking.
tabs = st.tabs(SUBJECT_CHOICES + ["Today's Revisions", "Productivity Tracking"])

# ----- Subject Tabs -----
for i, subject in enumerate(SUBJECT_CHOICES):
    with tabs[i]:
        st.header(subject)
        st.markdown(f"<div style='background-color: {TAB_HIGHLIGHT_COLOR}; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
        display_subject_tab_content(subject)
        st.markdown("</div>", unsafe_allow_html=True)

# ----- Today's Revisions Tab -----
with tabs[len(SUBJECT_CHOICES)]:
    st.header("Today's Revisions")
    view_mode = st.radio("View Mode", ["Today", "Select Date"], index=0)
    if view_mode == "Today":
        selected_date = datetime.date.today()
        st.info(f"Showing revisions for today: {selected_date.strftime('%Y-%m-%d')}")
    else:
        selected_date = st.date_input("Select a date", value=datetime.date.today())
        st.info(f"Showing revisions scheduled on: {selected_date.strftime('%Y-%m-%d')}")
    
    revision_entries = []
    for subject, chapters in st.session_state['subject_chapters_data'].items():
        for chapter_index, chapter in enumerate(chapters):
            for reminder_index, reminder in enumerate(chapter["reminders"]):
                if reminder["time"].date() == selected_date:
                    revision_entries.append((subject, chapter_index, chapter, reminder_index, reminder))
    
    st.markdown(f"**Total revisions found: {len(revision_entries)}**")
    
    # Pie chart summarizing revision statuses
    status_counts = {"Revised": 0, "Pending": 0}
    for entry in revision_entries:
        status_counts[entry[4]["status"]] += 1
    if revision_entries:
        df_status = pd.DataFrame({
            "Status": list(status_counts.keys()),
            "Count": list(status_counts.values())
        })
        fig = px.pie(df_status, names="Status", values="Count",
                     title="Revision Status Breakdown",
                     color_discrete_map={"Revised": COLOR_SUCCESS, "Pending": COLOR_WARNING})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No revisions scheduled for the selected date.")
    
    # Display each revision entry with a checkbox to mark as revised/pending
    for subject, chapter_index, chapter, reminder_index, reminder in revision_entries:
        with st.container():
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 10px;
                    margin-bottom: 10px;
                    background-color: #f9f9f9;
                ">
                    <strong>Subject:</strong> {subject} |
                    <strong>Chapter:</strong> {chapter['chapter_name']} |
                    <strong>Reminder:</strong> {reminder['type']} |
                    <strong>Time:</strong> {reminder['time'].strftime('%H:%M')}
                </div>
                """, unsafe_allow_html=True)
            col1, col2 = st.columns([4, 1])
            with col2:
                current_status = reminder["status"] == "Revised"
                checkbox_key = f"date_checkbox_{subject}_{chapter_index}_{reminder_index}"
                new_status = st.checkbox("Revised", value=current_status, key=checkbox_key)
                if new_status != current_status:
                    if new_status:
                        mark_reminder_revised(subject, chapter_index, reminder_index)
                    else:
                        mark_reminder_pending(subject, chapter_index, reminder_index)

# ----- Productivity Tracking Tab -----
with tabs[-1]:
    display_productivity_tracking()

st.markdown("""
---

""")

