import sys
from pathlib import Path
from src.providers.gmail_oauth_provider import GmailOAuth2Provider
from src.loggers.file_logger import FileLogger

def main():
    logger = FileLogger(name="Inspector", level="INFO")
    
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
    
    # Search specifically for daily.dev
    print("Fetching daily.dev emails...")
    results = provider.service.users().messages().list(
        userId='me',
        q='from:daily.dev',
        maxResults=3
    ).execute()
    
    messages = results.get('messages', [])
    
    with open("daily_dev_samples.txt", "w", encoding="utf-8") as f:
        for msg in messages:
            msg_detail = provider.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            email = provider._parse_email(msg_detail)
            body = provider._extract_body(msg_detail['payload'])
            
            f.write(f"=== SUBJECT: {email.subject} ===\n")
            f.write(f"=== DATE: {email.timestamp} ===\n")
            f.write(body)
            f.write("\n\n" + "="*50 + "\n\n")
            
    print("Dumped samples to daily_dev_samples.txt")

if __name__ == "__main__":
    main()
