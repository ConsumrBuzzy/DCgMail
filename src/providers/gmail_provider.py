"""
Gmail API provider implementation.

Based on Telesero_DNC_Automation's service account authentication pattern.
Implements the EmailProvider interface from src/interfaces.py.
"""

import os
from datetime import datetime
from typing import List
from pathlib import Path

from google.oauth2.service_account import Credentials
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.interfaces import (
    EmailProvider,
    Email,
    CredentialError,
    ProviderError,
    ConfigProvider,
    Logger,
)


class GmailProvider(EmailProvider):
    """Gmail API implementation using service account authentication."""

    GMAIL_SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.labels'
    ]

    def __init__(self, config: ConfigProvider, logger: Logger):
        """
        Initialize Gmail provider.

        Args:
            config: Configuration provider
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.service = None
        self.authenticated = False
        self.user_email = config.get("work_email", "me")

    def authenticate(self) -> bool:
        """
        Authenticate using service account (from Telesero pattern).

        Returns:
            True if authenticated successfully

        Raises:
            CredentialError if credentials are invalid/missing
        """
        try:
            # Try multiple credential paths (Telesero pattern)
            credential_paths = [
                os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                self.config.get('gmail_service_account'),
                'credentials/service_account.json',
                './credentials/service_account.json',
            ]

            credentials = None

            for creds_path in credential_paths:
                if creds_path and Path(creds_path).exists():
                    self.logger.info(f"Loading credentials from: {creds_path}")
                    credentials = Credentials.from_service_account_file(
                        creds_path,
                        scopes=self.GMAIL_SCOPES,
                        subject=self.user_email  # Domain-wide delegation
                    )
                    break

            # Fallback to Application Default Credentials
            if not credentials:
                self.logger.info("Attempting Application Default Credentials")
                credentials, _ = default(scopes=self.GMAIL_SCOPES)

            if not credentials:
                raise CredentialError(
                    "No valid credentials found. Set GOOGLE_APPLICATION_CREDENTIALS "
                    "or provide gmail_service_account in .env"
                )

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=credentials)
            self.authenticated = True
            self.logger.info("Gmail authentication successful")
            return True

        except Exception as e:
            self.logger.error(f"Gmail authentication failed: {e}", exception=e)
            raise CredentialError(f"Gmail authentication failed: {e}")

    def fetch_unread(self, limit: int = 50) -> List[Email]:
        """
        Fetch unread emails from Gmail.

        Args:
            limit: Maximum number of emails to fetch

        Returns:
            List of Email objects in reverse chronological order

        Raises:
            ProviderError if fetch fails
        """
        if not self.authenticated:
            raise ProviderError("Not authenticated. Call authenticate() first.")

        try:
            self.logger.info(f"Fetching up to {limit} unread emails...")

            # Query for unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=limit
            ).execute()

            messages = results.get('messages', [])
            self.logger.info(f"Found {len(messages)} unread messages")

            emails = []
            for msg in messages:
                email_data = self._parse_message(msg['id'])
                if email_data:
                    emails.append(email_data)

            self.logger.info(f"Successfully parsed {len(emails)} emails")
            return emails

        except HttpError as e:
            self.logger.error(f"Failed to fetch emails: {e}", exception=e)
            raise ProviderError(f"Failed to fetch emails: {e}")

    def _parse_message(self, msg_id: str) -> Email:
        """
        Parse Gmail message into Email object.

        Args:
            msg_id: Gmail message ID

        Returns:
            Email object or None if parsing fails
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            # Extract headers
            headers = {h['name']: h['value']
                      for h in message['payload']['headers']}

            # Get timestamp
            timestamp = datetime.fromtimestamp(
                int(message['internalDate']) / 1000
            )

            return Email(
                id=msg_id,
                sender=headers.get('From', 'Unknown'),
                subject=headers.get('Subject', '(no subject)'),
                snippet=message.get('snippet', ''),
                timestamp=timestamp,
                read=False,
                labels=message.get('labelIds', [])
            )

        except Exception as e:
            self.logger.error(f"Failed to parse message {msg_id}: {e}")
            return None

    def mark_as_read(self, email_id: str) -> bool:
        """
        Mark email as read.

        Args:
            email_id: Gmail message ID

        Returns:
            True if successful
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            self.logger.debug(f"Marked {email_id} as read")
            return True

        except Exception as e:
            self.logger.error(f"Failed to mark {email_id} as read: {e}")
            return False

    def add_label(self, email_id: str, label: str) -> bool:
        """
        Add label to email.

        Args:
            email_id: Gmail message ID
            label: Label name

        Returns:
            True if successful
        """
        try:
            # Get or create label ID
            label_id = self._get_label_id(label)
            if not label_id:
                return False

            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            self.logger.debug(f"Added label '{label}' to {email_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add label to {email_id}: {e}")
            return False

    def move_to_trash(self, email_id: str) -> bool:
        """
        Delete/trash email.

        Args:
            email_id: Gmail message ID

        Returns:
            True if successful
        """
        try:
            self.service.users().messages().trash(
                userId='me',
                id=email_id
            ).execute()
            self.logger.debug(f"Moved {email_id} to trash")
            return True

        except Exception as e:
            self.logger.error(f"Failed to trash {email_id}: {e}")
            return False

    def _get_label_id(self, label_name: str) -> str:
        """
        Get label ID by name, creating if needed.

        Args:
            label_name: Label name

        Returns:
            Label ID or None
        """
        try:
            results = self.service.users().labels().list(userId='me').execute()

            for label in results.get('labels', []):
                if label['name'] == label_name:
                    return label['id']

            # Create label if not found
            new_label = self.service.users().labels().create(
                userId='me',
                body={'name': label_name}
            ).execute()
            self.logger.info(f"Created new label: {label_name}")
            return new_label['id']

        except Exception as e:
            self.logger.error(f"Failed to get label {label_name}: {e}")
            return None
