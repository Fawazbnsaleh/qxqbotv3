"""
Telethon Configuration
"""
import os
from dotenv import load_dotenv
load_dotenv()

# API Credentials - MUST be set via environment variables!
_api_id = os.getenv("TELETHON_API_ID")
_api_hash = os.getenv("TELETHON_API_HASH")
_phone = os.getenv("TELETHON_PHONE")

if not _api_id or not _api_hash or not _phone:
    raise ValueError(
        "Missing required Telethon credentials! "
        "Set TELETHON_API_ID, TELETHON_API_HASH, and TELETHON_PHONE environment variables."
    )

API_ID = int(_api_id)
API_HASH = _api_hash
PHONE = _phone

# Session file path
SESSION_FILE = os.path.join(os.path.dirname(__file__), "session")

# Reports directory
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "live_reports")
