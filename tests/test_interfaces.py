"""
tests/test_interfaces.py - Contract and integration tests.

Verifies that concrete implementations satisfy the abstract interfaces,
and tests the pipeline orchestration with mock/stub collaborators.
"""

from datetime import datetime
from typing import List
from unittest.mock import MagicMock

import pytest

from src.interfaces import (
    CategorizedEmail,
    Email,
    EmailCollection,
    EmailProvider,
    Categorizer,
    Notifier,
    Logger,
    ProviderError,
)
from src.categorizer import RegexCategorizer
from src.logger import DCGMailLogger
from src.core import DCGMailPipeline
from tests.fixtures.sample_emails import (
    make_work_email,
    make_crypto_email,
    make_noise_email,
    sample_email_batch,
)


# ------------------------------------------------------------------
# Data model tests
# ------------------------------------------------------------------


class TestDataModels:
    """Test the shared data models."""

    def test_email_defaults(self):
        """Email should default to read=False and empty labels."""
        e = Email(
            id="1", sender="a@b.com", subject="Hi",
            snippet="...", timestamp=datetime.now(),
        )
        assert e.read is False
        assert e.labels == []

    def test_categorized_email_defaults(self):
        """CategorizedEmail should default to confidence=1.0, reason=None."""
        e = Email(
            id="1", sender="a@b.com", subject="Hi",
            snippet="...", timestamp=datetime.now(),
        )
        ce = CategorizedEmail(email=e, category="Work")
        assert ce.confidence == 1.0
        assert ce.reason is None

    def test_email_collection_timestamp(self):
        """EmailCollection should auto-populate timestamp."""
        ec = EmailCollection(emails=[], total_count=0, by_category={})
        assert ec.timestamp is not None


# ------------------------------------------------------------------
# Interface compliance tests
# ------------------------------------------------------------------


class TestInterfaceCompliance:
    """Verify concrete classes implement all abstract methods."""

    def test_regex_categorizer_is_categorizer(self):
        """RegexCategorizer must be a valid Categorizer subclass."""
        cat = RegexCategorizer(config_path="./config/categories.json")
        assert isinstance(cat, Categorizer)
        assert callable(cat.categorize)
        assert callable(cat.categorize_batch)
        assert callable(cat.get_categories)

    def test_logger_is_logger(self, tmp_path):
        """DCGMailLogger must be a valid Logger subclass."""
        log = DCGMailLogger(log_level="DEBUG", log_file=str(tmp_path / "test.log"))
        assert isinstance(log, Logger)
        assert callable(log.log)
        assert callable(log.error)


# ------------------------------------------------------------------
# Logger tests
# ------------------------------------------------------------------


class TestLogger:
    """Test the DCGMailLogger implementation."""

    def test_log_creates_file(self, tmp_path):
        """Logging should create the log file."""
        log_file = str(tmp_path / "test.log")
        logger = DCGMailLogger(log_level="DEBUG", log_file=log_file)
        logger.log("INFO", "test message")
        from pathlib import Path
        assert Path(log_file).exists()

    def test_log_writes_message(self, tmp_path):
        """The log file should contain the logged message."""
        log_file = str(tmp_path / "test.log")
        logger = DCGMailLogger(log_level="DEBUG", log_file=log_file)
        logger.log("INFO", "hello world")
        content = open(log_file).read()
        assert "hello world" in content

    def test_error_with_exception(self, tmp_path):
        """error() should log the exception details."""
        log_file = str(tmp_path / "test.log")
        logger = DCGMailLogger(log_level="DEBUG", log_file=log_file)
        logger.error("something broke", ValueError("bad value"))
        content = open(log_file).read()
        assert "something broke" in content
        assert "bad value" in content


# ------------------------------------------------------------------
# Pipeline integration tests (with mocks)
# ------------------------------------------------------------------


class StubProvider(EmailProvider):
    """A fake EmailProvider that returns canned data."""

    def __init__(self, emails: List[Email]):
        self._emails = emails

    def authenticate(self) -> bool:
        return True

    def fetch_unread(self, limit: int = 50) -> List[Email]:
        return self._emails[:limit]

    def mark_as_read(self, email_id: str) -> bool:
        return True

    def add_label(self, email_id: str, label: str) -> bool:
        return True

    def move_to_trash(self, email_id: str) -> bool:
        return True


class StubNotifier(Notifier):
    """A fake Notifier that records what was sent."""

    def __init__(self):
        self.summaries: List[EmailCollection] = []
        self.alerts: List[str] = []

    def send_summary(self, collection: EmailCollection) -> bool:
        self.summaries.append(collection)
        return True

    def send_alert(self, message: str) -> bool:
        self.alerts.append(message)
        return True


class TestPipeline:
    """Integration tests for DCGMailPipeline using stub collaborators."""

    @pytest.fixture
    def components(self, tmp_path):
        """Build a pipeline with stubs and a real categorizer."""
        emails = sample_email_batch()
        provider = StubProvider(emails)
        categorizer = RegexCategorizer(config_path="./config/categories.json")
        notifier = StubNotifier()
        logger = DCGMailLogger(log_level="DEBUG", log_file=str(tmp_path / "test.log"))
        pipeline = DCGMailPipeline(
            provider=provider,
            categorizer=categorizer,
            notifiers=[notifier],
            logger=logger,
        )
        return pipeline, notifier

    def test_pipeline_returns_collection(self, components):
        """run() should return an EmailCollection."""
        pipeline, _ = components
        result = pipeline.run(limit=50)
        assert isinstance(result, EmailCollection)
        assert result.total_count > 0

    def test_pipeline_notifies(self, components):
        """run() should send a summary to each notifier."""
        pipeline, notifier = components
        pipeline.run(limit=50)
        assert len(notifier.summaries) == 1
        assert notifier.summaries[0].total_count > 0

    def test_pipeline_dry_run_skips_notification(self, tmp_path):
        """In dry-run mode, notifiers should not be called."""
        emails = sample_email_batch()
        provider = StubProvider(emails)
        categorizer = RegexCategorizer(config_path="./config/categories.json")
        notifier = StubNotifier()
        logger = DCGMailLogger(log_level="DEBUG", log_file=str(tmp_path / "test.log"))
        pipeline = DCGMailPipeline(
            provider=provider,
            categorizer=categorizer,
            notifiers=[notifier],
            logger=logger,
            dry_run=True,
        )
        pipeline.run(limit=50)
        assert len(notifier.summaries) == 0

    def test_pipeline_empty_inbox(self, tmp_path):
        """An empty inbox should return an empty collection gracefully."""
        provider = StubProvider([])
        categorizer = RegexCategorizer(config_path="./config/categories.json")
        notifier = StubNotifier()
        logger = DCGMailLogger(log_level="DEBUG", log_file=str(tmp_path / "test.log"))
        pipeline = DCGMailPipeline(
            provider=provider,
            categorizer=categorizer,
            notifiers=[notifier],
            logger=logger,
        )
        result = pipeline.run()
        assert result.total_count == 0
        assert len(notifier.summaries) == 0

    def test_pipeline_collection_has_categories(self, components):
        """The result collection should have a populated by_category dict."""
        pipeline, _ = components
        result = pipeline.run(limit=50)
        assert len(result.by_category) > 0
        assert sum(result.by_category.values()) == result.total_count
