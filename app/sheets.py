import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()

SHEET_ID= os.getenv("GOOGLE_SHEETS_ID")
SCOPES= ["https://www.googleapis.com/auth/spreadsheets"]
CREDS_FILE= "credentials.json"

BOOKINGS_SHEET = "bookings"
SLOTS_SHEET= "slots"

COL_PATIENT = 0
COL_EMAIL   = 1
COL_DOCTOR  = 2
COL_DATE    = 3
COL_TIME    = 4
COL_STATUS  = 5

SLOT_DOCTOR = 0
SLOT_DATE   = 1
SLOT_TIME   = 2
SLOT_STATUS = 3

_service = None

def _get_service():
    global _service
    if _service is None:
        creds= Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        _service = build("sheets", "v4", credentials=creds)
    return _service


def _read_sheet(tab: str) -> list[list]:
    service = _get_service()
    result  = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"{tab}!A:Z"
    ).execute()
    rows = result.get("values", [])
    return rows


def _append_row(tab: str, row: list):
    service = _get_service()
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{tab}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]}
    ).execute()


def _update_cell(tab: str, row_index: int, col_index: int, value: str):
    service = _get_service()
    col_letter = chr(65 + col_index)  
    row_number = row_index + 2       
    cell_range = f"{tab}!{col_letter}{row_number}"
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=cell_range,
        valueInputOption="RAW",
        body={"values": [[value]]}
    ).execute()


def _delete_row(tab: str, row_index: int):
    service = _get_service()

    meta= service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheet_gid = None
    for s in meta["sheets"]:
        if s["properties"]["title"] == tab:
            sheet_gid = s["properties"]["sheetId"]
            break

    actual_index = row_index + 1

    service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={
            "requests": [{
                "deleteDimension": {
                    "range": {
                        "sheetId":    sheet_gid,
                        "dimension":  "ROWS",
                        "startIndex": actual_index,
                        "endIndex":   actual_index + 1,
                    }
                }
            }]
        }
    ).execute()


def generate_slots(doctors: list[dict], days_ahead: int = 14):
    from datetime import datetime, timedelta
    rows = _read_sheet(SLOTS_SHEET)
    if len(rows) > 1:
        return

    day_map = {
        "Sunday": 6, "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5
    }

    today= datetime.today()
    new_slots = []

    for doctor in doctors:
        working_days = doctor["working_days"]
        wh_start= doctor["working_hours"].split(" - ")[0].strip() 
        wh_end= doctor["working_hours"].split(" - ")[1].strip() 
        slot_dur= doctor["slot_duration_minutes"]

        def parse_time(t):
            t = t.lower().strip()
            if ":" in t:
                return datetime.strptime(t, "%I:%M%p")
            return datetime.strptime(t, "%I%p")

        start_dt = parse_time(wh_start)
        end_dt   = parse_time(wh_end)

        for i in range(days_ahead):
            day= today + timedelta(days=i)
            day_name= day.strftime("%A")
            if day_name not in working_days:
                continue
            date_str= day.strftime("%Y-%m-%d")

            current = start_dt
            while current < end_dt:
                time_str = current.strftime("%I:%M %p").lstrip("0")
                new_slots.append([doctor["name"], date_str, time_str, "free"])
                current += timedelta(minutes=slot_dur)

    service = _get_service()
    service.spreadsheets().values().append(
        spreadsheetId=SHEET_ID,
        range=f"{SLOTS_SHEET}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": new_slots}
    ).execute()


def get_free_slots(doctor_name: str, date: str) -> list[str]:
    rows = _read_sheet(SLOTS_SHEET)
    free = []
    for row in rows[1:]:   
        if (len(row) >= 4
                and row[SLOT_DOCTOR].lower() == doctor_name.lower()
                and row[SLOT_DATE]   == date
                and row[SLOT_STATUS] == "free"):
            free.append(row[SLOT_TIME])
    return free


def _find_slot_row(doctor_name: str, date: str, time: str) -> int | None:
    rows = _read_sheet(SLOTS_SHEET)
    for i, row in enumerate(rows[1:]):
        if (len(row) >= 4
                and row[SLOT_DOCTOR].lower() == doctor_name.lower()
                and row[SLOT_DATE]   == date
                and row[SLOT_TIME]   == time):
            return i
    return None


def mark_slot_booked(doctor_name: str, date: str, time: str):
    idx = _find_slot_row(doctor_name, date, time)
    if idx is not None:
        _update_cell(SLOTS_SHEET, idx, SLOT_STATUS, "booked")


def mark_slot_free(doctor_name: str, date: str, time: str):
    idx = _find_slot_row(doctor_name, date, time)
    if idx is not None:
        _update_cell(SLOTS_SHEET, idx, SLOT_STATUS, "free")


def _find_booking_row(patient_name: str) -> tuple[int, list] | tuple[None, None]:
    rows = _read_sheet(BOOKINGS_SHEET)
    for i, row in enumerate(rows[1:]):
        if (len(row) >= 6
                and row[COL_PATIENT].lower() == patient_name.lower()
                and row[COL_STATUS]  == "confirmed"):
            return i, row
    return None, None


def create_booking(patient_name: str, email: str, doctor: str, date: str, time: str) -> bool:
    free = get_free_slots(doctor, date)
    if time not in free:
        return False

    _append_row(BOOKINGS_SHEET, [patient_name, email, doctor, date, time, "confirmed"])
    mark_slot_booked(doctor, date, time)
    return True


def cancel_booking(patient_name: str) -> tuple[bool, dict]:
    idx, row = _find_booking_row(patient_name)
    if idx is None:
        return False, {}
    details = {
        "doctor": row[COL_DOCTOR],
        "date":   row[COL_DATE],
        "time":   row[COL_TIME],
        "email":  row[COL_EMAIL],
    }

    mark_slot_free(details["doctor"], details["date"], details["time"])
    _delete_row(BOOKINGS_SHEET, idx)
    return True, details


def update_booking(patient_name: str, field: str, new_value: str) -> tuple[bool, dict]:
    idx, row = _find_booking_row(patient_name)
    if idx is None:
        return False, {}
    old_details = {
        "doctor": row[COL_DOCTOR],
        "date":   row[COL_DATE],
        "time":   row[COL_TIME],
        "email":  row[COL_EMAIL],
    }

    field_map = {
        "doctor": COL_DOCTOR,
        "date":   COL_DATE,
        "time":   COL_TIME,
        "email":  COL_EMAIL,
    }

    if field not in field_map:
        return False, {}

    if field in ("doctor", "date", "time"):
        new_doctor = new_value if field == "doctor" else old_details["doctor"]
        new_date= new_value if field == "date"   else old_details["date"]
        new_time= new_value if field == "time"   else old_details["time"]

        free = get_free_slots(new_doctor, new_date)
        if new_time not in free:
            return False, {}

        mark_slot_free(old_details["doctor"], old_details["date"], old_details["time"])
        mark_slot_booked(new_doctor, new_date, new_time)

    _update_cell(BOOKINGS_SHEET, idx, field_map[field], new_value)

    updated = old_details.copy()
    updated[field] = new_value
    return True, updated


def get_booking(patient_name: str) -> dict | None:
    _, row = _find_booking_row(patient_name)
    if row is None:
        return None
    return {
        "patient_name": row[COL_PATIENT],
        "email": row[COL_EMAIL],
        "doctor": row[COL_DOCTOR],
        "date": row[COL_DATE],
        "time": row[COL_TIME],
        "status": row[COL_STATUS],
    }