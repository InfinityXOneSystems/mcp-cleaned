import os
from datetime import timedelta

# Scheduling
TEST_INTERVAL_HOURS = int(os.getenv("TEST_INTERVAL_HOURS", "4"))

# External references
GOOGLE_DRIVE_TEST_FOLDER_URL = "https://drive.google.com/drive/u/0/folders/1W1rXnEfHD6wU66tLfqZWYyYtqBQ42Wwf"
OMNI_TEST_SHEET_URL = "https://docs.google.com/spreadsheets/d/1OMaHQpa1Mz7qxc4CjNVED3SOn_JxBGoRdZNQE71R-OE/edit?gid=0#gid=0"

# Records base path
BASE_RECORDS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "records"))

# Subsystem list
SUBSYSTEMS = [
    "vscode",
    "github",
    "hostinger",
    "orchestrator",
    "crawler",
    "docker",
    "google",
    "intelligence",
    "unified_endpoints",
    "chatgpt_auto_builder",
]
