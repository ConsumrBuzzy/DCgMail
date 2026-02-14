import re

def parse_daily_dev(body):
    articles = []
    lines = body.split('\n')
    
    # Map URL -> List of (LineIndex, LineContent)
    url_occurrences = {}
    
    for i, line in enumerate(lines):
        # Find daily.dev post link
        match = re.search(r'(https://app\.daily\.dev/posts/[a-zA-Z0-9]+)', line)
        if match:
            url = match.group(1)
            if url not in url_occurrences:
                url_occurrences[url] = []
            url_occurrences[url].append(i)
            
    # Process each URL
    for url, indices in url_occurrences.items():
        candidates = []
        
        # Helper to extract text block before a line index
        def get_text_block(start_index):
            block = []
            curr = start_index - 1
            while curr >= 0:
                text = lines[curr].strip()
                if not text: 
                    if block: break 
                elif text.startswith('---'): break
                elif text.startswith('(') and ')' in text: break
                else:
                    block.insert(0, text)
                if len(block) > 5: break
                curr -= 1
            return " ".join(block)

        for idx in indices:
            candidates.append(get_text_block(idx))
            
        # Filter candidates
        # Remove empty, Headers, Read More, Logos
        valid = []
        for c in candidates:
            if not c: continue
            if "You might find" in c: continue
            if "Read more" in c: continue
            if "Logo" in c: continue
            if "Daily Dev Ltd" in c: continue
            if "CodeRabbit" in c: continue # Ads
            if "Get Started Today" in c: continue # Ads
            valid.append(c)
            
        if len(valid) >= 2:
            # Assume [Source, Title]
            source = valid[0]
            title = valid[1]
        elif len(valid) == 1:
            # Assume [Title] (Source might be part of it or missing)
            title = valid[0]
            source = "daily.dev"
        else:
            continue
            
        articles.append({
            "title": title,
            "source": source,
            "url": url
        })

    return articles

with open("daily_dev_samples.txt", "r", encoding="utf-8") as f:
    content = f.read()

emails = content.split("=== SUBJECT:")
for e in emails[1:]:
    print("\n--- EMAIL ---")
    parsed = parse_daily_dev(e)
    for p in parsed:
        print(f"[{p['source']}] {p['title']} ({p['url']})")
