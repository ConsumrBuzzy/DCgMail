"""
config/credentials.py - Safe credential loading

Loads secrets from environment variables (.env file).
Never hardcodes credentials.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file at startup
load_dotenv()


class CredentialsManager:
    """Manage credentials safely from environment or files."""
    
    @staticmethod
    def load_service_account():
        """
        Load Gmail service account credentials from file.
        
        Returns:
            dict: Service account JSON object
            
        Raises:
            FileNotFoundError: If service account file doesn't exist
            ValueError: If GMAIL_SERVICE_ACCOUNT env var not set
        """
        cred_path = os.getenv("GMAIL_SERVICE_ACCOUNT")
        if not cred_path:
            raise ValueError(
                "GMAIL_SERVICE_ACCOUNT environment variable not set. "
                "See .env.example and copy to .env"
            )
        
        cred_path = Path(cred_path)
        if not cred_path.exists():
            raise FileNotFoundError(
                f"Service account file not found: {cred_path}. "
                "Download from Google Cloud Console."
            )
        
        with open(cred_path) as f:
            return json.load(f)
    
    @staticmethod
    def get_telegram_token():
        """
        Get Telegram bot token from environment.
        
        Returns:
            str: Telegram bot token
            
        Raises:
            ValueError: If TELEGRAM_BOT_TOKEN not set
        """
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN environment variable not set. "
                "Get token from @BotFather on Telegram."
            )
        return token
    
    @staticmethod
    def get_work_email():
        """Get work email address from environment."""
        email = os.getenv("WORK_EMAIL")
        if not email:
            raise ValueError(
                "WORK_EMAIL environment variable not set. "
                "See .env.example"
            )
        return email
    
    @staticmethod
    def get_telegram_chat_id():
        """Get Telegram chat ID (optional, for debugging)."""
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id:
            return None
        try:
            return int(chat_id)
        except ValueError:
            raise ValueError(
                "TELEGRAM_CHAT_ID must be numeric. "
                "Get from @userinfobot on Telegram."
            )
    
    @staticmethod
    def validate_all():
        """
        Validate all required credentials at startup.
        
        Raises:
            ValueError: If any required credential is missing
        """
        required = [
            ("GMAIL_SERVICE_ACCOUNT", CredentialsManager.load_service_account),
            ("TELEGRAM_BOT_TOKEN", CredentialsManager.get_telegram_token),
            ("WORK_EMAIL", CredentialsManager.get_work_email),
        ]
        
        errors = []
        for name, getter in required:
            try:
                getter()
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
        
        if errors:
            raise ValueError(
                "Credential validation failed:\n" + "\n".join(errors)
            )
