#!/usr/bin/env python3
"""
Email History Analyzer for DCGMail (Pydantic-Free Version)

This tool pulls down email history and analyzes patterns to help build
intelligent filters and categories with Claude's assistance.
"""

import sys
import json
import base64
import argparse
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# Import interfaces and providers (Pydantic-free)
from src.interfaces import ConfigProvider, ConfigError, Email, Logger
from src.providers.gmail_provider import GmailProvider
from src.providers.gmail_oauth_provider import GmailOAuth2Provider
from src.loggers.file_logger import FileLogger

# ----------------------------------------------------------------------------
# Simple Config Provider (Analysis Only)
# ----------------------------------------------------------------------------
class SimpleConfigProvider(ConfigProvider):
    """
    Simple environment variable wrapper that doesn't use Pydantic.
    """
    def __init__(self):
        # Load .env manually if python-dotenv is available, otherwise assume env vars are set
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
            
    def get(self, key: str, default: str = None) -> str:
        # Convert key to env var format (e.g. "gmail_auth_type" -> "GMAIL_AUTH_TYPE")
        env_key = key.upper().replace("-", "_")
        val = os.environ.get(env_key)
        return val if val is not None else default

    def get_required(self, key: str) -> str:
        val = self.get(key)
        if not val:
            raise ConfigError(f"Missing required config: {key}")
        return val


class EmailAnalyzer:
    """Analyzes email history to discover patterns and suggest filters."""

    def __init__(self, provider, logger):
        self.provider = provider
        self.logger = logger
        self.emails = []
        self.analysis = {}

    def fetch_history(self, days: int = 30, limit: int = 500) -> List[Email]:
        self.logger.info(f"Fetching email history: {days} days, limit {limit}")
        try:
            self.provider.authenticate()
            self.logger.info("Fetching emails...")
            self.emails = self.provider.fetch_unread(limit=limit)
            self.logger.info(f"Fetched {len(self.emails)} emails for analysis")
            return self.emails
        except Exception as e:
            self.logger.error(f"Failed to fetch email history: {e}")
            return []

    def analyze_senders(self) -> Dict[str, Any]:
        self.logger.info("Analyzing sender patterns...")
        senders = [email.sender for email in self.emails]
        sender_counts = Counter(senders)
        
        domains = []
        for sender in senders:
            if '<' in sender and '>' in sender:
                email_part = sender.split('<')[1].split('>')[0]
            else:
                email_part = sender
            
            if '@' in email_part:
                domain = email_part.split('@')[1]
                domains.append(domain)
                
        domain_counts = Counter(domains)
        return {
            "total_unique_senders": len(sender_counts),
            "top_senders": sender_counts.most_common(50),
            "total_unique_domains": len(domain_counts),
            "top_domains": domain_counts.most_common(50),
        }

    def analyze_actions(self, categories_path: str) -> str:
        """
        Categorize emails based on config and generate a 'Morning Summary'.
        """
        self.logger.info("Generating Morning Summary...")
        
        # Load categories
        try:
            with open(categories_path, 'r') as f:
                categories = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load categories: {e}")
            return "Error loading configuration."

        # Import parser
        try:
            from src.parsers.daily_dev_parser import parse_daily_dev
        except ImportError:
            self.logger.warning("Could not import daily_dev_parser")
            parse_daily_dev = lambda x: []

        for email in self.emails:
            matched = False
            
            # Special handling for daily.dev to extract articles
            if "daily.dev" in email.sender.lower() and "digest" in email.subject.lower():
                # Parse body
                # We need the body, but Email object might only have snippet
                # Reread 'fetch' to ensure we get body? 
                # GmailProvider _parse_email does extract body.
                # But 'Email' struct doesn't have 'body' field in __init__? 
                # Let's check 'src/providers/gmail_oauth_provider.py' _parse_email
                # It calls _extract_body but does it save it?
                # The Email dataclass definition isn't visible here, but let's assume I need to fetch it or it's there.
                # Actually, check interfaces.py? No, let's just assume we need to add it or it exists.
                # Wait, the Email class in interfaces.py probably doesn't have 'body'.
                # I should probably add 'body' to Email class or just re-fetch here?
                # Re-fetching is slow. Let's look at interfaces.py first.
                pass 
                
            # Check against categories
            for cat_name, rules in categories.items():
                if matched: break
                
                action = rules.get("action", "none")
                patterns = rules.get("patterns", [])
                senders = rules.get("senders", [])
                
                # Check Sender OR Pattern
                is_sender = any(s in email.sender for s in senders)
                is_pattern = any(re.search(p, email.subject, re.IGNORECASE) or re.search(p, email.sender, re.IGNORECASE) for p in patterns)
                
                if is_sender or is_pattern:
                    matched = True
                    
                    if action == "digest":
                        # If it's a daily.dev email, we want to PARSE it, not just list it.
                        if "daily.dev" in email.sender:
                            # We need the full body. 
                            # The 'Email' object from fetch_history might not have it if I didn't verify it.
                            # In 'gmail_oauth_provider.py', the Email object is created.
                            # Let's rely on the provider having put the body in... somewhere?
                            # Actually, looking at previous view_file of gmail_oauth_provider, 
                            # Email(id=..., sender=..., subject=..., snippet=..., timestamp=..., read=..., labels=...)
                            # It DOES NOT store the body.
                            # I need to modify the Email class and the Provider to store the body.
                            pass

                        digest_articles.append({
                            "sender": email.sender,
                            "subject": email.subject,
                            "url": f"https://mail.google.com/mail/u/0/#inbox/{email.id}",
                            "timestamp": email.timestamp
                        })
                    
                    elif action == "summarize":
                        key = cat_name
                        if "ovh" in email.sender.lower(): key = "OVH Infrastructure"
                        if "zoom" in email.sender.lower(): key = "Zoom Status"
                        if "convoso" in email.sender.lower(): key = "Convoso Ops"
                        summaries[key] += 1
                        
                    elif action == "filter_marketing":
                        if re.search(r"welcome|last chance|webinar|join us", email.subject, re.IGNORECASE):
                            trash_count += 1
                        else:
                            promos_kept.append(email)
                            
                    elif action == "trash":
                        trash_count += 1

            if not matched:
                pass

        # === GENERATE THE EMAIL BODY ===
        lines = []
        lines.append(f"# 🌅 Morning Catch-Up: {datetime.now().strftime('%A, %b %d')}")
        lines.append("")
        
        # 1. High Priority Digest (Dev Articles)
        if digest_articles:
            lines.append("## 📚 Reads for Today")
            
            # Separate parsed vs generic
            # Actually, I need to fetch bodies for daily.dev emails NOW.
            # This is inefficient but safe: fetch the body if I need it.
            # Or better: Update Email class to have 'body'.
            # For now, I will use the provider to fetch the specific message body if it's daily.dev
            
            # Let's sort generic articles
            digest_articles.sort(key=lambda x: x['sender'])
            
            parsed_articles = []
            generic_articles = []
            
            for item in digest_articles:
                if "daily.dev" in item['sender']:
                     # Fetch body
                     try:
                         # Hacky access to provider
                         if hasattr(self.provider, 'service'):
                             msg = self.provider.service.users().messages().get(userId='me', id=item['url'].split('/')[-1], format='full').execute()
                             body = self.provider._extract_body(msg['payload'])
                             parsed = parse_daily_dev(body)
                             for p in parsed:
                                 parsed_articles.append({
                                     "sender": p['source'], # Use the extracted source!
                                     "subject": p['title'],
                                     "url": p['url'],
                                     "timestamp": item['timestamp']
                                 })
                     except Exception as e:
                         self.logger.error(f"Failed to parse daily.dev: {e}")
                         # Fallback
                         generic_articles.append(item)
                else:
                    generic_articles.append(item)

            # Combine
            all_items = parsed_articles + generic_articles
            # Unique by URL
            unique = {x['url']: x for x in all_items}.values()
            all_items = sorted(list(unique), key=lambda x: x['sender'])
            
            current_sender = None
            for item in all_items:
                sender_name = item['sender'].split('<')[0].strip('" ').strip()
                if sender_name != current_sender:
                    lines.append(f"\n### {sender_name}")
                    current_sender = sender_name
                
                lines.append(f"- [{item['subject']}]({item['url']})")
            lines.append("")

        # 2. Product Updates (Kept)
        if promos_kept:
            lines.append("## 🚀 Product Updates")
            promos_kept.sort(key=lambda x: x.sender)
            
            for email in promos_kept:
                sender_name = email.sender.split('<')[0].strip('" ').strip()
                icon = "☁️" if "google" in sender_name.lower() or "cloud" in sender_name.lower() else "🔹"
                lines.append(f"- {icon} **{sender_name}**: {email.subject}")
            lines.append("")

        # 3. Operational Summaries
        if summaries:
            lines.append("## 🛡️ Ops & Infrastructure")
            for k, v in summaries.items():
                lines.append(f"- **{k}**: {v} events")
            lines.append("")

        # 4. Filter Stats
        lines.append("## 🧹 Auto-Filtered")
        lines.append(f"- **Junk/Promos Removed:** {trash_count} emails")
        lines.append(f"- **Infrastructure Logs Archived:** {sum(summaries.values())} emails")

        return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="DCGMail Morning Generator")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--simulate", action="store_true", help="Generate the email body without sending")
    parser.add_argument("--send", action="store_true", help="Send the generated email to yourself")
    args = parser.parse_args()

    # Setup logger
    logger = FileLogger(name="MorningGen", level="INFO")
    
    # Setup config
    config = SimpleConfigProvider()
    
    logger.info("Initializing Gmail Provider...")
    if Path("./credentials/oauth_client.json").exists():
        provider = GmailOAuth2Provider(
            oauth_client_path="./credentials/oauth_client.json",
            token_path="./credentials/token.json",
            logger=logger
        )
    else:
        provider = GmailProvider(config=config, logger=logger)

    analyzer = EmailAnalyzer(provider, logger)
    
    print(f"Fetching {args.limit} emails...")
    analyzer.fetch_history(days=args.days, limit=args.limit)
    
    # Generate content
    report = analyzer.analyze_actions("config/categories.json")
    
    if args.simulate:
        print("\n" + "="*60)
        print(report)
        print("="*60 + "\n")
        
        with open("morning_brief.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("Draft saved to morning_brief.md")
        
    if args.send:
        print("Sending Morning Brief...")
        # Get user email - provider probably knows it or we assume 'me'
        # Gmail API 'me' alias works for authenticated user
        
        # Simple Markdown -> HTML conversion for the actual send
        # (The provider now has rudimentary handling, but let's improve the text passed to it slightly if needed)
        
        subject = f"🌅 Morning Catch-Up: {datetime.now().strftime('%A, %b %d')}"
        
        try:
            # We need to get the user's email address to send TO them
            # We can just use 'me' usually, but better to be explicit if possible
            # But the provider's send_email takes a 'to' address. 
            # Let's try to get profile, or just use the one from config
            user_profile = provider.service.users().getProfile(userId='me').execute()
            user_email = user_profile['emailAddress']
            
            provider.send_email(to_email=user_email, subject=subject, body=report)
            print(f"✅ Email sent successfully to {user_email}!")
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")

    if not args.simulate and not args.send:
        print("Please use --simulate to preview or --send to deliver.")

if __name__ == "__main__":
    main()
