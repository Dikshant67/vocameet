from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

import datetime
import os
import logging
import datetime 
from dateutil import parser
import pytz
SCOPES = ["https://www.googleapis.com/auth/calendar"]

logger = logging.getLogger("agent")

class CalendarService:
    """A service for interacting with Google Calendar."""

    def __init__(self, credentials_path: str = "../config/credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._get_calendar_service()

    def _get_calendar_service(self):
        """Authenticate and return the Google Calendar service object."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=8080,access_type="offline", prompt="consent")

            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        return build("calendar", "v3", credentials=creds)

    def create_meeting(self, summary: str, start_time: str, end_time: str, attendees: list[str],timezone : str):
        """Create a new calendar meeting."""
        cleaned_attendees = [email.replace(' ', '') for email in attendees]
        event = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": timezone},
            "end": {"dateTime": end_time, "timeZone": timezone},
            "attendees": [{"email": email} for email in cleaned_attendees],
        }
        created_event = self.service.events().insert(calendarId="primary", body=event).execute()
        return created_event.get("id"), created_event.get("htmlLink")

    def list_meetings(self, max_results: int = 10):
        """List upcoming meetings."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events_result = (
            self.service.events()
            .list(calendarId="primary", timeMin=now, maxResults=max_results, singleEvents=True, orderBy="startTime")
            .execute()
        )
        logger.info(events_result)
        return events_result.get("items", [])

    def cancel_meeting(self, event_id: str):
        """Cancel a meeting by event ID."""
        self.service.events().delete(calendarId="primary", eventId=event_id).execute()
        return True

    def reschedule_meeting(self, event_id: str, new_start: str, new_end: str):
        """Reschedule an existing meeting."""
        event = self.service.events().get(calendarId="primary", eventId=event_id).execute()
        event["start"]["dateTime"] = new_start
        event["end"]["dateTime"] = new_end
        updated_event = self.service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        return updated_event.get("htmlLink")    
    
    def process_events(self, events: list, timezone: str):
        """Convert raw Google Calendar events into frontend-friendly format."""
        try:
            
            tz = pytz.timezone(timezone)
    
            processed_events = []
            for event in events:
                #start_time_aware = parser.parse(event["start"]["dateTime"])
                #end_time_aware = parser.parse(event["end"]["dateTime"])
                start = event.get("start", {})
                if "dateTime" in start:
                    start_time_aware = parser.parse(start["dateTime"])
                elif "date" in start:
                    start_time_aware = parser.parse(start["date"])
                else:
            # If neither exists, skip
                    continue

                end = event.get("end", {})
                if "dateTime" in end:
                    end_time_aware = parser.parse(end["dateTime"])
                elif "date" in start:
                    end_time_aware = parser.parse(end["date"])
                else:
            # If neither exists, skip
                    continue


                processed_events.append({
                    "id": event.get("id", ""),
                    "title": event.get("summary", "No Title"),
                    "description": event.get("description", ""),
                    "location": event.get("location", ""),
                    "status": event.get("status", "confirmed"),
                    "organizer": event.get("organizer", {}).get("email", ""),
                    "creator": event.get("creator", {}).get("email", ""),
                    "created": event.get("created", ""),
                    "updated": event.get("updated", ""),
                    "attendees": event.get("attendees", []),
                    "hangoutLink": event.get("hangoutLink", ""),
                    "htmlLink": event.get("htmlLink", ""),
                    "recurrence": event.get("recurrence", []),
                    "recurringEventId": event.get("recurringEventId", ""),
                    "start": start_time_aware.astimezone(tz).isoformat(),
                    "end": end_time_aware.astimezone(tz).isoformat(),
                })
    
            return processed_events
    
        except Exception as e:
            logger.error(f"Error in process_events: {e}", exc_info=True)
            return []