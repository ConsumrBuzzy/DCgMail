"""
tests/fixtures/sample_emails.py - Mock email data for testing.

Provides factory functions that return Email objects with realistic
but fake data. No real credentials or PII.
"""

from datetime import datetime

from src.interfaces import Email


def make_work_email(
    id: str = "msg_work_001",
    sender: str = "susan.d@company.com",
    subject: str = "Sprint Review meeting invitation for Friday",
    snippet: str = "Please join the sprint review at 3pm. Jira board has been updated.",
    timestamp: datetime = None,
) -> Email:
    """Return a work-related email."""
    return Email(
        id=id,
        sender=sender,
        subject=subject,
        snippet=snippet,
        timestamp=timestamp or datetime(2025, 6, 1, 9, 0),
    )


def make_crypto_email(
    id: str = "msg_crypto_001",
    sender: str = "alerts@coinbase.com",
    subject: str = "Your Solana staking rewards are ready",
    snippet: str = "You earned 2.3 SOL from staking. Your wallet balance has been updated.",
    timestamp: datetime = None,
) -> Email:
    """Return a crypto-related email."""
    return Email(
        id=id,
        sender=sender,
        subject=subject,
        snippet=snippet,
        timestamp=timestamp or datetime(2025, 6, 1, 10, 0),
    )


def make_admin_email(
    id: str = "msg_admin_001",
    sender: str = "no-reply@paypal.com",
    subject: str = "Payment receipt for your recent invoice",
    snippet: str = "Your payment of $49.99 has been processed. Receipt attached.",
    timestamp: datetime = None,
) -> Email:
    """Return an admin/finance-related email."""
    return Email(
        id=id,
        sender=sender,
        subject=subject,
        snippet=snippet,
        timestamp=timestamp or datetime(2025, 6, 1, 11, 0),
    )


def make_noise_email(
    id: str = "msg_noise_001",
    sender: str = "deals@shop-spam.com",
    subject: str = "Limited time sale - 50% discount!",
    snippet: str = "Don't miss our special offer. Free shipping on orders over $25. Unsubscribe here.",
    timestamp: datetime = None,
) -> Email:
    """Return a promotional/noise email."""
    return Email(
        id=id,
        sender=sender,
        subject=subject,
        snippet=snippet,
        timestamp=timestamp or datetime(2025, 6, 1, 12, 0),
    )


def make_uncategorized_email(
    id: str = "msg_unknown_001",
    sender: str = "random@example.org",
    subject: str = "Hey, long time no see",
    snippet: str = "Just wanted to catch up. How have you been?",
    timestamp: datetime = None,
) -> Email:
    """Return an email that shouldn't match any category."""
    return Email(
        id=id,
        sender=sender,
        subject=subject,
        snippet=snippet,
        timestamp=timestamp or datetime(2025, 6, 1, 13, 0),
    )


def sample_email_batch() -> list:
    """Return a mixed batch of emails for batch-categorization tests."""
    return [
        make_work_email(),
        make_crypto_email(),
        make_admin_email(),
        make_noise_email(),
        make_uncategorized_email(),
        make_work_email(
            id="msg_work_002",
            sender="ci@github.com",
            subject="[PR] Pull request review requested",
            snippet="You have been requested to review a pull request.",
        ),
        make_crypto_email(
            id="msg_crypto_002",
            sender="notifications@phantom.app",
            subject="NFT airdrop claim available",
            snippet="A new NFT airdrop is available in your wallet.",
        ),
    ]
