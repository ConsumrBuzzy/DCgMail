#!/usr/bin/env python3
"""
Automated Git Commit Script for DCGMail

This script automates the full git commit process with auto-fixes:
1. Shows current git status
2. Runs auto-fixes (black, flake8, etc.)
3. Generates commit message suggestions
4. Stages all changes
5. Commits with the provided message
6. Pulls latest changes from remote
7. Pushes to remote repository

Usage:
    python commit.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from commit.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
