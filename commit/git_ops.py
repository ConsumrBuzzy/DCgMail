"""
Git operations wrapper for commit automation.

Provides safe, high-level git operations with proper error handling.
"""

import subprocess
from pathlib import Path


class GitOperations:
    """Safe git operations wrapper."""

    def __init__(self, repo_path: str | None = None) -> None:
        """Initialize GitOperations."""
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def run_command(
        self,
        cmd: list[str],
        check: bool = False,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run a git command in the repo directory."""
        return subprocess.run(
            ["git"] + cmd,
            cwd=self.repo_path,
            check=check,
            capture_output=capture_output,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def get_status(self) -> str:
        """Get git status output."""
        result = self.run_command(["status", "--porcelain"])
        return result.stdout.strip() if result.stdout.strip() else ""

    def get_current_branch(self) -> str:
        """Get current branch name."""
        result = self.run_command(["rev-parse", "--abbrev-ref", "HEAD"])
        return result.stdout.strip()

    def stage_all(self) -> bool:
        """Stage all changes."""
        result = self.run_command(["add", "."])
        return result.returncode == 0

    def commit(self, message: str, no_verify: bool = False) -> bool:
        """Commit with message."""
        cmd = ["commit", "-m", message]
        if no_verify:
            cmd.append("--no-verify")
        result = self.run_command(cmd)
        return result.returncode == 0

    def pull(self, branch: str) -> bool:
        """Pull from origin branch."""
        result = self.run_command(["pull", "origin", branch])
        return result.returncode == 0

    def push(self, branch: str) -> bool:
        """Push to origin branch."""
        result = self.run_command(["push", "origin", branch])
        return result.returncode == 0

    def get_diff_summary(self) -> str:
        """Get summary of changes for commit message generation."""
        result = self.run_command(["diff", "--cached", "--stat"])
        return result.stdout.strip()

    def get_changed_files(self) -> list[str]:
        """Get list of changed files."""
        result = self.run_command(["diff", "--cached", "--name-only"])
        if not result.stdout.strip():
            result = self.run_command(["diff", "--name-only"])
        if result.stdout.strip():
            return [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return []
