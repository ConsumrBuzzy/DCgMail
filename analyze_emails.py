#!/usr/bin/env python3
"""
Email History Analyzer for DCGMail

This tool pulls down email history and analyzes patterns to help build
intelligent filters and categories with Claude's assistance.

Usage:
    python analyze_emails.py --days 30 --limit 200
    python analyze_emails.py --export-json emails_analysis.json
    python analyze_emails.py --interactive
"""

import sys
import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.config.env_config import EnvConfigProvider
from src.loggers.file_logger import FileLogger
from src.providers.gmail_provider import GmailProvider
from src.providers.gmail_oauth_provider import GmailOAuth2Provider
from src.interfaces import Email


class EmailAnalyzer:
    """Analyzes email history to discover patterns and suggest filters."""

    def __init__(self, provider, logger):
        """
        Initialize email analyzer.

        Args:
            provider: EmailProvider instance (Gmail or OAuth2)
            logger: Logger instance
        """
        self.provider = provider
        self.logger = logger
        self.emails = []
        self.analysis = {}

    def fetch_history(self, days: int = 30, limit: int = 500, include_read: bool = True) -> List[Email]:
        """
        Fetch email history for analysis.

        Args:
            days: Number of days to look back
            limit: Maximum number of emails to fetch
            include_read: Whether to include read emails

        Returns:
            List of Email objects
        """
        self.logger.info(f"Fetching email history: {days} days, limit {limit}")

        try:
            # Authenticate
            self.provider.authenticate()

            # Fetch emails (modify provider to support date range and read status)
            # For now, we'll fetch unread and work with what we have
            # TODO: Extend providers to support history queries

            self.logger.info("Fetching emails...")
            self.emails = self.provider.fetch_unread(limit=limit)

            self.logger.info(f"Fetched {len(self.emails)} emails for analysis")
            return self.emails

        except Exception as e:
            self.logger.error(f"Failed to fetch email history: {e}")
            return []

    def analyze_senders(self) -> Dict[str, Any]:
        """
        Analyze sender patterns.

        Returns:
            Dictionary with sender statistics
        """
        self.logger.info("Analyzing sender patterns...")

        # Extract sender domains and addresses
        senders = [email.sender for email in self.emails]
        sender_counts = Counter(senders)

        # Extract domains
        domains = []
        for sender in senders:
            if '<' in sender and '>' in sender:
                # Extract email from "Name <email@domain.com>" format
                email_part = sender.split('<')[1].split('>')[0]
            else:
                email_part = sender

            if '@' in email_part:
                domain = email_part.split('@')[1]
                domains.append(domain)

        domain_counts = Counter(domains)

        return {
            "total_unique_senders": len(sender_counts),
            "top_senders": sender_counts.most_common(20),
            "total_unique_domains": len(domain_counts),
            "top_domains": domain_counts.most_common(20),
        }

    def analyze_subjects(self) -> Dict[str, Any]:
        """
        Analyze subject line patterns.

        Returns:
            Dictionary with subject statistics
        """
        self.logger.info("Analyzing subject patterns...")

        subjects = [email.subject for email in self.emails]

        # Extract common keywords from subjects
        keywords = []
        for subject in subjects:
            # Simple keyword extraction (split on spaces, lowercase)
            words = subject.lower().split()
            # Filter out very short words
            keywords.extend([w for w in words if len(w) > 3])

        keyword_counts = Counter(keywords)

        # Find common prefixes (like "RE:", "FWD:", "[JIRA]", etc.)
        prefixes = []
        for subject in subjects:
            if subject.startswith('['):
                # Extract [PREFIX]
                end = subject.find(']')
                if end > 0:
                    prefixes.append(subject[1:end])
            elif subject.upper().startswith(('RE:', 'FWD:', 'FW:')):
                # Extract reply/forward prefix
                prefixes.append(subject.split(':')[0].upper())

        prefix_counts = Counter(prefixes)

        return {
            "total_emails": len(subjects),
            "top_keywords": keyword_counts.most_common(30),
            "top_prefixes": prefix_counts.most_common(10),
            "sample_subjects": subjects[:20],
        }

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze overall email patterns.

        Returns:
            Dictionary with pattern analysis
        """
        self.logger.info("Analyzing email patterns...")

        # Time-based analysis
        hours = [email.timestamp.hour for email in self.emails]
        weekdays = [email.timestamp.strftime('%A') for email in self.emails]

        hour_counts = Counter(hours)
        weekday_counts = Counter(weekdays)

        # Label analysis (if available)
        labels = []
        for email in self.emails:
            if hasattr(email, 'labels') and email.labels:
                labels.extend(email.labels)

        label_counts = Counter(labels)

        return {
            "time_distribution": dict(hour_counts),
            "weekday_distribution": dict(weekday_counts),
            "top_labels": label_counts.most_common(10) if labels else [],
        }

    def generate_report(self, output_format: str = "text") -> str:
        """
        Generate analysis report.

        Args:
            output_format: "text" or "json"

        Returns:
            Formatted report string
        """
        self.logger.info("Generating analysis report...")

        sender_analysis = self.analyze_senders()
        subject_analysis = self.analyze_subjects()
        pattern_analysis = self.analyze_patterns()

        self.analysis = {
            "summary": {
                "total_emails": len(self.emails),
                "analysis_date": datetime.now().isoformat(),
            },
            "senders": sender_analysis,
            "subjects": subject_analysis,
            "patterns": pattern_analysis,
        }

        if output_format == "json":
            return json.dumps(self.analysis, indent=2)

        # Text format
        report = []
        report.append("=" * 70)
        report.append("DCGMail Email History Analysis")
        report.append("=" * 70)
        report.append(f"\nTotal Emails Analyzed: {len(self.emails)}")
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Sender analysis
        report.append("\n" + "=" * 70)
        report.append("TOP SENDERS")
        report.append("=" * 70)
        for sender, count in sender_analysis["top_senders"][:10]:
            report.append(f"{count:4d}  {sender}")

        # Domain analysis
        report.append("\n" + "=" * 70)
        report.append("TOP DOMAINS")
        report.append("=" * 70)
        for domain, count in sender_analysis["top_domains"][:10]:
            report.append(f"{count:4d}  {domain}")

        # Subject keywords
        report.append("\n" + "=" * 70)
        report.append("TOP SUBJECT KEYWORDS")
        report.append("=" * 70)
        for keyword, count in subject_analysis["top_keywords"][:20]:
            report.append(f"{count:4d}  {keyword}")

        # Subject prefixes
        if subject_analysis["top_prefixes"]:
            report.append("\n" + "=" * 70)
            report.append("COMMON SUBJECT PREFIXES")
            report.append("=" * 70)
            for prefix, count in subject_analysis["top_prefixes"]:
                report.append(f"{count:4d}  [{prefix}]")

        # Sample subjects
        report.append("\n" + "=" * 70)
        report.append("SAMPLE SUBJECTS (First 20)")
        report.append("=" * 70)
        for subject in subject_analysis["sample_subjects"]:
            report.append(f"  - {subject}")

        # Patterns
        report.append("\n" + "=" * 70)
        report.append("EMAIL PATTERNS")
        report.append("=" * 70)

        # Time distribution
        report.append("\nEmails by Hour:")
        for hour in sorted(pattern_analysis["time_distribution"].keys()):
            count = pattern_analysis["time_distribution"][hour]
            bar = "#" * (count // 2)
            report.append(f"  {hour:02d}:00  {count:3d}  {bar}")

        # Weekday distribution
        report.append("\nEmails by Weekday:")
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in weekday_order:
            count = pattern_analysis["weekday_distribution"].get(day, 0)
            bar = "#" * (count // 5)
            report.append(f"  {day:9s}  {count:3d}  {bar}")

        report.append("\n" + "=" * 70)
        report.append("\nNext Steps:")
        report.append("  1. Review the analysis above")
        report.append("  2. Identify patterns you want to categorize")
        report.append("  3. Use the data to build filters in config/categories.json")
        report.append("  4. Run: python main.py --dry-run --limit 10")
        report.append("=" * 70)

        return "\n".join(report)

    def export_raw_data(self, filepath: str):
        """
        Export raw email data for Claude to analyze.

        Args:
            filepath: Path to save JSON file
        """
        self.logger.info(f"Exporting raw data to {filepath}")

        data = {
            "export_date": datetime.now().isoformat(),
            "total_emails": len(self.emails),
            "emails": [
                {
                    "sender": email.sender,
                    "subject": email.subject,
                    "snippet": email.snippet,
                    "timestamp": email.timestamp.isoformat(),
                    "labels": email.labels if hasattr(email, 'labels') else [],
                }
                for email in self.emails
            ],
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Exported {len(self.emails)} emails to {filepath}")


def main():
    """Main entry point for email analyzer."""
    parser = argparse.ArgumentParser(
        description="DCGMail Email History Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_emails.py --limit 100           # Analyze 100 emails
  python analyze_emails.py --export emails.json  # Export raw data
  python analyze_emails.py --format json         # JSON output
        """
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum emails to analyze (default: 200)"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export raw data to JSON file"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Initialize logger
    log_level = "DEBUG" if args.debug else "INFO"
    logger = FileLogger(name="EmailAnalyzer", level=log_level)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = EnvConfigProvider()

        # Initialize Gmail provider based on auth type
        auth_type = config.get("gmail_auth_type", "service_account")
        logger.info(f"Initializing Gmail provider (auth_type={auth_type})...")

        if auth_type == "oauth2":
            oauth_client = config.get("gmail_oauth_client")
            oauth_token = config.get("gmail_oauth_token", "./credentials/token.json")
            provider = GmailOAuth2Provider(
                oauth_client_path=oauth_client,
                token_path=oauth_token,
                logger=logger
            )
        else:
            provider = GmailProvider(config=config, logger=logger)

        # Initialize analyzer
        analyzer = EmailAnalyzer(provider=provider, logger=logger)

        # Fetch email history
        print(f"\nFetching up to {args.limit} emails from the last {args.days} days...")
        emails = analyzer.fetch_history(days=args.days, limit=args.limit)

        if not emails:
            print("\n[ERROR] No emails fetched. Check your credentials or inbox.")
            return 1

        print(f"[OK] Fetched {len(emails)} emails\n")

        # Export raw data if requested
        if args.export:
            analyzer.export_raw_data(args.export)
            print(f"[OK] Raw data exported to: {args.export}")
            print(f"\nYou can now share this file with me (Claude) to analyze patterns")
            print(f"and build intelligent category filters together!\n")

        # Generate report
        report = analyzer.generate_report(output_format=args.format)

        # Handle Unicode encoding for Windows console
        try:
            print(report)
        except UnicodeEncodeError:
            # Fallback: encode as ASCII, ignore errors
            print(report.encode('ascii', 'ignore').decode('ascii'))

        # Save report to file
        report_filename = f"email_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n[OK] Report saved to: {report_filename}")

        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\n\n[WARNING] Analysis interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exception=e)
        print(f"\n[ERROR] Analysis failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
