# Intelligent Category Suggestions for Your Inbox

Based on analysis of 50 emails, here are recommended categories and filters:

---

## 📊 Email Pattern Analysis

### Top Senders:
1. **OVHcloud Status** (10 emails) - Infrastructure notifications
2. **Zoom Status** (4 emails) - Service incidents
3. **monday.com** (5 emails) - Product updates & promotions
4. **daily.dev** (2 emails) - Tech newsletter
5. **Medium** (4 emails) - Article digests
6. **CoinGecko** (2 emails) - Crypto news

### Key Patterns:
- **Maintenance notifications** (15 occurrences of "maintenance")
- **Incident reports** (9 occurrences of "incident")
- **AI/Tech content** (multiple newsletters)
- **Service status updates** (Zoom, OVH)
- **Crypto/Blockchain** (Aave, CoinGecko)

---

## 🎯 Recommended Categories

### 1. **Infrastructure** (High Priority)
**Purpose:** Critical server/service alerts and maintenance
**Patterns:**
- Sender domains: `status-ovhcloud.com`, `zoomstatus.com`
- Subject keywords: `maintenance`, `incident`, `load balancer`, `public cloud`
- Labels: Service status updates

**Suggested Filters:**
```json
{
  "name": "Infrastructure",
  "patterns": [
    "status-ovhcloud\\.com",
    "zoomstatus\\.com",
    "maintenance",
    "incident",
    "load balancer",
    "public cloud"
  ],
  "priority": "high",
  "action": "notify"
}
```

### 2. **Tech Newsletters** (Medium Priority)
**Purpose:** Learning content, technical articles
**Patterns:**
- Sender domains: `daily.dev`, `medium.com`, `substack.com`
- Subject keywords: `AI`, `Docker`, `LLMs`, `system design`
- Labels: Educational content

**Suggested Filters:**
```json
{
  "name": "Tech Learning",
  "patterns": [
    "daily\\.dev",
    "medium\\.com",
    "substack\\.com",
    "docker",
    "\\bllm",
    "system design",
    "best practices"
  ],
  "priority": "medium",
  "action": "archive_weekly"
}
```

### 3. **Product Updates** (Low Priority)
**Purpose:** SaaS product announcements, new features
**Patterns:**
- Sender domains: `monday.com`, `warp.dev`, `google.com`
- Subject keywords: `product update`, `new feature`, `introducing`
- Labels: CATEGORY_UPDATES

**Suggested Filters:**
```json
{
  "name": "Product Updates",
  "patterns": [
    "monday\\.com",
    "warp\\.dev",
    "product update",
    "introducing",
    "new feature"
  ],
  "priority": "low",
  "action": "archive"
}
```

### 4. **Crypto/Blockchain** (Medium Priority)
**Purpose:** Crypto news, blockchain updates
**Patterns:**
- Sender domains: `coingecko.com`, `alchemy.com`
- Subject keywords: `aave`, `dao`, `blockchain`
- Labels: Crypto-related

**Suggested Filters:**
```json
{
  "name": "Crypto",
  "patterns": [
    "coingecko\\.com",
    "alchemy\\.com",
    "\\baave\\b",
    "\\bdao\\b",
    "blockchain",
    "cryptocurrency"
  ],
  "priority": "medium",
  "action": "archive"
}
```

### 5. **Promotional** (Low Priority)
**Purpose:** Marketing emails, promotions
**Patterns:**
- Gmail labels: CATEGORY_PROMOTIONS
- Subject keywords: Generic marketing language
- Sender patterns: Marketing automation platforms

**Suggested Filters:**
```json
{
  "name": "Promotional",
  "patterns": [
    "CATEGORY_PROMOTIONS",
    "limited time",
    "special offer",
    "discount"
  ],
  "priority": "low",
  "action": "trash"
}
```

### 6. **Work/Business** (High Priority)
**Purpose:** Work-related communications
**Patterns:**
- Sender domains: `convoso.com` (your business)
- Subject keywords: `lead drips`, business-specific
- Labels: Work-related

**Suggested Filters:**
```json
{
  "name": "Work",
  "patterns": [
    "convoso\\.com",
    "lead drips",
    "burnt osd"
  ],
  "priority": "high",
  "action": "notify"
}
```

---

## 📅 Time-Based Insights

**Peak Email Hours:**
- 15:00 (6 emails) - 3 PM
- 16:00 (5 emails) - 4 PM
- **Recommendation:** Schedule inbox review at 5 PM

**Peak Days:**
- Thursday (25 emails) - 50% of weekly volume
- Wednesday (13 emails)
- Friday (12 emails)
- **Recommendation:** Run DCGMail twice on Thursdays

---

## 🛠️ Implementation Plan

### Step 1: Update categories.json

Replace the current `config/categories.json` with the suggested filters above.

### Step 2: Test

```bash
python main.py --dry-run --limit 20
```

Review the categorization results and adjust patterns.

### Step 3: Deploy

```bash
# Run automatically
python main.py --limit 50

# Schedule with Task Scheduler (Windows)
# Or cron (Linux/Mac)
```

---

## 🎨 Advanced Categorization Ideas

### Smart Filters (Future Enhancement)

**1. Urgent Infrastructure Alerts**
- Pattern: `incident.*critical` OR `service.*down`
- Action: Immediate SMS notification
- Priority: URGENT

**2. Weekly Digest**
- Consolidate "Tech Newsletters" category
- Send single Telegram message every Monday
- Include top 5 articles

**3. Auto-Archive**
- After 7 days, move "Product Updates" to archive
- After 30 days, delete "Promotional"

**4. Smart Prioritization**
- Use sender frequency to adjust priority
- If sender emails >10x/day, reduce priority
- If sender never replied to, mark as noise

---

## 📈 Next Steps

1. **Review these suggestions** - Do they match your workflow?
2. **Customize patterns** - Add your specific keywords
3. **Test thoroughly** - Run dry-runs first
4. **Iterate** - Adjust based on results
5. **Automate** - Schedule DCGMail to run hourly/daily

---

## 🔧 Quick Implementation

Want me to automatically generate the `categories.json` file based on these suggestions?

Just say: "Generate the categories.json file"

Or customize: "I want to prioritize crypto emails and ignore promotional"

---

**Generated:** 2026-02-13
**Based on:** 50 emails analyzed
**Tool:** DCGMail Email Analyzer
