"""
src/categorizer.py - Regex-based email categorizer.

Implements the Categorizer interface from interfaces.py.
Loads rules from config/categories.json and uses regex patterns
to match emails by subject, snippet, and sender address.
"""

import json
import re
from pathlib import Path
from typing import Dict, List

from src.interfaces import (
    Categorizer,
    CategorizedEmail,
    CategorizerError,
    Email,
)

_DEFAULT_CATEGORY = "Uncategorized"


class RegexCategorizer(Categorizer):
    """Categorize emails using regex rules loaded from a JSON config file."""

    def __init__(self, config_path: str = "./config/categories.json"):
        """
        Load category rules from the JSON config.

        Args:
            config_path: Path to the categories JSON file.

        Raises:
            CategorizerError: If the config file is missing or malformed.
        """
        self._rules: Dict[str, dict] = {}
        self._load_rules(config_path)

    def _load_rules(self, config_path: str) -> None:
        """
        Parse the JSON config and pre-compile regex patterns.

        Each category entry is expected to have:
          - patterns: list of regex strings matched against subject + snippet
          - senders: list of regex strings matched against sender address
          - priority: integer (lower = higher priority)
        """
        path = Path(config_path)
        if not path.exists():
            raise CategorizerError(f"Categories config not found: {config_path}")

        try:
            with open(path) as fh:
                raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise CategorizerError(f"Invalid JSON in {config_path}: {exc}") from exc

        for category, rule in raw.items():
            self._rules[category] = {
                "patterns": [re.compile(p) for p in rule.get("patterns", [])],
                "senders": [re.compile(s) for s in rule.get("senders", [])],
                "priority": rule.get("priority", 50),
            }

    # ------------------------------------------------------------------
    # Categorizer interface
    # ------------------------------------------------------------------

    def categorize(self, email: Email) -> str:
        """
        Assign a single category to an email.

        Matching logic:
          1. Check sender regexes first (more specific).
          2. Check subject + snippet regexes.
          3. If multiple categories match, pick the one with the lowest
             priority number (highest priority).
          4. Fall back to 'Uncategorized'.

        Args:
            email: The email to categorize.

        Returns:
            Category name string.
        """
        result = self._match(email)
        return result[0]

    def categorize_batch(self, emails: List[Email]) -> List[CategorizedEmail]:
        """
        Categorize a list of emails and return CategorizedEmail objects.

        Args:
            emails: List of Email instances.

        Returns:
            List of CategorizedEmail instances with confidence and reason.
        """
        results: List[CategorizedEmail] = []
        for email in emails:
            category, confidence, reason = self._match(email)
            results.append(
                CategorizedEmail(
                    email=email,
                    category=category,
                    confidence=confidence,
                    reason=reason,
                )
            )
        return results

    def get_categories(self) -> List[str]:
        """
        Return all categories defined in the config, plus the fallback.

        Returns:
            Sorted list of category names.
        """
        return sorted(self._rules.keys()) + [_DEFAULT_CATEGORY]

    # ------------------------------------------------------------------
    # Internal matching
    # ------------------------------------------------------------------

    def _match(self, email: Email) -> tuple:
        """
        Run all rules against an email and return the best match.

        Returns:
            (category, confidence, reason) tuple.
        """
        matches: List[tuple] = []
        text = f"{email.subject} {email.snippet}"

        for category, rule in self._rules.items():
            # Check sender patterns
            for pattern in rule["senders"]:
                if pattern.search(email.sender):
                    matches.append(
                        (category, 1.0, f"Sender matched: {pattern.pattern}", rule["priority"])
                    )

            # Check content patterns
            for pattern in rule["patterns"]:
                if pattern.search(text):
                    matches.append(
                        (category, 0.8, f"Pattern matched: {pattern.pattern}", rule["priority"])
                    )

        if not matches:
            return (_DEFAULT_CATEGORY, 0.0, "No rules matched")

        # Sort by priority (ascending) then confidence (descending)
        matches.sort(key=lambda m: (m[3], -m[1]))
        best = matches[0]
        return (best[0], best[1], best[2])
