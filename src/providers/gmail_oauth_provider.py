#!/usr/bin/env python3
"""
Gmail OAuth2 Provider - User Consent Flow

Provides Gmail access using OAuth2 user consent instead of service account
domain-wide delegation. Works without Google Workspace Admin Console access.

Usage:
    provider = GmailOAuth2Provider(
        oauth_client_path="./credentials/oauth_client.json",
        token_path="./credentials/token.json",
        logger=logger
    )
    provider.authenticate()  # Opens browser for first-time consent
    emails = provider.fetch_unread(limit=10)
"""

import json
import base64
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..interfaces import EmailProvider, Email, CredentialError, ProviderError


# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailOAuth2Provider(EmailProvider):
    """
    Gmail provider using OAuth2 user consent flow.

    Advantages over service account:
    - No Admin Console access required
    - Works with personal Gmail accounts
    - User explicitly grants permissions

    Disadvantages:
    - Requires one-time browser login
    - Token expires (7 days default, can be extended)
    - Less suitable for fully automated systems
    """

    def __init__(
        self,
        oauth_client_path: str,
        token_path: str = "./credentials/token.json",
        logger=None
    ):
        """
        Initialize Gmail OAuth2 provider.

        Args:
            oauth_client_path: Path to OAuth2 client credentials JSON
                (Downloaded from Google Cloud Console)
            token_path: Path to store/load refresh token
                (Auto-generated after first authentication)
            logger: Logger instance for debugging

        Raises:
            CredentialError: If oauth_client_path doesn't exist
        """
        self.oauth_client_path = oauth_client_path
        self.token_path = token_path
        self.logger = logger
        self.service = None
        self.credentials = None

        # Validate OAuth client file exists
        if not Path(oauth_client_path).exists():
            raise CredentialError(
                f"OAuth2 client credentials not found: {oauth_client_path}\n"
                "Download from: https://console.cloud.google.com/apis/credentials"
            )

    def authenticate(self) -> bool:
        """
        Authenticate using OAuth2 user consent flow.

        First run:
        - Opens browser for Google OAuth consent
        - User signs in and grants permissions
        - Refresh token saved to token_path

        Subsequent runs:
        - Loads token from token_path
        - Automatically refreshes if expired
        - No browser interaction needed

        Returns:
            True if authentication successful

        Raises:
            CredentialError: If authentication fails
        """
        try:
            creds = None

            # Load existing token if available
            if Path(self.token_path).exists():
                if self.logger:
                    self.logger.info(f"Loading OAuth2 token from {self.token_path}")
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

            # If no valid credentials, initiate OAuth2 flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Token expired, refresh it
                    if self.logger:
                        self.logger.info("Refreshing expired OAuth2 token...")
                    creds.refresh(Request())
                    if self.logger:
                        self.logger.info("OAuth2 token refreshed successfully")
                else:
                    # No token or no refresh token, run full OAuth2 flow
                    if self.logger:
                        self.logger.info("Starting OAuth2 consent flow...")
                        self.logger.info("Browser will open for authentication")

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.oauth_client_path, SCOPES
                    )

                    # Run local server for OAuth2 callback
                    creds = flow.run_local_server(port=0)

                    if self.logger:
                        self.logger.info("OAuth2 consent granted")

                # Save credentials for future use
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())

                if self.logger:
                    self.logger.info(f"OAuth2 token saved to {self.token_path}")

            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=creds)
            self.credentials = creds

            if self.logger:
                self.logger.info("Gmail OAuth2 authentication successful")

            return True

        except FileNotFoundError as e:
            raise CredentialError(f"OAuth2 client file not found: {e}")
        except Exception as e:
            raise CredentialError(f"OAuth2 authentication failed: {e}")

    def fetch_unread(self, limit: int = 50) -> List[Email]:
        """
        Fetch unread emails from inbox.

        Args:
            limit: Maximum number of emails to fetch

        Returns:
            List of Email objects

        Raises:
            ProviderError: If Gmail API call fails
        """
        if not self.service:
            raise ProviderError("Not authenticated. Call authenticate() first.")

        try:
            if self.logger:
                self.logger.info(f"Fetching up to {limit} unread emails...")

            # List unread messages
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX', 'UNREAD'],
                maxResults=limit
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                if self.logger:
                    self.logger.info("No unread emails found")
                return []

            if self.logger:
                self.logger.info(f"Found {len(messages)} unread email(s)")

            # Fetch full details for each message
            emails = []
            for msg in messages:
                msg_detail = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                email = self._parse_email(msg_detail)
                if email:
                    emails.append(email)

            if self.logger:
                self.logger.info(f"Successfully fetched {len(emails)} email(s)")

            return emails

        except Exception as e:
            raise ProviderError(f"Failed to fetch emails: {e}")

    def mark_as_read(self, email_id: str) -> bool:
        """
        Mark email as read by removing UNREAD label.

        Args:
            email_id: Gmail message ID

        Returns:
            True if successful

        Raises:
            ProviderError: If API call fails
        """
        if not self.service:
            raise ProviderError("Not authenticated. Call authenticate() first.")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            if self.logger:
                self.logger.info(f"Marked email {email_id} as read")

            return True

        except Exception as e:
            raise ProviderError(f"Failed to mark email as read: {e}")

    def add_label(self, email_id: str, label_name: str) -> bool:
        """
        Add label to email.

        Args:
            email_id: Gmail message ID
            label_name: Name of label to add

        Returns:
            True if successful

        Raises:
            ProviderError: If API call fails
        """
        if not self.service:
            raise ProviderError("Not authenticated. Call authenticate() first.")

        try:
            # Get or create label
            label_id = self._get_or_create_label(label_name)

            # Add label to message
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': [label_id]}
            ).execute()

            if self.logger:
                self.logger.info(f"Added label '{label_name}' to email {email_id}")

            return True

        except Exception as e:
            raise ProviderError(f"Failed to add label: {e}")

    def move_to_trash(self, email_id: str) -> bool:
        """
        Move email to trash.

        Args:
            email_id: Gmail message ID

        Returns:
            True if successful

        Raises:
            ProviderError: If API call fails
        """
        if not self.service:
            raise ProviderError("Not authenticated. Call authenticate() first.")

        try:
            self.service.users().messages().trash(
                userId='me',
                id=email_id
            ).execute()

            if self.logger:
                self.logger.info(f"Moved email {email_id} to trash")

            return True

        except Exception as e:
            raise ProviderError(f"Failed to move email to trash: {e}")

    def _parse_email(self, msg_detail: dict) -> Optional[Email]:
        """
        Parse Gmail API message into Email object.

        Args:
            msg_detail: Full message details from Gmail API

        Returns:
            Email object or None if parsing fails
        """
        try:
            headers = msg_detail['payload']['headers']
            header_dict = {h['name'].lower(): h['value'] for h in headers}

            # Extract email body
            body = self._extract_body(msg_detail['payload'])

            email = Email(
                id=msg_detail['id'],
                sender=header_dict.get('from', 'Unknown'),
                subject=header_dict.get('subject', '(No Subject)'),
                snippet=msg_detail.get('snippet', ''),
                timestamp=datetime.fromtimestamp(
                    int(msg_detail['internalDate']) / 1000
                ),
                read=False,
                labels=msg_detail.get('labelIds', [])
            )

            return email

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to parse email: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """Extract email body from message payload."""
        # Try to get plain text body
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')

        # Fallback to snippet or body data
        if 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            return base64.urlsafe_b64decode(data).decode('utf-8')

        return ""

    def _get_or_create_label(self, label_name: str) -> str:
        """Get label ID, creating it if it doesn't exist."""
        try:
            # List existing labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])

            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    return label['id']

            # Create new label
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }

            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()

            if self.logger:
                self.logger.info(f"Created new label: {label_name}")

            return created_label['id']

        except Exception as e:
            raise ProviderError(f"Failed to get/create label: {e}")
