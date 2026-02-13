"""
interfaces.py - SOLID Foundation for DCGMail

This module defines Abstract Base Classes that represent the "contracts"
for each component of the system. Any implementation (Gmail, Outlook, Regex,
LLM, Telegram, Email) must conform to these interfaces.

Benefit: Swap implementations without changing the orchestration logic.
Example: Move from Gmail to Outlook without touching core.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


# ============================================================================
# Data Models (Shared across all components)
# ============================================================================

@dataclass
class Email:
    """Represents a single email message."""
    id: str                      # Unique identifier (Gmail message ID, etc.)
    sender: str                  # Email address
    subject: str                 # Subject line
    snippet: str                 # First 200 chars of body
    timestamp: datetime          # When it arrived
    read: bool = False           # Read status
    labels: List[str] = None     # Gmail labels, if applicable
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []


@dataclass
class CategorizedEmail:
    """Represents an email with its category assigned."""
    email: Email
    category: str                # e.g., "Work", "Crypto", "Noise"
    confidence: float = 1.0      # 0.0 to 1.0 (for ML categorizers)
    reason: Optional[str] = None # Why it got this category (for debugging)


@dataclass
class EmailCollection:
    """A batch of emails with summary stats."""
    emails: List[CategorizedEmail]
    total_count: int
    by_category: Dict[str, int]  # {"Work": 5, "Crypto": 3, "Noise": 12}
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


# ============================================================================
# Interface 1: EmailProvider (S - Single Responsibility)
# ============================================================================

class EmailProvider(ABC):
    """
    Abstraction for fetching emails from any source.
    
    Implementations might include:
    - GmailProvider (uses Gmail API)
    - OutlookProvider (uses Microsoft Graph)
    - LocalMailboxProvider (reads from mbox files)
    
    Single Responsibility: Fetch and normalize emails from the source.
    """
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Validate credentials and establish connection.
        
        Returns:
            True if authenticated, False otherwise
            
        Raises:
            CredentialError if credentials are invalid/missing
        """
        pass
    
    @abstractmethod
    def fetch_unread(self, limit: int = 50) -> List[Email]:
        """
        Fetch unread emails from the provider.
        
        Args:
            limit: Maximum number of emails to fetch
            
        Returns:
            List of Email objects in reverse chronological order (newest first)
            
        Raises:
            ProviderError if fetch fails
        """
        pass
    
    @abstractmethod
    def mark_as_read(self, email_id: str) -> bool:
        """
        Mark a single email as read.
        
        Args:
            email_id: The email's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def add_label(self, email_id: str, label: str) -> bool:
        """
        Add a label/tag to an email (for organizing).
        
        Args:
            email_id: The email's unique identifier
            label: Label name (e.g., "Archived", "Review-Later")
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def move_to_trash(self, email_id: str) -> bool:
        """
        Delete/trash an email.
        
        Args:
            email_id: The email's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        pass


# ============================================================================
# Interface 2: Categorizer (O - Open/Closed, L - Liskov Substitution)
# ============================================================================

class Categorizer(ABC):
    """
    Abstraction for assigning categories to emails.
    
    Implementations might include:
    - RegexCategorizer (pattern matching)
    - LLMCategorizer (Gemini AI)
    - RuleBasedCategorizer (if/else logic)
    - HybridCategorizer (regex first, LLM fallback)
    
    Single Responsibility: Decide which category an email belongs to.
    """
    
    @abstractmethod
    def categorize(self, email: Email) -> str:
        """
        Assign a single category to an email.
        
        Args:
            email: Email object to categorize
            
        Returns:
            Category string (e.g., "Work", "Crypto", "Noise")
        """
        pass
    
    @abstractmethod
    def categorize_batch(self, emails: List[Email]) -> List[CategorizedEmail]:
        """
        Categorize multiple emails (more efficient than one-by-one).
        
        Args:
            emails: List of Email objects
            
        Returns:
            List of CategorizedEmail objects with confidence scores
        """
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """
        Return all possible categories this categorizer can assign.
        
        Returns:
            List of category names
        """
        pass


# ============================================================================
# Interface 3: Notifier (I - Interface Segregation)
# ============================================================================

class Notifier(ABC):
    """
    Abstraction for sending summaries/alerts.
    
    Implementations might include:
    - TelegramNotifier (Telegram bot)
    - EmailNotifier (send via email)
    - SlackNotifier (Slack channel)
    - StdoutNotifier (just print, for testing)
    
    Single Responsibility: Deliver categorized email summaries somewhere.
    """
    
    @abstractmethod
    def send_summary(self, collection: EmailCollection) -> bool:
        """
        Send a formatted summary of categorized emails.
        
        Args:
            collection: EmailCollection with categorized emails
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_alert(self, message: str) -> bool:
        """
        Send an urgent alert (e.g., "System error: Gmail API down").
        
        Args:
            message: Alert text
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass


# ============================================================================
# Interface 4: Logger (I - Interface Segregation)
# ============================================================================

class Logger(ABC):
    """
    Abstraction for logging events (separate from notifiers).
    
    This keeps system logs (errors, performance) separate from
    user-facing notifications (summaries, alerts).
    
    Implementations might include:
    - FileLogger (write to files)
    - StdoutLogger (print to console)
    - SentryLogger (error tracking service)
    """
    
    @abstractmethod
    def log(self, level: str, message: str) -> None:
        """
        Log a message.
        
        Args:
            level: "INFO", "WARNING", "ERROR", "DEBUG"
            message: Log message
        """
        pass
    
    @abstractmethod
    def error(self, message: str, exception: Exception = None) -> None:
        """
        Log an error with optional exception details.
        """
        pass


# ============================================================================
# Interface 5: ConfigProvider (D - Dependency Inversion)
# ============================================================================

class ConfigProvider(ABC):
    """
    Abstraction for configuration sources.
    
    Implementations might include:
    - EnvConfigProvider (.env files)
    - FileConfigProvider (JSON/YAML files)
    - SecretManagerConfigProvider (Google Cloud Secret Manager)
    
    Single Responsibility: Load and provide configuration.
    """
    
    @abstractmethod
    def get(self, key: str, default: str = None) -> str:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        pass
    
    @abstractmethod
    def get_required(self, key: str) -> str:
        """
        Get a required configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value
            
        Raises:
            ConfigError if key not found
        """
        pass


# ============================================================================
# Exception Hierarchy (Consistent error handling across components)
# ============================================================================

class DCGMailException(Exception):
    """Base exception for all DCGMail errors."""
    pass


class CredentialError(DCGMailException):
    """Raised when credentials are invalid or missing."""
    pass


class ProviderError(DCGMailException):
    """Raised when email provider fails (Gmail API down, etc.)."""
    pass


class CategorizerError(DCGMailException):
    """Raised when categorization fails."""
    pass


class NotifierError(DCGMailException):
    """Raised when notification fails (Telegram API down, etc.)."""
    pass


class ConfigError(DCGMailException):
    """Raised when configuration is missing or invalid."""
    pass


# ============================================================================
# Summary of SOLID Principles Applied
# ============================================================================

"""
S (Single Responsibility):
  - EmailProvider: Only fetches emails
  - Categorizer: Only categorizes
  - Notifier: Only sends notifications
  - Logger: Only logs
  - ConfigProvider: Only provides config

O (Open/Closed):
  - Add a new Categorizer (e.g., LLMCategorizer) without changing EmailProvider
  - Add a new Notifier (e.g., SlackNotifier) without changing core.py

L (Liskov Substitution):
  - Any Categorizer implementation can replace any other
  - Any Notifier implementation can replace any other
  - If it implements the interface, it works

I (Interface Segregation):
  - Notifier doesn't need to know about categorization
  - Logger doesn't need to know about email fetching
  - ConfigProvider doesn't need to know about Telegram

D (Dependency Inversion):
  - core.py depends on abstractions (EmailProvider, Categorizer, Notifier)
  - NOT on concrete implementations (GmailProvider, RegexCategorizer, etc.)
  - Swap implementations by changing a config file or constructor arg
"""
