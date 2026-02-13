# OAuth2 User Consent Setup (No Admin Console Required)

## Why This Method?

You have **Google Cloud Console** access (`cloud.google.com`) but NOT **Google Workspace Admin Console** (`admin.google.com`).

Domain-wide delegation requires Admin Console, but we can use **OAuth2 User Consent Flow** instead:

✅ Works with Google Cloud Console only
✅ No Admin Console access needed
✅ No domain-wide delegation required
✅ Works for any Gmail account (personal or workspace)

⚠️ Requires one-time manual login
⚠️ Token refresh needed every 7 days (can be automated)

---

## Step 1: Create OAuth2 Credentials (5 minutes)

### Using Google Cloud Console

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com
   - Select project: `dgautohub`

2. **Navigate to APIs & Services → Credentials**
   - URL: https://console.cloud.google.com/apis/credentials?project=dgautohub

3. **Create OAuth 2.0 Client ID**
   - Click: **+ CREATE CREDENTIALS** → **OAuth client ID**
   - Application type: **Desktop app**
   - Name: `DCGMail Desktop Client`
   - Click: **CREATE**

4. **Download Credentials**
   - Click **DOWNLOAD JSON** on the created credential
   - Save as: `credentials/oauth_client.json`

### Using gcloud CLI (Alternative)

```bash
# Create OAuth2 client ID
gcloud auth application-default login --client-id-file=credentials/oauth_client.json

# Or create manually
# (Unfortunately gcloud doesn't support creating OAuth2 credentials directly)
```

---

## Step 2: Configure OAuth Consent Screen

1. **Navigate to OAuth Consent Screen**
   - URL: https://console.cloud.google.com/apis/credentials/consent?project=dgautohub

2. **User Type**
   - Select: **Internal** (for Workspace users) OR **External** (for personal Gmail)
   - Click: **CREATE**

3. **App Information**
   - App name: `DCGMail`
   - User support email: `robert.d@consumrbuzz.com`
   - Developer contact: `robert.d@consumrbuzz.com`
   - Click: **SAVE AND CONTINUE**

4. **Scopes**
   - Click: **ADD OR REMOVE SCOPES**
   - Filter for: `gmail`
   - Select:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.modify`
   - Click: **UPDATE** → **SAVE AND CONTINUE**

5. **Test Users** (if External)
   - Add: `robert.d@consumrbuzz.com`
   - Click: **SAVE AND CONTINUE**

6. **Summary**
   - Review and click: **BACK TO DASHBOARD**

---

## Step 3: Update DCGMail Code

We need to modify the Gmail provider to support OAuth2 instead of service account.

### Option A: Create New OAuth2 Provider (Recommended)

Create `src/providers/gmail_oauth_provider.py`:

```python
"""Gmail provider using OAuth2 user consent flow."""

import os
import json
from pathlib import Path
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..interfaces import EmailProvider, Email, CredentialError, ProviderError

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

class GmailOAuth2Provider(EmailProvider):
    """Gmail provider with OAuth2 user consent."""

    def __init__(self, oauth_client_path: str, token_path: str = "credentials/token.json", logger=None):
        """
        Initialize Gmail OAuth2 provider.

        Args:
            oauth_client_path: Path to OAuth client credentials JSON
            token_path: Path to store refresh token
            logger: Logger instance
        """
        self.oauth_client_path = oauth_client_path
        self.token_path = token_path
        self.logger = logger
        self.service = None
        self.credentials = None

    def authenticate(self) -> bool:
        """Authenticate using OAuth2 user consent flow."""
        try:
            creds = None

            # Load existing token if available
            if Path(self.token_path).exists():
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                self.logger.info(f"Loaded existing OAuth2 token from {self.token_path}")

            # If no valid credentials, initiate OAuth2 flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing expired OAuth2 token...")
                    creds.refresh(Request())
                else:
                    self.logger.info("Starting OAuth2 consent flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.oauth_client_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    self.logger.info("OAuth2 consent granted, token obtained")

                # Save token for future use
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                self.logger.info(f"Saved OAuth2 token to {self.token_path}")

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            self.credentials = creds
            self.logger.info("Gmail OAuth2 authentication successful")
            return True

        except Exception as e:
            raise CredentialError(f"OAuth2 authentication failed: {e}")

    def fetch_unread(self, limit: int = 50) -> List[Email]:
        """Fetch unread emails (same as service account version)."""
        # ... (copy from gmail_provider.py)
        pass

    def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read (same as service account version)."""
        # ... (copy from gmail_provider.py)
        pass

    def add_label(self, email_id: str, label_name: str) -> bool:
        """Add label to email (same as service account version)."""
        # ... (copy from gmail_provider.py)
        pass

    def move_to_trash(self, email_id: str) -> bool:
        """Move email to trash (same as service account version)."""
        # ... (copy from gmail_provider.py)
        pass
```

### Option B: Add OAuth2 Support to Existing Provider

Modify `src/providers/gmail_provider.py` to support both auth methods:

```python
# Add to __init__:
self.auth_type = config.get("gmail_auth_type", "service_account")  # or "oauth2"

# Modify authenticate() method to check auth_type
if self.auth_type == "oauth2":
    # Use OAuth2 flow
else:
    # Use service account (existing code)
```

---

## Step 4: Update .env Configuration

Add OAuth2 settings to `.env`:

```bash
# Gmail Authentication Type (service_account or oauth2)
GMAIL_AUTH_TYPE=oauth2

# OAuth2 Client Credentials (for oauth2 type)
GMAIL_OAUTH_CLIENT=./credentials/oauth_client.json

# OAuth2 Token Storage (auto-generated)
GMAIL_OAUTH_TOKEN=./credentials/token.json

# Work Email (not needed for OAuth2, but kept for compatibility)
WORK_EMAIL=robert.d@consumrbuzz.com
```

---

## Step 5: First-Time Setup

### Run Initial Authentication

```bash
# This will open a browser for OAuth consent
python main.py --validate-creds
```

**What Happens:**
1. Browser opens to Google OAuth consent screen
2. Sign in with `robert.d@consumrbuzz.com`
3. Grant permissions to DCGMail
4. Token saved to `credentials/token.json`
5. Future runs use saved token (no browser needed)

### Token Refresh

The refresh token is valid for **7 days** by default. To extend:

1. **Google Cloud Console** → **OAuth consent screen**
2. Set **Publishing status** to **Production** (extends to 7 days)
3. For unlimited refresh: Verify app with Google (requires review)

---

## Step 6: Test

```bash
# Validate OAuth2 credentials
python main.py --validate-creds

# Dry run (no Telegram)
python main.py --dry-run --limit 5

# Full run
python main.py --limit 10
```

**Expected:**
- ✅ Browser opens for consent (first time only)
- ✅ Emails fetched successfully
- ✅ No `unauthorized_client` error

---

## Pros & Cons

### OAuth2 User Consent
✅ No Admin Console required
✅ Works with cloud.google.com only
✅ Works for personal Gmail
✅ More secure (user explicitly grants access)

⚠️ Requires manual login once
⚠️ Token expires (7 days default)
⚠️ Browser must be available for first auth

### Domain-Wide Delegation
✅ Fully automated (no user interaction)
✅ No token expiration
✅ Suitable for production

⚠️ Requires admin.google.com access
⚠️ Requires Workspace Admin role
⚠️ More complex setup

---

## Which Method Should We Use?

**For Your Use Case:**
Since you have `cloud.google.com` but NOT `admin.google.com`:

**→ Implement OAuth2 User Consent (Option A)**

This will work perfectly for your needs and doesn't require Admin Console access.

---

## Next Steps

**Option 1: I implement OAuth2 support (30 minutes)**
- Create `GmailOAuth2Provider`
- Update `main.py` to support both auth types
- Update `.env` configuration
- Test OAuth2 flow

**Option 2: Request Admin Console access**
- Contact your Workspace admin
- Ask for Admin Console access
- Use domain-wide delegation (original approach)

**Which would you prefer?** OAuth2 is faster and doesn't require any additional permissions.
