from langchain_core.tools import tool
from app.rag import search
from app.sheets import (get_free_slots,get_booking,create_booking,cancel_booking,update_booking,)
from app.email_service import (send_confirmation,send_cancellation,send_update,)


@tool
def search_clinic_info(query: str) -> str:
    """
    Search for information about doctors, their specializations, experience,
    working days, consultation fees, and general clinic FAQs like location,
    hours, parking, and insurance.
    Use this when the patient asks anything about the clinic or doctors.
    """
    result = search(query)
    return result


@tool
def check_availability(doctor_name: str, date: str) -> str:
    """
    Check available appointment slots for a specific doctor on a specific date.
    date must be in YYYY-MM-DD format.
    Use this before booking to show the patient what times are free.
    """
    slots = get_free_slots(doctor_name, date)
    if not slots:
        return f"No available slots for {doctor_name} on {date}."
    slots_str = ", ".join(slots)
    return f"Available slots for {doctor_name} on {date}: {slots_str}"


@tool
def book_appointment(patient_name: str,email: str,doctor: str,date: str,time: str) -> str:
    """
    Book an appointment for a patient.
    Requires: patient full name, email address, doctor full name,
    date (YYYY-MM-DD format), and time (must match an available slot exactly).
    Always check availability first before calling this tool.
    """
    success = create_booking(patient_name, email, doctor, date, time)
    if not success:
        return (f"Sorry, the slot at {time} with {doctor} on {date} is no longer available. "
            f"Please check availability again and choose another slot."
        )
    send_confirmation(email, patient_name, doctor, date, time)
    return (
        f"Appointment successfully booked for {patient_name} with {doctor} "
        f"on {date} at {time}. A confirmation email has been sent to {email}."
    )

@tool
def get_patient_booking(patient_name: str) -> str:
    """
    Retrieve the current active booking for a patient by their name.
    Use this when the patient asks about their existing appointment,
    or before cancelling or updating a booking.
    """
    booking = get_booking(patient_name)
    if not booking:
        return f"No active booking found for {patient_name}."
    return (
        f"Booking found for {patient_name}:\n"
        f"  Doctor: {booking['doctor']}\n"
        f"  Date:   {booking['date']}\n"
        f"  Time:   {booking['time']}\n"
        f"  Email:  {booking['email']}\n"
        f"  Status: {booking['status']}"
    )


@tool
def cancel_patient_booking(patient_name: str) -> str:
    """
    Cancel the active booking for a patient.
    Always confirm with the patient before calling this tool.
    A cancellation email will be sent automatically.
    """
    success, details = cancel_booking(patient_name)
    if not success:
        return f"No active booking found for {patient_name} to cancel."
    send_cancellation(details["email"],patient_name,details["doctor"],details["date"],details["time"],)
    return (
        f"Booking for {patient_name} with {details['doctor']} on "
        f"{details['date']} at {details['time']} has been successfully cancelled. "
        f"A cancellation email has been sent to {details['email']}."
    )

@tool
def update_patient_booking(patient_name: str,field: str,new_value: str) -> str:
    """
    Update a specific field in a patient's active booking.
    field must be one of: doctor, date, time, email.
    For time, date, or doctor changes, availability is checked automatically.
    A confirmation email with the update will be sent automatically.
    Always confirm the change with the patient before calling this tool.
    """
    success, updated = update_booking(patient_name, field, new_value)
    if not success:
        if not updated:
            return f"No active booking found for {patient_name}."
        return (
            f"Could not update booking — the requested {field} '{new_value}' "
            f"is not available. Please check availability and try again."
        )
    send_update(updated["email"],patient_name,updated["doctor"],updated["date"],updated["time"],field,new_value,)
    return (
        f"Booking for {patient_name} has been updated successfully. "
        f"{field.capitalize()} changed to {new_value}. "
        f"An update confirmation has been sent to {updated['email']}."
    )

tools = [search_clinic_info,check_availability,book_appointment,get_patient_booking,cancel_patient_booking,update_patient_booking,]
