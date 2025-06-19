import datetime
from googleapiclient.errors import HttpError
from tools.google_auth import get_calendar_service

def main():
    try:
        service = get_calendar_service()
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print('Getting the upcoming 10 events...')
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        print("\n--- Your Upcoming Events ---")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"Event: {event['summary']}")
            print(f"  Starts: {start}\n")
        print("--------------------------")

    except HttpError as error:
        print(f'An error occurred: {error}')
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()