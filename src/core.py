"""
src/core.py - Pipeline orchestration.

Ties EmailProvider -> Categorizer -> Notifier together.
Depends only on abstractions (interfaces), not concrete implementations,
following the Dependency Inversion Principle.
"""

from typing import List

from src.interfaces import (
    CategorizedEmail,
    EmailCollection,
    EmailProvider,
    Categorizer,
    Notifier,
    Logger,
    ProviderError,
    CategorizerError,
    NotifierError,
)


class DCGMailPipeline:
    """
    Main orchestration class that runs the fetch -> categorize -> notify pipeline.

    All dependencies are injected through the constructor so implementations
    can be swapped without changing this code.
    """

    def __init__(
        self,
        provider: EmailProvider,
        categorizer: Categorizer,
        notifiers: List[Notifier],
        logger: Logger,
        dry_run: bool = False,
    ):
        """
        Initialize the pipeline with all required components.

        Args:
            provider: An EmailProvider implementation (e.g. GmailProvider).
            categorizer: A Categorizer implementation (e.g. RegexCategorizer).
            notifiers: List of Notifier implementations to send results to.
            logger: A Logger implementation for system logging.
            dry_run: If True, fetch and categorize but skip notifications
                     and email modifications.
        """
        self._provider = provider
        self._categorizer = categorizer
        self._notifiers = notifiers
        self._logger = logger
        self._dry_run = dry_run

    def run(self, limit: int = 50) -> EmailCollection:
        """
        Execute the full pipeline: authenticate, fetch, categorize, notify.

        Args:
            limit: Maximum number of unread emails to process.

        Returns:
            The EmailCollection produced by the pipeline.

        Raises:
            ProviderError: If authentication or fetching fails.
            CategorizerError: If categorization fails.
        """
        self._logger.log("INFO", "Starting DCGMail pipeline")

        # 1. Authenticate
        self._authenticate()

        # 2. Fetch unread emails
        emails = self._fetch(limit)
        if not emails:
            self._logger.log("INFO", "No unread emails found. Done.")
            return EmailCollection(emails=[], total_count=0, by_category={})

        # 3. Categorize
        categorized = self._categorize(emails)

        # 4. Build collection
        collection = self._build_collection(categorized)
        self._log_summary(collection)

        # 5. Notify
        if self._dry_run:
            self._logger.log("INFO", "Dry-run mode — skipping notifications")
        else:
            self._notify(collection)

        self._logger.log("INFO", "Pipeline complete")
        return collection

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def _authenticate(self) -> None:
        """Authenticate the email provider."""
        self._logger.log("INFO", "Authenticating email provider...")
        try:
            self._provider.authenticate()
            self._logger.log("INFO", "Authentication successful")
        except Exception as exc:
            self._logger.error("Authentication failed", exc)
            raise

    def _fetch(self, limit: int):
        """Fetch unread emails from the provider."""
        self._logger.log("INFO", f"Fetching up to {limit} unread emails...")
        try:
            emails = self._provider.fetch_unread(limit=limit)
            self._logger.log("INFO", f"Fetched {len(emails)} emails")
            return emails
        except ProviderError as exc:
            self._logger.error("Email fetch failed", exc)
            raise

    def _categorize(self, emails) -> List[CategorizedEmail]:
        """Run the categorizer over fetched emails."""
        self._logger.log("INFO", "Categorizing emails...")
        try:
            categorized = self._categorizer.categorize_batch(emails)
            self._logger.log("INFO", "Categorization complete")
            return categorized
        except CategorizerError as exc:
            self._logger.error("Categorization failed", exc)
            raise

    def _build_collection(self, categorized: List[CategorizedEmail]) -> EmailCollection:
        """Build an EmailCollection with summary stats."""
        by_category: dict = {}
        for ce in categorized:
            by_category[ce.category] = by_category.get(ce.category, 0) + 1

        return EmailCollection(
            emails=categorized,
            total_count=len(categorized),
            by_category=by_category,
        )

    def _log_summary(self, collection: EmailCollection) -> None:
        """Log a brief summary of the categorization results."""
        for cat, count in sorted(collection.by_category.items()):
            self._logger.log("INFO", f"  {cat}: {count} emails")

    def _notify(self, collection: EmailCollection) -> None:
        """Send the collection through all configured notifiers."""
        for notifier in self._notifiers:
            name = type(notifier).__name__
            self._logger.log("INFO", f"Sending summary via {name}...")
            try:
                notifier.send_summary(collection)
                self._logger.log("INFO", f"{name}: sent successfully")
            except NotifierError as exc:
                # Log but don't crash — other notifiers may still work
                self._logger.error(f"{name} notification failed", exc)
