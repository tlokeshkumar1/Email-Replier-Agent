from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import os, time, re, base64, requests
from dotenv import load_dotenv
from threading import Thread

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from utils.gemini_utils import analyze_email
from utils.calendar_utils import create_meeting_event
from utils.email_utils import send_email_reply
from utils.whitelist import is_allowed_sender

load_dotenv()
app = FastAPI()

class EmailInput(BaseModel):
    from_email: str
    subject: str
    body: str

@app.post("/email")
def handle_email(email: EmailInput):
    if not is_allowed_sender(email.from_email):
        return {"reason": "sender not in whitelist"}

    summary, intent, reply_text, meeting_time = analyze_email(email.body)

    if intent == "reply":
        send_email_reply(email.from_email, reply_text)
        return {"status": "replied", "action": "reply", "summary": summary, "intent": intent}

    elif intent == "schedule_meeting":
        link = create_meeting_event(meeting_time, "Scheduled Meeting", email.from_email)
        followup = f"{reply_text}\n\nI've scheduled our meeting at {meeting_time}. You can join via this Google Meet link: {link}. Please let me know if this time works for you."
        send_email_reply(email.from_email, followup)
        return {"status": "scheduled", "action": "calendar", "link": link, "summary": summary, "intent": intent}

    elif intent == "urgent_meeting":
        start_time = datetime.utcnow() + timedelta(minutes=10)
        link = create_meeting_event(start_time, "Urgent Meeting", email.from_email)
        followup = f"{reply_text}\n\nI've created an urgent Google Meet that starts in 10 minutes. Join here: {link}. I'll be available to discuss immediately."
        send_email_reply(email.from_email, followup)
        return {"status": "urgent", "link": link, "summary": summary, "intent": intent}

    elif intent == "casual_meeting":
        start_time = datetime.utcnow() + timedelta(hours=1)
        link = create_meeting_event(start_time, "Casual Meeting", email.from_email)
        followup = f"{reply_text}\n\nLooking forward to catching up! I've scheduled a casual Google Meet in 1 hour. Here's the link: {link}."
        send_email_reply(email.from_email, followup)
        return {"status": "casual", "link": link, "summary": summary, "intent": intent}


# Gmail Polling Logic

processed_ids = set()

def get_gmail_service():
    creds = Credentials.from_authorized_user_file("token.json")
    return build("gmail", "v1", credentials=creds)

def extract_email_details(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = msg['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

    parts = msg['payload'].get('parts', [])
    body = ""
    for part in parts:
        if part['mimeType'] == 'text/plain':
            data = part['body'].get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break

    return sender, subject, body

def extract_email(from_field):
    match = re.search(r'<(.*?)>', from_field)
    return match.group(1) if match else from_field

def poll_gmail():
    service = get_gmail_service()
    while True:
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
        messages = results.get('messages', [])
        for msg in messages:
            msg_id = msg['id']
            if msg_id in processed_ids:
                continue

            sender, subject, body = extract_email_details(service, msg_id)
            email_only = extract_email(sender)
            payload = {"from_email": email_only, "subject": subject, "body": body}

            try:
                r = requests.post("http://localhost:8000/email", json=payload)
                print(f"Processed email from {email_only}: {r.status_code} {r.json()}")
                processed_ids.add(msg_id)
            except Exception as e:
                print("Error calling /email:", e)

        time.sleep(30)

@app.on_event("startup")
def start_gmail_poller():
    Thread(target=poll_gmail, daemon=True).start()
