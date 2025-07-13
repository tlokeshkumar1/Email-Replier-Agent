import base64
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_gmail_service():
    creds = Credentials.from_authorized_user_file("token.json")
    return build("gmail", "v1", credentials=creds)

def send_email_reply(to: str, message_text: str):
    service = get_gmail_service()
    message = {
        'raw': base64.urlsafe_b64encode(f"To: {to}\nSubject: Re: Auto-Reply\n\n{message_text}".encode("utf-8")).decode("utf-8")
    }
    service.users().messages().send(userId="me", body=message).execute()