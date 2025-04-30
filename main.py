import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import random
import os
import json
# Remove firebase_admin imports
# import firebase_admin
# from firebase_admin import credentials, db

# --- Define local file paths for data persistence ---
# The app will create these files in the directory it's run from if they don't exist.
DATA_FILE = "neet_prep_data.json"
TODO_FILE = "neet_prep_todo.json"

# Remove Firebase initialization block
# firebase_key_json = os.getenv("FIREBASE_KEY")
# if firebase_key_json:
#     firebase_key = json.loads(firebase_key_json)
#     cred = credentials.Certificate(firebase_key)
#     # Initialize Firebase only if not already initialized
#     if not firebase_admin._apps:
#         firebase_admin.initialize_app(cred, {
#             "databaseURL": "https://neetprep-9a499-default-rtdb.asia-southeast1.firebasedatabase.app/"
#         })
# else:
#     pass # Firebase is removed, so this key isn't needed

# ---------------- Set Page Config ----------------
st.set_page_config(
    page_title="NEET Exam Prep - Subject-wise Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Base Custom CSS ----------------
# Removed Google Fonts link - using system fonts instead
base_css = """
<style>
    /* Roboto font might not be available offline, using system sans-serif */
    html, body, [class*="css"]  {
        font-family: sans-serif; /* Or a system font stack like 'Arial, Helvetica, sans-serif' */
    }
    .main-header {
        background: linear-gradient(135deg, #007BFF, #66B2FF);
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
    }
    .sidebar .sidebar-content {
        padding: 20px;
        border-radius: 8px;
    }
    .stButton>button {
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
    }
    .stProgress>div>div {
        border-radius: 5px;
    }
    .dataframe-container {
        background: #ffffff;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
    }
    .section-divider {
        border: none;
        border-bottom: 1px solid #ddd;
        margin: 10px 0;
    }
    .container-box {
        background: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }
    /* Current time box styling */
    .current-time {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 10000;
        background: #ffffff;
        padding: 5px 10px;
        border-radius: 5px;
        box-shadow: 0px 2pspx 4px rgba(0,0,0,0.2);
        font-size: 14px;
        color: #333; /* Ensure visibility in different themes */
    }

    /* Dark Mode Specific Overrides */
    /* Added styles to ensure text and table content is visible in dark mode */
    .stApp > header { /* Target header in dark mode */
         background-color: #222; /* Match body background or similar */
         color: #ddd;
    }
    .dark-mode .dataframe-container table { color: #ddd !important; } /* Target dataframe text color */
    .dark-mode .dataframe-container thead th { color: #ddd !important; } /* Target dataframe header color */


</style>
"""
st.markdown(base_css, unsafe_allow_html=True)

# ---------------- Theme CSS Function ----------------
def apply_theme_css():
    theme = st.session_state.get("app_theme", "Light Mode")
    if theme == "Dark Mode":
        css = """
        <style>
            body, .stApp { background-color: #222; color: #ddd; }
            .stApp > header { background-color: #222; color: #ddd; } /* Apply to header as well */
            .sidebar .sidebar-content { background-color: #333; }
            .stButton>button { background-color: #555; color: #fff; }
            .stProgress>div>div { background-color: #888; }
            .current-time { background-color: #444; color: #ddd; }
            .dataframe-container { background: #444; color: #ddd; box-shadow: 0px 2px 4px rgba(255,255,255,0.1); }
            .dataframe-container table { color: #ddd !important; } /* Target dataframe text color */
            .dataframe-container thead th { color: #ddd !important; } /* Target dataframe header color */
            .container-box { background: #555; border: 1px solid #666; }
             /* Add a class to the body or main container to help style specific elements */
            body { /* Or a wrapper div if possible */
                 --text-color: #ddd; /* Use CSS variables if needed for complex theming */
            }
            .stApp {
                color: var(--text-color);
            }
        </style>
        """
    elif theme == "Colorful Mode":
        css = """
        <style>
            body, .stApp { background-color: #e0f7fa; color: #212529; }
            .stApp > header { background-color: #e0f7fa; color: #212529; } /* Apply to header */
            .sidebar .sidebar-content { background-color: #b2ebf2; }
            .stButton>button { background-color: #ff4081; color: #fff; }
            .stProgress>div>div { background-color: #ff4081; }
            .current-time { background-color: #fff; color: #212529; }
            .dataframe-container { background: #fff; color: #212529; box-shadow: 0px 2px 4px rgba(0,0,0,0.1); }
            .dataframe-container table { color: #212529 !important; }
            .dataframe-container thead th { color: #212529 !important; }
            .container-box { background: #f9f9f9; border: 1px solid #ddd; }
             body { --text-color: #212529; }
             .stApp { color: var(--text-color); }
        </style>
        """
    else:  # Light Mode
        css = """
        <style>
            body, .stApp { background-color: #F8F9FA; color: #212529; }
             .stApp > header { background-color: #F8F9FA; color: #212529; } /* Apply to header */
            .sidebar .sidebar-content { background-color: #f0f2f6; }
            .stButton>button { background-color: #007BFF; color: #fff; }
            .stProgress>div>div { background-color: #66B2FF; }
            .current-time { background-color: #fff; color: #212529; }
            .dataframe-container { background: #fff; color: #212529; box-shadow: 0px 2px 4px rgba(0,0,0,0.1); }
            .dataframe-container table { color: #212529 !important; }
            .dataframe-container thead th { color: #212529 !important; }
            .container-box { background: #f9f9f9; border: 1px solid #ddd; }
            body { --text-color: #212529; }
             .stApp { color: var(--text-color); }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


# ---------------- Current Date & Time in Top Right Corner ----------------
# This uses local datetime, no change needed.
current_time = datetime.datetime.now().strftime("%d/%m/%y %I:%M:%S %p")
st.markdown(f"""
    <div class="current-time">
        <strong>{current_time}</strong>
    </div>
    """, unsafe_allow_html=True)


# ---------------- Local Persistence Functions (Replacing Firebase) ----------------

# Helper to convert datetime objects to ISO strings for JSON saving
def convert_datetimes_to_iso(data):
    if isinstance(data, datetime.datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {k: convert_datetimes_to_iso(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_datetimes_to_iso(item) for item in data]
    else:
        return data

# Helper to convert ISO strings back to datetime objects after loading
def convert_iso_to_datetimes(data):
    if isinstance(data, str):
        try:
            # Attempt to parse as datetime, handle potential errors
            return datetime.datetime.fromisoformat(data)
        except ValueError:
            return data # Return string if not a valid ISO format
        except TypeError: # Handle cases where it's not a string
             return data
    elif isinstance(data, dict):
        return {k: convert_iso_to_datetimes(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_iso_to_datetimes(item) for item in data]
    else:
        return data

# MODIFIED: Removed st. calls from the loading function
def load_data_from_local(file_path, default_data=None):
    """Loads data from a local JSON file. Does NOT use st. calls."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            # Convert ISO strings back to datetime objects after loading
            return convert_iso_to_datetimes(data), "loaded" # Return data and status
        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            # Do not use st.warning or st.info here!
            # Return default data and an error status
            return default_data, "load_error" # Return default and status
    else:
        # Do not use st.warning or st.info here!
        # Return default data and a not_found status
        return default_data, "not_found" # Return default and status


# MODIFIED: save_data_to_local can keep st.error because saves usually happen during user interaction
def save_data_to_local(data, file_path):
    """Saves data to a local JSON file."""
    try:
        # Convert datetime objects to ISO strings before saving
        data_prepared = convert_datetimes_to_iso(data)
        with open(file_path, 'w') as f:
            json.dump(data_prepared, f, indent=4)
        # st.success(f"Data saved to {file_path}") # Optional: show save confirmation
    except Exception as e:
        # This st.error is generally safe because saves happen after the app is running
        st.error(f"Error saving data to {file_path}: {e}")


# Firebase persistence functions are now replaced by calls to local functions
# MODIFIED: Load functions now handle the status returned by load_data_from_local
def load_subject_data_local():
     data, status = load_data_from_local(DATA_FILE, default_data={subject: [] for subject in SUBJECT_CHOICES})
     # Display messages *after* loading is done and session state is initialized
     # Check if st exists before calling it (for edge case bare mode, though streamlit run should handle it)
     # This check is defensive programming; typically with streamlit run it's not needed here
     if 'streamlit' in globals() and hasattr(st, '_is_running_with_streamlit') and st._is_running_with_streamlit:
         if status == "not_found":
             st.info(f"No chapter data file found at `{DATA_FILE}`. Initializing with empty data.")
         elif status == "load_error":
              st.warning(f"Could not load chapter data from `{DATA_FILE}`. Initializing with empty data.")
     return data

def save_subject_data_local():
     save_data_to_local(st.session_state['subject_chapters_data'], DATA_FILE)

# MODIFIED: Load functions now handle the status returned by load_data_from_local
def load_todo_data_local():
    # Load all tasks, then filter based on timestamp (timestamp check still uses local time)
    all_tasks, status = load_data_from_local(TODO_FILE, default_data=[])
    # Display messages *after* loading is done and session state is initialized
    # Check if st exists before calling it
    if 'streamlit' in globals() and hasattr(st, '_is_running_with_streamlit') and st._is_running_with_streamlit:
        if status == "not_found":
             st.info(f"No todo data file found at `{TODO_FILE}`. Initializing with empty data.")
        elif status == "load_error":
              st.warning(f"Could not load todo data from `{TODO_FILE}`. Initializing with empty data.")

    if status != "load_error": # Process tasks only if loading was successful (or file not found but data initialized)
        current_time_dt = datetime.datetime.now()
        filtered_tasks = [
            task for task in all_tasks
            # Ensure timestamp is datetime for comparison after conversion attempt
            if "timestamp" in task and isinstance(convert_iso_to_datetimes(task["timestamp"]), datetime.datetime) and
               current_time_dt - convert_iso_to_datetimes(task["timestamp"]) < datetime.timedelta(days=1)
        ]
        return filtered_tasks
    else:
        return [] # Return empty list if loading failed


def save_todo_data_local(todo_list):
     save_data_to_local(todo_list, TODO_FILE)


# ---------------- Session State Initialization ----------------
SUBJECT_CHOICES = ["Botany", "Zoology", "Physics", "Chemistry"]
THEME_OPTIONS = ["Light Mode", "Dark Mode", "Colorful Mode"]

# Call the modified loading functions during initial session state setup
# These functions now return data and print st. messages *after* this point
if 'subject_chapters_data' not in st.session_state:
    st.session_state['subject_chapters_data'] = load_subject_data_local()
if 'app_theme' not in st.session_state:
    st.session_state['app_theme'] = "Light Mode"
if 'todo_list' not in st.session_state:
     st.session_state['todo_list'] = load_todo_data_local()

# ---------------- Color Palette (for CSV export and charts) ----------------
PRIMARY_COLOR = "#007BFF"
SECONDARY_COLOR = "#66B2FF"
TAB_HIGHLIGHT_COLOR = "#D1E7DD"
COLOR_SUCCESS = "#28A745"
COLOR_WARNING = "#DC3545"

# ---------------- Motivational Quotes & Study Tips ----------------
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

# ---------------- Helper Functions ----------------
# These functions use session state data which is now loaded/saved locally, no online calls here.
def _create_default_reminders(entry_datetime):
    return [
        {"reminder_id": 1, "type": "12 hour Reminder", "time": entry_datetime + datetime.timedelta(hours=12), "status": "Pending"},
        {"reminder_id": 2, "type": "3 days Reminder", "time": entry_datetime + datetime.timedelta(days=3), "status": "Pending"},
        {"reminder_id": 3, "type": "5 days Reminder", "time": entry_datetime + datetime.timedelta(days=5), "status": "Pending"},
    ]

def _prepare_csv_data(data):
    all_data = []
    for subject, chapters in data.items():
        for chapter in chapters:
            # Ensure datetimes are datetime objects before formatting (handle potential load issues)
            try:
                entry_dt = chapter['entry_datetime'] if isinstance(chapter['entry_datetime'], datetime.datetime) else datetime.datetime.fromisoformat(chapter['entry_datetime'])
            except (TypeError, ValueError):
                 entry_dt = chapter['entry_datetime'] # Use raw data if conversion fails

            for reminder in chapter['reminders']:
                 # Ensure reminder time is datetime object before formatting (handle potential load issues)
                try:
                    rem_time = reminder['time'] if isinstance(reminder['time'], datetime.datetime) else datetime.datetime.fromisoformat(reminder['time'])
                except (TypeError, ValueError):
                    rem_time = reminder['time'] # Use raw data if conversion fails

                all_data.append({
                    "Subject": subject,
                    "Chapter Name": chapter['chapter_name'],
                    "Entry Date": entry_dt.strftime("%d/%m/%y %I:%M %p") if isinstance(entry_dt, datetime.datetime) else str(entry_dt), # Format only if datetime
                    "Reminder Time": rem_time.strftime("%d/%m/%y %I:%M %p") if isinstance(rem_time, datetime.datetime) else str(rem_time), # Format only if datetime
                    "Status": reminder['status'],
                    "Exams Appeared": chapter['exams_appeared'],
                    "Exam Status": chapter['exam_status'],
                    "Time Spent (minutes)": chapter['time_spent']
                })
    return pd.DataFrame(all_data).to_csv(index=False).encode('utf-8')

def _aggregate_productivity_data(data, start_date=None):
    aggregated = {}
    for chapters in data.values():
        for chapter in chapters:
            for reminder in chapter["reminders"]:
                # Ensure reminder time is datetime object before getting date
                rem_time_dt = reminder["time"] if isinstance(reminder["time"], datetime.datetime) else convert_iso_to_datetimes(reminder["time"])
                # Safely handle potential non-datetime objects resulting from conversion failure
                if not isinstance(rem_time_dt, datetime.datetime):
                     continue # Skip if time could not be parsed as datetime

                r_date = rem_time_dt.date()
                if start_date and r_date < start_date:
                    continue
                aggregated.setdefault(r_date, {"total": 0, "revised": 0})
                aggregated[r_date]["total"] += 1
                if reminder["status"] == "Revised":
                    aggregated[r_date]["revised"] += 1
    return aggregated

# ---------------- Core Functions ----------------
# These functions now call the local save functions
def add_chapter_and_reminders(subject, chapter_name, entry_datetime, custom_reminders=None):
    reminders = custom_reminders if custom_reminders else _create_default_reminders(entry_datetime)
    st.session_state['subject_chapters_data'][subject].append({
        "chapter_name": chapter_name,
        "entry_datetime": entry_datetime, # Stored as datetime in session state
        "reminders": reminders, # Reminder times stored as datetime in session state
        "exams_appeared": 0,
        "exam_status": "Not Appeared",
        "time_spent": 0
    })
    save_subject_data_local() # Save to local file
    st.success(f"Chapter '{chapter_name}' added to {subject} with reminders starting {entry_datetime.strftime('%d/%m/%y %I:%M %p')}.")

def delete_chapter(subject, chapter_index):
    del st.session_state['subject_chapters_data'][subject][chapter_index]
    save_subject_data_local() # Save to local file
    st.success("Chapter deleted successfully!")
    st.experimental_rerun()

def mark_reminder_revised(subject, chapter_index, reminder_index):
    st.session_state['subject_chapters_data'][subject][chapter_index]['reminders'][reminder_index]['status'] = "Revised"
    save_subject_data_local() # Save to local file
    # st.experimental_rerun() # Rerun is handled by the checkbox interaction directly

def mark_reminder_pending(subject, chapter_index, reminder_index):
    st.session_state['subject_chapters_data'][subject][chapter_index]['reminders'][reminder_index]['status'] = "Pending"
    save_subject_data_local() # Save to local file
    # st.experimental_rerun() # Rerun is handled by the checkbox interaction directly


def calculate_subject_progress(subject):
    chapters = st.session_state['subject_chapters_data'][subject]
    if not chapters:
        return 0
    total = sum(len(ch["reminders"]) for ch in chapters)
    revised = sum(1 for ch in chapters for rem in ch["reminders"] if rem["status"] == "Revised")
    return (revised / total) * 100 if total else 0

def display_reminders_section(subject, chapter, chapter_index):
    rem_list = []
    for i, reminder in enumerate(chapter["reminders"]):
        # Use a unique key based on subject, chapter index, and reminder index
        key = f"{subject}_{chapter_index}_{i}_reminder_checkbox"
        current = reminder["status"] == "Revised"

        # Display reminder time correctly, ensuring it's a datetime object
        rem_time_dt = reminder["time"] if isinstance(reminder["time"], datetime.datetime) else convert_iso_to_datetimes(reminder["time"])
        rem_time_str = rem_time_dt.strftime("%d/%m/%y %I:%M %p") if isinstance(rem_time_dt, datetime.datetime) else str(reminder["time"]) # Fallback

        # Checkbox text includes the reminder type and time
        new_status = st.checkbox(f"{reminder['type']} ({rem_time_str})", value=current, key=key)

        if new_status != current:
            # Update status and save data only when the checkbox state changes
            if new_status:
                mark_reminder_revised(subject, chapter_index, i)
            else:
                mark_reminder_pending(subject, chapter_index, i)
            # Streamlit handles rerun automatically when a widget state changes and its value is captured


    # Optional: Display the dataframe summary *after* all checkboxes for this chapter are processed
    # This ensures the dataframe reflects the latest state after interactions
    summary_data = []
    for reminder in chapter["reminders"]:
         # Ensure reminder time is datetime object for display dataframe
        rem_time_dt = reminder["time"] if isinstance(reminder["time"], datetime.datetime) else convert_iso_to_datetimes(reminder["time"])
        rem_time_str = rem_time_dt.strftime("%d/%m/%y %I:%M %p") if isinstance(rem_time_dt, datetime.datetime) else str(reminder["time"])
        summary_data.append({
            "Reminder Type": reminder["type"],
            "Reminder Time": rem_time_str,
            "Status": reminder["status"]
        })

    if summary_data: # Only display if there are reminders
        st.markdown("<div class='dataframe-container'>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
         st.info("No reminders for this chapter.")


def display_time_spent_section(subject, chapter):
    # Use a form to wrap the number_input and button to prevent instant rerun on typing
    # Use a unique form key based on subject and chapter name
    with st.form(key=f"form_time_spent_{subject}_{chapter['chapter_name']}", clear_on_submit=False):
        # Use a unique key for the number input
        time_spent = st.number_input("Time Spent Studying (minutes):", value=chapter.get("time_spent", 0), min_value=0, step=5, key=f"time_spent_input_{subject}_{chapter['chapter_name']}")
        # REMOVED: key from form_submit_button
        update_button = st.form_submit_button("Update Time")
        if update_button:
            if time_spent != chapter.get("time_spent", 0):
                chapter["time_spent"] = time_spent
                save_subject_data_local() # Save to local file
                st.success("Time updated!")

def display_exam_tracking_section(subject, chapter, chapter_index):
    st.subheader(f"{subject} Exam Tracking - {chapter['chapter_name']}")
    # Use a form
    # Use a unique form key based on subject and chapter index
    with st.form(key=f"form_exam_tracking_{subject}_{chapter_index}", clear_on_submit=False):
        # Use unique keys for input widgets
        exam_appeared = st.number_input("Exams Appeared:", min_value=0, value=chapter.get("exams_appeared", 0), key=f"exam_count_input_{subject}_{chapter_index}")
        exam_status_text = st.text_input("Exam Status:", value=chapter.get("exam_status", "Not Appeared"), key=f"exam_status_input_{subject}_{chapter_index}", placeholder="e.g., Score, Performance")
        # REMOVED: key from form_submit_button
        update_button = st.form_submit_button("Update Exam Info")
        if update_button:
            chapter["exams_appeared"] = exam_appeared
            chapter["exam_status"] = exam_status_text
            save_subject_data_local() # Save to local file
            st.success("Exam info updated!")


def _get_chapter_item(subject_data, chapter_name):
    for idx, chapter in enumerate(subject_data):
        if chapter["chapter_name"] == chapter_name:
            return chapter, idx
    return None, -1

def display_subject_tab_content(subject):
    st.subheader(f"{subject} Revision Progress")
    progress = calculate_subject_progress(subject)
    st.progress(int(min(progress, 100)))
    st.write(f"Overall Revision: {progress:.2f}%")

    chapters = st.session_state['subject_chapters_data'][subject]
    chapter_names = [ch["chapter_name"] for ch in chapters]
    if not chapter_names:
        st.info(f"No chapters in {subject}. Please add one from the sidebar.")
        return

    # Use a unique key based on the subject for the selectbox
    selected = st.selectbox(f"Select {subject} Chapter:", ["Select Chapter"] + chapter_names, index=0, key=f"select_chapter_{subject}")
    if selected != "Select Chapter":
        chapter, idx = _get_chapter_item(chapters, selected)
        if chapter:
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            st.subheader("Reminders")
            # Pass the chapter index to display_reminders_section
            display_reminders_section(subject, chapter, idx)
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            st.subheader("Time Spent")
            display_time_spent_section(subject, chapter)
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            display_exam_tracking_section(subject, chapter, idx)
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            st.markdown("### Delete Chapter", unsafe_allow_html=True)
            # Use unique keys for checkbox and button based on subject and chapter name
            confirm_delete = st.checkbox(f"Confirm deletion of chapter '{selected}'", key=f"confirm_delete_{subject}_{selected}")
            if confirm_delete:
                # Use a unique key for the button
                if st.button(f"Delete Chapter '{selected}'", key=f"delete_{subject}_{selected}_button"):
                    delete_chapter(subject, idx)


def download_csv_data():
    # Uses the in-memory session state data, which is loaded from local file
    return _prepare_csv_data(st.session_state['subject_chapters_data'])

# ---------------- Productivity Tracking ----------------
def display_productivity_tracking():
    st.header("Productivity Tracking")
    # Use a unique key
    period = st.selectbox("Tracking Period:", ["Last 1 Week", "Last 1 Month", "All Time"], index=0, key="productivity_period_select")
    today = datetime.date.today()
    start_date = None
    if period == "Last 1 Week":
        start_date = today - datetime.timedelta(days=7)
    elif period == "Last 1 Month":
        start_date = today - datetime.timedelta(days=30)
    # Aggregates data from session state (loaded from local file)
    agg = _aggregate_productivity_data(st.session_state['subject_chapters_data'], start_date)
    df = pd.DataFrame([
        {"Date": d, "Total Reminders": stats["total"], "Revised": stats["revised"],
         "Productivity (%)": (stats["revised"] / stats["total"] * 100) if stats["total"] else 0}
        for d, stats in agg.items()
    ])
    if not df.empty:
        df.sort_values("Date", inplace=True)
        df["Date"] = df["Date"].apply(lambda d: d.strftime("%d/%m/%y"))
        fig = px.line(df, x="Date", y="Productivity (%)", markers=True, title="Daily Productivity")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No productivity data available for the selected period.")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("📚 NEET Prep App")
    with st.expander("App Theme", expanded=False):
        # Use a unique key
        st.session_state['app_theme'] = st.selectbox("Choose Theme:", THEME_OPTIONS, index=THEME_OPTIONS.index(st.session_state['app_theme']), key="sidebar_theme_select")
    with st.expander("Add New Chapter", expanded=True):
        # Use unique keys for input widgets
        subject = st.selectbox("Subject:", SUBJECT_CHOICES, key="add_chapter_subject_select")
        chapter_name = st.text_input("Chapter Name:", placeholder="e.g., Structure of Atom", key="add_chapter_name_input")
        entry_date = st.date_input("Entry Date:", value=datetime.date.today(), key="add_chapter_date_input")
        entry_time = st.time_input("Entry Time:", value=datetime.time(datetime.datetime.now().hour, datetime.datetime.now().minute), key="add_chapter_time_input")
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        st.subheader("Customize Revision Schedule (Optional)")
        # Use unique keys for checkboxes
        custom_12hr = st.checkbox("Use 12 hour Reminder?", value=True, key="custom_12hr_checkbox")
        custom_3day = st.checkbox("Use 3 days Reminder?", value=True, key="custom_3day_checkbox")
        custom_5day = st.checkbox("Use 5 days Reminder?", value=True, key="custom_5day_checkbox")

        # Use a form for adding a chapter to prevent reruns while typing
        with st.form("add_chapter_form", clear_on_submit=True):
            # Access values using their keys within the form submit logic
            # Get current values from session state which were set by the widgets above
            current_subject = st.session_state.get("add_chapter_subject_select", SUBJECT_CHOICES[0])
            current_chapter_name = st.session_state.get("add_chapter_name_input", "")
            current_entry_date = st.session_state.get("add_chapter_date_input", datetime.date.today())
            current_entry_time = st.session_state.get("add_chapter_time_input", datetime.time(datetime.datetime.now().hour, datetime.datetime.now().minute))
            current_custom_12hr = st.session_state.get("custom_12hr_checkbox", True)
            current_custom_3day = st.session_state.get("custom_3day_checkbox", True)
            current_custom_5day = st.session_state.get("custom_5day_checkbox", True)

            # REMOVED: key from form_submit_button
            form_add_button = st.form_submit_button("Add Chapter")

            if form_add_button:
                if current_chapter_name and current_subject:
                    entry_datetime = datetime.datetime.combine(current_entry_date, current_entry_time)
                    custom_reminders_list = []
                    if current_custom_12hr:
                        custom_reminders_list.append({
                            "reminder_id": 1,
                            "type": "12 hour Reminder",
                            "time": entry_datetime + datetime.timedelta(hours=12),
                            "status": "Pending"
                        })
                    if current_custom_3day:
                        custom_reminders_list.append({
                            "reminder_id": 2,
                            "type": "3 days Reminder",
                            "time": entry_datetime + datetime.timedelta(days=3),
                            "status": "Pending"
                        })
                    if current_custom_5day:
                        custom_reminders_list.append({
                            "reminder_id": 3,
                            "type": "5 days Reminder",
                            "time": entry_datetime + datetime.timedelta(days=5),
                            "status": "Pending"
                        })
                    add_chapter_and_reminders(current_subject, current_chapter_name, entry_datetime, custom_reminders_list)
                    # Form with clear_on_submit=True clears the inputs automatically

                else:
                    st.warning("Please enter a chapter name and select a subject.")

    with st.expander("Data Options", expanded=False):
        st.header("Download Data")
        csv_data = download_csv_data()
        # Use a unique key
        st.download_button(label="Download CSV", data=csv_data, file_name="neet_prep_data.csv", mime='text/csv', key="download_csv_button")
    st.header("Motivation")
    st.markdown(f"> *{random.choice(motivational_quotes)}*")
    st.header("Study Tips")
    with st.expander("See Study Tips"):
        for tip in study_tips:
            st.markdown(f"- {tip}")

# ---------------- Apply Theme CSS ----------------
apply_theme_css()

# ---------------- Main Panel & Tabs ----------------
st.markdown("<div class='main-header'><h1>NEET Prep Tracker Dashboard (Sathvik)</h1></div>", unsafe_allow_html=True)
tabs = st.tabs(SUBJECT_CHOICES + ["Today's Revisions", "Productivity Tracking", "To Do List"])

# ----- Subject Tabs -----
for idx, subject in enumerate(SUBJECT_CHOICES):
    # The tab title itself is unique, keys inside should be unique per subject+chapter
    with tabs[idx]:
        st.header(subject)
        st.markdown(f"<div class='dataframe-container' style='background-color:{TAB_HIGHLIGHT_COLOR}; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
        display_subject_tab_content(subject)
        st.markdown("</div>", unsafe_allow_html=True)

# ----- Today's Revisions Tab -----
with tabs[len(SUBJECT_CHOICES)]:
    st.header("Today's Revisions")
    # Use unique key
    mode = st.radio("View Mode", ["Today", "Select Date"], index=0, horizontal=True, key="revision_view_mode_radio")
    if mode == "Today":
        sel_date = datetime.date.today()
        st.info(f"Revisions for today: {sel_date.strftime('%d/%m/%y')}")
    else:
        # Use unique key
        sel_date = st.date_input("Select Date:", value=datetime.date.today(), key="revision_select_date_input")
        st.info(f"Revisions on: {sel_date.strftime('%d/%m/%y')}")

    revision_entries = []
    for subj, chapters in st.session_state['subject_chapters_data'].items():
        for c_idx, chapter in enumerate(chapters):
            for r_idx, reminder in enumerate(chapter["reminders"]):
                # Ensure reminder time is datetime object for date comparison
                rem_time_dt = reminder["time"] if isinstance(reminder["time"], datetime.datetime) else convert_iso_to_datetimes(reminder["time"])
                 # Safely handle potential non-datetime objects
                if isinstance(rem_time_dt, datetime.datetime) and rem_time_dt.date() == sel_date:
                    revision_entries.append((subj, c_idx, chapter, r_idx, reminder))

    st.markdown(f"**Total revisions found: {len(revision_entries)}**")
    if revision_entries:
        status_counts = {"Revised": 0, "Pending": 0}
        for entry in revision_entries:
            status_counts[entry[4]["status"]] += 1
        df_status = pd.DataFrame({"Status": list(status_counts.keys()), "Count": list(status_counts.values())})
        fig = px.pie(df_status, names="Status", values="Count", title="Revision Status Breakdown",
                     color_discrete_map={"Revised": COLOR_SUCCESS, "Pending": COLOR_WARNING})
        st.plotly_chart(fig, use_container_width=True)
        for i, (subj, c_idx, chapter, r_idx, reminder) in enumerate(revision_entries):
             # Ensure reminder time is datetime object for display
            rem_time_dt = reminder["time"] if isinstance(reminder["time"], datetime.datetime) else convert_iso_to_datetimes(reminder["time"])
            rem_time_str = rem_time_dt.strftime('%I:%M %p') if isinstance(rem_time_dt, datetime.datetime) else str(reminder['time'])

            with st.container():
                st.markdown(
                    f"<div class='container-box'>"
                    f"<strong>{subj}</strong> | {chapter['chapter_name']} | {reminder['type']} at {rem_time_str} | Status: {reminder['status']}"
                    f"</div>", unsafe_allow_html=True)
                # Use a key that is absolutely unique across all tabs and loops
                key = f"rev_today_{subj}_{c_idx}_{r_idx}_{i}_checkbox"
                current = reminder["status"] == "Revised"
                new_stat = st.checkbox("Mark Revised", value=current, key=key)
                if new_stat != current:
                    if new_stat:
                        mark_reminder_revised(subj, c_idx, r_idx)
                    else:
                        mark_reminder_pending(subj, c_idx, r_idx)
                    # Streamlit handles rerun because checkbox state changed

# ----- Productivity Tracking Tab -----
with tabs[len(SUBJECT_CHOICES) + 1]:
    display_productivity_tracking()

# ----- To Do List Tab -----
with tabs[-1]:
    st.header("To Do List")
    st.subheader("Add New Task")
    # Use a form for adding a task
    with st.form("add_todo_form", clear_on_submit=True):
        # Use a unique key
        new_task = st.text_input("Enter today's task:", key="new_todo_task_input")
        # REMOVED: key from form_submit_button
        add_task_button = st.form_submit_button("Add Task")
        if add_task_button:
            # Re-fetch value from session state
            current_new_task = st.session_state.get("new_todo_task_input", "")
            if current_new_task:
                new_task_entry = {
                    "task": current_new_task,
                    "status": "Pending",
                    "timestamp": datetime.datetime.now().isoformat() # Save as ISO string
                }
                st.session_state['todo_list'].append(new_task_entry)
                save_todo_data_local(st.session_state['todo_list']) # Save to local file
                st.success("Task added!")
            else:
                st.warning("Please enter a task.")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    st.subheader("Manual Tasks")
    if st.session_state['todo_list']:
        # Create a copy to iterate if deleting items
        todo_list_copy = st.session_state['todo_list'][:]
        for i, task in enumerate(todo_list_copy):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                # Use a unique key based on index and context
                key = f"todo_manual_{i}_checkbox"
                current = task["status"] == "Completed"
                new_val = st.checkbox(task["task"], value=current, key=key)
                if new_val != current:
                    # Find the index in the original list to update it
                    try:
                        # Use timestamp and task as identifiers in case list order changes unexpectedly
                        # Ensure comparing ISO strings or datetime objects consistently
                        task_ts = task.get("timestamp")
                        original_index = next((j for j, t in enumerate(st.session_state['todo_list']) if t["task"] == task["task"] and t.get("timestamp") == task_ts), -1)
                        if original_index != -1:
                             st.session_state['todo_list'][original_index]["status"] = "Completed" if new_val else "Pending"
                             save_todo_data_local(st.session_state['todo_list']) # Save to local file
                    except ValueError:
                        # Handle case where task might have been deleted already (unlikely with copy)
                         pass

            with col2:
                # Use a unique key based on index and context
                delete_key = f"delete_manual_{i}_button"
                if st.button("❌", key=delete_key):
                    # Find the index in the original list before deleting
                    try:
                        # Use timestamp and task as identifiers
                        task_ts = task.get("timestamp")
                        original_index = next((j for j, t in enumerate(st.session_state['todo_list']) if t["task"] == task["task"] and t.get("timestamp") == task_ts), -1)
                        if original_index != -1:
                            del st.session_state['todo_list'][original_index]
                            save_todo_data_local(st.session_state['todo_list']) # Save to local file
                            st.experimental_rerun() # Rerun needed after deletion
                    except ValueError:
                        pass # Task already deleted

        # st.markdown("</div>", unsafe_allow_html=True) # This div tag seems misplaced here
    else:
        st.info("No manual tasks added yet.")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.subheader("Today's Revision Reminders")
    today_date = datetime.date.today()
    rev_tasks = []
    for subj, chapters in st.session_state['subject_chapters_data'].items():
        for c_idx, chapter in enumerate(chapters):
            for r_idx, reminder in enumerate(chapter["reminders"]):
                # Ensure reminder time is datetime object for date comparison
                rem_time_dt = reminder["time"] if isinstance(reminder["time"], datetime.datetime) else convert_iso_to_datetimes(reminder["time"])
                # Safely handle potential non-datetime objects
                if isinstance(rem_time_dt, datetime.datetime) and rem_time_dt.date() == today_date:
                    rev_tasks.append((subj, c_idx, chapter, r_idx, reminder))

    if rev_tasks:
        for i, (subj, c_idx, chapter, r_idx, reminder) in enumerate(rev_tasks):
             # Ensure reminder time is datetime object for display
            rem_time_dt = reminder["time"] if isinstance(reminder["time"], datetime.datetime) else convert_iso_to_datetimes(reminder["time"])
            rem_time_str = rem_time_dt.strftime('%I:%M %p') if isinstance(rem_time_dt, datetime.datetime) else str(reminder['time'])

            with st.container():
                st.markdown(
                    f"<div class='container-box'>"
                    f"<strong>{subj}</strong> | {chapter['chapter_name']} | {reminder['type']} at {rem_time_str} | Status: {reminder['status']}"
                    f"</div>", unsafe_allow_html=True)
                # Use a key that is absolutely unique across all tabs and loops
                key = f"todo_rev_{subj}_{c_idx}_{r_idx}_{i}_checkbox"
                current = reminder["status"] == "Revised"
                new_stat = st.checkbox("Mark Revised", value=current, key=key)
                if new_stat != current:
                    if new_stat:
                        mark_reminder_revised(subj, c_idx, r_idx)
                    else:
                        mark_reminder_pending(subj, c_idx, r_idx)
                    # Streamlit handles rerun because checkbox state changed
    else:
        st.info("No revision reminders scheduled for today.")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.subheader("Today's To-Do Overview")
    total_manual = len(st.session_state['todo_list'])
    completed_manual = sum(1 for t in st.session_state['todo_list'] if t["status"] == "Completed")
    total_rev = len(rev_tasks)
    completed_rev = sum(1 for entry in rev_tasks if entry[4]["status"] == "Revised")
    total_tasks = total_manual + total_rev
    completed_tasks = completed_manual + completed_rev
    pending_tasks = total_tasks - completed_tasks
    if total_tasks > 0:
        df_overview = pd.DataFrame({
            "Status": ["Completed", "Pending"],
            "Count": [completed_tasks, pending_tasks]
        })
        fig = px.pie(df_overview, names="Status", values="Count", title="Today's To-Do Status")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks for today.")

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
