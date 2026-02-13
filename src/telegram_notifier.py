"""
src/telegram_notifier.py - Telegram notification implementation.

Implements the Notifier interface from interfaces.py.
Uses the python-telegram-bot library to send formatted email
summaries and urgent alerts to a Telegram chat.
"""

from typing import Optional

import telegram

from config.credentials import CredentialsManager
from src.interfaces import (
    EmailCollection,
    Notifier,
    NotifierError,
)


class TelegramNotifier(Notifier):
    """Send email summaries and alerts via a Telegram bot."""

    def __init__(self, chat_id: Optional[int] = None):
        """
        Initialize with bot token from environment and optional chat_id.

        Args:
            chat_id: Telegram chat ID to send messages to.
                     If None, reads from TELEGRAM_CHAT_ID env var.

        Raises:
            NotifierError: If the bot token or chat ID is unavailable.
        """
        try:
            token = CredentialsManager.get_telegram_token()
            self._bot = telegram.Bot(token=token)
        except ValueError as exc:
            raise NotifierError(str(exc)) from exc

        if chat_id is not None:
            self._chat_id = chat_id
        else:
            resolved = CredentialsManager.get_telegram_chat_id()
            if resolved is None:
                raise NotifierError(
                    "TELEGRAM_CHAT_ID not set. Provide chat_id or set the env var."
                )
            self._chat_id = resolved

    # ------------------------------------------------------------------
    # Notifier interface
    # ------------------------------------------------------------------

    def send_summary(self, collection: EmailCollection) -> bool:
        """
        Format an EmailCollection as a readable briefing and send it.

        Args:
            collection: The categorized email collection.

        Returns:
            True on success.

        Raises:
            NotifierError: If the Telegram API call fails.
        """
        message = self._format_summary(collection)
        return self._send(message)

    def send_alert(self, message: str) -> bool:
        """
        Send an urgent alert message.

        Args:
            message: Plain-text alert.

        Returns:
            True on success.

        Raises:
            NotifierError: If the Telegram API call fails.
        """
        formatted = f"🚨 *ALERT*\n\n{self._escape_markdown(message)}"
        return self._send(formatted)

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """Escape special Markdown V2 characters in text."""
        special = r"_*[]()~`>#+-=|{}.!"
        for ch in special:
            text = text.replace(ch, f"\\{ch}")
        return text

    def _format_summary(self, collection: EmailCollection) -> str:
        """
        Build a Telegram-friendly summary of categorized emails.

        Args:
            collection: The EmailCollection to format.

        Returns:
            MarkdownV2-formatted string.
        """
        lines = [
            f"📬 *DCGMail Briefing*",
            f"Total: {collection.total_count} emails",
            "",
        ]

        # Category breakdown
        for cat, count in sorted(collection.by_category.items()):
            lines.append(f"*{self._escape_markdown(cat)}*: {count}")

        lines.append("")

        # Individual emails grouped by category
        by_cat: dict = {}
        for ce in collection.emails:
            by_cat.setdefault(ce.category, []).append(ce)

        for cat in sorted(by_cat):
            lines.append(f"─── {self._escape_markdown(cat)} ───")
            for ce in by_cat[cat]:
                sender = self._escape_markdown(ce.email.sender)
                subject = self._escape_markdown(ce.email.subject)
                lines.append(f"• {subject}")
                lines.append(f"  From: {sender}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Send helper
    # ------------------------------------------------------------------

    def _send(self, text: str) -> bool:
        """
        Send a message via the Telegram bot (synchronous wrapper).

        Args:
            text: MarkdownV2 formatted message.

        Returns:
            True on success.

        Raises:
            NotifierError: On any Telegram API error.
        """
        try:
            import asyncio

            async def _do_send():
                await self._bot.send_message(
                    chat_id=self._chat_id,
                    text=text,
                    parse_mode="MarkdownV2",
                )

            # Run the async send in a new event loop if none is running,
            # otherwise schedule it on the existing loop.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Already inside an async context — create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, _do_send()).result()
            else:
                asyncio.run(_do_send())

            return True
        except Exception as exc:
            raise NotifierError(f"Telegram send failed: {exc}") from exc
