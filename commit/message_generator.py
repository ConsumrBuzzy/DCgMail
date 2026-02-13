"""
Intelligent commit message generator for DCGMail.

Analyzes changes and generates appropriate commit messages.
"""

from pathlib import Path
from commit.git_ops import GitOperations


class MessageGenerator:
    """Generates intelligent commit messages based on changes."""

    # File category patterns for DCGMail
    CATEGORIES = {
        "test": ["test", "tests/"],
        "docs": [".md", "readme", "doc"],
        "config": [".yaml", ".yml", ".json", ".toml", ".ini", ".env", "requirements"],
        "src": ["src/", "interfaces", "providers", "categorizers", "notifiers"],
        "commit": ["commit/", "commit.py"],
        "credentials": ["credentials/"],
    }

    def __init__(self, git_ops: GitOperations) -> None:
        """Initialize MessageGenerator."""
        self.git_ops = git_ops

    def generate_smart_message(self) -> str:
        """Generate an intelligent commit message based on current changes."""
        files = self.git_ops.get_changed_files()

        if not files:
            return "chore: Update project files"

        # Categorize files
        categorized = self._categorize_files(files)

        # Generate message
        return self._build_message(files, categorized)

    def _categorize_files(self, files: list[str]) -> dict[str, list[str]]:
        """Categorize files into groups."""
        categorized = {cat: [] for cat in self.CATEGORIES}
        uncategorized = []

        for file in files:
            file_lower = file.lower()
            matched = False

            for category, patterns in self.CATEGORIES.items():
                if any(pattern in file_lower for pattern in patterns):
                    categorized[category].append(file)
                    matched = True
                    break

            if not matched:
                uncategorized.append(file)

        if uncategorized:
            categorized["other"] = uncategorized

        return {k: v for k, v in categorized.items() if v}

    def _get_primary_category(self, categorized: dict[str, list[str]]) -> str:
        """Determine the primary category based on file counts."""
        if not categorized:
            return "other"

        # Priority order for DCGMail
        priority = ["src", "docs", "config", "commit", "test", "other"]

        for cat in priority:
            if cat in categorized:
                return cat

        return list(categorized.keys())[0]

    def _get_prefix(self, category: str) -> str:
        """Get conventional commit prefix for category."""
        prefixes = {
            "src": "feat: ",
            "test": "test: ",
            "docs": "docs: ",
            "config": "chore: ",
            "commit": "chore: ",
            "other": "chore: ",
        }
        return prefixes.get(category, "chore: ")

    def _describe_changes(self, categorized: dict[str, list[str]]) -> str:
        """Generate description of changes."""
        parts = []

        for category, files in categorized.items():
            if category == "docs":
                parts.append("documentation")
            elif category == "test":
                parts.append("tests")
            elif category == "config":
                parts.append("configuration")
            elif category == "src":
                # Try to be more specific about src changes
                if any("provider" in f.lower() for f in files):
                    parts.append("providers")
                elif any("categorizer" in f.lower() for f in files):
                    parts.append("categorizers")
                elif any("notifier" in f.lower() for f in files):
                    parts.append("notifiers")
                else:
                    parts.append("core components")
            elif category == "commit":
                parts.append("commit automation")
            else:
                parts.append(f"{category} files")

        if not parts:
            return "Update project files"

        if len(parts) == 1:
            return f"Update {parts[0]}"
        elif len(parts) == 2:
            return f"Update {parts[0]} and {parts[1]}"
        else:
            return f"Update {', '.join(parts[:-1])}, and {parts[-1]}"

    def _build_message(
        self, files: list[str], categorized: dict[str, list[str]]
    ) -> str:
        """Build the final commit message."""
        primary = self._get_primary_category(categorized)
        prefix = self._get_prefix(primary)

        # Single file case
        if len(files) == 1:
            filename = Path(files[0]).name
            return f"{prefix}Update {filename}"

        # Multiple files case
        description = self._describe_changes(categorized)

        # Build detailed message
        message_parts = [f"{prefix}{description}"]

        # Add file details
        message_parts.append("")
        for category, cat_files in categorized.items():
            if len(cat_files) <= 3:
                for file in cat_files:
                    message_parts.append(f"- {file}")
            else:
                message_parts.append(f"- {len(cat_files)} {category} files")

        # Add co-author
        message_parts.append("")
        message_parts.append("Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>")

        return "\n".join(message_parts)
