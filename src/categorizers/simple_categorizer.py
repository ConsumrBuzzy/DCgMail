"""
Simple regex-based email categorizer for DCGMail.

Based on TeleseroBalancerOct2025's categorization patterns.
Implements the Categorizer interface from src/interfaces.py.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any

from src.interfaces import (
    Categorizer,
    Email,
    CategorizedEmail,
    ConfigError,
    Logger,
)


class SimpleCategorizer(Categorizer):
    """
    Simple regex-based categorizer using rules from JSON config.

    Matches emails against patterns and sender domains with priority-based selection.
    """

    def __init__(self, config_path: str, logger: Logger):
        """
        Initialize categorizer with rules from config file.

        Args:
            config_path: Path to categories.json config file
            logger: Logger instance

        Raises:
            ConfigError: If config file missing or invalid JSON
        """
        self.logger = logger
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise ConfigError(
                f"Categories config not found: {config_path}. "
                f"Create this file with categorization rules."
            )

        try:
            with open(self.config_path, encoding='utf-8') as f:
                self.categories = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {config_path}: {e}")

        self.logger.info(f"Loaded {len(self.categories)} categories from config")

    def categorize(self, email: Email) -> str:
        """
        Assign category to single email based on rules.

        Args:
            email: Email to categorize

        Returns:
            Category name (string)
        """
        matches = []

        for category, rules in self.categories.items():
            if self._matches_rules(email, rules):
                priority = rules.get("priority", 999)
                matches.append((category, priority))
                self.logger.debug(
                    f"Email {email.id} matched category '{category}' (priority {priority})"
                )

        if not matches:
            self.logger.debug(f"Email {email.id} uncategorized")
            return "Uncategorized"

        # Sort by priority (lowest number = highest priority)
        matches.sort(key=lambda x: x[1])
        selected_category = matches[0][0]

        self.logger.debug(
            f"Email {email.id} categorized as '{selected_category}' "
            f"({len(matches)} matches, priority {matches[0][1]})"
        )

        return selected_category

    def categorize_batch(self, emails: List[Email]) -> List[CategorizedEmail]:
        """
        Categorize multiple emails.

        Args:
            emails: List of Email objects

        Returns:
            List of CategorizedEmail objects with confidence scores
        """
        results = []

        for email in emails:
            category = self.categorize(email)
            confidence = 1.0 if category != "Uncategorized" else 0.0

            results.append(CategorizedEmail(
                email=email,
                category=category,
                confidence=confidence,
                reason=f"Matched rules for '{category}'" if confidence > 0 else "No matching rules"
            ))

        self.logger.info(
            f"Categorized {len(emails)} emails: "
            f"{sum(1 for r in results if r.confidence > 0)} matched, "
            f"{sum(1 for r in results if r.confidence == 0)} uncategorized"
        )

        return results

    def get_categories(self) -> List[str]:
        """
        Return all category names from config.

        Returns:
            List of category names
        """
        return list(self.categories.keys())

    def _matches_rules(self, email: Email, rules: Dict[str, Any]) -> bool:
        """
        Check if email matches categorization rules.

        Args:
            email: Email to check
            rules: Category rules dict with 'patterns' and 'senders'

        Returns:
            True if email matches all specified rules
        """
        # Check sender rules (if specified)
        senders = rules.get("senders", [])
        if senders:
            if not self._matches_sender(email.sender, senders):
                return False

        # Check pattern rules (if specified)
        patterns = rules.get("patterns", [])
        if patterns:
            # Combine subject and snippet for pattern matching
            text = f"{email.subject} {email.snippet}".lower()

            if not self._matches_patterns(text, patterns):
                return False

        # If we got here, all specified rules matched
        # (or there were no rules, which also counts as a match)
        return True

    def _matches_sender(self, sender: str, allowed_senders: List[str]) -> bool:
        """
        Check if sender email matches allowed list.

        Supports:
        - Domain matching: @company.com matches any sender from that domain
        - Exact matching: exact email address

        Args:
            sender: Email sender (e.g., "John Doe <john@company.com>")
            allowed_senders: List of allowed senders/domains

        Returns:
            True if sender matches any allowed sender
        """
        # Extract email from "Name <email>" format
        email_match = re.search(r'<(.+?)>', sender)
        if email_match:
            sender_email = email_match.group(1).lower()
        else:
            sender_email = sender.lower()

        for allowed in allowed_senders:
            if allowed.startswith("@"):
                # Domain match: @company.com
                if sender_email.endswith(allowed.lower()):
                    return True
            else:
                # Exact match
                if sender_email == allowed.lower():
                    return True

        return False

    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """
        Check if text matches any of the regex patterns.

        Args:
            text: Text to search (already lowercase)
            patterns: List of regex patterns

        Returns:
            True if any pattern matches
        """
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error as e:
                # Invalid regex pattern - log warning and skip
                self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                continue

        return False
