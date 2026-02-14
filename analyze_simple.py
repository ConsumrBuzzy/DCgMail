#!/usr/bin/env python3
"""
Email History Analyzer for DCGMail (Pydantic-Free Version)

This tool pulls down email history and analyzes patterns to help build
intelligent filters and categories with Claude's assistance.
"""

import sys
import json
import argparse
import os
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any

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

        # Buckets for our morning email
        digest_articles = []      # For "Dev_Articles" -> List of links
        summaries = defaultdict(int) # For "Infrastructure" -> Counts
        promos_filtered = 0       # For "Product_Updates" (marketing)
        promos_kept = []          # For "Product_Updates" (real updates)
        trash_count = 0           # For "Promotional"

        import re

        for email in self.emails:
            matched = False
            
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
                        digest_articles.append(email)
                    
                    elif action == "summarize":
                        key = cat_name
                        if "ovh" in email.sender.lower(): key = "OVH Infrastructure"
                        if "zoom" in email.sender.lower(): key = "Zoom Status"
                        if "convoso" in email.sender.lower(): key = "Convoso Ops"
                        summaries[key] += 1
                        
                    elif action == "filter_marketing":
                        # If "welcome" or "last chance" in subject -> Trash it
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
            # Sort by Sender
            digest_articles.sort(key=lambda x: x.sender)
            
            current_sender = None
            for email in digest_articles:
                sender_name = email.sender.split('<')[0].strip('" ').strip()
                if sender_name != current_sender:
                    lines.append(f"\n### {sender_name}")
                    current_sender = sender_name
                
                lines.append(f"- [{email.subject}](https://mail.google.com/mail/u/0/#inbox/{email.id})")
            lines.append("")

        # 2. Product Updates (Kept)
        if promos_kept:
            lines.append("## 🚀 Product Updates")
            # Sort by Sender
            promos_kept.sort(key=lambda x: x.sender)
            
            for email in promos_kept:
                sender_name = email.sender.split('<')[0].strip('" ').strip()
                # Highlight Google/Cloud
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
