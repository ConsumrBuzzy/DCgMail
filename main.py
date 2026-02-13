#!/usr/bin/env python3
"""
DCGMail - Intelligent Inbox Automation

Main entry point for the DCGMail email processing pipeline.
Coordinates Gmail API, categorization, and Telegram notifications.

Usage:
    python main.py                           # Normal run
    python main.py --dry-run                 # Fetch & categorize only, no Telegram
    python main.py --validate-creds          # Validate credentials and exit
    python main.py --limit 10 --debug        # Fetch 10 emails with debug logging
"""

import sys
import argparse
from pathlib import Path

from src.config.env_config import EnvConfigProvider
from src.loggers.file_logger import FileLogger
from src.providers.gmail_provider import GmailProvider
from src.categorizers.simple_categorizer import SimpleCategorizer
from src.notifiers.telegram_notifier import TelegramNotifier
from src.core import EmailProcessor
from src.interfaces import (
    ConfigError,
    CredentialError,
    ProviderError,
    NotifierError,
)


def validate_credentials(config: EnvConfigProvider, logger: FileLogger) -> bool:
    """
    Validate all required credentials.

    Args:
        config: Configuration provider
        logger: Logger instance

    Returns:
        True if all credentials are valid
    """
    try:
        # Check Gmail credentials
        gmail_sa = config.get("gmail_service_account")
        if not gmail_sa or not Path(gmail_sa).exists():
            logger.error("Gmail service account not found")
            print("[ERROR] Gmail service account not found")
            print(f"   Expected: {gmail_sa}")
            print("   Set GMAIL_SERVICE_ACCOUNT in .env")
            return False

        work_email = config.get("work_email")
        if not work_email:
            logger.error("Work email not configured")
            print("[ERROR] Work email not configured")
            print("   Set WORK_EMAIL in .env")
            return False

        # Check Telegram credentials (only if not dry-run)
        telegram_token = config.get("telegram_bot_token")
        telegram_chat = config.get("telegram_chat_id")

        if not telegram_token:
            logger.warning("Telegram bot token not configured")
            print("[WARNING] Telegram bot token not configured")
            print("   Set TELEGRAM_BOT_TOKEN in .env (or use --dry-run)")

        if not telegram_chat:
            logger.warning("Telegram chat ID not configured")
            print("[WARNING] Telegram chat ID not configured")
            print("   Set TELEGRAM_CHAT_ID in .env (or use --dry-run)")

        logger.info("Credential validation passed")
        return True

    except Exception as e:
        logger.error(f"Credential validation error: {e}", exception=e)
        return False


def main():
    """Main entry point for DCGMail."""
    parser = argparse.ArgumentParser(
        description="DCGMail: Intelligent inbox automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                        # Normal run
  python main.py --dry-run              # Fetch & categorize, no Telegram
  python main.py --validate-creds       # Validate credentials
  python main.py --limit 10 --debug     # Fetch 10 emails with debug logging
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and categorize emails, but don't send Telegram notification"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of emails to fetch (default: 50)"
    )
    parser.add_argument(
        "--validate-creds",
        action="store_true",
        help="Validate credentials and exit"
    )
    parser.add_argument(
        "--categories",
        type=str,
        default="config/categories.json",
        help="Path to categories config file (default: config/categories.json)"
    )

    args = parser.parse_args()

    # Initialize logger
    log_level = "DEBUG" if args.debug else "INFO"
    logger = FileLogger(name="DCGMail", level=log_level)

    try:
        # Load configuration
        logger.info("Loading configuration from .env")
        config = EnvConfigProvider()

        # Validate credentials
        logger.info("Validating credentials...")
        if not validate_credentials(config, logger):
            print("\n[ERROR] Credential validation failed. Check .env file.")
            return 1

        if args.validate_creds:
            print("\n[SUCCESS] All credentials valid")
            return 0

        # Initialize Gmail provider
        logger.info("Initializing Gmail provider...")
        gmail_provider = GmailProvider(config=config, logger=logger)

        # Initialize categorizer
        logger.info("Initializing email categorizer...")
        if not Path(args.categories).exists():
            logger.error(f"Categories config not found: {args.categories}")
            print(f"\n[ERROR] Categories config not found: {args.categories}")
            return 1

        categorizer = SimpleCategorizer(
            config_path=args.categories,
            logger=logger
        )

        # Initialize Telegram notifier (optional for dry-run)
        notifier = None
        if not args.dry_run:
            telegram_token = config.get("telegram_bot_token")
            telegram_chat_id = config.get("telegram_chat_id")

            if telegram_token and telegram_chat_id:
                logger.info("Initializing Telegram notifier...")
                try:
                    notifier = TelegramNotifier(
                        bot_token=telegram_token,
                        chat_id=int(telegram_chat_id),
                        logger=logger
                    )
                except CredentialError as e:
                    logger.error(f"Telegram initialization failed: {e}")
                    print(f"\n[ERROR] Telegram Error: {e}")
                    print("   Use --dry-run to skip Telegram")
                    return 1
            else:
                logger.warning("Telegram not configured, running in dry-run mode")
                print("\n[WARNING] Telegram not configured, running in dry-run mode")
                args.dry_run = True

        # Initialize email processor
        logger.info(f"Starting DCGMail pipeline (dry_run={args.dry_run})")
        processor = EmailProcessor(
            provider=gmail_provider,
            categorizer=categorizer,
            notifier=notifier,
            logger=logger,
            dry_run=args.dry_run
        )

        # Run the pipeline
        success = processor.process(limit=args.limit)

        if success:
            logger.info("Pipeline completed successfully")
            print("\n[SUCCESS] DCGMail completed successfully")
            return 0
        else:
            logger.error("Pipeline failed")
            print("\n[ERROR] DCGMail pipeline failed")
            return 3

    except CredentialError as e:
        logger.error(f"Credential error: {e}", exception=e)
        print(f"\n[ERROR] Credential Error: {e}")
        print("   Check your .env file and credentials/service_account.json")
        return 1

    except ProviderError as e:
        logger.error(f"Provider error: {e}", exception=e)
        print(f"\n[ERROR] Provider Error: {e}")
        print("   Gmail API may be unreachable or credentials invalid")
        return 2

    except NotifierError as e:
        logger.error(f"Notifier error: {e}", exception=e)
        print(f"\n[ERROR] Notifier Error: {e}")
        print("   Telegram API may be unreachable or bot token invalid")
        return 3

    except ConfigError as e:
        logger.error(f"Configuration error: {e}", exception=e)
        print(f"\n[ERROR] Configuration Error: {e}")
        print("   Check your .env file and config/categories.json")
        return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\n\n[WARNING] Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exception=e)
        print(f"\n[ERROR] Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 99


if __name__ == "__main__":
    sys.exit(main())
