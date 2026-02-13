"""
Core email processing orchestration for DCGMail.

Coordinates EmailProvider, Categorizer, and Notifier components.
"""

from typing import Optional

from src.interfaces import (
    EmailProvider,
    Categorizer,
    Notifier,
    Logger,
    EmailCollection,
    ProviderError,
    CategorizerError,
    NotifierError,
)


class EmailProcessor:
    """
    Core orchestrator for DCGMail email processing pipeline.

    Coordinates: Fetch → Categorize → Notify
    """

    def __init__(
        self,
        provider: EmailProvider,
        categorizer: Categorizer,
        notifier: Optional[Notifier],
        logger: Logger,
        dry_run: bool = False,
    ):
        """
        Initialize email processor.

        Args:
            provider: Email provider (e.g., GmailProvider)
            categorizer: Email categorizer (e.g., SimpleCategorizer)
            notifier: Notification provider (e.g., TelegramNotifier), optional for dry-run
            logger: Logger instance
            dry_run: If True, skip sending notifications
        """
        self.provider = provider
        self.categorizer = categorizer
        self.notifier = notifier
        self.logger = logger
        self.dry_run = dry_run

        if dry_run:
            self.logger.info("Running in DRY-RUN mode (no notifications will be sent)")

    def process(self, limit: int = 50) -> bool:
        """
        Execute full email processing pipeline.

        Steps:
        1. Authenticate with email provider
        2. Fetch unread emails
        3. Categorize emails
        4. Build summary collection
        5. Send notification (unless dry-run)

        Args:
            limit: Maximum number of emails to fetch

        Returns:
            True if successful, False if any step failed
        """
        try:
            # Step 1: Authenticate
            self.logger.info("Step 1: Authenticating with email provider...")
            if not self.provider.authenticate():
                self.logger.error("Authentication failed")
                return False

            # Step 2: Fetch emails
            self.logger.info(f"Step 2: Fetching up to {limit} unread emails...")
            emails = self.provider.fetch_unread(limit=limit)

            if not emails:
                self.logger.info("No unread emails found")
                # Still successful - just nothing to do
                if self.notifier and not self.dry_run:
                    self.notifier.send_alert("No new emails")
                return True

            self.logger.info(f"Fetched {len(emails)} unread emails")

            # Step 3: Categorize
            self.logger.info("Step 3: Categorizing emails...")
            categorized_emails = self.categorizer.categorize_batch(emails)

            # Step 4: Build collection
            by_category = {}
            for cat_email in categorized_emails:
                category = cat_email.category
                if category not in by_category:
                    by_category[category] = 0
                by_category[category] += 1

            collection = EmailCollection(
                emails=categorized_emails,
                total_count=len(emails),
                by_category=by_category
            )

            # Log summary
            self.logger.info("Categorization complete:")
            for category, count in sorted(
                by_category.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                self.logger.info(f"  {category}: {count} emails")

            # Step 5: Send notification
            if self.dry_run:
                self.logger.info("Step 4: DRY-RUN mode - skipping notification")
                self._print_summary(collection)
                return True
            else:
                if not self.notifier:
                    self.logger.warning("No notifier configured - skipping notification")
                    return True

                self.logger.info("Step 4: Sending notification...")
                success = self.notifier.send_summary(collection)

                if success:
                    self.logger.info("Notification sent successfully")
                    return True
                else:
                    self.logger.error("Failed to send notification")
                    return False

        except ProviderError as e:
            self.logger.error(f"Provider error: {e}", exception=e)
            return False

        except CategorizerError as e:
            self.logger.error(f"Categorizer error: {e}", exception=e)
            return False

        except NotifierError as e:
            self.logger.error(f"Notifier error: {e}", exception=e)
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error in pipeline: {e}", exception=e)
            return False

    def _print_summary(self, collection: EmailCollection):
        """
        Print summary to console (for dry-run mode).

        Args:
            collection: EmailCollection to summarize
        """
        print("\n" + "=" * 70)
        print("EMAIL SUMMARY (DRY-RUN)")
        print("=" * 70)
        print(f"\nTotal Emails: {collection.total_count}")
        print("\nBy Category:")

        for category, count in sorted(
            collection.by_category.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {category:20s}: {count:3d} emails")

            # Show sample emails
            category_emails = [
                e.email for e in collection.emails
                if e.category == category
            ][:3]  # Show max 3 per category

            for email in category_emails:
                subject = email.subject[:50] + "..." if len(email.subject) > 50 else email.subject
                print(f"    - {subject}")

        print("=" * 70 + "\n")
