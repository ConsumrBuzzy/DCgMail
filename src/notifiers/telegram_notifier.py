"""
Telegram notifier implementation for DCGMail.

Based on PhantomArbiter's TelegramManager pattern with simple mode support.
Implements the Notifier interface from src/interfaces.py.
"""

import requests
from typing import Optional

from src.interfaces import (
    Notifier,
    EmailCollection,
    CategorizedEmail,
    CredentialError,
    NotifierError,
    Logger,
)


def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2 format.

    MarkdownV2 requires escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for MarkdownV2
    """
    special_chars = r'_*[]()~`>#+-=|{}.!'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


class TelegramNotifier(Notifier):
    """
    Telegram bot notifier implementation.

    Uses simple requests-based approach (no async) for reliability.
    Based on PhantomArbiter's TELEGRAM_SIMPLE_MODE pattern.
    """

    def __init__(self, bot_token: str, chat_id: int, logger: Logger):
        """
        Initialize Telegram notifier.

        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Telegram chat ID for recipient
            logger: Logger instance

        Raises:
            CredentialError: If bot_token is missing
        """
        if not bot_token:
            raise CredentialError("TELEGRAM_BOT_TOKEN not provided")

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logger
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

        self.logger.info("Telegram notifier initialized (simple mode)")

    def send_summary(self, collection: EmailCollection) -> bool:
        """
        Send formatted email summary via Telegram.

        Args:
            collection: EmailCollection with categorized emails

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Build formatted message
            message = self._format_summary(collection)

            # Send via Telegram API
            success = self._send_message(message, parse_mode="HTML")

            if success:
                self.logger.info(f"Sent briefing: {collection.total_count} emails")
            else:
                self.logger.error("Failed to send summary")

            return success

        except Exception as e:
            self.logger.error(f"Failed to send summary: {e}", exception=e)
            return False

    def send_alert(self, message: str) -> bool:
        """
        Send urgent alert via Telegram.

        Args:
            message: Alert message text

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Format alert with prefix
            alert_text = f"🚨 <b>ALERT</b>: {message}"

            # Send
            success = self._send_message(alert_text, parse_mode="HTML")

            if success:
                self.logger.info("Alert sent successfully")
            else:
                self.logger.error("Failed to send alert")

            return success

        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}", exception=e)
            return False

    def _send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send message via Telegram API using requests.

        Based on PhantomArbiter's _simple_send pattern.

        Args:
            text: Message text
            parse_mode: Parse mode (HTML or MarkdownV2)

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                return True
            else:
                self.logger.error(
                    f"Telegram API error: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Telegram request failed: {e}")
            return False

    def _format_summary(self, collection: EmailCollection) -> str:
        """
        Format EmailCollection as HTML Telegram message.

        Args:
            collection: EmailCollection to format

        Returns:
            Formatted HTML message string
        """
        lines = [
            "📧 <b>Morning Briefing</b>",
            ""
        ]

        # Category emojis
        emoji_map = {
            "Work": "🔴",
            "Crypto": "📊",
            "Admin": "⚠️",
            "Newsletters": "📰",
            "Personal": "💬",
            "Noise": "🗑️",
            "Uncategorized": "❓"
        }

        # Group emails by category
        emails_by_category = {}
        for cat_email in collection.emails:
            category = cat_email.category
            if category not in emails_by_category:
                emails_by_category[category] = []
            emails_by_category[category].append(cat_email.email)

        # Add summary for each category
        for category, count in sorted(
            collection.by_category.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            emoji = emoji_map.get(category, "📌")
            lines.append(f"{emoji} <b>{category}</b>: {count} email{'s' if count != 1 else ''}")

            # List individual emails (limit to 3 per category)
            if category in emails_by_category:
                emails = emails_by_category[category][:3]
                for email in emails:
                    # Extract sender name/email
                    sender = self._format_sender(email.sender)
                    subject = self._truncate(email.subject, 50)
                    lines.append(f"  • {subject} ({sender})")

                # Show "and N more" if truncated
                if len(emails_by_category[category]) > 3:
                    remaining = len(emails_by_category[category]) - 3
                    lines.append(f"  <i>...and {remaining} more</i>")

            lines.append("")  # Empty line between categories

        # Total summary
        lines.append(f"✅ <b>Total:</b> {collection.total_count} emails processed")

        return "\n".join(lines)

    def _format_sender(self, sender: str) -> str:
        """
        Extract readable sender from email address.

        Args:
            sender: Email sender string (e.g., "John Doe <john@example.com>")

        Returns:
            Formatted sender (e.g., "john@example.com" or "John Doe")
        """
        # Extract email from "Name <email>" format
        if "<" in sender and ">" in sender:
            # Try to get name first
            name_part = sender.split("<")[0].strip().strip('"')
            email_part = sender.split("<")[1].split(">")[0].strip()

            # Use name if available, otherwise email
            return name_part if name_part else email_part
        else:
            return sender

    def _truncate(self, text: str, max_length: int) -> str:
        """
        Truncate text to max length with ellipsis.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
