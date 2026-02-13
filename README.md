# DCGMail: The Morning Headache Resolver

**A SOLID-based Python automation engine to triage and categorize work inbox emails, delivering a unified "Morning Briefing" via Telegram.**

```
6:30 AM → Your alarm goes off
6:35 AM → DCGMail runs, reads your work inbox
6:36 AM → Telegram notification arrives:

📧 Morning Briefing:
├─ 🔴 Work: 3 Urgent (Teams mentions, GCP alerts)
├─ 📊 Crypto: 2 Updates (Solana airdrop, trading signal)
├─ ⚠️  Admin: 1 Action (Payroll statement ready)
└─ 🗑️  Archived: 15 newsletters
```

---

## Vision

**Problem:** Your work inbox has ~30 unread emails every morning. You spend 15 minutes sorting signal from noise.

**Solution:** DCGMail automates this using Python + Gmail API + Telegram, with a SOLID architecture so you can swap providers later.

**Long-term Goal:** DCGMail becomes the "nervous system" of your personal automation stack, connecting to Google Sheets (expense tracking), GitHub Actions (crypto alerts), and other tools.

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- A Gmail work account
- A Telegram account (personal)
- Google Cloud Project (free tier is fine)

### 2. Clone & Setup

```bash
git clone https://github.com/yourusername/DCGMail.git
cd DCGMail

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with YOUR credentials
nano .env  # Or open in your editor
```

### 3. Get Credentials

#### Google Cloud Service Account (Gmail API)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project: `DCGMail`
3. Enable APIs: **Gmail API**
4. Create Service Account:
   - Service Accounts → Create Service Account
   - Name: `dcgmail-robot`
   - Skip permissions (for now)
5. Create JSON Key:
   - Click the service account
   - Keys → Add Key → Create new key → JSON
   - Save to `credentials/service_account.json`
6. Delegate Gmail Access (Google Workspace Admin):
   - Go back to Service Account → Show Advanced Settings → Copy Client ID
   - Go to [Google Workspace Admin](https://admin.google.com) → Security → API Controls → Domain-wide Delegation
   - Add Client ID with scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     ```

#### Telegram Bot Token
1. Open Telegram, search for `@BotFather`
2. Send `/start`, then `/newbot`
3. Name your bot: `DCGMail`
4. Copy the token: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
5. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```

#### Your Telegram Chat ID (Optional, for direct messages)
1. Go to `@userinfobot` on Telegram
2. Send `/start`
3. Copy your numeric ID
4. Add to `.env`:
   ```
   TELEGRAM_CHAT_ID=123456789
   ```

### 4. Run It

```bash
# Dry run (just fetch emails, don't send Telegram yet)
python main.py --dry-run

# Real run (sends Telegram alert)
python main.py

# Set up cron job (runs every morning at 6:30 AM)
# Edit with: crontab -e
# Add: 30 6 * * * cd /path/to/DCGMail && /path/to/venv/bin/python main.py
```

---

## Project Structure

```
DCGMail/
├── README.md                       # This file
├── SECURITY.md                     # Security architecture (READ THIS)
├── requirements.txt                # Python dependencies
├── .gitignore                      # Prevents credential leaks
├── .env.example                    # Template for .env
│
├── config/
│   ├── __init__.py
│   ├── credentials.py              # Load secrets safely
│   ├── settings.py                 # Non-secret configuration
│   └── categories.json             # Categorization rules (Regex patterns)
│
├── credentials/                    # NOT COMMITTED (.gitignore)
│   ├── service_account.json        # Gmail robot (KEEP PRIVATE)
│   └── .env                        # Local secrets (KEEP PRIVATE)
│
├── src/
│   ├── __init__.py
│   ├── interfaces.py               # SOLID: Abstract base classes
│   ├── gmail_provider.py           # Fetch emails from Gmail
│   ├── categorizer.py              # Categorize emails (Regex + LLM)
│   ├── telegram_notifier.py        # Send Telegram alerts
│   ├── logger.py                   # System logging
│   └── core.py                     # Orchestration (ties it together)
│
├── tests/
│   ├── test_categorizer.py         # Unit tests (no credentials needed)
│   ├── test_interfaces.py          # Contract testing
│   └── fixtures/
│       └── sample_emails.py        # Mock email data for testing
│
└── main.py                         # Entry point
```

---

## SOLID Architecture Explained

### Why SOLID?
You want to be able to:
1. Swap Gmail for Outlook (if your company switches)
2. Add AI categorization without rewriting regex logic
3. Add a Slack notifier alongside Telegram
4. Test each component independently

SOLID makes all of this possible.

### The 5 Principles

**S - Single Responsibility**
- `EmailProvider`: Only fetches emails
- `Categorizer`: Only categorizes
- `Notifier`: Only sends alerts

**O - Open/Closed**
- Open for extension: Add `LLMCategorizer` without touching `EmailProvider`
- Closed for modification: Don't rewrite `EmailProvider`

**L - Liskov Substitution**
- Any `Categorizer` can replace any other
- If it implements the interface, it works

**I - Interface Segregation**
- `Notifier` doesn't need to know about categorization
- Don't force unrelated methods on one class

**D - Dependency Inversion**
- `core.py` depends on abstractions (`EmailProvider`), not implementations (`GmailProvider`)
- Swap `GmailProvider` for `OutlookProvider` by changing one line of code

### Example: Swapping Providers

**Before SOLID (Bad):**
```python
# core.py
from gmail_provider import GmailProvider
provider = GmailProvider()  # Hard-coded dependency

# Now if you want Outlook, you have to rewrite core.py
```

**After SOLID (Good):**
```python
# core.py
from interfaces import EmailProvider

provider = create_provider(config.PROVIDER_TYPE)  # Could be Gmail, Outlook, etc.

# main.py
from config import settings
from src.gmail_provider import GmailProvider
from src.outlook_provider import OutlookProvider

def create_provider(provider_type: str) -> EmailProvider:
    if provider_type == "gmail":
        return GmailProvider()
    elif provider_type == "outlook":
        return OutlookProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_type}")
```

---

## Security

**TL;DR:** Your credentials never go on GitHub.

### How It Works

1. **`.env` File (Local Only)**
   - Stores: `GMAIL_SERVICE_ACCOUNT`, `TELEGRAM_BOT_TOKEN`, etc.
   - **Never committed** (see `.gitignore`)
   - Only on your laptop

2. **`credentials/` Folder (Local Only)**
   - Stores: `service_account.json` (Gmail robot key)
   - **Never committed** (see `.gitignore`)
   - Only on your laptop

3. **GitHub (Public)**
   - Code: Yes, public review
   - `.env.example`: Yes, shows what keys you need
   - Real credentials: No, never uploaded

### If Credentials Leak

**Google Service Account:**
1. Go to Google Cloud Console
2. Service Accounts → Click your account → Keys
3. Delete the compromised JSON key
4. Generate a new one
5. Update `.env`
6. Restart the script
→ Old credentials are instantly revoked

**Telegram Bot Token:**
1. Message `@BotFather` on Telegram
2. `/revoke` → Select your bot
3. `/newtoken` → Copy new token
4. Update `.env`
5. Restart the script
→ Old token is instantly revoked

**See `SECURITY.md` for detailed threat model and recovery procedures.**

---

## Configuration

### `.env` File

Copy from `.env.example` and fill in:

```bash
# Gmail Service Account credentials
GMAIL_SERVICE_ACCOUNT=./credentials/service_account.json

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Your work email
WORK_EMAIL=your.work@company.com

# Your Telegram Chat ID (optional, for debugging)
TELEGRAM_CHAT_ID=your_numeric_id_here

# Categories config (which emails go where)
CATEGORIES_CONFIG=./config/categories.json
```

### `config/categories.json`

Defines how emails are categorized:

```json
{
  "Work": {
    "patterns": ["Teams", "Jira", "Susan D.", "meeting invitation"],
    "senders": ["@company.com"]
  },
  "Crypto": {
    "patterns": ["Solana", "airdrop", "DEX", "NFT"],
    "senders": ["@coinbase.com", "@solflare"]
  },
  "Admin": {
    "patterns": ["payroll", "statement", "invoice", "receipt"],
    "senders": ["@paypal.com", "@coinbase.com"]
  },
  "Noise": {
    "patterns": ["newsletter", "unsubscribe", "promotional", "sale"],
    "senders": []
  }
}
```

---

## Usage

### Command Line

```bash
# Show help
python main.py --help

# Dry run (no Telegram sent)
python main.py --dry-run

# Real run
python main.py

# Set Telegram Chat ID (one-time setup)
python main.py --set-chat-id

# Debug mode (verbose logging)
python main.py --debug
```

### Scheduled (Cron Job)

```bash
# Edit cron table
crontab -e

# Add this line (runs daily at 6:30 AM)
30 6 * * * cd /path/to/DCGMail && /path/to/venv/bin/python main.py >> /tmp/dcgmail.log 2>&1
```

### GitHub Actions (Advanced)

To run in the cloud without a local machine:

1. Store secrets in GitHub:
   - Go to Settings → Secrets and variables → Actions
   - Add: `GMAIL_SERVICE_ACCOUNT_JSON`, `TELEGRAM_BOT_TOKEN`, etc.

2. Create `.github/workflows/morning-briefing.yml`:
```yaml
name: Morning Briefing

on:
  schedule:
    - cron: '30 6 * * *'  # 6:30 AM UTC daily

jobs:
  briefing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          GMAIL_SERVICE_ACCOUNT: ${{ secrets.GMAIL_SERVICE_ACCOUNT_JSON }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
```

---

## Development

### Running Tests

```bash
# All tests
pytest tests/

# Specific test
pytest tests/test_categorizer.py

# With coverage
pytest --cov=src tests/
```

### Adding a New Categorizer

Want to use AI instead of regex?

1. **Create `src/llm_categorizer.py`:**
```python
from src.interfaces import Categorizer, Email, CategorizedEmail

class LLMCategorizer(Categorizer):
    def categorize(self, email: Email) -> str:
        # Use Gemini API to categorize
        pass
    
    def categorize_batch(self, emails):
        # Batch process with LLM
        pass
    
    def get_categories(self):
        return ["Work", "Crypto", "Admin", "Noise"]
```

2. **Update `config/settings.py`:**
```python
CATEGORIZER_TYPE = "llm"  # Instead of "regex"
```

3. **Update `src/core.py`:**
```python
from src.llm_categorizer import LLMCategorizer

def create_categorizer(type: str):
    if type == "regex":
        return RegexCategorizer()
    elif type == "llm":
        return LLMCategorizer()
```

4. **That's it.** No other code changes needed (SOLID principle).

### Adding a New Notifier

Want to add Slack alongside Telegram?

1. **Create `src/slack_notifier.py`:**
```python
from src.interfaces import Notifier, EmailCollection

class SlackNotifier(Notifier):
    def send_summary(self, collection: EmailCollection) -> bool:
        # Post to Slack channel
        pass
    
    def send_alert(self, message: str) -> bool:
        # Post alert to Slack
        pass
```

2. **Update `src/core.py`:**
```python
def create_notifiers(config):
    notifiers = []
    if config.TELEGRAM_ENABLED:
        notifiers.append(TelegramNotifier())
    if config.SLACK_ENABLED:
        notifiers.append(SlackNotifier())
    return notifiers
```

3. **Add to config:**
```bash
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## Project Status

### ✅ Completed
- [ ] Architecture documentation (SOLID interfaces)
- [ ] Security documentation
- [ ] Project structure
- [ ] `.gitignore` and `.env.example`

### 🔄 In Progress
- [ ] `config/credentials.py` (load secrets safely)
- [ ] `src/gmail_provider.py` (fetch emails)
- [ ] `src/categorizer.py` (regex-based categorization)
- [ ] `src/telegram_notifier.py` (send alerts)

### ⏳ Planned
- [ ] `main.py` (orchestration)
- [ ] Unit tests
- [ ] GitHub Actions workflow
- [ ] LLM categorizer (Gemini AI)
- [ ] Google Sheets integration (expense tracking)

---

## FAQ

**Q: Why SOLID from day one?**  
A: Because you mentioned cloning this for your personal inbox later. SOLID means "build once, adapt forever."

**Q: Can I use this without Google Cloud?**  
A: Not right now (requires Gmail API). But the architecture supports Outlook, ProtonMail, etc. later.

**Q: Is my work email data safe?**  
A: Yes. The script runs locally on your machine. Credentials never leave your laptop except to authenticate with Google/Telegram APIs.

**Q: Can I run this in the cloud?**  
A: Yes, via GitHub Actions (see Advanced section). Credentials stored in GitHub Secrets.

**Q: What if I have 1000 unread emails?**  
A: The script fetches the last 50 by default. Change the limit in `config/settings.py`.

**Q: How do I debug if something breaks?**  
A: Run with `--debug` flag and check logs. See `src/logger.py` for details.

---

## Contributing

This is a personal project, but feel free to fork and adapt for your own inbox automation.

### Ideas for Extensions
- Add expense tracking to Google Sheets
- Integrate with GitHub Issues for "parking lot" tasks
- Build a dashboard (React/Vue) to visualize email trends
- Add calendar integration (block time for unread emails)
- Build a Slack bot version

---

## License

MIT License. Do with it what you will.

---

## Current State of Play

**Phase: Exploration**

You're right now at the "lay the foundation" stage:
1. ✅ Decide on SOLID principles (done)
2. ✅ Define interfaces (done - `interfaces.py`)
3. ✅ Document security (done - `SECURITY.md`)
4. ⏳ **Next: Implement Gmail provider** (fetch emails)
5. ⏳ Implement categorizer (regex rules)
6. ⏳ Implement Telegram notifier (send alerts)
7. ⏳ Orchestrate in `core.py`

This README is your "north star." Bookmark it. Every feature you add should fit into this architecture.

---

## Questions?

Open an Issue in this repo or chat with your Pair Programming AI (me!) to iterate on any part.

Good luck, Weekend Warrior. 🚀
