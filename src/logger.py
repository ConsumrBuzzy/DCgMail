"""
src/logger.py - File + stdout logging implementation.

Implements the Logger interface from interfaces.py.
Writes logs to both a file and stdout simultaneously.
"""

import logging
import os
import sys
from pathlib import Path

from src.interfaces import Logger as LoggerInterface

# Map string levels to logging constants
_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

_instance_counter = 0


class DCGMailLogger(LoggerInterface):
    """Logger implementation using Python's built-in logging module."""

    def __init__(self, log_level: str = "INFO", log_file: str = "./logs/dcgmail.log"):
        """
        Initialize logger with file and stdout handlers.

        Args:
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR).
            log_file: Path to the log file.
        """
        global _instance_counter
        _instance_counter += 1
        self._logger = logging.getLogger(f"dcgmail.{_instance_counter}")
        self._logger.setLevel(_LEVEL_MAP.get(log_level.upper(), logging.INFO))
        self._logger.propagate = False

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Stdout handler
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        self._logger.addHandler(stdout_handler)

        # File handler (create directory if needed)
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    def log(self, level: str, message: str) -> None:
        """
        Log a message at the given level.

        Args:
            level: One of DEBUG, INFO, WARNING, ERROR.
            message: The log message.
        """
        numeric_level = _LEVEL_MAP.get(level.upper(), logging.INFO)
        self._logger.log(numeric_level, message)

    def error(self, message: str, exception: Exception = None) -> None:
        """
        Log an error with optional exception traceback.

        Args:
            message: Error description.
            exception: Optional exception instance for traceback.
        """
        if exception:
            self._logger.error("%s: %s", message, exception, exc_info=True)
        else:
            self._logger.error(message)
