# import ast
# from datetime import datetime, timedelta
# from zoneinfo import ZoneInfo

# from calendar_tools import (
#     get_todays_date,
#     set_user_home_timezone,
#     check_availability,
#     create_meeting,
#     delete_calendar_event,
#     reschedule_calendar_event,
#     parse_natural_date
# )

# def test_all_calendar_tools():
#     user_id = "test_user_001"
#     timezone = "America/New_York"
#     event1_title = "Project Planning Session"
#     event2_title = "Weekly Team Sync"
#     event3_title = "Sprint Demo (ISO Input)"

#     print("============================================")
#     print(f"🗓️  RUNNING CALENDAR TOOL INTEGRATION TEST")
#     print(f"🕖 Timezone: {timezone}")
#     print("============================================")

#     print("\n🛠️  --- Setting User Timezone ---")
#     print(set_user_home_timezone.invoke({"user_id": user_id, "timezone": timezone}))

#     print("\n📅  --- Getting Today's Date ---")
#     print(f"Today according to the tool is: {get_todays_date.invoke({})}")

#     print("\n🧠  --- Parsing Natural Dates ---")
#     print(f"🔸 'next Monday'         -> {parse_natural_date('next Monday', timezone)}")
#     print(f"🔸 'first of next month' -> {parse_natural_date('first day of next month', timezone)}")
#     print(f"🔸 'August 10, 2025'     -> {parse_natural_date('August 10, 2025', timezone)}")

#     print("\n🔍  --- Checking Availability ---")
#     availability_result = check_availability.invoke({
#         "user_id": user_id,
#         "search_date": "next Friday",
#         "start_time": "9:00AM",
#         "end_time": "12:00PM",
#         "duration_minutes": 30,
#         "timezone": timezone
#     })
#     print(f"Availability on next Friday: {availability_result}")
    
#     try:
#         slots_str = availability_result.split("Available slots found: ")[-1]
#         available_slots = ast.literal_eval(slots_str)
#         if available_slots:
#             print(f"✅ Successfully found {len(available_slots)} available slots.")
#     except (IndexError, SyntaxError, ValueError):
#         print("ℹ️  No available slots found or result was not parsable, continuing test.")

#     print(f"\n➕  --- Creating Meeting 1: '{event1_title}' (natural date) ---")
#     print(create_meeting.invoke({
#         "title": event1_title,
#         "start_time_str": "next Wednesday at 10am",
#         "duration_minutes": 45,
#         "event_timezone": timezone
#     }))

#     print(f"\n➕  --- Creating Meeting 2: '{event2_title}' (natural date) ---")
#     print(create_meeting.invoke({
#         "title": event2_title,
#         "start_time_str": "next Thursday at 2:30pm",
#         "duration_minutes": 30,
#         "event_timezone": timezone
#     }))

#     print(f"\n➕  --- Creating Meeting 3: '{event3_title}' (ISO format) ---")
#     iso_dt = (datetime.now(ZoneInfo(timezone)) + timedelta(days=7)).replace(hour=15, minute=0, second=0, microsecond=0).astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
#     print(create_meeting.invoke({
#         "title": event3_title,
#         "start_time_str": iso_dt,
#         "duration_minutes": 60,
#         "event_timezone": timezone
#     }))

#     print(f"\n🔁  --- Rescheduling Meeting 1 using ISO ---")
#     iso_resched = (datetime.now(ZoneInfo(timezone)) + timedelta(days=10)).replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
#     print(reschedule_calendar_event.invoke({
#         "old_event_name": event1_title,
#         "new_start_iso": iso_resched,
#         "new_timezone": timezone
#     }))

#     print(f"\n🔁  --- Rescheduling Meeting 3 using natural date ---")
#     print(reschedule_calendar_event.invoke({
#         "old_event_name": event3_title,
#         "new_start_iso": "next Saturday at 3:00pm",
#         "new_timezone": timezone
#     }))

#     print(f"\n❌  --- Deleting Meeting 2 using specific natural date ---")
#     print(delete_calendar_event.invoke({
#         "event_name": event2_title,
#         "event_date": "next Thursday"
#     }))

#     print(f"\n❌  --- Deleting Meeting 1 (by name only) ---")
#     print(delete_calendar_event.invoke({
#         "event_name": event1_title
#     }))

#     print(f"\n❌  --- Deleting Meeting 3 (by name only) ---")
#     print(delete_calendar_event.invoke({
#         "event_name": event3_title
#     }))

#     print("\n============================================")
#     print("✅  TEST SCRIPT COMPLETED")
#     print("============================================")

# if __name__ == "__main__":
#     test_all_calendar_tools()
import traceback
from calendar_tools import check_availability

def run_test(name, data, expect_success=True):
    print(f"\n🧪 {name}")
    try:
        result = check_availability.invoke(data)
        print(f"✅ {result}")
        if not expect_success:
            print("❌ Unexpected success")
    except Exception:
        if expect_success:
            print("❌ Unexpected failure")
        else:
            print("❌ Expected failure")
        traceback.print_exc()

def test_check_availability_cases():
    uid = "test_user_02"
    tz = "America/New_York"

    run_test("TC01_ValidSearch", {
        "user_id": uid,
        "search_date": "next Monday",
        "start_time": "9:00AM",
        "end_time": "11:00AM",
        "duration_minutes": 30,
        "timezone": tz
    })

    run_test("TC02_ZeroWindow", {
        "user_id": uid,
        "search_date": "next Tuesday",
        "start_time": "2:00PM",
        "end_time": "2:00PM",
        "duration_minutes": 60,
        "timezone": tz
    }, expect_success=False)

    run_test("TC03_InvalidFormat_Space", {
        "user_id": uid,
        "search_date": "next Tuesday",
        "start_time": "2:00 PM",
        "end_time": "3:00 PM",
        "duration_minutes": 30,
        "timezone": tz
    }, expect_success=False)

    run_test("TC04_InvalidFormat_MissingMinutes", {
        "user_id": uid,
        "search_date": "next Wednesday",
        "start_time": "2PM",
        "end_time": "4PM",
        "duration_minutes": 30,
        "timezone": tz
    }, expect_success=False)

    run_test("TC05_InvalidTimeOrder", {
        "user_id": uid,
        "search_date": "next Thursday",
        "start_time": "4:00PM",
        "end_time": "3:00PM",
        "duration_minutes": 30,
        "timezone": tz
    }, expect_success=False)

    run_test("TC06_DurationTooLong", {
        "user_id": uid,
        "search_date": "next Friday",
        "start_time": "9:00AM",
        "end_time": "9:30AM",
        "duration_minutes": 60,
        "timezone": tz
    }, expect_success=False)

    run_test("TC07_MissingDuration", {
        "user_id": uid,
        "search_date": "next Saturday",
        "start_time": "9:00AM",
        "end_time": "11:00AM",
        "timezone": tz
    }, expect_success=False)

    run_test("TC08_MissingUserID", {
        "search_date": "next Sunday",
        "start_time": "9:00AM",
        "end_time": "11:00AM",
        "duration_minutes": 30,
        "timezone": tz
    }, expect_success=False)

    run_test("TC09_InvalidTimezone", {
        "user_id": uid,
        "search_date": "next Monday",
        "start_time": "9:00AM",
        "end_time": "11:00AM",
        "duration_minutes": 30,
        "timezone": "Mars/Phobos"
    }, expect_success=False)

    run_test("TC10_NaturalDateString", {
        "user_id": uid,
        "search_date": "first day of next month",
        "start_time": "10:00AM",
        "end_time": "12:00PM",
        "duration_minutes": 30,
        "timezone": tz
    })

    run_test("TC11_MultipleSlots", {
        "user_id": uid,
        "search_date": "next Tuesday",
        "start_time": "9:00AM",
        "end_time": "5:00PM",
        "duration_minutes": 30,
        "timezone": tz
    })

if __name__ == "__main__":
    test_check_availability_cases()
