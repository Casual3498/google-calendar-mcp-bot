"""Configuration settings for the bot."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Google Calendar Settings
# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Get credentials path - support both Docker and local paths
GOOGLE_CALENDAR_CREDENTIALS_PATH_ENV = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH")
if GOOGLE_CALENDAR_CREDENTIALS_PATH_ENV and not os.path.exists(GOOGLE_CALENDAR_CREDENTIALS_PATH_ENV):
    # If env var is set but file doesn't exist (e.g. Docker path on local), use local path
    GOOGLE_CALENDAR_CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, "credentials", "google_credentials.json")
else:
    # Use env var if it exists and file is there, otherwise use default local path
    GOOGLE_CALENDAR_CREDENTIALS_PATH = GOOGLE_CALENDAR_CREDENTIALS_PATH_ENV or os.path.join(PROJECT_ROOT, "credentials", "google_credentials.json")

# MCP Server Configuration (using nspady/google-calendar-mcp)
MCP_SERVER_COMMAND = "npx"
MCP_SERVER_ARGS = ["-y", "@cocal/google-calendar-mcp"]

# Ensure GOOGLE_OAUTH_CREDENTIALS is set for MCP server
if not os.getenv("GOOGLE_OAUTH_CREDENTIALS"):
    # Set it to the credentials path if not already set
    credentials_path = os.path.join(PROJECT_ROOT, "credentials", "google_credentials.json")
    if os.path.exists(credentials_path):
        os.environ["GOOGLE_OAUTH_CREDENTIALS"] = credentials_path

# Validate required settings
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env file")
