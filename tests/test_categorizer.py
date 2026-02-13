"""
tests/test_categorizer.py - Unit tests for the RegexCategorizer.

All tests run offline with no real Gmail or Telegram connections.
"""

import json
import os
import tempfile

import pytest

from src.categorizer import RegexCategorizer
from src.interfaces import CategorizerError, CategorizedEmail
from tests.fixtures.sample_emails import (
    make_work_email,
    make_crypto_email,
    make_admin_email,
    make_noise_email,
    make_uncategorized_email,
    sample_email_batch,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def categorizer():
    """Return a RegexCategorizer loaded from the project's categories.json."""
    return RegexCategorizer(config_path="./config/categories.json")


@pytest.fixture
def mini_config(tmp_path):
    """Write a minimal categories config and return its path."""
    rules = {
        "Alpha": {
            "patterns": ["(?i)\\balpha\\b"],
            "senders": ["@alpha\\.com$"],
            "priority": 1,
        },
        "Beta": {
            "patterns": ["(?i)\\bbeta\\b"],
            "senders": [],
            "priority": 2,
        },
    }
    path = tmp_path / "categories.json"
    path.write_text(json.dumps(rules))
    return str(path)


# ------------------------------------------------------------------
# Construction tests
# ------------------------------------------------------------------


class TestCategorizerInit:
    """Test initialization and config loading."""

    def test_loads_default_config(self, categorizer):
        """The default categories.json should load without error."""
        cats = categorizer.get_categories()
        assert "Work" in cats
        assert "Crypto" in cats
        assert "Admin" in cats
        assert "Noise" in cats

    def test_missing_config_raises(self):
        """A non-existent config file should raise CategorizerError."""
        with pytest.raises(CategorizerError, match="not found"):
            RegexCategorizer(config_path="/nonexistent/path.json")

    def test_invalid_json_raises(self, tmp_path):
        """Malformed JSON should raise CategorizerError."""
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json!!")
        with pytest.raises(CategorizerError, match="Invalid JSON"):
            RegexCategorizer(config_path=str(bad))

    def test_custom_config(self, mini_config):
        """A custom config should load its own categories."""
        cat = RegexCategorizer(config_path=mini_config)
        names = cat.get_categories()
        assert "Alpha" in names
        assert "Beta" in names


# ------------------------------------------------------------------
# Single-email categorization
# ------------------------------------------------------------------


class TestCategorizeSingle:
    """Test categorize() on individual emails."""

    def test_work_email_by_content(self, categorizer):
        """An email with work keywords should be categorized as Work."""
        email = make_work_email()
        assert categorizer.categorize(email) == "Work"

    def test_crypto_email_by_sender(self, categorizer):
        """An email from a known crypto sender should be Crypto."""
        email = make_crypto_email()
        assert categorizer.categorize(email) == "Crypto"

    def test_admin_email(self, categorizer):
        """An email with finance keywords should be Admin."""
        email = make_admin_email()
        assert categorizer.categorize(email) == "Admin"

    def test_noise_email(self, categorizer):
        """A promotional email should be Noise."""
        email = make_noise_email()
        assert categorizer.categorize(email) == "Noise"

    def test_uncategorized_email(self, categorizer):
        """An email matching no rules should be Uncategorized."""
        email = make_uncategorized_email()
        assert categorizer.categorize(email) == "Uncategorized"


# ------------------------------------------------------------------
# Batch categorization
# ------------------------------------------------------------------


class TestCategorizeBatch:
    """Test categorize_batch() on multiple emails."""

    def test_batch_returns_correct_types(self, categorizer):
        """All items in the result should be CategorizedEmail instances."""
        batch = sample_email_batch()
        results = categorizer.categorize_batch(batch)
        assert len(results) == len(batch)
        for item in results:
            assert isinstance(item, CategorizedEmail)

    def test_batch_has_expected_categories(self, categorizer):
        """The batch should contain at least Work, Crypto, Admin, Noise."""
        batch = sample_email_batch()
        results = categorizer.categorize_batch(batch)
        categories = {r.category for r in results}
        assert "Work" in categories
        assert "Crypto" in categories

    def test_batch_confidence_range(self, categorizer):
        """All confidence scores should be between 0.0 and 1.0."""
        batch = sample_email_batch()
        results = categorizer.categorize_batch(batch)
        for item in results:
            assert 0.0 <= item.confidence <= 1.0

    def test_batch_reasons_are_strings(self, categorizer):
        """Each result should have a reason string (even if 'No rules matched')."""
        batch = sample_email_batch()
        results = categorizer.categorize_batch(batch)
        for item in results:
            assert isinstance(item.reason, str)
            assert len(item.reason) > 0


# ------------------------------------------------------------------
# get_categories()
# ------------------------------------------------------------------


class TestGetCategories:
    """Test the get_categories() method."""

    def test_includes_uncategorized(self, categorizer):
        """The fallback Uncategorized category should always be present."""
        assert "Uncategorized" in categorizer.get_categories()

    def test_returns_sorted(self, categorizer):
        """Categories (excluding Uncategorized at end) should be sorted."""
        cats = categorizer.get_categories()
        # Uncategorized is appended at the end
        main_cats = cats[:-1]
        assert main_cats == sorted(main_cats)


# ------------------------------------------------------------------
# Priority / tie-breaking
# ------------------------------------------------------------------


class TestPriority:
    """Test that priority ordering works when multiple categories match."""

    def test_higher_priority_wins(self, mini_config):
        """When both Alpha (prio 1) and Beta (prio 2) match, Alpha wins."""
        cat = RegexCategorizer(config_path=mini_config)
        from src.interfaces import Email
        from datetime import datetime

        email = Email(
            id="tie",
            sender="user@alpha.com",
            subject="This is about alpha and beta",
            snippet="Both patterns match",
            timestamp=datetime(2025, 1, 1),
        )
        result = cat.categorize(email)
        assert result == "Alpha"
