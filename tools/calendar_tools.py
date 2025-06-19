import os
import re
import calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional,Dict,Optional
import dateparser
from dotenv import load_dotenv
from langchain_core.tools import tool
import pickle
import json
from tools.google_auth import get_calendar_service

load_dotenv()

GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2,
    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
}

def retrieve_timezones() -> Dict[str, str]:
    """Loads user timezones from the pickle file, handling errors gracefully."""
    path = os.getenv("USERS_TIMEZONES_PATH")
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return {}

def parse_natural_date(natural_str: str, reference_timezone: str = "UTC") -> str:
    natural_str_lower = natural_str.strip().lower()
    today = datetime.now(ZoneInfo(reference_timezone))

    if natural_str_lower == "today":
        return today.date().isoformat()
    if natural_str_lower == "tomorrow":
        return (today + timedelta(days=1)).date().isoformat()

    weekday_match = re.search(r"(this|next)?\s*(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", natural_str_lower)
    if weekday_match:
        when, weekday_str = weekday_match.groups()
        target_weekday = WEEKDAYS[weekday_str]
        current_weekday = today.weekday()
        days_ahead = (target_weekday - current_weekday + 7) % 7
        if when == "next":
            days_ahead += 7
        elif when is None and days_ahead == 0:
            days_ahead = 7
        target_date = today + timedelta(days=days_ahead)
        return target_date.date().isoformat()

    if "last day of this month" in natural_str_lower or "end of this month" in natural_str_lower:
        _, num_days = calendar.monthrange(today.year, today.month)
        target_date = today.replace(day=num_days)
        return target_date.date().isoformat()

    if "last weekday of this month" in natural_str_lower:
        _, num_days = calendar.monthrange(today.year, today.month)
        last_day = today.replace(day=num_days)
        if last_day.weekday() == 5:
            target_date = last_day - timedelta(days=1)
        elif last_day.weekday() == 6:
            target_date = last_day - timedelta(days=2)
        else:
            target_date = last_day
        return target_date.date().isoformat()

    if "first day of next month" in natural_str_lower or "next month start" in natural_str_lower:
        first_of_this_month = today.replace(day=1)
        first_of_next_month = (first_of_this_month + timedelta(days=32)).replace(day=1)
        return first_of_next_month.date().isoformat()

    parsed_dt = dateparser.parse(
        natural_str,
        languages=['en'],
        settings={'TIMEZONE': reference_timezone, 'RETURN_AS_TIMEZONE_AWARE': True, 'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': today}
    )
    if not parsed_dt:
        raise ValueError(f"Unable to parse a valid date from the input: '{natural_str}'.")
    return parsed_dt.date().isoformat()

def _find_unique_event(service, event_name: str, event_date: Optional[str] = None):
    try:
        now_utc = datetime.now(ZoneInfo("UTC"))
        if event_date:
            event_date_iso = parse_natural_date(event_date)
            time_min = datetime.fromisoformat(f"{event_date_iso}T00:00:00").astimezone(ZoneInfo("UTC"))
            time_max = datetime.fromisoformat(f"{event_date_iso}T23:59:59").astimezone(ZoneInfo("UTC"))
        else:
            time_min = now_utc
            time_max = now_utc + timedelta(days=365)

        events_result = service.events().list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            q=event_name,
            singleEvents=True
        ).execute()
        events = events_result.get('items', [])

        if not events:
            date_info = f"on {event_date}" if event_date else "in the future"
            return None, f"Error: No event named '{event_name}' found {date_info}."

        if len(events) > 1:
            event_options = []
            for event in events:
                start_dt = datetime.fromisoformat(event['start'].get('dateTime')).astimezone(now_utc.tzinfo)
                event_options.append(f"'{event['summary']}' on {start_dt.strftime('%A, %B %d at %I:%M %p %Z')}")
            return None, f"Ambiguity Error: Found multiple events named '{event_name}'. Please be more specific by providing the date. Options found: {'; '.join(event_options)}."

        return events[0], None
    except Exception as e:
        return None, f"An error occurred while finding the event: {e}"

@tool
def get_todays_date() -> str:
    """
    Returns today's date in 'YYYY-MM-DD' format. No input arguments required.
    """
    return datetime.now().strftime('%Y-%m-%d')

@tool
def set_user_home_timezone(user_id: str, timezone: str) -> str:
    """
    Sets the user's home timezone. 
    Arguments: user_id (unique user identifier), timezone (IANA timezone string, e.g., 'Asia/Kolkata').
    """

    user_timezones = retrieve_timezones()
    try:
        ZoneInfo(timezone)
        user_timezones[user_id] = timezone
        with open(os.getenv("USERS_TIMEZONES_PATH"),"wb") as f: 
            pickle.dump(user_timezones,f)
        return f"Success. User's home timezone has been set to {timezone}."
    except Exception as e:
        return f"An error occurred: {str(e)}"

@tool 
def retrieve_user_timezone(user_id:str):
    """
    Return the user's home timezone. 
    Arguments: user_id (unique user identifier).
    """
    user_timezones = retrieve_timezones()
    if user_id in user_timezones.keys():
        return f"Timezone of user's ID {user_id} is {user_timezones[user_id]}"
    else: 
        return f"Timezone of user's ID {user_id} not found."

@tool
def check_availability(search_date: str, start_time: str, end_time: str, duration_minutes: int, timezone: str) -> str:
    """
    Checks for available time slots. If the requested window is busy, it AUTOMATICALLY searches for the next available slot within the next 7 days and suggests it.
    Arguments: search_date (e.g., 'next Monday', 'tomorrow'), start_time (e.g., '9:00AM' not like '9AM' or '9 AM' or '9 am' same for PM), end_time (e.g., '5:00PM' not like 5PM or 5 PM or 5pm same for AM), duration_minutes, timezone.
    """
    start_time=start_time.replace(" ","")
    end_time=end_time.replace(" ","")
    try:
        search_date_iso = parse_natural_date(search_date, timezone)
        search_start_date = datetime.fromisoformat(search_date_iso)
    except Exception as e:
        return f"Date parsing error: {e}"

    user_home_zone_str = timezone
    try:
        search_tz = ZoneInfo(timezone)
        home_tz = ZoneInfo(user_home_zone_str)
        start_dt_naive = datetime.fromisoformat(f"{search_date_iso}T{datetime.strptime(start_time, '%I:%M%p').strftime('%H:%M:%S')}")
        end_dt_naive = datetime.fromisoformat(f"{search_date_iso}T{datetime.strptime(end_time, '%I:%M%p').strftime('%H:%M:%S')}")
        start_dt_aware = start_dt_naive.replace(tzinfo=search_tz)
        end_dt_aware = end_dt_naive.replace(tzinfo=search_tz)
    except Exception as e:
        return f"Error parsing date/time. Details: {e}"

    start_utc = start_dt_aware.astimezone(ZoneInfo("UTC"))
    end_utc = end_dt_aware.astimezone(ZoneInfo("UTC"))
    service = get_calendar_service()
    events_result = service.events().list(calendarId=GOOGLE_CALENDAR_ID, timeMin=start_utc.isoformat(), timeMax=end_utc.isoformat(), singleEvents=True, orderBy='startTime').execute()
    busy_slots = events_result.get('items', [])
    available_slots = []
    current_time_utc = start_utc
    meeting_duration = timedelta(minutes=duration_minutes)

    for event in busy_slots:
        event_start_utc = datetime.fromisoformat(event['start'].get('dateTime'))
        if current_time_utc + meeting_duration <= event_start_utc:
            available_slots.append(current_time_utc)
        current_time_utc = max(current_time_utc, datetime.fromisoformat(event['end'].get('dateTime')))
    if current_time_utc + meeting_duration <= end_utc:
        available_slots.append(current_time_utc)

    if available_slots:
        formatted_results = []
        for slot_utc in available_slots:
            slot_in_search_tz = slot_utc.astimezone(search_tz)
            slot_in_home_tz = slot_utc.astimezone(home_tz)
            formatted_results.append({
                "utc_iso_format": slot_utc.isoformat(),
                "target_timezone_format": slot_in_search_tz.strftime('%I:%M %p (%Z)'),
                "home_timezone_format": slot_in_home_tz.strftime('%I:%M %p your time (%Z)')
            })
        return f"Available slots found: {formatted_results}"

    conflict_reason = f" The requested time on {search_date} is fully booked"
    if busy_slots:
        conflicting_names = [event.get('summary', 'Untitled') for event in busy_slots]
        conflict_reason += f" by: {', '.join(conflicting_names)}."
    else:
        conflict_reason += "."
        
    for i in range(1, 8):
        next_day_to_check = search_start_date + timedelta(days=i)
        window_start = next_day_to_check.replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=search_tz)
        window_end = next_day_to_check.replace(hour=20, minute=0, second=0, microsecond=0, tzinfo=search_tz)
        
        start_utc_fb = window_start.astimezone(ZoneInfo("UTC"))
        end_utc_fb = window_end.astimezone(ZoneInfo("UTC"))

        fb_events_result = service.events().list(calendarId=GOOGLE_CALENDAR_ID, timeMin=start_utc_fb.isoformat(), timeMax=end_utc_fb.isoformat(), singleEvents=True, orderBy='startTime').execute()
        fb_busy_slots = fb_events_result.get('items', [])
        fb_current_time = start_utc_fb
        
        for event in fb_busy_slots:
            event_start_utc = datetime.fromisoformat(event['start'].get('dateTime'))
            if fb_current_time + meeting_duration <= event_start_utc:
                slot_utc = fb_current_time
                slot_in_home_tz = slot_utc.astimezone(home_tz)
                suggestion = f"The next available slot is on {slot_in_home_tz.strftime('%A, %B %d at %I:%M %p %Z')}."
                return f"{conflict_reason} {suggestion}"
            fb_current_time = max(fb_current_time, datetime.fromisoformat(event['end'].get('dateTime')))

        if fb_current_time + meeting_duration <= end_utc_fb:
            slot_utc = fb_current_time
            slot_in_home_tz = slot_utc.astimezone(home_tz)
            suggestion = f"The next available slot is on {slot_in_home_tz.strftime('%A, %B %d at %I:%M %p %Z')}."
            return f"{conflict_reason} {suggestion}"

    return f"{conflict_reason} No other availability was found in the next 7 days."

@tool
def delete_calendar_event(event_name: str, event_date: Optional[str] = None) -> str:
    """
    Deletes a calendar event. 
    Arguments: event_name (title of the event), event_date (Optional. e.g., 'next Friday', '2024-09-15'). If omitted, finds a unique future event.
    """
    service = get_calendar_service()
    event_to_delete, error = _find_unique_event(service, event_name, event_date)
    if error:
        return error
    try:
        service.events().delete(calendarId=GOOGLE_CALENDAR_ID, eventId=event_to_delete['id']).execute()
        return f"Success. The event '{event_name}' has been deleted."
    except Exception as e:
        return f"An error occurred while deleting the event: {e}"

@tool
def reschedule_calendar_event(old_event_name: str, new_start_iso: str, new_timezone: str, old_event_date: Optional[str] = None) -> str:
    """
    Reschedules a calendar event. 
    Arguments: old_event_name, new_start_iso (e.g., '2025-06-30T14:00:00' or 'next Friday at 4pm'), new_timezone (IANA string), old_event_date (Optional. e.g., 'this Friday').
    """

    service = get_calendar_service()
    original_event, error = _find_unique_event(service, old_event_name, old_event_date)
    if error:
        return error

    try:
        try:
            new_start_dt = datetime.fromisoformat(new_start_iso)
            if new_start_dt.tzinfo is None:
                new_start_aware = new_start_dt.replace(tzinfo=ZoneInfo(new_timezone))
            else:
                new_start_aware = new_start_dt.astimezone(ZoneInfo(new_timezone))
        except ValueError:
            date_part_iso = parse_natural_date(new_start_iso, new_timezone)
            date_obj = datetime.fromisoformat(date_part_iso).date()

            time_match = re.search(r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b', new_start_iso, re.IGNORECASE)
            if not time_match:
                time_match = re.search(r'\b(\d{1,2}:\d{2})\b', new_start_iso)
                if not time_match:
                    return f"Error: Could not find a specific time in new_start_iso: '{new_start_iso}'."

            time_str = time_match.group(1)
            time_obj = None
            for fmt in ('%I:%M%p', '%I%p', '%H:%M'):
                try:
                    time_obj = datetime.strptime(time_str.replace(" ", "").upper(), fmt).time()
                    break
                except ValueError:
                    continue
            if time_obj is None:
                return f"Error: Unrecognized time format in '{time_str}'."

            naive_dt = datetime.combine(date_obj, time_obj)
            new_start_aware = naive_dt.replace(tzinfo=ZoneInfo(new_timezone))

        original_start = datetime.fromisoformat(original_event['start']['dateTime'])
        original_end = datetime.fromisoformat(original_event['end']['dateTime'])
        duration = original_end - original_start
        new_end_aware = new_start_aware + duration

        original_event['start']['dateTime'] = new_start_aware.isoformat()
        original_event['start']['timeZone'] = new_timezone
        original_event['end']['dateTime'] = new_end_aware.isoformat()
        original_event['end']['timeZone'] = new_timezone

        service.events().update(calendarId=GOOGLE_CALENDAR_ID, eventId=original_event['id'], body=original_event).execute()
        return f"Success. The event '{old_event_name}' has been rescheduled to {new_start_aware.strftime('%A, %B %d at %I:%M %p %Z')}."
    except Exception as e:
        return f"An error occurred while rescheduling: {e}"

@tool
def create_meeting(title: str, start_time_str: str, duration_minutes: int, event_timezone: str) -> str:
    """
    Creates a new calendar meeting. 
    Arguments: title, start_time_str (e.g., '2025-06-30T14:00:00Z' or 'next Friday at 2:30pm'), duration_minutes, event_timezone (e.g., 'America/New_York').
    """

    try:
        service = get_calendar_service()
        try:
            if "T" in start_time_str:
                dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo(event_timezone))
                else:
                    dt = dt.astimezone(ZoneInfo(event_timezone))
            else:
                raise ValueError
        except Exception:
            date_part_iso = parse_natural_date(start_time_str, event_timezone)
            date_obj = datetime.fromisoformat(date_part_iso).date()
            time_str_match = re.search(r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b', start_time_str, re.IGNORECASE)
            if not time_str_match:
                time_str_match = re.search(r'\b(\d{1,2}:\d{2})\b', start_time_str)
                if not time_str_match:
                    return f"Error: Could not find a specific time in your request: '{start_time_str}'."
            time_str = time_str_match.group(1)
            time_obj = None
            for fmt in ('%I:%M%p', '%I%p', '%H:%M'):
                try:
                    time_obj = datetime.strptime(time_str.replace(" ", "").upper(), fmt).time()
                    break
                except ValueError:
                    continue
            if time_obj is None:
                return f"Error: Could not understand the time format of '{time_str}'."
            naive_datetime = datetime.combine(date_obj, time_obj)
            dt = naive_datetime.replace(tzinfo=ZoneInfo(event_timezone))
            if dt < datetime.now(ZoneInfo(event_timezone)):
                if not any(day in start_time_str.lower() for day in ['today', 'tomorrow'] + list(WEEKDAYS.keys())):
                    dt += timedelta(days=1)
        end_dt = dt + timedelta(minutes=duration_minutes)
        event = {
            'summary': title,
            'start': {'dateTime': dt.isoformat(), 'timeZone': event_timezone},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': event_timezone},
        }
        created_event = service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event).execute()
        return f"Success. The meeting '{title}' has been scheduled. View it here: {created_event.get('htmlLink')}"
    except Exception as e:
        return f"An error occurred: {e}"