import re
from collections import defaultdict

def parse_daily_dev(body):
    articles = []
    
    # 1. Find all daily.dev post URLs
    # Pattern: https://app.daily.dev/posts/[ID]...
    # We want the base URL up to the ID, ignoring query params for deduplication
    raw_links = re.findall(r'(https://app\.daily\.dev/posts/[a-zA-Z0-9]+)', body)
    unique_links = list(set(raw_links))
    
    print(f"DEBUG: Found {len(unique_links)} unique post links.")
    
    for url in unique_links:
        # 2. For each URL, find the text preceding it
        # We search for the specific URL (escape dots)
        safe_url = re.escape(url)
        
        # Pattern:
        # Capture text that doesn't start with a '(', to avoid capturing previous links
        # Text... \n ( URL )
        # We need to be careful about newlines.
        
        # Strategy: Find the URL index, look backwards to the previous double-newline or separator lines
        
        # Actually, let's use the explicit text-dump format we saw:
        # "Some Text ( URL )"
        # The text might span multiple lines, but usually not empty lines.
        
        pattern = r'((?:(?!\n\n|----\n).)+?)\s*\(\s*' + safe_url + r'.*?\)'
        matches = re.findall(pattern, body, re.DOTALL)
        
        # matches is a list of strings (the text before the link)
        
        cleaned_matches = []
        for m in matches:
            text = m.strip()
            # Remove leading newlines/spaces
            text = re.sub(r'[\r\n]+', ' ', text).strip()
            cleaned_matches.append(text)
            
        # Analyze matches
        # Usually: [Source, Title, "Read more ->"]
        # Or: [Title, "Read more ->"] if source is missing?
        
        title = "Unknown Article"
        source = "daily.dev"
        
        filtered = [m for m in cleaned_matches if "Read more" not in m and "Logo" not in m and "CodeRabbit" not in m]
        
        if len(filtered) >= 2:
            # Assume First is Source, Second is Title (Based on "Tech World With Milan ... Learn fundamentals")
            source = filtered[0]
            title = filtered[1]
        elif len(filtered) == 1:
            title = filtered[0]
        else:
            # If all were filtered (e.g. only Read more), skip
            continue
            
        articles.append({
            "title": title,
            "source": source,
            "url": url
        })
            
    return articles

with open("daily_dev_samples.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Mock processing per email
emails = content.split("=== SUBJECT:")
for e in emails[1:]:
    print("\n--- EMAIL ---")
    parsed = parse_daily_dev(e)
    for p in parsed:
        print(f"[{p['source']}] {p['title']} ({p['url']})")
