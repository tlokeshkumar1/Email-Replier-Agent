from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

def get_calendar_service():
    creds = Credentials.from_authorized_user_file("token.json")
    return build("calendar", "v3", credentials=creds)

def create_meeting_event(start_time: datetime, summary: str, attendee_email: str):
    service = get_calendar_service()
    timezone = 'Asia/Kolkata'
    start = start_time.replace(tzinfo=pytz.utc).astimezone(pytz.timezone(timezone))
    end = start + timedelta(minutes=30)

    event = {
        'summary': summary,
        'start': {'dateTime': start.isoformat(), 'timeZone': timezone},
        'end': {'dateTime': end.isoformat(), 'timeZone': timezone},
        'attendees': [{'email': attendee_email}],
        'conferenceData': {
            'createRequest': {
                'requestId': 'meet1234',
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        }
    }

    created_event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()

    return created_event['hangoutLink']