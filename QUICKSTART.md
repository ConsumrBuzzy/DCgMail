# DCGMail Quick Start Guide

Get DCGMail running in 15 minutes.

---

## Prerequisites

- Python 3.9+ installed
- A Gmail work account
- A Telegram account
- Google Cloud Project access

---

## Step 1: Install Dependencies (2 minutes)

```bash
# Navigate to project
cd DCgMail

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure Gmail API (5 minutes)

### Option A: Using gcloud CLI (Recommended)

```bash
# Install gcloud CLI if needed
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Create project
gcloud projects create dcgmail-project --name="DCGMail"

# Set active project
gcloud config set project dcgmail-project

# Enable Gmail API
gcloud services enable gmail.googleapis.com

# Create service account
gcloud iam service-accounts create dcgmail-bot \
  --display-name="DCGMail Service Account"

# Generate key
gcloud iam service-accounts keys create credentials/service_account.json \
  --iam-account=dcgmail-bot@dcgmail-project.iam.gserviceaccount.com

# Get Client ID for domain-wide delegation
gcloud iam service-accounts describe \
  dcgmail-bot@dcgmail-project.iam.gserviceaccount.com \
  --format="value(oauth2ClientId)"
```

### Option B: Using Google Cloud Console

1. Go to https://console.cloud.google.com
2. Create new project: "DCGMail"
3. Enable Gmail API
4. Create Service Account → Generate JSON key
5. Save to `credentials/service_account.json`

### Domain-Wide Delegation (Required)

1. Go to https://admin.google.com
2. Security → API Controls → Domain-wide Delegation
3. Add Client ID (from above) with scopes:
   ```
   https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/gmail.modify
   ```

---

## Step 3: Configure Telegram Bot (3 minutes)

### Create Bot

1. Open Telegram, search for `@BotFather`
2. Send: `/newbot`
3. Follow prompts to name your bot
4. Copy the token: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### Get Your Chat ID

**Option 1: Use @userinfobot**
1. Search for `@userinfobot` on Telegram
2. Send `/start`
3. Copy your numeric ID

**Option 2: Use curl**
```bash
# Message your bot with: /start
# Then run:
TOKEN="your_bot_token_here"
curl -s "https://api.telegram.org/bot${TOKEN}/getUpdates" | jq '.result[0].message.chat.id'
```

---

## Step 4: Configure Environment (2 minutes)

```bash
# Copy template
cp .env.example .env

# Edit .env
nano .env  # or: code .env
```

Fill in:
```bash
# Gmail API
GMAIL_SERVICE_ACCOUNT=./credentials/service_account.json
WORK_EMAIL=your.email@company.com

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321

# Configuration
LOG_LEVEL=INFO
MAX_EMAILS=50
DRY_RUN=false
```

---

## Step 5: Test (3 minutes)

### Validate Credentials
```bash
python main.py --validate-creds
```

Expected output:
```
✅ All credentials valid
```

### Dry Run (No Telegram)
```bash
python main.py --dry-run --limit 5
```

Expected output:
```
======================================================================
EMAIL SUMMARY (DRY-RUN)
======================================================================

Total Emails: 5

By Category:
  Work                :   3 emails
    - Teams: New assignment from John Smith
    - GCP Alert: High memory usage detected
    - Code Review: PR #123 needs review

  Crypto              :   2 emails
    - Solana airdrop notification
    - Weekly trading signal
======================================================================
```

### Real Run (Sends Telegram)
```bash
python main.py --limit 5
```

Check Telegram - you should receive the briefing!

---

## Step 6: Schedule Daily Execution (Optional)

### Windows: Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "DCGMail Morning Briefing"
4. Trigger: Daily at 6:30 AM
5. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\DCgMail\main.py`
   - Start in: `C:\path\to\DCgMail`

### Mac/Linux: Cron

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths):
30 6 * * * cd /path/to/DCgMail && /path/to/venv/bin/python main.py >> /tmp/dcgmail.log 2>&1
```

---

## Customization

### Edit Categories

Edit `config/categories.json` to customize categorization:

```json
{
  "Work": {
    "patterns": ["teams", "jira", "meeting"],
    "senders": ["@company.com"],
    "priority": 1
  },
  "Personal": {
    "patterns": ["family", "friend"],
    "senders": ["@gmail.com"],
    "priority": 5
  }
}
```

**Pattern matching:**
- Case-insensitive regex
- Matches subject + snippet
- Lower priority number = higher priority

**Sender matching:**
- `@company.com` - matches any sender from domain
- `john@company.com` - exact email match

---

## Troubleshooting

### "Credential validation failed"
- Check `credentials/service_account.json` exists
- Verify `GMAIL_SERVICE_ACCOUNT` path in `.env`
- Ensure domain-wide delegation is configured

### "401 Unauthorized" from Gmail
- Service account JSON is invalid
- Re-download from Google Cloud Console

### "403 Forbidden" from Gmail
- Domain-wide delegation not configured
- Scopes not correct in Admin Console
- `WORK_EMAIL` doesn't match delegated user

### "Telegram token invalid"
- Check `TELEGRAM_BOT_TOKEN` in `.env`
- Re-generate token from @BotFather if needed

### "No emails found"
- Check `WORK_EMAIL` is correct
- Verify there are unread emails in inbox
- Try increasing `--limit`

---

## Command Reference

```bash
# Validate credentials
python main.py --validate-creds

# Dry run (no Telegram)
python main.py --dry-run

# Fetch specific number of emails
python main.py --limit 10

# Debug mode (verbose logging)
python main.py --debug

# Custom categories file
python main.py --categories /path/to/categories.json

# Help
python main.py --help
```

---

## Security Best Practices

1. **Never commit credentials**
   - `.env` is gitignored
   - `credentials/` is gitignored
   - Always use `.env.example` as template

2. **Service account security**
   - Limit scopes to minimum needed
   - Use domain-wide delegation (not OAuth)
   - Rotate keys periodically

3. **Telegram security**
   - Keep bot token secret
   - Only share chat ID with trusted services
   - Disable bot if compromised

---

## What's Next?

1. **Monitor first week**
   - Check logs: `/tmp/dcgmail.log` (or wherever configured)
   - Verify categorization accuracy
   - Adjust `config/categories.json` as needed

2. **Extend functionality**
   - Add more categories
   - Implement LLM categorization (Gemini API)
   - Integrate with Google Sheets for logging
   - Add expense tracking automation

3. **Contribute**
   - Report issues
   - Submit PRs
   - Share your categories.json patterns

---

## Support

- **Documentation:** See README.md
- **Security:** See DCGMail_SECURITY.md
- **Architecture:** See src/interfaces.py
- **Issues:** https://github.com/ConsumrBuzzy/DCgMail/issues

---

**You're all set! DCGMail will now automate your inbox every morning.** 🚀
