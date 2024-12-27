from typing import List, Dict, Any, Optional
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dataclasses import dataclass

@dataclass
class TimeSlot:
    start_time: datetime.datetime
    end_time: datetime.datetime
    is_available: bool

class CalendarCheckingAgent:
    def __init__(self, google_auth_manager):
        self.credentials = google_auth_manager.get_credentials()
        self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
        
    def get_availability(self, 
                        start_time: datetime.datetime,
                        end_time: datetime.datetime,
                        calendar_id: str = 'primary') -> List[TimeSlot]:
        """Check calendar availability for a given time period"""
        
        # Ensure timezone awareness and format properly for Google Calendar API
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=datetime.timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=datetime.timezone.utc)
        
        # Format timestamps according to RFC3339 spec
        time_min = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        time_max = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Get events from calendar
        events_result = self.calendar_service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Create list of busy time slots
        busy_slots = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Handle all-day events differently
            if 'T' not in start:  # All-day event
                start = f"{start}T00:00:00Z"
                end = f"{end}T23:59:59Z"
            
            start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
            busy_slots.append(TimeSlot(start_dt, end_dt, False))
        
        # Find available slots between busy periods
        available_slots = []
        current_time = start_time
        
        for busy_slot in busy_slots:
            if current_time < busy_slot.start_time:
                available_slots.append(TimeSlot(
                    current_time,
                    busy_slot.start_time,
                    True
                ))
            current_time = busy_slot.end_time
        
        # Add final available slot if there's time after last busy slot
        if current_time < end_time:
            available_slots.append(TimeSlot(
                current_time,
                end_time,
                True
            ))
        
        return available_slots
    
    def find_next_available_slot(self, 
                               duration: datetime.timedelta,
                               start_from: datetime.datetime = None,
                               calendar_id: str = 'primary') -> Optional[TimeSlot]:
        """Find the next available time slot of specified duration"""
        if start_from is None:
            start_from = datetime.datetime.now(datetime.timezone.utc)
            
        # Look ahead 7 days by default
        end_time = start_from + datetime.timedelta(days=7)
        
        available_slots = self.get_availability(start_from, end_time, calendar_id)
        
        for slot in available_slots:
            slot_duration = slot.end_time - slot.start_time
            if slot_duration >= duration:
                return TimeSlot(
                    slot.start_time,
                    slot.start_time + duration,
                    True
                )
                
        return None
    
    def check_slot_availability(self,
                              start_time: datetime.datetime,
                              end_time: datetime.datetime,
                              calendar_id: str = 'primary') -> bool:
        """Check if a specific time slot is available"""
        events_result = self.calendar_service.events().list(
            calendarId=calendar_id,
            timeMin=start_time.isoformat() + 'Z',
            timeMax=end_time.isoformat() + 'Z',
            singleEvents=True
        ).execute()
        
        return len(events_result.get('items', [])) == 0 