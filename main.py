import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import random
import json
import requests
import copy

# --- Load App Passcode ---
APP_PASSCODE = None
PASSCODE_LOADED = False
try:
    APP_PASSCODE = st.secrets["app"]["passcode"]
    if APP_PASSCODE and APP_PASSCODE != "YOUR_CHOSEN_STRONG_PASSCODE": # Basic validation
        PASSCODE_LOADED = True
    else:
        st.error("App passcode is missing or using placeholder in secrets.")
except KeyError:
    st.error("Missing 'passcode' under '[app]' section in Streamlit secrets.")
except Exception as e:
     st.error(f"Error loading app passcode: {e}")

# ---------------- JSONBin.io Configuration & Secrets Loading ----------------
# (Keep this section as it was, loading JSONBIN_API_KEY and JSONBIN_BIN_ID)
SECRETS_LOADED = False
JSONBIN_API_KEY = None
JSONBIN_BIN_ID = None

try:
    # Attempt to load secrets using Streamlit's built-in method
    JSONBIN_API_KEY = st.secrets["jsonbin"]["api_key"]
    JSONBIN_BIN_ID = st.secrets["jsonbin"]["bin_id"]
    SECRETS_LOADED = True
    # Basic validation
    if not JSONBIN_API_KEY or JSONBIN_API_KEY == "YOUR_NEW_SECURE_X_MASTER_KEY":
         st.error("❌ JSONBin API Key is missing or using placeholder in secrets.")
         SECRETS_LOADED = False
    if not JSONBIN_BIN_ID or JSONBIN_BIN_ID == "YOUR_JSONBIN_BIN_ID":
        st.error("❌ JSONBin Bin ID is missing or using placeholder in secrets.")
        SECRETS_LOADED = False

except KeyError as e:
    st.error(f"❌ Secrets Configuration Error: Missing key {e}.")
    st.info("Ensure '[jsonbin]' section with 'api_key' and 'bin_id' exists in Streamlit secrets.")
except Exception as e:
    st.error(f"❌ An unexpected error occurred loading secrets: {e}")

# Only proceed with JSONBin loading if app passcode is potentially available
# The actual API calls will fail later if JSONBin secrets are wrong
# if not SECRETS_LOADED: # Commenting this out, let the app try to load passcode first
#     st.warning("JSONBin Secrets not loaded correctly. Online data features might fail.")


# --- API Constants ---
JSONBIN_BASE_URL = "https://api.jsonbin.io/v3/b"
REQUEST_TIMEOUT = 15 # Seconds for API request timeout

# ---------------- Set Page Config (MUST be the first Streamlit command) ----------------
st.set_page_config(
    page_title="NEET Exam Prep - Subject-wise Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Password Protection Logic ----------------

def check_password():
    """Returns `True` if the user had entered the correct password."""
    if not PASSCODE_LOADED:
        st.error("App passcode not configured correctly. Cannot verify.")
        return False # Cannot proceed without a configured passcode

    # Check if password already entered successfully in this session
    if st.session_state.get("password_correct", False):
        return True

    # Show input form
    st.title("🔒 Enter Passcode")
    st.write("Please enter the passcode to access the application.")
    password_attempt = st.text_input("Passcode", type="password", key="password_attempt_input")

    if st.button("Login", key="password_submit_button"):
        if password_attempt == APP_PASSCODE:
            st.session_state["password_correct"] = True
            # Clear the input field by rerunning (optional but good UX)
            st.rerun()
        else:
            st.error("😕 Incorrect passcode. Please try again.")
            st.session_state["password_correct"] = False

    return False # Return False if login button not clicked or password incorrect

# --- Main App Execution ---

# Initialize password status if not already done
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

# Check password before proceeding
if not check_password():
    st.stop() # Stop execution if password check fails or form is shown

# --- If password is correct, proceed with the rest of the app ---
st.success("✅ Access Granted") # Optional feedback

# --- The rest of your original code starts here ---

# ---------------- Base Custom CSS (Keep as is) ----------------
base_css = """
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"]  {
        font-family: 'Roboto', sans-serif;
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
        box-shadow: 0px 2px 4px rgba(0,0,0,0.2);
        font-size: 14px;
    }
</style>
"""
st.markdown(base_css, unsafe_allow_html=True)

# ---------------- Theme CSS Function (Keep as is) ----------------
def apply_theme_css():
    # ... (rest of the theme CSS function remains the same)
    theme = st.session_state.get("app_theme", "Light Mode")
    if theme == "Dark Mode":
        css = """
        <style>
            body, .stApp { background-color: #222; color: #ddd; }
            .sidebar .sidebar-content { background-color: #333; }
            .stButton>button { background-color: #555; color: #fff; }
            .stProgress>div>div { background-color: #888; }
            .dataframe-container { background: #333; border: 1px solid #555;} /* Dark mode adjustment */
            .container-box { background: #444; border: 1px solid #666;} /* Dark mode adjustment */
        </style>
        """
    elif theme == "Colorful Mode":
        css = """
        <style>
            body, .stApp { background-color: #e0f7fa; color: #212529; }
            .sidebar .sidebar-content { background-color: #b2ebf2; }
            .stButton>button { background-color: #ff4081; color: #fff; }
            .stProgress>div>div { background-color: #ff4081; }
            .dataframe-container { background: #ffffff; } /* Ensure contrast */
            .container-box { background: #f0f8ff; border: 1px solid #b2ebf2;} /* Colorful mode adjustment */
        </style>
        """
    else:  # Light Mode
        css = """
        <style>
            body, .stApp { background-color: #F8F9FA; color: #212529; }
            .sidebar .sidebar-content { background-color: #f0f2f6; }
            .stButton>button { background-color: #007BFF; color: #fff; }
            .stProgress>div>div { background-color: #66B2FF; }
             /* Default styles are mostly fine for light mode */
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


# ---------------- Current Date & Time in Top Right Corner (Keep as is) ----------------
current_time_str = datetime.datetime.now().strftime("%d/%m/%y %I:%M:%S %p")
st.markdown(f"""
    <div class="current-time">
        <strong>{current_time_str}</strong>
    </div>
    """, unsafe_allow_html=True)


# ---------------- JSONBin Persistence Functions ----------------
# (Keep these functions: _get_headers, _process_loaded_data, _prepare_data_for_saving,
#  load_data_from_jsonbin, save_data_to_jsonbin as they were in the previous correct version)
def _get_headers(api_key):
    """Returns the necessary headers for JSONBin API requests."""
    if not api_key or api_key == "YOUR_NEW_SECURE_X_MASTER_KEY": # Check against placeholder
        # Don't show error here if secrets are loaded, let the calling function handle None
        return None
    return {
        'Content-Type': 'application/json',
        'X-Master-Key': api_key
    }

def _process_loaded_data(data):
    """Converts ISO string dates/times back to datetime objects after loading."""
    # --- This function remains unchanged ---
    if not isinstance(data, dict): return data
    if "subject_chapters_data" in data and isinstance(data["subject_chapters_data"], dict):
        for subject, chapters in data["subject_chapters_data"].items():
            if isinstance(chapters, list):
                for chapter in chapters:
                    if isinstance(chapter, dict):
                        if "entry_datetime" in chapter and isinstance(chapter["entry_datetime"], str):
                            try: chapter["entry_datetime"] = datetime.datetime.fromisoformat(chapter["entry_datetime"])
                            except ValueError: pass
                        if "reminders" in chapter and isinstance(chapter["reminders"], list):
                            for reminder in chapter["reminders"]:
                                if isinstance(reminder, dict) and "time" in reminder and isinstance(reminder["time"], str):
                                    try: reminder["time"] = datetime.datetime.fromisoformat(reminder["time"])
                                    except ValueError: pass
    if "todo_data" in data and isinstance(data["todo_data"], list):
        for task in data["todo_data"]:
             if isinstance(task, dict) and "timestamp" in task and isinstance(task["timestamp"], str):
                 try: task["timestamp"] = datetime.datetime.fromisoformat(task["timestamp"])
                 except ValueError: pass
    return data

def _prepare_data_for_saving(data):
    """Converts datetime objects to ISO strings before saving to JSON."""
     # --- This function remains unchanged ---
    data_copy = copy.deepcopy(data)
    if not isinstance(data_copy, dict): return data_copy
    if "subject_chapters_data" in data_copy and isinstance(data_copy["subject_chapters_data"], dict):
        for subject, chapters in data_copy["subject_chapters_data"].items():
             if isinstance(chapters, list):
                for chapter in chapters:
                    if isinstance(chapter, dict):
                        if "entry_datetime" in chapter and isinstance(chapter["entry_datetime"], datetime.datetime):
                            chapter["entry_datetime"] = chapter["entry_datetime"].isoformat()
                        if "reminders" in chapter and isinstance(chapter["reminders"], list):
                            for reminder in chapter["reminders"]:
                                if isinstance(reminder, dict) and "time" in reminder and isinstance(reminder["time"], datetime.datetime):
                                    reminder["time"] = reminder["time"].isoformat()
    if "todo_data" in data_copy and isinstance(data_copy["todo_data"], list):
        for task in data_copy["todo_data"]:
             if isinstance(task, dict) and "timestamp" in task and isinstance(task["timestamp"], datetime.datetime):
                 task["timestamp"] = task["timestamp"].isoformat()
    return data_copy

@st.cache_data(ttl=300)
def load_data_from_jsonbin(_api_key, _bin_id):
    """Loads the entire data structure from the specified JSONBin bin."""
    # --- This function remains unchanged ---
    if not SECRETS_LOADED or not _api_key or not _bin_id:
        st.warning("Cannot load data: Missing JSONBin API Key or Bin ID in secrets.")
        return None
    st.info(f"Fetching latest data from JSONBin...")
    headers = _get_headers(_api_key)
    if headers is None:
        st.error("Cannot load data: Invalid API Key.")
        return None
    url = f"{JSONBIN_BASE_URL}/{_bin_id}/latest"
    try:
        with st.spinner("Connecting to JSONBin..."):
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            raw_data = response.json().get("record")
            if not raw_data:
                 st.warning("JSONBin bin is empty. Initializing with default structure.")
                 return {"subject_chapters_data": {subject: [] for subject in SUBJECT_CHOICES}, "todo_data": []}
            elif isinstance(raw_data, dict) and "subject_chapters_data" in raw_data and "todo_data" in raw_data:
                processed_data = _process_loaded_data(raw_data)
                st.success("Data loaded and processed successfully.")
                return processed_data
            else:
                st.error("Loaded data structure from JSONBin is unexpected.")
                st.json(raw_data)
                st.warning("Using default empty structure due to unexpected format.")
                return {"subject_chapters_data": {subject: [] for subject in SUBJECT_CHOICES}, "todo_data": []}
    except requests.exceptions.Timeout:
        st.error(f"Error loading data: Request timed out after {REQUEST_TIMEOUT}s.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error loading data from JSONBin: {e}")
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                st.error(f"Error: Bin ID '{_bin_id}' not found on JSONBin.")
                st.info("Please create the bin or check the Bin ID in secrets.")
                return {"subject_chapters_data": {subject: [] for subject in SUBJECT_CHOICES}, "todo_data": []}
            elif e.response.status_code == 401:
                st.error(f"Error: Unauthorized (401). Check your API Key (X-Master-Key) in Streamlit secrets.")
            try: st.json({"error_details": e.response.json()})
            except json.JSONDecodeError: st.text(e.response.text)
        return None
    except json.JSONDecodeError:
        st.error("Error: Could not decode JSON response from JSONBin.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during loading: {e}")
        return None

def save_data_to_jsonbin(api_key, bin_id, data_to_save):
    """Saves the entire data structure (overwrites) to the specified JSONBin bin."""
    # --- This function remains unchanged ---
    if not SECRETS_LOADED or not api_key or not bin_id:
         st.error("Cannot save data: Missing JSONBin API Key or Bin ID in secrets.")
         return False
    headers = _get_headers(api_key)
    if headers is None:
        st.error("Cannot save data: Invalid API Key.")
        return False
    if data_to_save is None:
        st.warning("Attempted to save 'None' data. Aborting save.")
        return False
    prepared_data = _prepare_data_for_saving(data_to_save)
    url = f"{JSONBIN_BASE_URL}/{bin_id}"
    try:
        with st.spinner("Saving data to JSONBin..."):
            response = requests.put(url, headers=headers, json=prepared_data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        if response.status_code == 200:
             st.cache_data.clear()
             return True
        else:
            st.warning(f"Data save might have failed. Status code: {response.status_code}")
            try: st.json({"response": response.json()})
            except json.JSONDecodeError: st.text(response.text)
            return False
    except requests.exceptions.Timeout:
        st.error(f"Error saving data: Request timed out after {REQUEST_TIMEOUT}s.")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Error saving data to JSONBin: {e}")
        if hasattr(e, 'response') and e.response is not None:
             if e.response.status_code == 401:
                 st.error(f"Error: Unauthorized (401). Check your API Key (X-Master-Key) in Streamlit secrets.")
             try: st.json({"error_details": e.response.json()})
             except json.JSONDecodeError: st.text(e.response.text)
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during saving: {e}")
        return False

# ---------------- Session State Initialization ----------------
SUBJECT_CHOICES = ["Botany", "Zoology", "Physics", "Chemistry"]
THEME_OPTIONS = ["Light Mode", "Dark Mode", "Colorful Mode"]
DEFAULT_APP_DATA = {
    "subject_chapters_data": {subject: [] for subject in SUBJECT_CHOICES},
    "todo_data": []
}

# Initialize main data structure *only if password is correct*
# This is moved down slightly to happen after password check passes
if 'app_data' not in st.session_state:
    if SECRETS_LOADED: # Check if JSONBin secrets are loaded
        st.session_state['app_data'] = load_data_from_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID)
        if st.session_state['app_data'] is None:
            st.error("CRITICAL: Failed to load data after login. Using temporary empty structure.")
            st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)
    else:
        st.warning("JSONBin Secrets not loaded. Using temporary empty structure. Data will not be saved online.")
        st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)

# Initialize theme (can happen even if not logged in)
if 'app_theme' not in st.session_state:
    st.session_state['app_theme'] = "Light Mode" # Default theme

# Ensure data structure integrity (run this after loading or setting default)
if not isinstance(st.session_state.get('app_data'), dict):
     st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)
if "subject_chapters_data" not in st.session_state.get('app_data', {}): # Safer check
     st.session_state['app_data']["subject_chapters_data"] = copy.deepcopy(DEFAULT_APP_DATA["subject_chapters_data"])
if "todo_data" not in st.session_state.get('app_data', {}): # Safer check
     st.session_state['app_data']["todo_data"] = copy.deepcopy(DEFAULT_APP_DATA["todo_data"])

# --- The rest of your code (Color Palette, Quotes, Helper Functions, Core Functions, UI rendering) ---
# --- remains exactly the same as in the previous version. ---
# --- It will only be executed if the password check passed. ---

# ---------------- Color Palette (Keep as is) ----------------
PRIMARY_COLOR = "#007BFF"
# ... rest of palettes

# ---------------- Motivational Quotes & Study Tips (Keep as is) ----------------
motivational_quotes = [
    "The expert in anything was once a beginner.",
    # ... rest of quotes
]
study_tips = [
    "Plan your study schedule and stick to it.",
     # ... rest of tips
]

# ---------------- Helper Functions (Keep as is) ----------------
def _create_default_reminders(entry_datetime):
    # ... (remains the same)
    return [
        {"reminder_id": 1, "type": "12 hour Reminder", "time": entry_datetime + datetime.timedelta(hours=12), "status": "Pending"},
        {"reminder_id": 2, "type": "3 days Reminder", "time": entry_datetime + datetime.timedelta(days=3), "status": "Pending"},
        {"reminder_id": 3, "type": "5 days Reminder", "time": entry_datetime + datetime.timedelta(days=5), "status": "Pending"},
    ]

def _prepare_csv_data(subject_data):
    # ... (remains the same)
    all_data = []
    if not isinstance(subject_data, dict):
        return pd.DataFrame(all_data).to_csv(index=False).encode('utf-8')
    # ... (rest of function) ...
    return pd.DataFrame(all_data).to_csv(index=False).encode('utf-8')


def _aggregate_productivity_data(subject_data, start_date=None):
    # ... (remains the same)
    aggregated = {}
    if not isinstance(subject_data, dict): return aggregated
    # ... (rest of function) ...
    return aggregated

# ---------------- Core Functions (Keep as is) ----------------
def add_chapter_and_reminders(subject, chapter_name, entry_datetime, custom_reminders=None):
    # ... (remains the same)
    subject_chapters = st.session_state['app_data']['subject_chapters_data']
    # ... (rest of function) ...

def delete_chapter(subject, chapter_index):
    # ... (remains the same)
    subject_chapters = st.session_state['app_data']['subject_chapters_data']
    # ... (rest of function) ...

def mark_reminder_revised(subject, chapter_index, reminder_index):
    # ... (remains the same)
    subject_chapters = st.session_state['app_data']['subject_chapters_data']
    # ... (rest of function) ...

def mark_reminder_pending(subject, chapter_index, reminder_index):
    # ... (remains the same)
    subject_chapters = st.session_state['app_data']['subject_chapters_data']
    # ... (rest of function) ...

def calculate_subject_progress(subject):
     # ... (remains the same)
    subject_chapters_data = st.session_state['app_data'].get('subject_chapters_data', {})
     # ... (rest of function) ...

def display_reminders_section(subject, chapter, chapter_index):
    # ... (remains the same)
    rem_list = []
    # ... (rest of function) ...

def display_time_spent_section(subject, chapter, chapter_index):
    # ... (remains the same)
    key = f"time_spent_{subject}_{chapter_index}"
    # ... (rest of function) ...

def display_exam_tracking_section(subject, chapter, chapter_index):
    # ... (remains the same)
    st.subheader(f"Exam Tracking")
    # ... (rest of function) ...

def _get_chapter_item(subject_chapters_list, chapter_name):
    # ... (remains the same)
    if not isinstance(subject_chapters_list, list): return None, -1
    # ... (rest of function) ...

def display_subject_tab_content(subject):
    # ... (remains the same)
    subject_chapters_data = st.session_state['app_data'].get('subject_chapters_data', {})
    # ... (rest of function) ...

def download_csv_data():
     # ... (remains the same)
    subject_chapters = st.session_state['app_data'].get('subject_chapters_data', {})
    return _prepare_csv_data(subject_chapters)

# ---------------- Productivity Tracking (Keep as is) ----------------
def display_productivity_tracking():
     # ... (remains the same)
    st.header("Productivity Tracking")
    # ... (rest of function) ...

# ---------------- Sidebar (Keep as is) ----------------
# This will only appear AFTER successful login
with st.sidebar:
    st.title("📚 NEET Prep App")
    # ... (rest of sidebar code remains the same) ...
    with st.expander("App Theme", expanded=False):
        selected_theme = st.selectbox("Choose Theme:", THEME_OPTIONS, index=THEME_OPTIONS.index(st.session_state.get('app_theme', "Light Mode")))
        if selected_theme != st.session_state.get('app_theme'):
            st.session_state['app_theme'] = selected_theme
            st.rerun()

    with st.expander("Add New Chapter", expanded=True):
         # ... (add chapter code) ...
         pass # Placeholder for brevity

    with st.expander("Data Options", expanded=False):
         # ... (download code) ...
         pass # Placeholder for brevity

    st.header("Motivation")
    st.markdown(f"> *{random.choice(motivational_quotes)}*")
    st.header("Study Tips")
    with st.expander("See Study Tips"):
        for tip in study_tips:
            st.markdown(f"- {tip}")

# ---------------- Apply Theme CSS ----------------
apply_theme_css() # Apply theme regardless of login state, or move inside check? Better outside.

# ---------------- Main Panel & Tabs (Keep as is) ----------------
# This will only appear AFTER successful login
st.markdown("<div class='main-header'><h1>NEET Prep Tracker Dashboard</h1></div>", unsafe_allow_html=True)
tabs = st.tabs(SUBJECT_CHOICES + ["Today's Revisions", "Productivity Tracking", "To Do List"])

# ----- Subject Tabs -----
for idx, subject in enumerate(SUBJECT_CHOICES):
    with tabs[idx]:
        # ... (subject tab code remains the same) ...
         st.header(subject)
         st.markdown(f"<div style='background-color:{TAB_HIGHLIGHT_COLOR}; padding: 15px; border-radius: 8px; border: 1px solid #ccc;'>", unsafe_allow_html=True)
         display_subject_tab_content(subject)
         st.markdown("</div>", unsafe_allow_html=True)


# ----- Today's Revisions Tab -----
with tabs[len(SUBJECT_CHOICES)]:
    # ... (today's revisions code remains the same) ...
    st.header("Today's Revisions")
    # ... (rest of tab code) ...

# ----- Productivity Tracking Tab -----
with tabs[len(SUBJECT_CHOICES) + 1]:
    # ... (productivity tracking code remains the same) ...
    display_productivity_tracking()

# ----- To Do List Tab -----
with tabs[-1]:
    # ... (to do list code remains the same) ...
    st.header("To Do List")
    # ... (rest of tab code) ...


st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
# End of script
