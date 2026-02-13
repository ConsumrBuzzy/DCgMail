# Next Steps - Ready to Run!

## Current Status ✅

- ✅ Python 3.12 environment ready
- ✅ All dependencies installed
- ✅ OAuth2 provider implemented
- ✅ Setup wizard created and fixed for Windows
- ✅ Documentation complete
- ✅ Code tested and committed

## What You Need to Do (5 Minutes)

### Option 1: Run the Interactive Wizard (Easiest)

```bash
python setup_oauth2.py
```

**The wizard will:**
1. Open Google Cloud Console in your browser
2. Guide you step-by-step to create OAuth2 credentials
3. Help you download `oauth_client.json`
4. Update your `.env` automatically
5. Test authentication (opens browser for consent)

Just follow the prompts!

---

### Option 2: Manual Setup (If You Prefer)

**Step 1: Create OAuth2 Credentials (3 minutes)**

1. Go to: https://console.cloud.google.com/apis/credentials?project=dgautohub

2. Configure OAuth Consent Screen (if not done):
   - Click "OAuth consent screen"
   - User type: **Internal** (for Workspace) or **External** (personal Gmail)
   - App name: `DCGMail`
   - User support email: `robert.d@consumrbuzz.com`
   - Add scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     ```
   - If External: Add test user `robert.d@consumrbuzz.com`

3. Create OAuth Client ID:
   - Go to "Credentials" tab
   - Click **+ CREATE CREDENTIALS** → **OAuth client ID**
   - Application type: **Desktop app**
   - Name: `DCGMail Desktop Client`
   - Click **CREATE**

4. Download the credentials:
   - Find "DCGMail Desktop Client" in the list
   - Click the download icon
   - Save as: `./credentials/oauth_client.json`

**Step 2: Update Configuration (30 seconds)**

Add to `.env`:
```bash
GMAIL_AUTH_TYPE=oauth2
```

**Step 3: Test Authentication (1 minute)**

```bash
python main.py --validate-creds
```

This will:
1. Open your browser
2. Ask you to sign in to Google
3. Request permission to access Gmail
4. Save the token to `./credentials/token.json`
5. Show "[SUCCESS] All credentials valid"

---

## After Setup is Complete

### Test Email Fetching

```bash
# Dry run (no Telegram, just fetch and categorize)
python main.py --dry-run --limit 5
```

Expected output:
```
[SUCCESS] DCGMail completed successfully

======================================================================
EMAIL SUMMARY (DRY-RUN)
======================================================================

Total Emails: 5

By Category:
  Work                :   3 emails
  Personal            :   2 emails
======================================================================
```

### Configure Telegram (Optional)

1. Create bot via Telegram:
   - Message `@BotFather`
   - Send `/newbot`
   - Follow prompts
   - Copy the bot token

2. Get your chat ID:
   - Message `@userinfobot`
   - Send `/start`
   - Copy your numeric ID

3. Update `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TELEGRAM_CHAT_ID=987654321
   ```

### Run DCGMail

```bash
# Full run with Telegram notifications
python main.py --limit 10
```

---

## Troubleshooting

### "oauth_client.json not found"
- Download OAuth2 credentials from Google Cloud Console
- Save to `./credentials/oauth_client.json`
- Make sure the filename is exact

### Browser doesn't open
- Copy the URL from terminal and open manually
- Complete the OAuth consent in the browser
- The authorization will be detected automatically

### "Access blocked: This app isn't verified"
- Click "Advanced" → "Go to DCGMail (unsafe)"
- This is normal for testing/development apps
- Your app is safe, it just hasn't been submitted for Google verification

### "Invalid grant" error
- Delete `./credentials/token.json`
- Run `python main.py --validate-creds` again
- Complete the browser consent flow

---

## Files Created During Setup

```
credentials/
├── oauth_client.json       # You download this from Google Cloud Console
├── token.json              # Auto-generated after first authentication
└── service_account.json    # Existing (not needed for OAuth2)
```

---

## Quick Command Reference

```bash
# Run setup wizard
python setup_oauth2.py

# Validate credentials (opens browser first time)
python main.py --validate-creds

# Test dry-run
python main.py --dry-run --limit 5

# Debug mode
python main.py --dry-run --limit 3 --debug

# Full run
python main.py --limit 10

# Help
python main.py --help
```

---

## What Happens During OAuth2 Flow

1. **First Run:**
   - Browser opens to Google OAuth consent screen
   - You sign in with `robert.d@consumrbuzz.com`
   - Google shows: "DCGMail wants to access your Gmail"
   - You click "Allow"
   - Token saved to `./credentials/token.json`

2. **Subsequent Runs:**
   - DCGMail loads token from `./credentials/token.json`
   - No browser interaction needed
   - Token auto-refreshes if expired
   - Works for 7 days (extendable)

---

## Ready to Start!

**Recommended command:**
```bash
python setup_oauth2.py
```

This will guide you through everything step-by-step.

**Total time:** 5 minutes from start to processing emails! 🚀

---

## Support

- **Quick Start:** `OAUTH2_QUICKSTART.md`
- **Full Documentation:** `OAUTH2_SETUP.md`
- **Troubleshooting:** See documentation or run with `--debug`
- **Validate Setup:** `python main.py --validate-creds`

**All code is tested and ready. Just need to create the OAuth2 credentials!**
