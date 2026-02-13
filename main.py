"""
main.py - DCGMail entry point.

Parses CLI arguments, wires up the SOLID components, and runs the pipeline.
"""

import argparse
import sys

from config import settings
from config.credentials import CredentialsManager
from src.logger import DCGMailLogger
from src.gmail_provider import GmailProvider
from src.categorizer import RegexCategorizer
from src.telegram_notifier import TelegramNotifier
from src.core import DCGMailPipeline
from src.interfaces import DCGMailException


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        prog="dcgmail",
        description="DCGMail — Work inbox categorization + Telegram alerts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=settings.DRY_RUN,
        help="Fetch and categorize but skip notifications and email modifications.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=settings.MAX_EMAILS_PER_RUN,
        help=f"Max emails to fetch (default: {settings.MAX_EMAILS_PER_RUN}).",
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=settings.CATEGORIES_CONFIG_PATH,
        help="Path to categories JSON config.",
    )
    parser.add_argument(
        "--validate-creds",
        action="store_true",
        help="Validate all credentials and exit.",
    )
    return parser.parse_args()


def main() -> int:
    """
    Wire up components and run the DCGMail pipeline.

    Returns:
        Exit code (0 = success, 1 = error).
    """
    args = parse_args()

    # Logger
    log_level = "DEBUG" if args.debug else settings.LOG_LEVEL
    logger = DCGMailLogger(log_level=log_level, log_file=settings.LOG_FILE)

    # Credential validation mode
    if args.validate_creds:
        logger.log("INFO", "Validating credentials...")
        try:
            CredentialsManager.validate_all()
            logger.log("INFO", "All credentials valid.")
            return 0
        except ValueError as exc:
            logger.error("Credential validation failed", exc)
            return 1

    # Build components
    try:
        provider = GmailProvider()
        categorizer = RegexCategorizer(config_path=args.categories)
        notifiers = []
        if not args.dry_run:
            notifiers.append(TelegramNotifier())

        pipeline = DCGMailPipeline(
            provider=provider,
            categorizer=categorizer,
            notifiers=notifiers,
            logger=logger,
            dry_run=args.dry_run,
        )
    except DCGMailException as exc:
        logger.error("Failed to initialize components", exc)
        return 1

    # Run pipeline
    try:
        pipeline.run(limit=args.limit)
        return 0
    except DCGMailException as exc:
        logger.error("Pipeline failed", exc)
        return 1
    except KeyboardInterrupt:
        logger.log("WARNING", "Interrupted by user")
        return 130


if __name__ == "__main__":
    sys.exit(main())
