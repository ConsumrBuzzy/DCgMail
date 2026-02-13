#!/usr/bin/env python3
"""
Commit CLI - Main entry point for the commit automation system.

Usage:
    python commit.py
"""

from commit.git_ops import GitOperations
from commit.message_generator import MessageGenerator


def main() -> None:
    """Main entry point for automated commit system."""
    print("=" * 70)
    print("DCGMail Auto-Commit System")
    print("=" * 70)

    # Initialize components
    git_ops = GitOperations()
    msg_generator = MessageGenerator(git_ops)

    # Show current status
    print("\nCurrent git status:")
    print("-" * 70)
    status = git_ops.get_status()
    if not status:
        print("No changes to commit.")
        return
    print(status)
    print("-" * 70)

    # Get current branch
    branch = git_ops.get_current_branch()
    print(f"\nCurrent branch: {branch}")

    # Stage all changes
    print("\nStaging all changes...")
    git_ops.stage_all()

    # Generate smart commit message
    print("\nGenerating smart commit message...")
    smart_message = msg_generator.generate_smart_message()

    # Show the smart message
    print("\nCommit message:")
    print("-" * 70)
    print(smart_message)
    print("-" * 70)

    # Auto-commit
    print("\nCommitting...")
    if git_ops.commit(smart_message, no_verify=True):
        print("SUCCESS: Changes committed successfully")
    else:
        print("ERROR: Commit failed.")
        return

    # Auto-pull
    print(f"\nPulling from origin/{branch}...")
    if git_ops.pull(branch):
        print("SUCCESS: Pull successful")
    else:
        print("WARNING: Pull had issues - continuing...")

    # Auto-push
    print(f"\nPushing to origin/{branch}...")
    if git_ops.push(branch):
        print("SUCCESS: Changes pushed successfully")
    else:
        print("ERROR: Push failed.")

    print("\n" + "=" * 70)
    print("Auto-commit complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
