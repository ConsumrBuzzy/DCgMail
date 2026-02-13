# DCGMail: Security Architecture

## The Core Principle: "Public Code, Private Secrets"

Your repo is public, but your credentials never touch it. This document outlines how to build DCGMail so it's secure from day one and extensible as you grow.

---

## 1. The Credential Problem (And the Solution)

### What You're Worried About
- Work Gmail credentials exposed in a public repo = career risk
- Telegram Bot token leaked = someone controlling your automation
- Google Cloud credentials = someone using your GCP quota/billing

### The SOLID Solution: Environment-Based Configuration

Instead of hardcoding secrets, we use **environment variables** + **a credentials schema** that you never commit.

**The Flow:**
```
Your Local Machine (Private)
├── credentials/
│   ├── service_account.json  (NEVER commit - add to .gitignore)
│   ├── telegram_bot_token    (NEVER commit - add to .gitignore)
│   └── google_oauth.json     (NEVER commit - add to .gitignore)
├── .env.local                (NEVER commit - add to .gitignore)
└── .gitignore                (COMMITTED - tells Git to ignore secrets)

Public GitHub Repo
├── config/
│   └── credentials_schema.json (EXAMPLE/TEMPLATE - shows structure, NO real secrets)
├── .gitignore                  (prevents accidental commits)
├── README.md                   (setup instructions)
└── [all Python code]
```

---

## 2. Credential Management Strategy

### Option A: Local Environment Variables (Simplest for Weekend Warrior)

**Setup:**
```bash
# Create a .env file (DO NOT COMMIT)
echo "GMAIL_SERVICE_ACCOUNT=/path/to/service_account.json" >> .env
echo "TELEGRAM_BOT_TOKEN=your_token_here" >> .env
echo "WORK_EMAIL=your.work@email.com" >> .env
```

**In your code:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_SERVICE_ACCOUNT = os.getenv("GMAIL_SERVICE_ACCOUNT")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WORK_EMAIL = os.getenv("WORK_EMAIL")

# Validate at startup
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set. See .env.example")
```

**In `.gitignore` (COMMITTED):**
```
.env
.env.local
credentials/
*.json
telegram_token
```

### Option B: Google Cloud Secret Manager (Advanced, but still free-tier friendly)

If you decide to deploy to Google Cloud later:
```python
from google.cloud import secretmanager

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT_ID")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# At runtime (no credentials file needed on the server)
telegram_token = get_secret("telegram-bot-token")
```

**Benefit:** Your laptop has a credentials file, but the cloud doesn't.

---

## 3. The Service Account Pattern (For Gmail Access)

### What is a Service Account?
A service account is a "robot" that Google creates for your app. It's not your personal account—it has limited permissions to only what you grant it.

**Security Benefit:** If the service account credentials leak, Google lets you revoke them instantly. Your actual Gmail password remains safe.

### Setup Process (One-Time, Never Repeat)

1. **Go to Google Cloud Console**
   - Project: `DCGMail` (create a new one)
   - Enable APIs: Gmail API, Google Sheets API

2. **Create a Service Account**
   - Go to "Service Accounts"
   - Click "Create Service Account"
   - Name: `dcgmail-robot`
   - Grant role: None (you'll delegate via Gmail delegation)

3. **Create a JSON Key**
   - Click the service account
   - "Keys" tab → "Add Key" → "Create new key"
   - Type: JSON
   - Download and save to `credentials/service_account.json`
   - **NEVER commit this file**

4. **Delegate Gmail Access (Workspace Domain Admin Only)**
   - Go to Service Account → "Show Advanced Settings"
   - Copy the "Client ID"
   - Go to [Google Workspace Admin Console](https://admin.google.com)
   - Security → API Controls → Domain-wide Delegation
   - Add Client ID with scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     ```

### Code Pattern (Safe from Day One)

```python
# config/credentials.py
import json
import os
from pathlib import Path

class CredentialsManager:
    """Manage credentials safely from environment or files."""
    
    @staticmethod
    def load_service_account():
        """Load Gmail service account from credentials/ folder."""
        cred_path = os.getenv("GMAIL_SERVICE_ACCOUNT")
        if not cred_path:
            raise ValueError("GMAIL_SERVICE_ACCOUNT env var not set")
        
        with open(cred_path) as f:
            return json.load(f)
    
    @staticmethod
    def get_telegram_token():
        """Load Telegram bot token."""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        return token
```

---

## 4. Credential Rotation & Revocation

### If Your Credentials Leak
You have an "off switch" that doesn't require pushing code:

**Google Service Account:**
```bash
# Delete the compromised key in Google Cloud Console
# Go to Service Accounts → Keys → Delete
# Generate a new JSON key
# Update your .env file
# Restart the script
# Done. No code changes.
```

**Telegram Bot Token:**
```bash
# Talk to @BotFather on Telegram
# /revoke → Select your bot
# /newtoken → Paste the new token into .env
# Restart the script
# Done.
```

---

## 5. Work Inbox Specific Concerns

### Your Work Email Access Pattern
Since you're accessing your work inbox, we assume one of:

1. **You Own the Gmail Account** (Personal work email)
   - Use Service Account delegation (see above)
   - Only you have the service account JSON

2. **You Use Google Workspace (Company Domain)**
   - Domain admin approves service account delegation
   - Even cleaner: the company OAuth is separate from personal credentials

3. **Your Company Uses Outlook/Exchange**
   - Swap Gmail API for Microsoft Graph API later (SOLID principle!)
   - The Python architecture remains identical
   - Just swap the `EmailProvider` implementation

---

## 6. Project Structure (Credentials-Safe)

```
DCGMail/
├── .gitignore                    # COMMITTED - prevents secret leaks
├── .env.example                  # COMMITTED - template for .env
├── README.md                     # Instructions for setup
├── requirements.txt
│
├── config/
│   ├── __init__.py
│   ├── credentials.py            # Load secrets safely
│   ├── settings.py               # Non-secret config
│   └── credentials_schema.json   # Example structure (NO real values)
│
├── credentials/                  # NOT COMMITTED (.gitignore)
│   ├── service_account.json      # Your Gmail robot
│   └── telegram_token            # Your bot token
│
├── src/
│   ├── __init__.py
│   ├── interfaces.py             # Abstract base classes (SOLID)
│   ├── gmail_provider.py         # Gmail-specific logic
│   ├── categorizer.py            # Categorization logic
│   ├── telegram_notifier.py      # Telegram alerts
│   └── core.py                   # Main orchestration
│
└── tests/
    ├── test_categorizer.py       # Unit tests (no secrets needed)
    └── test_interfaces.py        # Contract testing
```

---

## 7. .gitignore (Your Safety Net)

```gitignore
# Credentials - NEVER commit
.env
.env.local
.env.*.local
credentials/
*.json
telegram_token
service_account.json

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
```

---

## 8. .env.example (The Template You DO Commit)

This goes in the repo so users know what environment variables are needed:

```bash
# .env.example - Copy this to .env and fill in YOUR values
# NEVER commit your actual .env file

# Gmail Service Account path
GMAIL_SERVICE_ACCOUNT=/path/to/credentials/service_account.json

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here_get_from_botfather

# Work email to monitor
WORK_EMAIL=your.work.email@company.com

# Telegram Chat ID (your personal chat with the bot)
TELEGRAM_CHAT_ID=your_numeric_id_here

# Optional: Categorization rules file
CATEGORIZATION_CONFIG=./config/categories.json
```

---

## 9. Documentation (Security Angle)

In your README, add a **Security Setup** section:

```markdown
## Security Setup

### 1. Google Cloud Service Account
- Create a new GCP project
- Enable Gmail API
- Create a service account key (JSON)
- Download to `credentials/service_account.json`
- **NEVER commit this file** (already in .gitignore)

### 2. Telegram Bot Token
- Talk to @BotFather on Telegram
- Create a new bot or use existing
- Get the token
- Store in `.env` as TELEGRAM_BOT_TOKEN

### 3. Local Environment
```bash
cp .env.example .env
# Edit .env with YOUR credentials
# .env is in .gitignore - it will never be committed
```

### Credential Rotation
If you suspect a leak:
1. Delete the Service Account key in GCP Console
2. Revoke the bot token with @BotFather
3. Generate new credentials
4. Update .env
5. Restart the script

No code changes needed.
```

---

## 10. The "Skeptical Auditor" Questions

### "What if someone forks my repo and steals ideas?"
That's open source. Encryption isn't relevant here. The value is your *architecture*, not the code.

### "What if GitHub gets hacked?"
Your credentials aren't on GitHub (they're in .gitignore). Only your *code* is there. Even if the repo is compromised, hackers don't have access tokens.

### "What if someone submits a PR that includes credentials?"
GitHub has commit hooks to catch API keys. But also: *review PRs before merging*.

### "Can I use this on multiple machines?"
Yes. Copy `credentials/` and `.env` to each machine. Or use Google Cloud Secret Manager (Option B).

### "What if I want to CI/CD this later?"
Store secrets in GitHub Secrets (GitHub Actions) or your deployment platform's secret manager. The code doesn't need to change—just the environment.

---

## 11. Next Steps

1. **Create `.gitignore`** immediately (before writing code)
2. **Create `.env.example`** as a template
3. **Initialize the `config/credentials.py`** module (SOLID Dependency Inversion)
4. **Write unit tests** that mock credentials (test without real secrets)

This way, you can build securely from day one and publish with confidence.

---

## Summary Table

| Concern | Solution | Effort |
|---------|----------|--------|
| Credentials in repo | .gitignore + .env | 5 min |
| Token leak | Instant revocation (no code changes) | 2 min |
| Code review security | Credentials not in repo to leak | Automatic |
| Multiple machines | Copy credentials/ and .env | 1 min |
| Cloud deployment | Move to Secret Manager | Easy swap later |
| Auditing | Credentials isolated from code | Built-in |

---

## The Philosophy

**You're building a *public tool* that processes *private data*.**

The architecture reflects this: the tool is open for review, but the data flows through private, isolated credential channels. This is the same pattern used by enterprises.

Proceed with confidence.
