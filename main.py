import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import random
import json
import requests
import copy
from typing import Dict, List, Any, Optional, Tuple

# ---------------------------- CONFIGURATION & CONSTANTS ----------------------------
# --- App Passcode Configuration ---
APP_PASSCODE_CONFIG = {
    "key_name": "passcode",
    "placeholder": "YOUR_CHOSEN_STRONG_PASSCODE",
    "section": "app"
}

# --- JSONBin.io Configuration ---
JSONBIN_CONFIG = {
    "api_key_name": "api_key",
    "bin_id_name": "bin_id",
    "api_key_placeholder": "YOUR_NEW_SECURE_X_MASTER_KEY",
    "bin_id_placeholder": "YOUR_JSONBIN_BIN_ID",
    "section": "jsonbin",
    "base_url": "https://api.jsonbin.io/v3/b",
    "request_timeout": 15  # Seconds
}

# --- App Constants ---
SUBJECT_CHOICES = ["Botany", "Zoology", "Physics", "Chemistry"]
THEME_OPTIONS = ["Light Mode", "Dark Mode", "Colorful Mode"]
DEFAULT_APP_DATA = {
    "subject_chapters_data": {subject: [] for subject in SUBJECT_CHOICES},
    "todo_data": []
}
PRIMARY_COLOR = "#007BFF"
SECONDARY_COLOR = "#66B2FF"
TAB_HIGHLIGHT_COLOR = "#D1E7DD" # Used for light mode
TAB_HIGHLIGHT_COLOR_DARK = "#444444" # For dark mode
COLOR_SUCCESS = "#28A745"
COLOR_WARNING = "#DC3545" # Often used for pending/errors


# ---------------------------- SECRETS LOADING & VALIDATION ----------------------------
def load_secret(section: str, key_name: str, placeholder: Optional[str] = None) -> Optional[str]:
    """Safely loads a secret, provides feedback, and checks against placeholder."""
    try:
        value = st.secrets[section][key_name]
        if not value:
            st.error(f"Secret '{key_name}' in section '[{section}]' is empty.")
            return None
        if placeholder and value == placeholder:
            st.warning(f"Secret '{key_name}' in section '[{section}]' is using the placeholder value. Please update it.")
            return None # Treat placeholder as invalid for critical secrets
        return value
    except KeyError:
        st.error(f"Missing secret '{key_name}' under '[{section}]' section in Streamlit secrets.")
        return None
    except Exception as e:
        st.error(f"Error loading secret '{key_name}': {e}")
        return None

APP_PASSCODE = load_secret(APP_PASSCODE_CONFIG["section"], APP_PASSCODE_CONFIG["key_name"], APP_PASSCODE_CONFIG["placeholder"])
JSONBIN_API_KEY = load_secret(JSONBIN_CONFIG["section"], JSONBIN_CONFIG["api_key_name"], JSONBIN_CONFIG["api_key_placeholder"])
JSONBIN_BIN_ID = load_secret(JSONBIN_CONFIG["section"], JSONBIN_CONFIG["bin_id_name"], JSONBIN_CONFIG["bin_id_placeholder"])

PASSCODE_CONFIGURED = bool(APP_PASSCODE)
JSONBIN_SECRETS_CONFIGURED = bool(JSONBIN_API_KEY and JSONBIN_BIN_ID)

# ---------------- Set Page Config (MUST be the first Streamlit command) ----------------
st.set_page_config(
    page_title="NEET Exam Prep - Subject-wise Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------- PASSWORD PROTECTION ----------------------------
def check_password():
    if not PASSCODE_CONFIGURED:
        st.error("App passcode not configured correctly by the administrator. Access denied.")
        return False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 Enter Passcode")
    st.write("Please enter the passcode to access the application.")
    password_attempt = st.text_input("Passcode", type="password", key="password_attempt_input")

    if st.button("Login", key="password_submit_button"):
        if password_attempt == APP_PASSCODE:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("😕 Incorrect passcode. Please try again.")
            st.session_state["password_correct"] = False
    return False

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not check_password():
    st.stop()

# --- Post-Password Check: Verify JSONBin Secrets ---
if not JSONBIN_SECRETS_CONFIGURED:
    st.warning("JSONBin Secrets are not (or incorrectly) configured. Online data saving/loading will fail. The app will use temporary local data.")
    # App can continue with local data, but persistence is disabled.

# ---------------------------- CSS STYLING ----------------------------
def get_app_css(theme: str) -> str:
    base_css = f"""
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"]  {{
            font-family: 'Roboto', sans-serif;
        }}
        .main-header {{
            background: linear-gradient(135deg, {PRIMARY_COLOR}, {SECONDARY_COLOR});
            padding: 20px; border-radius: 8px; text-align: center; color: white; margin-bottom: 20px;
        }}
        .sidebar .sidebar-content {{ padding: 20px; border-radius: 8px; }}
        .stButton>button {{ border: none; border-radius: 5px; padding: 8px 16px; }}
        .stProgress>div>div {{ border-radius: 5px; }}
        .dataframe-container {{ background: #ffffff; border-radius: 8px; padding: 10px; box-shadow: 0px 2px 4px rgba(0,0,0,0.1); }}
        .section-divider {{ border: none; border-bottom: 1px solid #ddd; margin: 10px 0; }}
        .container-box {{ background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin-bottom: 10px; }}
        .current-time {{
            position: fixed; top: 10px; right: 10px; z-index: 10000;
            background: #ffffff; padding: 5px 10px; border-radius: 5px;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.2); font-size: 14px;
        }}
    """
    theme_css = ""
    if theme == "Dark Mode":
        theme_css = f"""
            body, .stApp {{ background-color: #222; color: #ddd; }}
            .sidebar .sidebar-content {{ background-color: #333; }}
            .stButton>button {{ background-color: #555; color: #fff; }}
            .stProgress>div>div {{ background-color: #888; }}
            .dataframe-container {{ background: #333; border: 1px solid #555;}}
            .container-box {{ background: #444; border: 1px solid #666;}}
            .current-time {{ background: #333; color: #ddd; border: 1px solid #555; }}
        """
    elif theme == "Colorful Mode":
        theme_css = f"""
            body, .stApp {{ background-color: #e0f7fa; color: #212529; }}
            .sidebar .sidebar-content {{ background-color: #b2ebf2; }}
            .stButton>button {{ background-color: #ff4081; color: #fff; }}
            .stProgress>div>div {{ background-color: #ff4081; }}
            .dataframe-container {{ background: #ffffff; }}
            .container-box {{ background: #f0f8ff; border: 1px solid #b2ebf2;}}
        """
    else:  # Light Mode
        theme_css = f"""
            body, .stApp {{ background-color: #F8F9FA; color: #212529; }}
            .sidebar .sidebar-content {{ background-color: #f0f2f6; }}
            .stButton>button {{ background-color: {PRIMARY_COLOR}; color: #fff; }}
            .stProgress>div>div {{ background-color: {SECONDARY_COLOR}; }}
        """
    return f"{base_css}\n{theme_css}\n</style>"

# ---------------------------- CURRENT TIME DISPLAY ----------------------------
# Placeholder for current time, will be updated dynamically if desired, or just once on load
current_time_placeholder = st.empty()
def display_current_time():
    current_time_str = datetime.datetime.now().strftime("%d/%m/%y %I:%M:%S %p")
    current_time_placeholder.markdown(f"""
        <div class="current-time">
            <strong>{current_time_str}</strong>
        </div>
        """, unsafe_allow_html=True)

display_current_time() # Initial display

# ---------------------------- JSONBIN.IO PERSISTENCE ----------------------------
def _get_jsonbin_headers() -> Optional[Dict[str, str]]:
    if not JSONBIN_SECRETS_CONFIGURED: # Relies on global check
        return None
    return {
        'Content-Type': 'application/json',
        'X-Master-Key': JSONBIN_API_KEY
    }

def _process_datetime_fields(data_node: Any, to_iso: bool) -> Any:
    """Recursively processes datetime fields to/from ISO format."""
    if isinstance(data_node, dict):
        new_dict = {}
        for k, v in data_node.items():
            if isinstance(v, datetime.datetime):
                new_dict[k] = v.isoformat() if to_iso else datetime.datetime.fromisoformat(v) if isinstance(v, str) else v
            elif k in ["entry_datetime", "timestamp", "time"] and isinstance(v, str) and not to_iso: # Specific keys for loading
                try:
                    new_dict[k] = datetime.datetime.fromisoformat(v)
                except ValueError:
                    new_dict[k] = v # Keep as string if invalid
            else:
                new_dict[k] = _process_datetime_fields(v, to_iso)
        return new_dict
    elif isinstance(data_node, list):
        return [_process_datetime_fields(item, to_iso) for item in data_node]
    return data_node

def _prepare_data_for_saving(data: Dict[str, Any]) -> Dict[str, Any]:
    """Converts datetime objects to ISO strings before saving to JSON."""
    return _process_datetime_fields(copy.deepcopy(data), to_iso=True)

def _process_loaded_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Converts ISO string dates/times back to datetime objects after loading."""
    return _process_datetime_fields(data, to_iso=False)


@st.cache_data(ttl=300) # Cache data for 5 minutes
def load_data_from_jsonbin() -> Optional[Dict[str, Any]]:
    if not JSONBIN_SECRETS_CONFIGURED:
        st.warning("Cannot load data: JSONBin secrets not configured.")
        return None

    headers = _get_jsonbin_headers()
    if headers is None: # Should be caught by JSONBIN_SECRETS_CONFIGURED, but as a safeguard
        st.error("Cannot load data: API Key issue (should not happen if secrets configured).")
        return None

    url = f"{JSONBIN_CONFIG['base_url']}/{JSONBIN_BIN_ID}/latest"
    try:
        with st.spinner("Fetching latest data from JSONBin..."):
            response = requests.get(url, headers=headers, timeout=JSONBIN_CONFIG['request_timeout'])
            response.raise_for_status()
            raw_data = response.json().get("record")

            if not raw_data:
                st.warning("JSONBin bin is empty. Initializing with default structure.")
                return copy.deepcopy(DEFAULT_APP_DATA)
            if isinstance(raw_data, dict) and "subject_chapters_data" in raw_data and "todo_data" in raw_data:
                return _process_loaded_data(raw_data)
            else:
                st.error("Loaded data structure from JSONBin is unexpected. Using default empty structure.")
                st.json(raw_data) # Show problematic data
                return copy.deepcopy(DEFAULT_APP_DATA)

    except requests.exceptions.Timeout:
        st.error(f"Error loading data: Request timed out after {JSONBIN_CONFIG['request_timeout']}s.")
    except requests.exceptions.HTTPError as e:
        st.error(f"Error loading data from JSONBin (HTTP {e.response.status_code}): {e}")
        if e.response.status_code == 404:
            st.error(f"Bin ID '{JSONBIN_BIN_ID}' not found. Please create the bin or check the Bin ID.")
            return copy.deepcopy(DEFAULT_APP_DATA) # Return default if bin not found
        elif e.response.status_code == 401:
            st.error("Unauthorized (401). Check your JSONBin API Key.")
        try: st.json({"error_details": e.response.json()})
        except json.JSONDecodeError: st.text(e.response.text)
    except json.JSONDecodeError:
        st.error("Error: Could not decode JSON response from JSONBin.")
    except Exception as e:
        st.error(f"An unexpected error occurred during loading: {e}")
    return None # Indicate failure for most errors except specific cases like 404

def save_data_to_jsonbin(data_to_save: Dict[str, Any]) -> bool:
    if not JSONBIN_SECRETS_CONFIGURED:
        st.error("Cannot save data: JSONBin secrets not configured.")
        return False

    headers = _get_jsonbin_headers()
    if headers is None:
        st.error("Cannot save data: API Key issue.")
        return False
    if data_to_save is None:
        st.warning("Attempted to save 'None' data. Aborting save.")
        return False

    prepared_data = _prepare_data_for_saving(data_to_save)
    url = f"{JSONBIN_CONFIG['base_url']}/{JSONBIN_BIN_ID}"
    try:
        with st.spinner("Saving data to JSONBin..."):
            response = requests.put(url, headers=headers, json=prepared_data, timeout=JSONBIN_CONFIG['request_timeout'])
            response.raise_for_status()

        st.cache_data.clear() # IMPORTANT: Clear cache after successful save
        return True
    except requests.exceptions.Timeout:
        st.error(f"Error saving data: Request timed out after {JSONBIN_CONFIG['request_timeout']}s.")
    except requests.exceptions.HTTPError as e:
        st.error(f"Error saving data to JSONBin (HTTP {e.response.status_code}): {e}")
        if e.response.status_code == 401:
             st.error("Unauthorized (401). Check your JSONBin API Key.")
        try: st.json({"error_details": e.response.json()})
        except json.JSONDecodeError: st.text(e.response.text)
    except Exception as e:
        st.error(f"An unexpected error occurred during saving: {e}")
    return False

# ---------------------------- SESSION STATE INITIALIZATION & HELPERS ----------------------------
def get_app_data() -> Dict[str, Any]:
    return st.session_state.get('app_data', copy.deepcopy(DEFAULT_APP_DATA))

def get_subject_chapters_data() -> Dict[str, List[Dict]]:
    app_data = get_app_data()
    return app_data.get("subject_chapters_data", {})

def get_todo_data() -> List[Dict]:
    app_data = get_app_data()
    return app_data.get("todo_data", [])

def initialize_session_state():
    if 'app_data' not in st.session_state:
        if JSONBIN_SECRETS_CONFIGURED:
            loaded_data = load_data_from_jsonbin()
            if loaded_data is None:
                st.error("CRITICAL: Failed to load data after login. Using temporary empty structure.")
                st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)
            else:
                st.session_state['app_data'] = loaded_data
                st.success("Data loaded successfully from JSONBin.")
        else:
            st.warning("Using temporary empty local data as JSONBin is not configured. Changes will not be saved online.")
            st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)

    if 'app_theme' not in st.session_state:
        st.session_state['app_theme'] = "Light Mode"

    # Ensure data structure integrity (defensive programming)
    app_data = st.session_state.get('app_data')
    if not isinstance(app_data, dict) \
       or "subject_chapters_data" not in app_data \
       or "todo_data" not in app_data:
        st.warning("App data structure was invalid. Resetting to default.")
        st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)
    
    # Ensure all subjects exist in subject_chapters_data
    for subject in SUBJECT_CHOICES:
        if subject not in st.session_state['app_data']['subject_chapters_data']:
            st.session_state['app_data']['subject_chapters_data'][subject] = []


initialize_session_state()

# ---------------------------- MOTIVATIONAL CONTENT ----------------------------
motivational_quotes = [
    "The expert in anything was once a beginner.", "Believe you can and you're halfway there.",
    "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    "The only way to do great work is to love what you do.", "Your future is created by what you do today, not tomorrow."
]
study_tips = [
    "Plan your study schedule and stick to it.", "Use active recall and spaced repetition techniques.",
    "Practice with past papers regularly.", "Take short breaks to avoid burnout.",
    "Stay hydrated and get enough sleep."
]

# ---------------------------- HELPER & CORE FUNCTIONS ----------------------------
def _create_default_reminders(entry_datetime: datetime.datetime) -> List[Dict]:
    return [
        {"reminder_id": 1, "type": "12 hour Reminder", "time": entry_datetime + datetime.timedelta(hours=12), "status": "Pending"},
        {"reminder_id": 2, "type": "3 days Reminder", "time": entry_datetime + datetime.timedelta(days=3), "status": "Pending"},
        {"reminder_id": 3, "type": "5 days Reminder", "time": entry_datetime + datetime.timedelta(days=5), "status": "Pending"},
    ]

def _prepare_csv_data() -> bytes:
    subject_data = get_subject_chapters_data()
    all_data = []
    for subject, chapters in subject_data.items():
        for chapter in chapters:
            for reminder in chapter.get('reminders', []):
                all_data.append({
                    "Subject": subject,
                    "Chapter Name": chapter.get('chapter_name', 'N/A'),
                    "Entry Date": chapter.get('entry_datetime', 'N/A').strftime("%d/%m/%y %I:%M %p") if isinstance(chapter.get('entry_datetime'), datetime.datetime) else 'N/A',
                    "Reminder Time": reminder.get('time', 'N/A').strftime("%d/%m/%y %I:%M %p") if isinstance(reminder.get('time'), datetime.datetime) else 'N/A',
                    "Status": reminder.get('status', 'N/A'),
                    "Exams Appeared": chapter.get('exams_appeared', 0),
                    "Exam Status": chapter.get('exam_status', 'Not Appeared'),
                    "Time Spent (minutes)": chapter.get('time_spent', 0)
                })
    return pd.DataFrame(all_data).to_csv(index=False).encode('utf-8')

def _aggregate_productivity_data(start_date: Optional[datetime.date] = None) -> Dict:
    subject_data = get_subject_chapters_data()
    aggregated = {}
    for chapters in subject_data.values():
        for chapter in chapters:
            for reminder in chapter.get("reminders", []):
                reminder_time_obj = reminder.get("time")
                if isinstance(reminder_time_obj, datetime.datetime):
                    r_date = reminder_time_obj.date()
                    if start_date and r_date < start_date:
                        continue
                    aggregated.setdefault(r_date, {"total": 0, "revised": 0})
                    aggregated[r_date]["total"] += 1
                    if reminder.get("status") == "Revised":
                        aggregated[r_date]["revised"] += 1
    return aggregated

def add_chapter_and_reminders(subject: str, chapter_name: str, entry_datetime: datetime.datetime, custom_reminders: Optional[List[Dict]] = None):
    app_data = get_app_data()
    reminders = custom_reminders if custom_reminders else _create_default_reminders(entry_datetime)
    new_chapter = {
        "chapter_name": chapter_name, "entry_datetime": entry_datetime, "reminders": reminders,
        "exams_appeared": 0, "exam_status": "Not Appeared", "time_spent": 0
    }
    app_data['subject_chapters_data'][subject].append(new_chapter)
    if save_data_to_jsonbin(app_data):
        st.success(f"Chapter '{chapter_name}' added to {subject} and saved.")
        st.rerun()
    else:
        st.error("Failed to save chapter online. Reverting local change.")
        app_data['subject_chapters_data'][subject].pop() # Revert

def delete_chapter(subject: str, chapter_index: int):
    app_data = get_app_data()
    chapters_list = app_data['subject_chapters_data'][subject]
    if 0 <= chapter_index < len(chapters_list):
        chapter_name = chapters_list[chapter_index].get('chapter_name', 'this chapter')
        original_chapter_data = copy.deepcopy(chapters_list[chapter_index]) # For revert
        del chapters_list[chapter_index]
        if save_data_to_jsonbin(app_data):
            st.success(f"Chapter '{chapter_name}' deleted successfully!")
            st.rerun()
        else:
            st.error("Failed to save deletion online. Reverting local change.")
            chapters_list.insert(chapter_index, original_chapter_data) # Revert
    else:
        st.error("Invalid chapter index for deletion.")

def update_reminder_statuses(subject: str, chapter_index: int, updated_statuses: List[bool]):
    """Updates multiple reminder statuses and saves once."""
    app_data = get_app_data()
    chapter = app_data['subject_chapters_data'][subject][chapter_index]
    original_reminders = copy.deepcopy(chapter['reminders'])
    changed = False
    for i, new_status_is_revised in enumerate(updated_statuses):
        current_status = chapter['reminders'][i]['status']
        target_status = "Revised" if new_status_is_revised else "Pending"
        if current_status != target_status:
            chapter['reminders'][i]['status'] = target_status
            changed = True
    
    if changed:
        if save_data_to_jsonbin(app_data):
            st.success("Reminder statuses updated successfully.")
            st.rerun()
        else:
            st.error("Failed to save reminder status updates. Reverting local changes.")
            chapter['reminders'] = original_reminders # Revert
    else:
        st.info("No changes in reminder statuses to save.")


def calculate_subject_progress(subject: str) -> float:
    chapters = get_subject_chapters_data().get(subject, [])
    total, revised = 0, 0
    for ch in chapters:
        reminders = ch.get("reminders", [])
        total += len(reminders)
        revised += sum(1 for rem in reminders if rem.get("status") == "Revised")
    return (revised / total) * 100 if total else 0

def display_reminders_section(subject: str, chapter: Dict, chapter_index: int):
    reminders = chapter.get("reminders", [])
    if not reminders:
        st.caption("No reminders found for this chapter.")
        return

    with st.form(key=f"form_reminders_{subject}_{chapter_index}"):
        st.subheader("Manage Reminders")
        rem_list_display = []
        # Store current status for checkboxes
        current_statuses = [rem.get("status") == "Revised" for rem in reminders]
        updated_statuses_values = []

        for i, reminder in enumerate(reminders):
            # Use unique key for each checkbox inside the form
            status_is_revised = st.checkbox(
                f"{reminder.get('type', 'Unknown')} @ {reminder.get('time', 'N/A').strftime('%d/%m %I:%M%p') if isinstance(reminder.get('time'), datetime.datetime) else 'N/A'}",
                value=current_statuses[i],
                key=f"rem_cb_{subject}_{chapter_index}_{i}_form"
            )
            updated_statuses_values.append(status_is_revised)
            rem_list_display.append({
                "Reminder Type": reminder.get("type", "N/A"),
                "Reminder Time": reminder.get("time", "N/A").strftime("%d/%m/%y %I:%M %p") if isinstance(reminder.get('time'), datetime.datetime) else 'N/A',
                "Status": "Revised" if status_is_revised else "Pending" # Show potential new status
            })
        
        if st.form_submit_button("Update Reminder Statuses"):
            update_reminder_statuses(subject, chapter_index, updated_statuses_values)
            # Rerun is handled by update_reminder_statuses on success

    # Display current state (or what it would be post-submit)
    with st.container():
        st.markdown("<div class='dataframe-container'>", unsafe_allow_html=True)
        if rem_list_display:
            st.dataframe(pd.DataFrame(rem_list_display), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def display_time_spent_section(subject: str, chapter: Dict, chapter_index: int):
    current_time_spent = chapter.get("time_spent", 0)
    
    with st.form(key=f"time_spent_form_{subject}_{chapter_index}"):
        time_spent_input = st.number_input(
            "Time Spent Studying (minutes):",
            value=current_time_spent,
            min_value=0,
            step=5,
            key=f"time_spent_input_{subject}_{chapter_index}"
        )
        submitted = st.form_submit_button("Update Time Spent")

    if submitted and time_spent_input != current_time_spent:
        app_data = get_app_data()
        # Access chapter directly from app_data to ensure we modify the session state version
        chapter_to_update = app_data['subject_chapters_data'][subject][chapter_index]
        original_time = chapter_to_update.get("time_spent", 0)
        chapter_to_update["time_spent"] = time_spent_input
        if save_data_to_jsonbin(app_data):
            st.success("Time spent updated successfully!")
            st.rerun()
        else:
            st.error("Failed to save time spent online. Reverting.")
            chapter_to_update["time_spent"] = original_time # Revert
    elif submitted:
        st.info("No change in time spent.")


def display_exam_tracking_section(subject: str, chapter: Dict, chapter_index: int):
    st.subheader(f"Exam Tracking")
    current_exam_appeared = chapter.get("exams_appeared", 0)
    current_exam_status = chapter.get("exam_status", "Not Appeared")

    with st.form(key=f"exam_tracking_form_{subject}_{chapter_index}"):
        exam_appeared = st.number_input("Exams Appeared:", min_value=0, value=current_exam_appeared)
        exam_status_text = st.text_input("Exam Status:", value=current_exam_status, placeholder="e.g., Score, Performance")
        submitted = st.form_submit_button("Update Exam Info")

    if submitted:
        if exam_appeared != current_exam_appeared or exam_status_text != current_exam_status:
            app_data = get_app_data()
            chapter_to_update = app_data['subject_chapters_data'][subject][chapter_index]
            # Store originals for revert
            original_appeared = chapter_to_update["exams_appeared"]
            original_status = chapter_to_update["exam_status"]

            chapter_to_update["exams_appeared"] = exam_appeared
            chapter_to_update["exam_status"] = exam_status_text
            if save_data_to_jsonbin(app_data):
                st.success("Exam info updated!")
                st.rerun()
            else:
                st.error("Failed to save exam info online. Reverting.")
                chapter_to_update["exams_appeared"] = original_appeared
                chapter_to_update["exam_status"] = original_status
        else:
            st.info("No changes detected in exam info.")

def _get_chapter_item(subject: str, chapter_name: str) -> Tuple[Optional[Dict], int]:
    chapters_list = get_subject_chapters_data().get(subject, [])
    for idx, chapter in enumerate(chapters_list):
        if chapter.get("chapter_name") == chapter_name:
            return chapter, idx
    return None, -1

def display_subject_tab_content(subject: str):
    st.subheader(f"{subject} Revision Progress")
    progress = calculate_subject_progress(subject)
    st.progress(int(min(progress, 100)))
    st.write(f"Overall Revision: {progress:.2f}%")

    chapters_list = get_subject_chapters_data().get(subject, [])
    chapter_names = [ch.get("chapter_name", f"Unnamed Chapter {i}") for i, ch in enumerate(chapters_list)]
    
    if not chapter_names:
        st.info(f"No chapters in {subject}. Please add one from the sidebar.")
        return

    selected_chapter_name = st.selectbox(f"Select {subject} Chapter:", ["Select Chapter"] + chapter_names, index=0, key=f"select_{subject}")
    if selected_chapter_name != "Select Chapter":
        chapter_data, chapter_idx = _get_chapter_item(subject, selected_chapter_name)
        if chapter_data is not None and chapter_idx != -1:
            # Pass a copy to display functions if they don't modify, or ensure they get from session_state
            display_reminders_section(subject, chapter_data, chapter_idx)
            st.markdown("<br>", unsafe_allow_html=True)
            display_time_spent_section(subject, chapter_data, chapter_idx)
            st.markdown("<br>", unsafe_allow_html=True)
            display_exam_tracking_section(subject, chapter_data, chapter_idx)
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            
            st.markdown("### Delete Chapter", unsafe_allow_html=True)
            confirm_delete = st.checkbox("Confirm deletion", key=f"confirm_delete_{subject}_{chapter_idx}", help=f"Tick this box to enable deletion of '{selected_chapter_name}'.")
            if st.button("Delete Chapter Permanently", key=f"delete_{subject}_{chapter_idx}", disabled=not confirm_delete, type="primary"):
                delete_chapter(subject, chapter_idx)
        else:
             st.warning(f"Could not find details for chapter: {selected_chapter_name}")

def get_revisions_for_date(target_date: datetime.date) -> List[Tuple[str, int, Dict, int, Dict]]:
    """Fetches all revision entries for a specific date."""
    revision_entries = []
    subject_data = get_subject_chapters_data()
    for subj, chapters in subject_data.items():
        for c_idx, chapter in enumerate(chapters):
            for r_idx, reminder in enumerate(chapter.get("reminders", [])):
                reminder_time_obj = reminder.get("time")
                if isinstance(reminder_time_obj, datetime.datetime) and reminder_time_obj.date() == target_date:
                    revision_entries.append((subj, c_idx, chapter, r_idx, reminder))
    return revision_entries

def display_revision_entries_list(revision_entries: List[Tuple[str, int, Dict, int, Dict]], list_key_prefix: str):
    """Displays a list of revision entries with interactive checkboxes."""
    if not revision_entries:
        st.info(f"No revisions scheduled.")
        return

    # Use a form to batch updates for these checkboxes too
    with st.form(key=f"form_{list_key_prefix}_revisions"):
        checkbox_states = {} # To store the new state of checkboxes
        for idx, (subj, c_idx, chapter, r_idx, reminder) in enumerate(revision_entries):
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                st.markdown(
                    f"<div class='container-box' style='margin-bottom: 2px;'>"
                    f"<strong>{subj}</strong> | {chapter.get('chapter_name','N/A')} | {reminder.get('type','N/A')} at "
                    f"{reminder.get('time','N/A').strftime('%I:%M %p') if isinstance(reminder.get('time'),datetime.datetime) else 'N/A'}"
                    f"</div>", unsafe_allow_html=True)
            with col2:
                key = f"{list_key_prefix}_cb_{subj}_{c_idx}_{r_idx}_{idx}"
                current_is_revised = reminder.get("status") == "Revised"
                new_is_revised = st.checkbox("Done", value=current_is_revised, key=key, label_visibility="collapsed")
                checkbox_states[(subj, c_idx, r_idx)] = new_is_revised
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        if st.form_submit_button("Update All Displayed Revision Statuses"):
            app_data = get_app_data()
            original_app_data_copy = copy.deepcopy(app_data) # For potential full revert
            any_change_attempted = False

            for (subj, c_idx, r_idx), new_is_revised in checkbox_states.items():
                try:
                    reminder_to_update = app_data['subject_chapters_data'][subj][c_idx]['reminders'][r_idx]
                    current_status = reminder_to_update['status']
                    target_status = "Revised" if new_is_revised else "Pending"
                    if current_status != target_status:
                        reminder_to_update['status'] = target_status
                        any_change_attempted = True
                except (KeyError, IndexError):
                    st.error(f"Error accessing reminder for {subj} - Chapter {c_idx} - Reminder {r_idx}. Skipping.")
                    continue
            
            if any_change_attempted:
                if save_data_to_jsonbin(app_data):
                    st.success("Revision statuses updated.")
                    st.rerun()
                else:
                    st.error("Failed to save revision status updates. Reverting local changes.")
                    st.session_state['app_data'] = original_app_data_copy # Revert all changes
                    st.rerun() # Rerun to show reverted state
            else:
                st.info("No changes in revision statuses to save.")


# ---------------------------- SIDEBAR ----------------------------
with st.sidebar:
    st.title("📚 NEET Prep App")
    with st.expander("App Theme", expanded=False):
        current_theme = st.session_state.get('app_theme', "Light Mode")
        selected_theme = st.selectbox("Choose Theme:", THEME_OPTIONS, index=THEME_OPTIONS.index(current_theme), key="theme_select")
        if selected_theme != current_theme:
            st.session_state['app_theme'] = selected_theme
            st.rerun()

    with st.expander("Add New Chapter", expanded=True):
        # Use st.form for adding a new chapter
        with st.form(key="add_chapter_form"):
            subject_form = st.selectbox("Subject:", SUBJECT_CHOICES, key="add_subj_form")
            chapter_name_form = st.text_input("Chapter Name:", placeholder="e.g., Structure of Atom", key="add_chap_name_form")
            entry_date_form = st.date_input("Entry Date:", value=datetime.date.today(), key="add_date_form")
            entry_time_form = st.time_input("Entry Time:", value=datetime.datetime.now().time().replace(second=0, microsecond=0), key="add_time_form")
            
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            st.caption("Revision Schedule (Default: 12hr, 3 day, 5 day)")
            use_12hr_form = st.checkbox("12 hour Reminder", value=True, key="add_cb_12hr_form")
            use_3day_form = st.checkbox("3 days Reminder", value=True, key="add_cb_3day_form")
            use_5day_form = st.checkbox("5 days Reminder", value=True, key="add_cb_5day_form")
            
            submitted_add_chapter = st.form_submit_button("Add Chapter")

            if submitted_add_chapter:
                if chapter_name_form and subject_form:
                    entry_datetime = datetime.datetime.combine(entry_date_form, entry_time_form)
                    custom_reminders = []
                    rid_counter = 1
                    if use_12hr_form:
                        custom_reminders.append({"reminder_id": rid_counter, "type": "12 hour Reminder", "time": entry_datetime + datetime.timedelta(hours=12), "status": "Pending"}); rid_counter+=1
                    if use_3day_form:
                        custom_reminders.append({"reminder_id": rid_counter, "type": "3 days Reminder", "time": entry_datetime + datetime.timedelta(days=3), "status": "Pending"}); rid_counter+=1
                    if use_5day_form:
                        custom_reminders.append({"reminder_id": rid_counter, "type": "5 days Reminder", "time": entry_datetime + datetime.timedelta(days=5), "status": "Pending"}); rid_counter+=1
                    
                    add_chapter_and_reminders(subject_form, chapter_name_form, entry_datetime, custom_reminders)
                    # Rerun is handled by add_chapter_and_reminders on success
                else:
                    st.warning("Please enter a chapter name and select a subject.")

    with st.expander("Data Options", expanded=False):
        st.header("Download Data")
        st.download_button(label="Download Study Data (CSV)", data=_prepare_csv_data(), file_name="neet_prep_data.csv", mime='text/csv', key="download_csv_btn")

    st.header("Motivation")
    st.markdown(f"> *{random.choice(motivational_quotes)}*")
    st.header("Study Tips")
    with st.expander("See Study Tips", expanded=False):
        for tip in study_tips: st.markdown(f"- {tip}")

# ---------------------------- APPLY THEME & MAIN PANEL ----------------------------
st.markdown(get_app_css(st.session_state.app_theme), unsafe_allow_html=True)
st.markdown("<div class='main-header'><h1>NEET Prep Tracker Dashboard</h1></div>", unsafe_allow_html=True)

tab_titles = SUBJECT_CHOICES + ["Today's Revisions", "Productivity Tracking", "To Do List"]
tabs = st.tabs(tab_titles)

# ----- Subject Tabs -----
for idx, subject_name in enumerate(SUBJECT_CHOICES):
    with tabs[idx]:
        st.header(subject_name)
        tab_bg_color = TAB_HIGHLIGHT_COLOR_DARK if st.session_state.app_theme == "Dark Mode" else TAB_HIGHLIGHT_COLOR
        st.markdown(f"<div style='background-color:{tab_bg_color}; padding: 15px; border-radius: 8px; border: 1px solid #ccc;'>", unsafe_allow_html=True)
        display_subject_tab_content(subject_name)
        st.markdown("</div>", unsafe_allow_html=True)

# ----- Today's Revisions Tab -----
with tabs[len(SUBJECT_CHOICES)]:
    st.header("Today's Revisions")
    mode = st.radio("View Mode", ["Today", "Select Date"], index=0, horizontal=True, key="rev_view_mode")
    sel_date = datetime.date.today() if mode == "Today" else st.date_input("Select Date:", value=datetime.date.today(), key="rev_date_select")
    
    st.info(f"Showing revisions for: {sel_date.strftime('%d %b, %Y')}")
    todays_revision_entries = get_revisions_for_date(sel_date)
    st.markdown(f"**Total revisions found: {len(todays_revision_entries)}**")

    if todays_revision_entries:
        status_counts = {"Revised": 0, "Pending": 0}
        for _, _, _, _, reminder in todays_revision_entries:
            status_counts[reminder.get("status", "Pending")] += 1
        
        if sum(status_counts.values()) > 0:
            df_status = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
            df_status['Status'] = pd.Categorical(df_status['Status'], categories=["Revised", "Pending"], ordered=True)
            fig_pie = px.pie(df_status, names="Status", values="Count", title="Revision Status Breakdown",
                             color="Status", color_discrete_map={"Revised": COLOR_SUCCESS, "Pending": COLOR_WARNING})
            fig_pie.update_traces(textinfo='percent+value')
            st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("---")
        display_revision_entries_list(todays_revision_entries, "today_rev_tab")

# ----- Productivity Tracking Tab -----
with tabs[len(SUBJECT_CHOICES) + 1]:
    st.header("Productivity Tracking")
    period = st.selectbox("Tracking Period:", ["Last 1 Week", "Last 1 Month", "All Time"], key="prod_period")
    start_date_prod = None
    if period == "Last 1 Week": start_date_prod = datetime.date.today() - datetime.timedelta(days=7)
    elif period == "Last 1 Month": start_date_prod = datetime.date.today() - datetime.timedelta(days=30)

    agg_data = _aggregate_productivity_data(start_date_prod)
    if agg_data:
        df_prod = pd.DataFrame([
            {"Date": d, "Total Reminders": stats["total"], "Revised": stats["revised"],
             "Productivity (%)": (stats["revised"] / stats["total"] * 100) if stats["total"] else 0}
            for d, stats in agg_data.items()
        ]).sort_values("Date")
        df_prod_display = df_prod.copy()
        df_prod_display["Date"] = df_prod_display["Date"].apply(lambda d: d.strftime("%d/%m/%y"))
        
        fig_line = px.line(df_prod_display, x="Date", y="Productivity (%)", markers=True, title="Daily Productivity Trend")
        st.plotly_chart(fig_line, use_container_width=True)
        st.dataframe(df_prod_display, use_container_width=True)
    else:
        st.info("No productivity data available for the selected period.")

# ----- To Do List Tab -----
with tabs[-1]:
    st.header("To Do List")
    app_data_todo = get_app_data() # Get main app_data dict for modification

    # Add New Manual Task
    with st.form("add_todo_task_form"):
        new_task_text = st.text_input("Enter new task:", key="new_todo_task_input_form", placeholder="Enter new task...")
        submitted_add_task = st.form_submit_button("Add Task")
    
    if submitted_add_task:
        if new_task_text:
            new_task_entry = {"task": new_task_text, "status": "Pending", "timestamp": datetime.datetime.now()}
            app_data_todo['todo_data'].append(new_task_entry)
            if save_data_to_jsonbin(app_data_todo):
                st.success("Task added!")
                st.rerun()
            else:
                st.error("Failed to save task online. Reverting.")
                app_data_todo['todo_data'].pop()
        else:
            st.warning("Please enter a task.")
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # Manual Tasks List
    st.subheader("Manual Tasks")
    todo_list = get_todo_data() # Get current list
    if todo_list:
        with st.form("manual_tasks_form"):
            indices_to_delete_todo = []
            task_statuses_todo = {} # (index, new_status_is_completed)

            for i, task in enumerate(todo_list):
                col1, col2, col3 = st.columns([0.75, 0.15, 0.1])
                with col1:
                    current_is_completed = task.get("status", "Pending") == "Completed"
                    new_is_completed = st.checkbox(
                        task.get("task", "Unnamed Task"), 
                        value=current_is_completed, 
                        key=f"todo_cb_{i}_form"
                    )
                    task_statuses_todo[i] = new_is_completed
                with col2:
                    # Timestamp display
                    ts = task.get("timestamp")
                    if isinstance(ts, datetime.datetime):
                        st.caption(ts.strftime("%d/%m %H:%M"))
                with col3:
                    if st.button("🗑️", key=f"delete_todo_btn_{i}_form", help="Delete Task"):
                       indices_to_delete_todo.append(i) # Mark for deletion outside form submission logic

            submitted_update_todos = st.form_submit_button("Update Manual Tasks Statuses")

        # Handle deletions immediately if button clicked (outside form logic for direct action)
        if indices_to_delete_todo:
            indices_to_delete_todo.sort(reverse=True)
            original_todo_list_copy = copy.deepcopy(app_data_todo['todo_data'])
            num_deleted = 0
            for index in indices_to_delete_todo:
                if 0 <= index < len(app_data_todo['todo_data']):
                    del app_data_todo['todo_data'][index]
                    num_deleted += 1
            if num_deleted > 0:
                if save_data_to_jsonbin(app_data_todo):
                    st.success(f"{num_deleted} Task(s) deleted.")
                    st.rerun()
                else:
                    st.error("Failed to save deletions online. Reverting.")
                    app_data_todo['todo_data'] = original_todo_list_copy
                    st.rerun()
        
        # Handle status updates from form submission
        if submitted_update_todos:
            original_todo_list_copy = copy.deepcopy(app_data_todo['todo_data'])
            changed_todo_status = False
            for i, new_is_completed in task_statuses_todo.items():
                task_to_update = app_data_todo['todo_data'][i]
                current_status_str = task_to_update.get("status", "Pending")
                target_status_str = "Completed" if new_is_completed else "Pending"
                if current_status_str != target_status_str:
                    task_to_update["status"] = target_status_str
                    changed_todo_status = True
            
            if changed_todo_status:
                if save_data_to_jsonbin(app_data_todo):
                    st.success("Manual task statuses updated.")
                    st.rerun()
                else:
                    st.error("Failed to update manual task statuses. Reverting.")
                    app_data_todo['todo_data'] = original_todo_list_copy
                    st.rerun()
            else:
                st.info("No changes in manual task statuses.")
    else:
        st.info("No manual tasks added yet.")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # Today's Revision Reminders (as Tasks) - Refactored
    st.subheader("Today's Revision Reminders (as Tasks)")
    revision_tasks_for_today = get_revisions_for_date(datetime.date.today())
    display_revision_entries_list(revision_tasks_for_today, "todo_rev_list")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # Today's To-Do Overview
    st.subheader("Today's To-Do Overview")
    total_manual = len(todo_list)
    completed_manual = sum(1 for t in todo_list if t.get("status") == "Completed")
    total_rev_tasks = len(revision_tasks_for_today)
    completed_rev_tasks = sum(1 for _,_,_,_,rem in revision_tasks_for_today if rem.get("status") == "Revised")
    
    total_overall_tasks = total_manual + total_rev_tasks
    completed_overall_tasks = completed_manual + completed_rev_tasks
    pending_overall_tasks = total_overall_tasks - completed_overall_tasks

    if total_overall_tasks > 0:
        df_overview = pd.DataFrame({
            "Status": ["Completed", "Pending"], "Count": [completed_overall_tasks, pending_overall_tasks]
        })
        df_overview['Status'] = pd.Categorical(df_overview['Status'], categories=["Completed", "Pending"], ordered=True)
        fig_overview = px.pie(df_overview, names="Status", values="Count", title="Today's Task Status",
                              color="Status", color_discrete_map={"Completed": COLOR_SUCCESS, "Pending": COLOR_WARNING})
        fig_overview.update_traces(textposition='inside', textinfo='percent+value')
        st.plotly_chart(fig_overview, use_container_width=True)
    else:
        st.info("No tasks for today to generate overview.")

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
# Consider adding a small footer or app version if needed
# st.caption("NEET Prep Tracker v1.1")
