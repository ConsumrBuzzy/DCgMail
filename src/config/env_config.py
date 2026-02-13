"""
Environment-based configuration provider for DCGMail.

Uses Pydantic Settings for type-safe configuration management.
Based on Telesero_DNC_Automation/config/settings.py pattern.
"""

import os
from functools import lru_cache
from typing import Optional
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.interfaces import ConfigProvider, ConfigError


class DCGMailSettings(BaseSettings):
    """Application configuration loaded from environment variables/.env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Gmail API Configuration
    gmail_auth_type: str = Field(
        default="service_account",
        env="GMAIL_AUTH_TYPE",
        description="Authentication type: 'service_account' or 'oauth2'"
    )
    gmail_service_account: str = Field(
        default="./credentials/service_account.json",
        env="GMAIL_SERVICE_ACCOUNT",
        description="Path to service account JSON (for service_account auth)"
    )
    gmail_oauth_client: str = Field(
        default="./credentials/oauth_client.json",
        env="GMAIL_OAUTH_CLIENT",
        description="Path to OAuth2 client JSON (for oauth2 auth)"
    )
    gmail_oauth_token: str = Field(
        default="./credentials/token.json",
        env="GMAIL_OAUTH_TOKEN",
        description="Path to OAuth2 token storage (auto-generated)"
    )
    work_email: str = Field(
        default="",
        env="WORK_EMAIL",
        description="Work email address (for service_account auth)"
    )

    # Telegram Configuration
    telegram_bot_token: str = Field(
        default="",
        env="TELEGRAM_BOT_TOKEN",
    )
    telegram_chat_id: str = Field(
        default="",
        env="TELEGRAM_CHAT_ID",
    )
    telegram_simple_mode: str = Field(
        default="true",
        env="TELEGRAM_SIMPLE_MODE",
    )

    # Categorization Configuration
    categorization_config: str = Field(
        default="./config/categories.json",
        env="CATEGORIZATION_CONFIG",
    )

    # Application Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
    )
    max_emails: int = Field(
        default=50,
        env="MAX_EMAILS",
    )
    dry_run: bool = Field(
        default=False,
        env="DRY_RUN",
    )

    @field_validator("gmail_service_account")
    @classmethod
    def validate_service_account_path(cls, value: str) -> str:
        """Validate that service account file exists if not using env var."""
        # If it's set via GOOGLE_APPLICATION_CREDENTIALS, that takes precedence
        env_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if env_creds:
            return env_creds

        # Otherwise check the provided path
        if value and not Path(value).exists():
            # Don't fail here - let the provider handle missing credentials
            pass
        return value

    @field_validator("dry_run", mode="before")
    @classmethod
    def parse_dry_run(cls, value) -> bool:
        """Parse dry_run from string to bool."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return False


@lru_cache()
def get_settings() -> DCGMailSettings:
    """Return cached instance of settings."""
    return DCGMailSettings()


class EnvConfigProvider(ConfigProvider):
    """
    Environment-based configuration provider using Pydantic.

    Implements the ConfigProvider interface from src/interfaces.py.
    """

    def __init__(self):
        """Initialize config provider with Pydantic settings."""
        self.settings = get_settings()

    def get(self, key: str, default: str = None) -> str:
        """
        Get a configuration value.

        Args:
            key: Configuration key (case-insensitive, uses snake_case)
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        # Convert to snake_case for Pydantic compatibility
        key_snake = key.lower().replace("-", "_")

        value = getattr(self.settings, key_snake, None)

        # Convert to string for interface compatibility
        if value is None:
            return default

        return str(value)

    def get_required(self, key: str) -> str:
        """
        Get a required configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            ConfigError if key not found or empty
        """
        value = self.get(key)

        if not value or value == "None":
            raise ConfigError(
                f"Required configuration missing: {key}. "
                f"Please set {key.upper()} in your .env file."
            )

        return value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value."""
        value = self.get(key, str(default))
        return value.lower() in ("true", "1", "yes")

    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value."""
        value = self.get(key, str(default))
        try:
            return int(value)
        except ValueError:
            return default
