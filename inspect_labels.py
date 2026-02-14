import sys
from pathlib import Path
from src.providers.gmail_oauth_provider import GmailOAuth2Provider
from src.loggers.file_logger import FileLogger

def main():
    logger = FileLogger(name="LabelInspector", level="INFO")
    
    if Path("./credentials/oauth_client.json").exists():
        provider = GmailOAuth2Provider(
            oauth_client_path="./credentials/oauth_client.json",
            token_path="./credentials/token.json",
            logger=logger
        )
    else:
        print("No creds found")
        return

    provider.authenticate()
    
    print("Fetching labels...")
    results = provider.service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    
    print(f"Found {len(labels)} labels:")
    for label in labels:
        print(f"- {label['name']} (ID: {label['id']}, Type: {label['type']})")

if __name__ == "__main__":
    main()
