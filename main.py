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
        # Avoid showing error if placeholder is used, check PASSCODE_LOADED later
        if APP_PASSCODE == "YOUR_CHOSEN_STRONG_PASSCODE":
            st.error("App passcode is using placeholder value in secrets.")
        else:
            st.error("App passcode is missing in secrets.")
except KeyError:
    st.error("Missing 'passcode' under '[app]' section in Streamlit secrets.")
except Exception as e:
     st.error(f"Error loading app passcode: {e}")

# ---------------- JSONBin.io Configuration & Secrets Loading ----------------
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
         # st.error("❌ JSONBin API Key is missing or using placeholder in secrets.") # Error shown by _get_headers if needed
         SECRETS_LOADED = False
    if not JSONBIN_BIN_ID or JSONBIN_BIN_ID == "YOUR_JSONBIN_BIN_ID":
        # st.error("❌ JSONBin Bin ID is missing or using placeholder in secrets.") # Error shown later if needed
        SECRETS_LOADED = False

except KeyError as e:
    st.error(f"❌ Secrets Configuration Error: Missing key {e} in '[jsonbin]' section.")
except Exception as e:
    st.error(f"❌ An unexpected error occurred loading JSONBin secrets: {e}")

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
        st.error("App passcode not configured correctly by administrator. Cannot verify.")
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
            # Clear the input field by rerunning
            st.rerun()
        else:
            st.error("😕 Incorrect passcode. Please try again.")
            st.session_state["password_correct"] = False
            # Optionally clear the input field after failed attempt
            # st.session_state.password_attempt_input = ""

    return False # Return False if login button not clicked or password incorrect

# --- Main App Execution ---

# Initialize password status if not already done
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

# Check password before proceeding
if not check_password():
    st.stop() # Stop execution if password check fails or form is shown

# --- If password is correct, proceed with the rest of the app ---
# Optionally hide the success message after a short delay or keep it simple
# st.success("✅ Access Granted")

# Check if JSONBin secrets were loaded correctly *after* password check passes
if not SECRETS_LOADED:
    st.warning("JSONBin Secrets not loaded correctly. Online data saving/loading will fail.")
    # Decide if the app should stop completely if JSONBin secrets are essential
    # st.stop()

# ---------------- Base Custom CSS ----------------
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

# ---------------- Theme CSS Function ----------------
def apply_theme_css():
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


# ---------------- Current Date & Time in Top Right Corner ----------------
current_time_str = datetime.datetime.now().strftime("%d/%m/%y %I:%M:%S %p")
st.markdown(f"""
    <div class="current-time">
        <strong>{current_time_str}</strong>
    </div>
    """, unsafe_allow_html=True)


# ---------------- JSONBin Persistence Functions ----------------

def _get_headers(api_key):
    """Returns the necessary headers for JSONBin API requests."""
    # This check assumes SECRETS_LOADED applies to JSONBin secrets specifically
    if not SECRETS_LOADED or not api_key or api_key == "YOUR_NEW_SECURE_X_MASTER_KEY":
        return None # Let calling function handle None and show error if needed
    return {
        'Content-Type': 'application/json',
        'X-Master-Key': api_key
    }

def _process_loaded_data(data):
    """Converts ISO string dates/times back to datetime objects after loading."""
    if not isinstance(data, dict):
        return data # Return as is if not a dictionary

    # Process subject chapters
    if "subject_chapters_data" in data and isinstance(data["subject_chapters_data"], dict):
        for subject, chapters in data["subject_chapters_data"].items():
            if isinstance(chapters, list):
                for chapter in chapters:
                    if isinstance(chapter, dict):
                        # Convert entry_datetime
                        if "entry_datetime" in chapter and isinstance(chapter["entry_datetime"], str):
                            try:
                                chapter["entry_datetime"] = datetime.datetime.fromisoformat(chapter["entry_datetime"])
                            except ValueError:
                                pass # Keep original string if invalid format
                        # Convert reminder times
                        if "reminders" in chapter and isinstance(chapter["reminders"], list):
                            for reminder in chapter["reminders"]:
                                if isinstance(reminder, dict) and "time" in reminder and isinstance(reminder["time"], str):
                                    try:
                                        reminder["time"] = datetime.datetime.fromisoformat(reminder["time"])
                                    except ValueError:
                                        pass # Keep original string if invalid format
    # Process todo list
    if "todo_data" in data and isinstance(data["todo_data"], list):
        for task in data["todo_data"]:
             if isinstance(task, dict) and "timestamp" in task and isinstance(task["timestamp"], str):
                 try:
                     task["timestamp"] = datetime.datetime.fromisoformat(task["timestamp"])
                 except ValueError:
                     pass # Keep original string if invalid format

    return data

def _prepare_data_for_saving(data):
    """Converts datetime objects to ISO strings before saving to JSON."""
    # Create a deep copy to avoid modifying the original session state object directly
    data_copy = copy.deepcopy(data)

    if not isinstance(data_copy, dict):
        return data_copy # Return as is if not a dictionary

    # Process subject chapters
    if "subject_chapters_data" in data_copy and isinstance(data_copy["subject_chapters_data"], dict):
        for subject, chapters in data_copy["subject_chapters_data"].items():
             if isinstance(chapters, list):
                for chapter in chapters:
                    if isinstance(chapter, dict):
                        # Convert entry_datetime
                        if "entry_datetime" in chapter and isinstance(chapter["entry_datetime"], datetime.datetime):
                            chapter["entry_datetime"] = chapter["entry_datetime"].isoformat()
                        # Convert reminder times
                        if "reminders" in chapter and isinstance(chapter["reminders"], list):
                            for reminder in chapter["reminders"]:
                                if isinstance(reminder, dict) and "time" in reminder and isinstance(reminder["time"], datetime.datetime):
                                    reminder["time"] = reminder["time"].isoformat()
    # Process todo list
    if "todo_data" in data_copy and isinstance(data_copy["todo_data"], list):
        for task in data_copy["todo_data"]:
             if isinstance(task, dict) and "timestamp" in task and isinstance(task["timestamp"], datetime.datetime):
                 task["timestamp"] = task["timestamp"].isoformat()

    return data_copy

@st.cache_data(ttl=300) # Cache data for 5 minutes (300 seconds)
def load_data_from_jsonbin(_api_key, _bin_id):
    """Loads the entire data structure from the specified JSONBin bin."""
    if not SECRETS_LOADED or not _api_key or not _bin_id:
        st.warning("Cannot load data: JSONBin secrets configuration issue.")
        return None # Return None to indicate failure

    st.info(f"Fetching latest data from JSONBin...")
    headers = _get_headers(_api_key)
    if headers is None:
        st.error("Cannot load data: Invalid API Key.")
        return None

    url = f"{JSONBIN_BASE_URL}/{_bin_id}/latest"
    try:
        with st.spinner("Connecting to JSONBin..."):
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status() # Raise HTTPError for bad responses

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
    if not SECRETS_LOADED or not api_key or not bin_id:
         st.error("Cannot save data: JSONBin secrets configuration issue.")
         return False # Indicate failure

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
            response.raise_for_status() # Raise HTTPError for bad responses

        if response.status_code == 200:
             st.cache_data.clear() # IMPORTANT: Clear cache after successful save
             return True # Indicate success
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
        return False # Indicate failure
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
if 'app_data' not in st.session_state:
    if SECRETS_LOADED: # Check if JSONBin secrets are loaded
        st.session_state['app_data'] = load_data_from_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID)
        if st.session_state['app_data'] is None:
            st.error("CRITICAL: Failed to load data after login. Using temporary empty structure.")
            st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)
    else:
        # Warning about JSONBin secrets not loaded was already shown if applicable
        st.warning("Using temporary empty structure as JSONBin secrets are not fully loaded. Data will not persist online.")
        st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)


# Initialize theme
if 'app_theme' not in st.session_state:
    st.session_state['app_theme'] = "Light Mode" # Default theme

# Ensure data structure integrity (run this after loading or setting default)
if not isinstance(st.session_state.get('app_data'), dict):
     st.session_state['app_data'] = copy.deepcopy(DEFAULT_APP_DATA)
if "subject_chapters_data" not in st.session_state.get('app_data', {}): # Safer check
     st.session_state['app_data']["subject_chapters_data"] = copy.deepcopy(DEFAULT_APP_DATA["subject_chapters_data"])
if "todo_data" not in st.session_state.get('app_data', {}): # Safer check
     st.session_state['app_data']["todo_data"] = copy.deepcopy(DEFAULT_APP_DATA["todo_data"])


# ---------------- Color Palette ----------------
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
def _create_default_reminders(entry_datetime):
    return [
        {"reminder_id": 1, "type": "12 hour Reminder", "time": entry_datetime + datetime.timedelta(hours=12), "status": "Pending"},
        {"reminder_id": 2, "type": "3 days Reminder", "time": entry_datetime + datetime.timedelta(days=3), "status": "Pending"},
        {"reminder_id": 3, "type": "5 days Reminder", "time": entry_datetime + datetime.timedelta(days=5), "status": "Pending"},
    ]


def _prepare_csv_data(subject_data): # Accepts subject_chapters_data part
    all_data = []
    if not isinstance(subject_data, dict):
        return pd.DataFrame(all_data).to_csv(index=False).encode('utf-8')

    for subject, chapters in subject_data.items():
        if isinstance(chapters, list):
            for chapter in chapters:
                if isinstance(chapter, dict):
                    reminders = chapter.get('reminders', [])
                    if not isinstance(reminders, list): reminders = []
                    for reminder in reminders:
                         if isinstance(reminder, dict):
                            all_data.append({
                                "Subject": subject,
                                "Chapter Name": chapter.get('chapter_name', 'N/A'),
                                "Entry Date": chapter.get('entry_datetime', 'N/A').strftime("%d/%m/%y %I:%M %p") if isinstance(chapter.get('entry_datetime'), datetime.datetime) else chapter.get('entry_datetime', 'N/A'),
                                "Reminder Time": reminder.get('time', 'N/A').strftime("%d/%m/%y %I:%M %p") if isinstance(reminder.get('time'), datetime.datetime) else reminder.get('time', 'N/A'),
                                "Status": reminder.get('status', 'N/A'),
                                "Exams Appeared": chapter.get('exams_appeared', 0),
                                "Exam Status": chapter.get('exam_status', 'Not Appeared'),
                                "Time Spent (minutes)": chapter.get('time_spent', 0)
                            })
    return pd.DataFrame(all_data).to_csv(index=False).encode('utf-8')


def _aggregate_productivity_data(subject_data, start_date=None): # Accepts subject_chapters_data part
    aggregated = {}
    if not isinstance(subject_data, dict):
        return aggregated

    for chapters in subject_data.values():
         if isinstance(chapters, list):
            for chapter in chapters:
                 if isinstance(chapter, dict):
                    reminders = chapter.get("reminders", [])
                    if not isinstance(reminders, list): reminders = []
                    for reminder in reminders:
                         if isinstance(reminder, dict):
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


# ---------------- Core Functions ----------------
def add_chapter_and_reminders(subject, chapter_name, entry_datetime, custom_reminders=None):
    subject_chapters = st.session_state['app_data']['subject_chapters_data']
    reminders = custom_reminders if custom_reminders else _create_default_reminders(entry_datetime)
    subject_chapters[subject].append({
        "chapter_name": chapter_name,
        "entry_datetime": entry_datetime,
        "reminders": reminders,
        "exams_appeared": 0,
        "exam_status": "Not Appeared",
        "time_spent": 0
    })
    if save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
        st.success(f"Chapter '{chapter_name}' added to {subject} and saved online.")
    else:
        st.error("Failed to save chapter online.")
        subject_chapters[subject].pop()

def delete_chapter(subject, chapter_index):
    subject_chapters = st.session_state['app_data']['subject_chapters_data']
    if 0 <= chapter_index < len(subject_chapters[subject]):
        chapter_name = subject_chapters[subject][chapter_index].get('chapter_name', 'this chapter')
        original_chapter = copy.deepcopy(subject_chapters[subject][chapter_index]) # Backup for revert
        del subject_chapters[subject][chapter_index]
        if save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
            st.success(f"Chapter '{chapter_name}' deleted successfully!")
            st.rerun()
        else:
            st.error("Failed to save deletion online.")
            # Revert deletion
            subject_chapters[subject].insert(chapter_index, original_chapter)
            st.cache_data.clear() # Clear cache as state might be inconsistent
    else:
        st.error("Invalid chapter index for deletion.")


def mark_reminder_revised(subject, chapter_index, reminder_index):
    subject_chapters = st.session_state['app_data']['subject_chapters_data']
    try:
        current_status = subject_chapters[subject][chapter_index]['reminders'][reminder_index]['status']
        if current_status == "Revised": return # Already revised, do nothing
        subject_chapters[subject][chapter_index]['reminders'][reminder_index]['status'] = "Revised"
        if not save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
            st.error("Failed to save status update online.")
            subject_chapters[subject][chapter_index]['reminders'][reminder_index]['status'] = current_status # Revert
        else:
             st.rerun()
    except (IndexError, KeyError):
        st.error("Error updating reminder status.")


def mark_reminder_pending(subject, chapter_index, reminder_index):
    subject_chapters = st.session_state['app_data']['subject_chapters_data']
    try:
        current_status = subject_chapters[subject][chapter_index]['reminders'][reminder_index]['status']
        if current_status == "Pending": return # Already pending, do nothing
        subject_chapters[subject][chapter_index]['reminders'][reminder_index]['status'] = "Pending"
        if not save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
            st.error("Failed to save status update online.")
            subject_chapters[subject][chapter_index]['reminders'][reminder_index]['status'] = current_status # Revert
        else:
            st.rerun()
    except (IndexError, KeyError):
        st.error("Error updating reminder status.")


def calculate_subject_progress(subject):
    subject_chapters_data = st.session_state['app_data'].get('subject_chapters_data', {})
    chapters = subject_chapters_data.get(subject, [])
    if not chapters or not isinstance(chapters, list): return 0
    total = 0
    revised = 0
    for ch in chapters:
        if isinstance(ch, dict):
           reminders = ch.get("reminders", [])
           if isinstance(reminders, list):
               total += len(reminders)
               revised += sum(1 for rem in reminders if isinstance(rem, dict) and rem.get("status") == "Revised")
    return (revised / total) * 100 if total else 0


def display_reminders_section(subject, chapter, chapter_index):
    rem_list = []
    reminders = chapter.get("reminders", [])
    if not isinstance(reminders, list): reminders = []

    for i, reminder in enumerate(reminders):
         if isinstance(reminder, dict):
            key = f"rem_cb_{subject}_{chapter_index}_{i}" # Unique key
            current = reminder.get("status") == "Revised"
            new_status = st.checkbox(reminder.get("type", "Unknown Type"), value=current, key=key)
            # Handle state change directly based on checkbox interaction
            if new_status != current:
                if new_status:
                    mark_reminder_revised(subject, chapter_index, i)
                else:
                    mark_reminder_pending(subject, chapter_index, i)
            # Append data for dataframe display (reflects current state)
            rem_list.append({
                "Reminder Type": reminder.get("type", "N/A"),
                "Reminder Time": reminder.get("time", "N/A").strftime("%d/%m/%y %I:%M %p") if isinstance(reminder.get("time"), datetime.datetime) else reminder.get("time", "N/A"),
                "Status": "Revised" if reminder.get("status") == "Revised" else "Pending"
            })
    with st.container():
        st.markdown("<div class='dataframe-container'>", unsafe_allow_html=True)
        if rem_list:
            st.dataframe(pd.DataFrame(rem_list), use_container_width=True)
        else:
            st.caption("No reminders found for this chapter.")
        st.markdown("</div>", unsafe_allow_html=True)


def display_time_spent_section(subject, chapter, chapter_index):
    key = f"time_spent_{subject}_{chapter_index}"
    current_time_spent = chapter.get("time_spent", 0)
    time_spent = st.number_input("Time Spent Studying (minutes):", value=current_time_spent, min_value=0, step=5, key=key)
    if time_spent != current_time_spent:
        chapter["time_spent"] = time_spent
        if save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
             st.success("Time updated!")
        else:
             st.error("Failed to save time spent online.")
             chapter["time_spent"] = current_time_spent


def display_exam_tracking_section(subject, chapter, chapter_index):
    st.subheader(f"Exam Tracking")
    exam_count_key = f"exam_count_{subject}_{chapter_index}"
    exam_status_key = f"exam_status_{subject}_{chapter_index}"
    current_exam_appeared = chapter.get("exams_appeared", 0)
    current_exam_status = chapter.get("exam_status", "Not Appeared")

    exam_appeared = st.number_input("Exams Appeared:", min_value=0, value=current_exam_appeared, key=exam_count_key)
    exam_status_text = st.text_input("Exam Status:", value=current_exam_status, key=exam_status_key, placeholder="e.g., Score, Performance")

    if st.button("Update Exam Info", key=f"update_exam_{subject}_{chapter_index}"):
        # Only save if changes were made
        if exam_appeared != current_exam_appeared or exam_status_text != current_exam_status:
            chapter["exams_appeared"] = exam_appeared
            chapter["exam_status"] = exam_status_text
            if save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
                st.success("Exam info updated!")
                st.rerun() # Rerun to ensure display reflects saved state
            else:
                st.error("Failed to save exam info online.")
                chapter["exams_appeared"] = current_exam_appeared
                chapter["exam_status"] = current_exam_status
        else:
            st.info("No changes detected in exam info.")


def _get_chapter_item(subject_chapters_list, chapter_name):
    if not isinstance(subject_chapters_list, list): return None, -1
    for idx, chapter in enumerate(subject_chapters_list):
        if isinstance(chapter, dict) and chapter.get("chapter_name") == chapter_name:
            return chapter, idx
    return None, -1


def display_subject_tab_content(subject):
    subject_chapters_data = st.session_state['app_data'].get('subject_chapters_data', {})
    chapters_list = subject_chapters_data.get(subject, [])

    st.subheader(f"{subject} Revision Progress")
    progress = calculate_subject_progress(subject)
    st.progress(int(min(progress, 100)))
    st.write(f"Overall Revision: {progress:.2f}%")

    if not isinstance(chapters_list, list):
        st.error("Data format error for this subject.")
        return

    chapter_names = [ch.get("chapter_name", f"Unnamed Chapter {i}") for i, ch in enumerate(chapters_list) if isinstance(ch, dict)]
    if not chapter_names:
        st.info(f"No chapters in {subject}. Please add one from the sidebar.")
        return

    selected_chapter_name = st.selectbox(f"Select {subject} Chapter:", ["Select Chapter"] + chapter_names, index=0, key=f"select_{subject}")
    if selected_chapter_name != "Select Chapter":
        chapter, chapter_idx = _get_chapter_item(chapters_list, selected_chapter_name)
        if chapter and chapter_idx != -1:
            display_reminders_section(subject, chapter, chapter_idx)
            st.markdown("<br>", unsafe_allow_html=True) # Add some space
            display_time_spent_section(subject, chapter, chapter_idx)
            st.markdown("<br>", unsafe_allow_html=True)
            display_exam_tracking_section(subject, chapter, chapter_idx)
            st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
            st.markdown("### Delete Chapter", unsafe_allow_html=True)
            confirm_delete = st.checkbox("Confirm deletion", key=f"confirm_delete_{subject}_{chapter_idx}", help=f"Tick this box to enable deletion of '{selected_chapter_name}'.")
            # Disable button if checkbox is not ticked
            delete_button_disabled = not confirm_delete
            if st.button("Delete Chapter Permanently", key=f"delete_{subject}_{chapter_idx}", disabled=delete_button_disabled, type="primary"):
                delete_chapter(subject, chapter_idx) # Handles saving and rerun
        else:
             st.warning(f"Could not find details for chapter: {selected_chapter_name}")


def download_csv_data():
    subject_chapters = st.session_state['app_data'].get('subject_chapters_data', {})
    return _prepare_csv_data(subject_chapters)

# ---------------- Productivity Tracking ----------------
def display_productivity_tracking():
    st.header("Productivity Tracking")
    subject_chapters = st.session_state['app_data'].get('subject_chapters_data', {})

    period = st.selectbox("Tracking Period:", ["Last 1 Week", "Last 1 Month", "All Time"], key="prod_period")
    today = datetime.date.today()
    start_date = None
    if period == "Last 1 Week":
        start_date = today - datetime.timedelta(days=7)
    elif period == "Last 1 Month":
        start_date = today - datetime.timedelta(days=30)

    agg = _aggregate_productivity_data(subject_chapters, start_date)
    if agg:
        df = pd.DataFrame([
            {"Date": d, "Total Reminders": stats["total"], "Revised": stats["revised"],
             "Productivity (%)": (stats["revised"] / stats["total"] * 100) if stats["total"] else 0}
            for d, stats in agg.items()
        ])
        # Ensure data is sorted by date for the line chart
        df.sort_values("Date", inplace=True)
        # Format date for display after sorting
        df_display = df.copy()
        df_display["Date"] = df_display["Date"].apply(lambda d: d.strftime("%d/%m/%y"))

        fig = px.line(df_display, x="Date", y="Productivity (%)", markers=True, title="Daily Productivity Trend")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No productivity data available for the selected period.")

# ---------------- Sidebar ----------------
# This will only appear AFTER successful login
with st.sidebar:
    st.title("📚 NEET Prep App")
    with st.expander("App Theme", expanded=False):
        current_theme = st.session_state.get('app_theme', "Light Mode")
        selected_theme = st.selectbox("Choose Theme:", THEME_OPTIONS, index=THEME_OPTIONS.index(current_theme), key="theme_select")
        if selected_theme != current_theme:
            st.session_state['app_theme'] = selected_theme
            st.rerun()

    with st.expander("Add New Chapter", expanded=True):
        subject = st.selectbox("Subject:", SUBJECT_CHOICES, key="add_subj")
        chapter_name = st.text_input("Chapter Name:", placeholder="e.g., Structure of Atom", key="add_chap_name")
        entry_date = st.date_input("Entry Date:", value=datetime.date.today(), key="add_date")
        entry_time = st.time_input("Entry Time:", value=datetime.time(datetime.datetime.now().hour, datetime.datetime.now().minute), key="add_time")
        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
        st.caption("Revision Schedule (Default: 12hr, 3 day, 5 day)")
        use_12hr = st.checkbox("12 hour Reminder", value=True, key="add_cb_12hr")
        use_3day = st.checkbox("3 days Reminder", value=True, key="add_cb_3day")
        use_5day = st.checkbox("5 days Reminder", value=True, key="add_cb_5day")

        if st.button("Add Chapter", key="add_chap_btn"):
            if chapter_name and subject:
                entry_datetime = datetime.datetime.combine(entry_date, entry_time)
                custom_reminders = []
                reminder_id_counter = 1 # Simple counter for this addition
                if use_12hr:
                    custom_reminders.append({"reminder_id": reminder_id_counter, "type": "12 hour Reminder", "time": entry_datetime + datetime.timedelta(hours=12), "status": "Pending"})
                    reminder_id_counter += 1
                if use_3day:
                    custom_reminders.append({"reminder_id": reminder_id_counter, "type": "3 days Reminder", "time": entry_datetime + datetime.timedelta(days=3), "status": "Pending"})
                    reminder_id_counter += 1
                if use_5day:
                    custom_reminders.append({"reminder_id": reminder_id_counter, "type": "5 days Reminder", "time": entry_datetime + datetime.timedelta(days=5), "status": "Pending"})
                    reminder_id_counter += 1

                add_chapter_and_reminders(subject, chapter_name, entry_datetime, custom_reminders)
                st.rerun()
            else:
                st.warning("Please enter a chapter name and select a subject.")

    with st.expander("Data Options", expanded=False):
        st.header("Download Data")
        csv_data = download_csv_data()
        st.download_button(label="Download Study Data (CSV)", data=csv_data, file_name="neet_prep_data.csv", mime='text/csv', key="download_csv_btn")

    st.header("Motivation")
    st.markdown(f"> *{random.choice(motivational_quotes)}*")
    st.header("Study Tips")
    with st.expander("See Study Tips"):
        for tip in study_tips:
            st.markdown(f"- {tip}")


# ---------------- Apply Theme CSS ----------------
apply_theme_css()

# ---------------- Main Panel & Tabs ----------------
st.markdown("<div class='main-header'><h1>NEET Prep Tracker Dashboard</h1></div>", unsafe_allow_html=True)
tab_titles = SUBJECT_CHOICES + ["Today's Revisions", "Productivity Tracking", "To Do List"]
tabs = st.tabs(tab_titles)

# ----- Subject Tabs -----
for idx, subject in enumerate(SUBJECT_CHOICES):
    with tabs[idx]:
        st.header(subject)
        st.markdown(f"<div style='background-color:{TAB_HIGHLIGHT_COLOR if st.session_state.get('app_theme') != 'Dark Mode' else '#444'}; padding: 15px; border-radius: 8px; border: 1px solid #ccc;'>", unsafe_allow_html=True)
        display_subject_tab_content(subject)
        st.markdown("</div>", unsafe_allow_html=True)


# ----- Today's Revisions Tab -----
with tabs[len(SUBJECT_CHOICES)]:
    st.header("Today's Revisions")
    mode = st.radio("View Mode", ["Today", "Select Date"], index=0, horizontal=True, key="rev_view_mode")
    if mode == "Today":
        sel_date = datetime.date.today()
        st.info(f"Showing revisions for today: {sel_date.strftime('%d %b, %Y')}")
    else:
        sel_date = st.date_input("Select Date:", value=datetime.date.today(), key="rev_date_select")
        st.info(f"Showing revisions for: {sel_date.strftime('%d %b, %Y')}")

    revision_entries = []
    subject_chapters_data = st.session_state['app_data'].get('subject_chapters_data', {})

    for subj, chapters in subject_chapters_data.items():
        if isinstance(chapters, list):
            for c_idx, chapter in enumerate(chapters):
                 if isinstance(chapter, dict):
                    reminders = chapter.get("reminders", [])
                    if not isinstance(reminders, list): reminders = []
                    for r_idx, reminder in enumerate(reminders):
                         if isinstance(reminder, dict):
                            reminder_time_obj = reminder.get("time")
                            if isinstance(reminder_time_obj, datetime.datetime) and reminder_time_obj.date() == sel_date:
                                revision_entries.append((subj, c_idx, chapter, r_idx, reminder))

    st.markdown(f"**Total revisions found for {sel_date.strftime('%d %b')}: {len(revision_entries)}**")
    if revision_entries:
        status_counts = {"Revised": 0, "Pending": 0}
        for entry in revision_entries:
            status_counts[entry[4].get("status", "Pending")] += 1
        if sum(status_counts.values()) > 0:
            df_status = pd.DataFrame({"Status": list(status_counts.keys()), "Count": list(status_counts.values())})
            df_status['Status'] = pd.Categorical(df_status['Status'], categories=["Revised", "Pending"], ordered=True)
            fig = px.pie(df_status, names="Status", values="Count", title="Revision Status Breakdown",
                         color="Status", color_discrete_map={"Revised": COLOR_SUCCESS, "Pending": COLOR_WARNING})
            fig.update_traces(textinfo='percent+value')
            st.plotly_chart(fig, use_container_width=True)
        else:
             st.info("No applicable reminders found to calculate status.")

        st.markdown("---")
        for subj, c_idx, chapter, r_idx, reminder in revision_entries:
            with st.container():
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(
                        f"<div class='container-box' style='margin-bottom: 2px;'>" # Reduced margin
                        f"<strong>{subj}</strong> | {chapter.get('chapter_name','N/A')} | {reminder.get('type','N/A')} at {reminder.get('time','N/A').strftime('%I:%M %p') if isinstance(reminder.get('time'),datetime.datetime) else 'N/A'}"
                        f"</div>", unsafe_allow_html=True)
                with col2:
                    key = f"rev_cb_{subj}_{c_idx}_{r_idx}" # Checkbox key
                    current = reminder.get("status") == "Revised"
                    new_stat = st.checkbox("Done", value=current, key=key, label_visibility="collapsed") # Hide label
                    if new_stat != current:
                        if new_stat:
                            mark_reminder_revised(subj, c_idx, r_idx)
                        else:
                            mark_reminder_pending(subj, c_idx, r_idx)
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True) # Spacer
    else:
        st.info(f"No revisions scheduled for {sel_date.strftime('%d %b, %Y')}.")


# ----- Productivity Tracking Tab -----
with tabs[len(SUBJECT_CHOICES) + 1]:
    display_productivity_tracking()


# ----- To Do List Tab -----
with tabs[-1]:
    st.header("To Do List")
    st.subheader("Add New Task")
    new_task_text = st.text_input("Enter today's task:", key="new_todo_task_input", label_visibility="collapsed", placeholder="Enter new task...")
    if st.button("Add Task", key="add_task_button"):
        if new_task_text:
            new_task_entry = {
                "task": new_task_text,
                "status": "Pending",
                "timestamp": datetime.datetime.now()
            }
            st.session_state['app_data']['todo_data'].append(new_task_entry)
            if save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
                st.success("Task added!")
                st.rerun()
            else:
                 st.error("Failed to save task online.")
                 st.session_state['app_data']['todo_data'].pop()
        else:
            st.warning("Please enter a task.")
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    st.subheader("Manual Tasks")
    todo_list = st.session_state['app_data'].get('todo_data', [])
    if not isinstance(todo_list, list):
        st.error("To-Do list data is corrupted.")
        todo_list = []

    if todo_list:
        indices_to_delete = []
        # Filter tasks older than, say, 3 days to keep the list manageable? (Optional)
        # display_list = [task for task in todo_list if isinstance(task.get('timestamp'), datetime.datetime) and (datetime.datetime.now() - task['timestamp']).days < 3]
        display_list = todo_list # Show all for now

        for i, task in enumerate(display_list): # Use original index 'i' if using full list
            if isinstance(task, dict):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    key = f"todo_cb_{i}"
                    current_status = task.get("status", "Pending") == "Completed"
                    new_status_val = st.checkbox(task.get("task", "Unnamed Task"), value=current_status, key=key)
                    if new_status_val != current_status:
                        task["status"] = "Completed" if new_status_val else "Pending"
                        if not save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
                             st.error(f"Failed to update status for task: {task.get('task')}")
                             task["status"] = "Completed" if current_status else "Pending"
                        else:
                             st.rerun()

                with col2:
                    delete_key = f"delete_btn_{i}"
                    if st.button("🗑️", key=delete_key, help="Delete Task"):
                       # Find the actual index in the original list if filtering was applied
                       # For now, assuming 'i' matches the index in st.session_state['app_data']['todo_data']
                       indices_to_delete.append(i)

        if indices_to_delete:
            indices_to_delete.sort(reverse=True)
            original_todo_list = copy.deepcopy(st.session_state['app_data']['todo_data'])
            num_deleted = 0
            for index in indices_to_delete:
                if 0 <= index < len(st.session_state['app_data']['todo_data']):
                    del st.session_state['app_data']['todo_data'][index]
                    num_deleted += 1
            if num_deleted > 0:
                if save_data_to_jsonbin(JSONBIN_API_KEY, JSONBIN_BIN_ID, st.session_state['app_data']):
                     st.success(f"{num_deleted} Task(s) deleted.")
                     st.rerun()
                else:
                     st.error("Failed to save deletions online.")
                     st.session_state['app_data']['todo_data'] = original_todo_list # Revert

    else:
        st.info("No manual tasks added yet.")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.subheader("Today's Revision Reminders (as Tasks)")
    today_date_rev = datetime.date.today()
    subject_chapters_data_rev = st.session_state['app_data'].get('subject_chapters_data', {})
    rev_tasks = []
    for subj, chapters in subject_chapters_data_rev.items():
         if isinstance(chapters, list):
            for c_idx, chapter in enumerate(chapters):
                 if isinstance(chapter, dict):
                    reminders = chapter.get("reminders", [])
                    if not isinstance(reminders, list): reminders = []
                    for r_idx, reminder in enumerate(reminders):
                        if isinstance(reminder, dict):
                           reminder_time_obj = reminder.get("time")
                           if isinstance(reminder_time_obj, datetime.datetime) and reminder_time_obj.date() == today_date_rev:
                               rev_tasks.append((subj, c_idx, chapter, r_idx, reminder))

    if rev_tasks:
        for subj, c_idx, chapter, r_idx, reminder in rev_tasks:
            with st.container():
                 col1, col2 = st.columns([0.85, 0.15])
                 with col1:
                    task_text = f"Revise: {subj} - {chapter.get('chapter_name','N/A')} ({reminder.get('type','N/A')})"
                    st.markdown(f"<div class='container-box' style='margin-bottom: 2px;'>{task_text}</div>", unsafe_allow_html=True)
                 with col2:
                    key = f"todo_rev_cb_{subj}_{c_idx}_{r_idx}"
                    current_rev_status = reminder.get("status", "Pending") == "Revised"
                    new_rev_status = st.checkbox("Done", value=current_rev_status, key=key, label_visibility="collapsed")
                    if new_rev_status != current_rev_status:
                        if new_rev_status:
                            mark_reminder_revised(subj, c_idx, r_idx)
                        else:
                            mark_reminder_pending(subj, c_idx, r_idx)
                 st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True) # Spacer
    else:
        st.info("No revision reminders scheduled for today.")

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.subheader("Today's To-Do Overview")
    total_manual = len(st.session_state['app_data'].get('todo_data', []))
    completed_manual = sum(1 for t in st.session_state['app_data'].get('todo_data', []) if isinstance(t, dict) and t.get("status") == "Completed")
    total_rev = len(rev_tasks)
    completed_rev = sum(1 for entry in rev_tasks if entry[4].get("status") == "Revised")
    total_tasks = total_manual + total_rev
    completed_tasks = completed_manual + completed_rev
    pending_tasks = total_tasks - completed_tasks
    if total_tasks > 0:
        df_overview = pd.DataFrame({
            "Status": ["Completed", "Pending"],
            "Count": [completed_tasks, pending_tasks]
        })
        df_overview['Status'] = pd.Categorical(df_overview['Status'], categories=["Completed", "Pending"], ordered=True)
        fig = px.pie(df_overview, names="Status", values="Count", title="Today's Task Status",
                      color="Status", color_discrete_map={"Completed": COLOR_SUCCESS, "Pending": COLOR_WARNING}
                     )
        fig.update_traces(textposition='inside', textinfo='percent+value') # Show percentage and value
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks for today to generate overview.")

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
# End of script
