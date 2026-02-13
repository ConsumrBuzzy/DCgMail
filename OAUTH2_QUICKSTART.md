# OAuth2 Quick Start (5 Minutes)

## Why OAuth2?

You have **cloud.google.com** access but NOT **admin.google.com** (Google Workspace Admin Console).

✅ OAuth2 works with cloud.google.com only
✅ No Admin Console access required
✅ Same functionality as domain-wide delegation
✅ One-time browser login

---

## Automated Setup (Recommended)

Run the setup wizard:

```bash
python setup_oauth2.py
```

This interactive script will:
1. Open Google Cloud Console for you
2. Guide you through creating OAuth2 credentials
3. Help you download oauth_client.json
4. Update your .env configuration
5. Test authentication

**Time:** 5 minutes

---

## Manual Setup (If Preferred)

### Step 1: Create OAuth2 Credentials (3 minutes)

1. **Go to Credentials Page**
   - URL: https://console.cloud.google.com/apis/credentials?project=dgautohub

2. **Configure OAuth Consent Screen** (if not done)
   - Click: OAuth consent screen
   - User type: **Internal** (for Workspace) or **External** (personal Gmail)
   - App name: `DCGMail`
   - User support email: `robert.d@consumrbuzz.com`
   - Add scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.modify
     ```
   - If External: Add test user `robert.d@consumrbuzz.com`

3. **Create OAuth Client ID**
   - Click: **+ CREATE CREDENTIALS** → **OAuth client ID**
   - Application type: **Desktop app**
   - Name: `DCGMail Desktop Client`
   - Click: **CREATE**

4. **Download Credentials**
   - Click the download icon (⬇) next to your new OAuth client
   - Save as: `./credentials/oauth_client.json`

### Step 2: Update Configuration (30 seconds)

Edit `.env`:

```bash
# Change this line:
GMAIL_AUTH_TYPE=oauth2

# OAuth2 credentials (already configured):
GMAIL_OAUTH_CLIENT=./credentials/oauth_client.json
GMAIL_OAUTH_TOKEN=./credentials/token.json
```

### Step 3: Test Authentication (1 minute)

```bash
python main.py --validate-creds
```

**What happens:**
1. Browser opens to Google OAuth consent page
2. Sign in with `robert.d@consumrbuzz.com`
3. Click "Allow" to grant permissions
4. Token saved to `./credentials/token.json`
5. Validation succeeds

**Future runs:** Token is reused, no browser needed!

---

## Verify Setup

```bash
# Validate credentials
python main.py --validate-creds

# Expected output:
# [SUCCESS] All credentials valid
```

```bash
# Test dry-run
python main.py --dry-run --limit 5

# Expected: Fetches emails successfully
```

---

## Token Refresh

OAuth2 tokens expire after **7 days** by default.

### Extend Token Life

1. **Google Cloud Console** → **OAuth consent screen**
2. Set **Publishing status** to **Production**
3. This extends token life (may require app verification)

### Auto-Refresh

DCGMail automatically refreshes expired tokens when you run it.

---

## Troubleshooting

### "oauth_client.json not found"
- Download OAuth2 credentials from Google Cloud Console
- Save as `./credentials/oauth_client.json`
- Verify path in `.env`: `GMAIL_OAUTH_CLIENT=./credentials/oauth_client.json`

### Browser doesn't open
- Run: `python main.py --validate-creds` again
- Check firewall/antivirus blocking port 8080
- Manually visit the URL shown in terminal

### "Access blocked: This app isn't verified"
- Click "Advanced" → "Go to DCGMail (unsafe)"
- This is normal for testing/development
- To remove warning: Submit app for Google verification (optional)

### "Invalid grant" error
- Token expired or revoked
- Delete `./credentials/token.json`
- Run `python main.py --validate-creds` again

---

## Comparison: OAuth2 vs Domain-Wide Delegation

| Feature | OAuth2 | Domain-Wide Delegation |
|---------|--------|------------------------|
| **Setup Time** | 5 minutes | 5 minutes + admin approval |
| **Requirements** | cloud.google.com only | admin.google.com required |
| **User Interaction** | One-time browser login | None |
| **Token Expiration** | 7 days (extendable) | Never |
| **Best For** | Development, personal use | Production, automation |

**For your case:** OAuth2 is perfect since you have cloud.google.com but not admin.google.com.

---

## Next Steps

Once OAuth2 is working:

1. **Test email fetching:**
   ```bash
   python main.py --dry-run --limit 10
   ```

2. **Configure Telegram (optional):**
   - Follow `QUICKSTART.md` Step 3
   - Update `.env` with bot token and chat ID

3. **Run DCGMail:**
   ```bash
   python main.py --limit 20
   ```

4. **Schedule automation:**
   - See `QUICKSTART.md` Step 6
   - Windows: Task Scheduler
   - Mac/Linux: Cron

---

**You're ready to go!** 🚀

Run `python setup_oauth2.py` to get started in 5 minutes.
