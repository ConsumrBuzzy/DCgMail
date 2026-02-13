"""
src/gmail_provider.py - Gmail API implementation of EmailProvider.

Uses a Google service account to fetch, label, and manage emails
via the Gmail API. Credentials are loaded from environment variables
through config/credentials.py — never hardcoded.
"""

import base64
from datetime import datetime
from typing import List

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config.credentials import CredentialsManager
from src.interfaces import (
    Email,
    EmailProvider,
    CredentialError,
    ProviderError,
)

# Gmail API scopes needed for read + modify operations
_SCOPES = ["https://mail.google.com/"]


class GmailProvider(EmailProvider):
    """Fetch and manage emails through the Gmail API."""

    def __init__(self):
        """Initialize without connecting — call authenticate() first."""
        self._service = None
        self._user_email = None

    def authenticate(self) -> bool:
        """
        Build an authenticated Gmail API service using a service account
        with domain-wide delegation.

        Returns:
            True when the service is ready.

        Raises:
            CredentialError: If credentials are missing or invalid.
        """
        try:
            sa_info = CredentialsManager.load_service_account()
            self._user_email = CredentialsManager.get_work_email()

            credentials = service_account.Credentials.from_service_account_info(
                sa_info, scopes=_SCOPES
            )
            # Delegate to the target mailbox
            delegated = credentials.with_subject(self._user_email)

            self._service = build("gmail", "v1", credentials=delegated)
            return True
        except (ValueError, FileNotFoundError) as exc:
            raise CredentialError(str(exc)) from exc
        except Exception as exc:
            raise CredentialError(f"Gmail authentication failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_service(self):
        """Raise ProviderError if authenticate() hasn't been called."""
        if self._service is None:
            raise ProviderError("Not authenticated. Call authenticate() first.")

    @staticmethod
    def _parse_message(msg: dict) -> Email:
        """
        Convert a raw Gmail API message resource into an Email dataclass.

        Args:
            msg: Full message resource from the Gmail API.

        Returns:
            An Email instance.
        """
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}

        # Parse the internal date (ms since epoch)
        ts_ms = int(msg.get("internalDate", 0))
        timestamp = datetime.fromtimestamp(ts_ms / 1000)

        return Email(
            id=msg["id"],
            sender=headers.get("From", ""),
            subject=headers.get("Subject", "(no subject)"),
            snippet=msg.get("snippet", ""),
            timestamp=timestamp,
            read="UNREAD" not in msg.get("labelIds", []),
            labels=msg.get("labelIds", []),
        )

    # ------------------------------------------------------------------
    # EmailProvider interface
    # ------------------------------------------------------------------

    def fetch_unread(self, limit: int = 50) -> List[Email]:
        """
        Fetch up to *limit* unread emails, newest first.

        Args:
            limit: Maximum number of emails to return.

        Returns:
            List of Email objects.

        Raises:
            ProviderError: If the API call fails.
        """
        self._require_service()
        try:
            response = (
                self._service.users()
                .messages()
                .list(
                    userId="me",
                    q="is:unread",
                    maxResults=limit,
                )
                .execute()
            )

            message_ids = response.get("messages", [])
            emails: List[Email] = []

            for msg_stub in message_ids:
                full = (
                    self._service.users()
                    .messages()
                    .get(userId="me", id=msg_stub["id"], format="full")
                    .execute()
                )
                emails.append(self._parse_message(full))

            return emails
        except Exception as exc:
            raise ProviderError(f"Failed to fetch emails: {exc}") from exc

    def mark_as_read(self, email_id: str) -> bool:
        """
        Remove the UNREAD label from an email.

        Args:
            email_id: Gmail message ID.

        Returns:
            True on success.

        Raises:
            ProviderError: If the API call fails.
        """
        self._require_service()
        try:
            self._service.users().messages().modify(
                userId="me",
                id=email_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
            return True
        except Exception as exc:
            raise ProviderError(f"Failed to mark email as read: {exc}") from exc

    def add_label(self, email_id: str, label: str) -> bool:
        """
        Add a label to an email. Creates the label if it doesn't exist.

        Args:
            email_id: Gmail message ID.
            label: Human-readable label name.

        Returns:
            True on success.

        Raises:
            ProviderError: If the API call fails.
        """
        self._require_service()
        try:
            label_id = self._get_or_create_label(label)
            self._service.users().messages().modify(
                userId="me",
                id=email_id,
                body={"addLabelIds": [label_id]},
            ).execute()
            return True
        except Exception as exc:
            raise ProviderError(f"Failed to add label: {exc}") from exc

    def move_to_trash(self, email_id: str) -> bool:
        """
        Move an email to the trash.

        Args:
            email_id: Gmail message ID.

        Returns:
            True on success.

        Raises:
            ProviderError: If the API call fails.
        """
        self._require_service()
        try:
            self._service.users().messages().trash(
                userId="me", id=email_id
            ).execute()
            return True
        except Exception as exc:
            raise ProviderError(f"Failed to trash email: {exc}") from exc

    # ------------------------------------------------------------------
    # Label management helpers
    # ------------------------------------------------------------------

    def _get_or_create_label(self, name: str) -> str:
        """
        Return the label ID for *name*, creating it if necessary.

        Args:
            name: Human-readable label name.

        Returns:
            Gmail label ID string.
        """
        labels = (
            self._service.users()
            .labels()
            .list(userId="me")
            .execute()
            .get("labels", [])
        )
        for lbl in labels:
            if lbl["name"] == name:
                return lbl["id"]

        created = (
            self._service.users()
            .labels()
            .create(userId="me", body={"name": name})
            .execute()
        )
        return created["id"]
