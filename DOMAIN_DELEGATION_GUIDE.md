# Domain-Wide Delegation Setup Guide

## Current Status
✅ Service account created: `dcgmail-bot@dgautohub.iam.gserviceaccount.com`
✅ OAuth2 Client ID: `117030078206154067665`
✅ Service account key: `credentials/service_account.json`
⚠️ **Domain-wide delegation: PENDING**

---

## Why This Is Required

The service account needs domain-wide delegation to:
- Access Gmail on behalf of `robert.d@consumrbuzz.com`
- Read and modify emails (mark as read, add labels)
- Work without user interaction (automated inbox processing)

**Current Error:**
```
unauthorized_client: Client is unauthorized to retrieve access tokens
```

---

## Method 1: Google Workspace Admin Console (Recommended - 5 minutes)

### Step 1: Access Admin Console
1. Go to: https://admin.google.com
2. Sign in with Google Workspace admin account
3. Navigate to: **Security** → **Access and data control** → **API Controls**

### Step 2: Manage Domain-Wide Delegation
1. Scroll to **Domain-wide delegation** section
2. Click **Manage Domain Wide Delegation**
3. Click **Add new**

### Step 3: Configure Client Access
- **Client ID:** `117030078206154067665`
- **OAuth Scopes:**
  ```
  https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify
  ```
- **Description:** DCGMail inbox automation (optional)

### Step 4: Authorize
1. Click **Authorize**
2. Wait 5-10 minutes for propagation (Google's propagation delay)
3. Test with: `python main.py --dry-run --limit 5`

---

## Method 2: Using Google Cloud Directory API (Alternative)

If you don't have direct Admin Console access, you can use the Directory API with an admin account:

### Prerequisites
- Admin credentials for `consumrbuzz.com` domain
- Directory API enabled (we'll enable it)

### Step 1: Enable Directory API
```bash
gcloud services enable admin.googleapis.com
```

### Step 2: Create OAuth2 Credentials for Domain Admin
```bash
# This creates OAuth2 credentials for interactive admin login
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/admin.directory.user
```

### Step 3: Use Admin SDK to Configure Delegation
Unfortunately, the **Admin SDK does NOT support programmatic domain-wide delegation configuration**. The Google Workspace Admin Console is the ONLY way to configure this.

This is a security measure by Google to prevent unauthorized delegation.

---

## Method 3: Alternative Authentication (OAuth2 User Consent)

If domain-wide delegation is not possible, we can use OAuth2 user consent flow instead:

### Pros:
- No Admin Console access required
- Works for personal Gmail accounts
- No domain-wide delegation needed

### Cons:
- Requires manual login once
- Token expires after 7 days (need refresh)
- Less suitable for automation

### Implementation Steps:

1. **Create OAuth2 Credentials**
```bash
# Create OAuth2 client ID
gcloud auth application-default login
```

2. **Modify Gmail Provider**
We'd need to update `src/providers/gmail_provider.py` to support OAuth2 flow instead of service account.

**Should we implement this alternative?** It would require code changes but removes the Admin Console requirement.

---

## Method 4: Using Cloud Identity (For G Suite Basic/Business)

If using Cloud Identity or G Suite:

### Step 1: Verify Domain Ownership
```bash
# Check if domain is verified
gcloud domains list-user-verified
```

### Step 2: Admin Console Access
Domain-wide delegation still requires Admin Console access. There's no programmatic alternative.

---

## Recommended Approach

**For Production (Recommended):**
- Use **Method 1** (Admin Console) - 5 minutes
- Contact your Google Workspace admin if you don't have access
- Provide them with:
  - Client ID: `117030078206154067665`
  - Scopes: `https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify`
  - Purpose: Automated inbox processing for `robert.d@consumrbuzz.com`

**For Testing/Development:**
- Use **Method 3** (OAuth2 User Consent) - requires code changes
- Less suitable for automation but works without admin access

---

## Verification After Setup

Once domain-wide delegation is configured:

```bash
# Test authentication
python main.py --validate-creds

# Test Gmail access (dry-run)
python main.py --dry-run --limit 5

# Full test
python main.py --limit 10
```

**Expected:** No `unauthorized_client` error, emails fetched successfully.

---

## Troubleshooting

### Error: "unauthorized_client"
**Cause:** Domain-wide delegation not configured
**Fix:** Complete Method 1 setup in Admin Console

### Error: "403 Forbidden"
**Cause:** Scopes don't match or wrong email
**Fix:** Verify scopes exactly match:
```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
```

### Error: "404 Not Found"
**Cause:** Service account deleted or Client ID incorrect
**Fix:** Verify Client ID: `117030078206154067665`

### Delegation Works But No Emails
**Cause:** Propagation delay
**Fix:** Wait 10-15 minutes after authorization

---

## Security Notes

✅ **Limited Scopes:** Only Gmail read/modify access
✅ **Single User:** Delegation only for `robert.d@consumrbuzz.com`
✅ **No Write Access:** Cannot send emails, only read/mark as read
✅ **Auditable:** All actions logged in Google Workspace audit logs

---

## Next Steps

**Immediate:**
1. Contact Google Workspace admin or access Admin Console yourself
2. Add Client ID `117030078206154067665` with Gmail scopes
3. Wait 10 minutes for propagation
4. Test with `python main.py --dry-run --limit 5`

**Alternative:**
Let me know if you want to implement OAuth2 user consent (Method 3) instead - this removes the Admin Console requirement but requires code changes.

---

## Quick Reference

| Item | Value |
|------|-------|
| Service Account | dcgmail-bot@dgautohub.iam.gserviceaccount.com |
| Client ID | 117030078206154067665 |
| Scopes | gmail.readonly, gmail.modify |
| Delegated User | robert.d@consumrbuzz.com |
| Admin Console | https://admin.google.com |
| Setup Time | 5 minutes + 10 min propagation |

---

**Unfortunately, there is NO gcloud CLI command to configure domain-wide delegation.** This is a deliberate security restriction by Google.

The Admin Console UI is the ONLY method to authorize domain-wide delegation for service accounts.
