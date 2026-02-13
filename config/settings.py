"""
config/settings.py - Non-secret application settings

These settings are safe to commit to version control.
Secrets (credentials) come from environment variables in .env
"""

# Categorizer type: "regex" or "llm" (future)
CATEGORIZER_TYPE = "regex"

# Email provider type: "gmail" or "outlook" (future)
EMAIL_PROVIDER_TYPE = "gmail"

# Default notifiers: "telegram", "email", etc.
NOTIFIERS = ["telegram"]

# Email fetching
MAX_EMAILS_PER_RUN = 50
FETCH_UNREAD_ONLY = True

# Categorization
CATEGORIES_CONFIG_PATH = "./config/categories.json"

# Telegram
TELEGRAM_POLLING_INTERVAL = 30  # seconds

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "./logs/dcgmail.log"

# Dry-run mode (fetch but don't modify or send notifications)
DRY_RUN = False
