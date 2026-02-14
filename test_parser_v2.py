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
        # We process the first 2 occurrences found (Source, Title)
        # Sometimes there's only 1 (if layouts change), but usually 2+
        
        # Helper to extract text block before a line index
        def get_text_block(start_index):
            block = []
            # Start from line *before* the link line
            curr = start_index - 1
            while curr >= 0:
                text = lines[curr].strip()
                if not text: # Empty line
                    if block: break # Stop if we already have content
                    # If we don't have content yet, keep going (skip trailing empty lines)
                elif text.startswith('---'): # Separator
                    break
                elif text.startswith('(') and ')' in text: # Another link
                    break
                else:
                    block.insert(0, text) # Prepend
                
                # Safety break for long blocks
                if len(block) > 5: break
                curr -= 1
            return " ".join(block)

        # Candidate 1: Source (usually the first occurrence)
        candidate1 = ""
        candidate2 = ""
        
        if len(indices) > 0:
            candidate1 = get_text_block(indices[0])
            
        if len(indices) > 1:
            candidate2 = get_text_block(indices[1])
            
        # Logic to determine which is Title
        # Usually: 
        # Occ 1: "Source Name"
        # Occ 2: "Title of Article"
        # Occ 3: "Read more" (Empty block or "Read more")
        
        title = candidate2 if candidate2 else candidate1
        source = candidate1 if candidate2 else "daily.dev"
        
        # Filters
        if "Read more" in title or "Logo" in title: continue
        if not title: continue
        
        # Cleanup
        # If title starts with "You might find...", remove it (it's a header)
        if "You might find these articles interesting" in title:
            # The source is usually afterwards? 
            # Actually in the sample: 
            # "You might find these articles interesting"
            # (Link)
            # "Tech World..."
            # (Link)
            # So "You might..." is associated with a link? No.
            # Wait, line 16 has a link but NO text before it except the header.
            # That link is likely the "Feed" link, not a specific post?
            # No, it looks like a post link.
            pass

        # If title matches source, and looks like a name, accept it.
        
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
