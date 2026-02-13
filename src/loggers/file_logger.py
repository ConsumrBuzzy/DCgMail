"""
Simple file-based logger for DCGMail.

Implements the Logger interface from src/interfaces.py.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.interfaces import Logger as LoggerInterface


class FileLogger(LoggerInterface):
    """
    File and console logger implementation.

    Uses Python's built-in logging module with both file and console handlers.
    """

    def __init__(self, name: str = "DCGMail", level: str = "INFO", log_file: Optional[str] = None):
        """
        Initialize logger.

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file: Optional log file path
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

    def log(self, level: str, message: str) -> None:
        """
        Log a message.

        Args:
            level: "INFO", "WARNING", "ERROR", "DEBUG"
            message: Log message
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        log_level = level_map.get(level.upper(), logging.INFO)
        self.logger.log(log_level, message)

    def error(self, message: str, exception: Exception = None) -> None:
        """
        Log an error with optional exception details.

        Args:
            message: Error message
            exception: Optional exception object
        """
        if exception:
            self.logger.error(f"{message}: {exception}", exc_info=True)
        else:
            self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
