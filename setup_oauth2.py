#!/usr/bin/env python3
"""
OAuth2 Setup Helper for DCGMail

This script guides you through creating OAuth2 credentials for DCGMail
without needing Google Workspace Admin Console access.

Usage:
    python setup_oauth2.py

Requirements:
    - Google Cloud Console access (cloud.google.com)
    - Project: dgautohub
    - Gmail API enabled
"""

import webbrowser
import sys
from pathlib import Path

# Terminal colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text):
    """Print section header."""
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}{text}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")


def print_step(number, text):
    """Print step number and description."""
    print(f"{BOLD}{GREEN}Step {number}:{RESET} {text}")


def print_info(text):
    """Print info message."""
    print(f"{YELLOW}[INFO]{RESET} {text}")


def check_oauth_client_exists():
    """Check if OAuth2 client credentials already exist."""
    oauth_path = Path("./credentials/oauth_client.json")
    return oauth_path.exists()


def main():
    """Run OAuth2 setup wizard."""
    print_header("DCGMail OAuth2 Setup Wizard")

    print("This wizard will help you set up OAuth2 authentication for DCGMail.")
    print("OAuth2 allows DCGMail to access Gmail WITHOUT requiring Admin Console access.\n")

    # Check if credentials already exist
    if check_oauth_client_exists():
        print_info("OAuth2 client credentials already exist at ./credentials/oauth_client.json")
        response = input("\nDo you want to replace them? (y/n): ").lower()
        if response != 'y':
            print("\nSetup cancelled.")
            return 0

    print_header("Prerequisites")
    print("[OK] Google Cloud Console access (cloud.google.com)")
    print("[OK] Project: dgautohub")
    print("[OK] Gmail API enabled")

    input("\nPress Enter to continue...")

    # Step 1: Navigate to Google Cloud Console
    print_header("Step 1: Create OAuth2 Client ID")

    print_step(1, "Open Google Cloud Console Credentials page")
    print("\nURL: https://console.cloud.google.com/apis/credentials?project=dgautohub")

    response = input("\nOpen this URL in browser? (y/n): ").lower()
    if response == 'y':
        webbrowser.open("https://console.cloud.google.com/apis/credentials?project=dgautohub")
        print(f"{GREEN}[OK]{RESET} Opened in browser\n")

    input("Press Enter when you're ready for the next step...")

    # Step 2: Configure OAuth consent screen
    print_header("Step 2: Configure OAuth Consent Screen (if not done)")

    print_step(1, "Click 'OAuth consent screen' in the left sidebar")
    print_step(2, "Select user type:")
    print("   - Internal: For consumrbuzz.com Workspace users")
    print("   - External: For personal Gmail (requires adding test users)")
    print_step(3, "Fill in app information:")
    print("   - App name: DCGMail")
    print("   - User support email: robert.d@consumrbuzz.com")
    print("   - Developer contact: robert.d@consumrbuzz.com")
    print_step(4, "Click 'Save and Continue'")
    print_step(5, "Add scopes:")
    print("   - https://www.googleapis.com/auth/gmail.readonly")
    print("   - https://www.googleapis.com/auth/gmail.modify")
    print_step(6, "Click 'Save and Continue'")
    print_step(7, "If External: Add test user 'robert.d@consumrbuzz.com'")
    print_step(8, "Click 'Save and Continue'")

    input("\nPress Enter when OAuth consent screen is configured...")

    # Step 3: Create OAuth Client ID
    print_header("Step 3: Create OAuth 2.0 Client ID")

    print_step(1, "Go back to 'Credentials' tab")
    print_step(2, "Click '+ CREATE CREDENTIALS' at the top")
    print_step(3, "Select 'OAuth client ID'")
    print_step(4, "Application type: 'Desktop app'")
    print_step(5, "Name: 'DCGMail Desktop Client'")
    print_step(6, "Click 'CREATE'")

    input("\nPress Enter when OAuth Client ID is created...")

    # Step 4: Download credentials
    print_header("Step 4: Download OAuth Client Credentials")

    print_step(1, "In the credentials list, find 'DCGMail Desktop Client'")
    print_step(2, "Click the download icon (download) on the right")
    print_step(3, "Save the JSON file as:")
    print(f"   {BOLD}./credentials/oauth_client.json{RESET}")

    print_info("\nMake sure the file is named exactly 'oauth_client.json'")

    input("\nPress Enter when you've downloaded the file...")

    # Step 5: Verify download
    print_header("Step 5: Verify Setup")

    if check_oauth_client_exists():
        print(f"{GREEN}[OK]{RESET} Found: ./credentials/oauth_client.json")
    else:
        print(f"{YELLOW}[WARN]{RESET} NOT FOUND: ./credentials/oauth_client.json")
        print("\nPlease download the OAuth client credentials and save as:")
        print("./credentials/oauth_client.json")
        return 1

    # Step 6: Update .env
    print_header("Step 6: Update .env Configuration")

    print("Add this line to your .env file:")
    print(f"\n{CYAN}GMAIL_AUTH_TYPE=oauth2{RESET}\n")

    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()

        if 'GMAIL_AUTH_TYPE' in env_content:
            print(f"{GREEN}[OK]{RESET} GMAIL_AUTH_TYPE already configured in .env")
        else:
            response = input("Add GMAIL_AUTH_TYPE=oauth2 to .env now? (y/n): ").lower()
            if response == 'y':
                # Check if there's already an auth type line
                lines = env_content.split('\n')
                new_lines = []
                added = False

                for line in lines:
                    if line.strip().startswith('#') and 'Gmail' in line and not added:
                        new_lines.append(line)
                        new_lines.append('GMAIL_AUTH_TYPE=oauth2')
                        added = True
                    else:
                        new_lines.append(line)

                if not added:
                    new_lines.insert(0, 'GMAIL_AUTH_TYPE=oauth2')

                with open(env_path, 'w') as f:
                    f.write('\n'.join(new_lines))

                print(f"{GREEN}[OK]{RESET} Added GMAIL_AUTH_TYPE=oauth2 to .env")

    # Step 7: Test authentication
    print_header("Step 7: Test OAuth2 Authentication")

    print("Now test the OAuth2 authentication:")
    print(f"\n{CYAN}python main.py --validate-creds{RESET}\n")
    print("This will:")
    print("  1. Open your browser for Google OAuth consent")
    print("  2. Ask you to sign in and grant permissions")
    print("  3. Save the refresh token to ./credentials/token.json")
    print("  4. Future runs will use the saved token (no browser needed)")

    response = input("\nRun the test now? (y/n): ").lower()
    if response == 'y':
        print("\nRunning: python main.py --validate-creds\n")
        import subprocess
        result = subprocess.run([sys.executable, "main.py", "--validate-creds"])
        if result.returncode == 0:
            print(f"\n{GREEN}[OK]{RESET} OAuth2 authentication successful!")
        else:
            print(f"\n{YELLOW}[WARN]{RESET} Authentication failed. Check the error above.")
            return 1

    # Success!
    print_header("Setup Complete!")

    print(f"{GREEN}[OK]{RESET} OAuth2 credentials configured")
    print(f"{GREEN}[OK]{RESET} Ready to use DCGMail")

    print("\nNext steps:")
    print("  1. Test with: python main.py --dry-run --limit 5")
    print("  2. Configure Telegram bot (optional)")
    print("  3. Run: python main.py --limit 10")

    print(f"\n{BOLD}You're all set!{RESET}\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(130)
