import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES        = ["https://www.googleapis.com/auth/gmail.send"]
OAUTH_FILE    = "gmail_oauth.json"
TOKEN_FILE    = "token.json"
CLINIC_EMAIL  = os.getenv("CLINIC_EMAIL")
CLINIC_NAME   = "Cairo Medical Center"

_service = None


def _get_service():
    """
    Return (or create) the Gmail API service.
    First run: opens browser for OAuth consent.
    After that: uses saved token.json automatically.
    """
    global _service
    if _service is not None:
        return _service

    creds = None

    # Load saved token if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid token, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(OAUTH_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)


        # Save token for future runs
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    _service = build("gmail", "v1", credentials=creds)
    return _service


def _send_email(to: str, subject: str, html_body: str):
    """
    Build and send an email via Gmail API.
    Encodes the message in base64 as required by the API.
    """
    service = _get_service()

    message = MIMEMultipart("alternative")
    message["From"]    = f"{CLINIC_NAME} <{CLINIC_EMAIL}>"
    message["To"]      = to
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()


# ── Email templates ───────────────────────────────────────────────────────────
def send_confirmation(to: str, patient_name: str, doctor: str, date: str, time: str):
    """Send a booking confirmation email."""
    subject = f"Appointment Confirmed — {CLINIC_NAME}"
    body    = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
        <h2 style="color: #2c7be5;">Appointment Confirmed</h2>
        <p>Dear <strong>{patient_name}</strong>,</p>
        <p>Your appointment has been successfully booked. Here are your details:</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Doctor</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{doctor}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Date</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{date}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Time</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{time}</td>
            </tr>
        </table>
        <p style="margin-top: 20px;">Please arrive 10 minutes early and bring your national ID.</p>
        <p>If you need to cancel or reschedule, please contact us as soon as possible.</p>
        <br>
        <p>Best regards,<br><strong>{CLINIC_NAME}</strong></p>
    </div>
    """
    _send_email(to, subject, body)


def send_cancellation(to: str, patient_name: str, doctor: str, date: str, time: str):
    """Send a cancellation confirmation email."""
    subject = f"Appointment Cancelled — {CLINIC_NAME}"
    body    = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
        <h2 style="color: #e25c2c;">Appointment Cancelled</h2>
        <p>Dear <strong>{patient_name}</strong>,</p>
        <p>Your appointment has been successfully cancelled. Here were your details:</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Doctor</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{doctor}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Date</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{date}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Time</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{time}</td>
            </tr>
        </table>
        <p style="margin-top: 20px;">We hope to see you again soon. Feel free to book a new appointment anytime.</p>
        <br>
        <p>Best regards,<br><strong>{CLINIC_NAME}</strong></p>
    </div>
    """
    _send_email(to, subject, body)


def send_update(to: str, patient_name: str, doctor: str, date: str, time: str, changed_field: str, new_value: str):
    """Send an update confirmation email."""
    subject = f"Appointment Updated — {CLINIC_NAME}"
    body    = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
        <h2 style="color: #2c7be5;">Appointment Updated </h2>
        <p>Dear <strong>{patient_name}</strong>,</p>
        <p>Your appointment has been updated. Your <strong>{changed_field}</strong> has been changed to <strong>{new_value}</strong>.</p>
        <p>Here are your updated appointment details:</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Doctor</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{doctor}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Date</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{date}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Time</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{time}</td>
            </tr>
        </table>
        <p style="margin-top: 20px;">If you did not request this change, please contact us immediately.</p>
        <br>
        <p>Best regards,<br><strong>{CLINIC_NAME}</strong></p>
    </div>
    """
    _send_email(to, subject, body)


