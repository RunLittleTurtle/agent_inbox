import logging
import asyncio
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import Iterable
import pytz
import os
import json

from dateutil import parser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from eaia.schemas import EmailData

# Load executive AI assistant's local .env file for Gmail credentials
from dotenv import load_dotenv
_EXEC_AI_ROOT = Path(__file__).parent.parent
load_dotenv(_EXEC_AI_ROOT / '.env')

logger = logging.getLogger(__name__)
_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]


async def get_credentials(
    user_email: str,
    config: dict | None = None,
    langsmith_api_key: str | None = None
) -> Credentials:
    """Get Google API credentials using existing OAuth setup.

    Args:
        user_email: User's Gmail email address
        config: LangGraph config dict for loading credentials from Supabase user_secrets
        langsmith_api_key: Not used (kept for compatibility)

    Returns:
        Google OAuth2 credentials
    """
    logger.info(f"[get_credentials] Starting credential fetch for {user_email}")

    # Try to load from user_secrets table (via global config API)
    client_id = None
    client_secret = None
    refresh_token = None

    if config:
        try:
            import httpx

            # Extract user_id from LangGraph config
            logger.debug(f"[get_credentials] Config structure: {list(config.keys())}")

            user_id = config.get("configurable", {}).get("user_id")
            if not user_id:
                metadata = config.get("metadata", {})
                user_id = metadata.get("user_id") or metadata.get("clerk_user_id")
                logger.debug(f"[get_credentials] Extracted user_id from metadata: {user_id}")
            else:
                logger.debug(f"[get_credentials] Extracted user_id from configurable: {user_id}")

            if user_id:
                # Fetch global config (which includes user_secrets)
                config_api_url = os.getenv("CONFIG_API_URL", "http://localhost:8000")
                logger.info(f"[get_credentials] Fetching from CONFIG_API_URL: {config_api_url}")
                logger.info(f"[get_credentials] User ID: {user_id}")

                async with httpx.AsyncClient(timeout=5.0) as client_http:
                    fetch_url = f"{config_api_url}/api/config/values"
                    fetch_params = {"agent_id": "global", "user_id": user_id}
                    logger.debug(f"[get_credentials] Request: GET {fetch_url} params={fetch_params}")

                    response = await client_http.get(fetch_url, params=fetch_params)
                    logger.debug(f"[get_credentials] Response status: {response.status_code}")

                    if response.status_code == 200:
                        data = response.json()
                        google_workspace = data.get("google_workspace", {})
                        client_id = google_workspace.get("google_client_id")
                        client_secret = google_workspace.get("google_client_secret")
                        refresh_token = google_workspace.get("google_refresh_token")

                        # Log what we got (masked)
                        logger.debug(f"[get_credentials] Has client_id: {bool(client_id)}")
                        logger.debug(f"[get_credentials] Has client_secret: {bool(client_secret)}")
                        logger.debug(f"[get_credentials] Has refresh_token: {bool(refresh_token)}")

                        if all([client_id, client_secret, refresh_token]):
                            logger.info("✓ [get_credentials] Loaded Google credentials from user_secrets (Supabase)")
                        else:
                            missing = []
                            if not client_id: missing.append("client_id")
                            if not client_secret: missing.append("client_secret")
                            if not refresh_token: missing.append("refresh_token")
                            logger.warning(f"✗ [get_credentials] Incomplete credentials from Supabase. Missing: {', '.join(missing)}")
                    else:
                        logger.warning(f"✗ [get_credentials] Config API returned status {response.status_code}: {response.text[:200]}")
            else:
                logger.warning("✗ [get_credentials] No user_id found in config - skipping Supabase fetch")
                logger.debug(f"[get_credentials] Config keys checked: configurable.user_id, metadata.user_id, metadata.clerk_user_id")
        except Exception as e:
            logger.error(f"✗ [get_credentials] Failed to load credentials from user_secrets: {e}")
            import traceback
            logger.debug(f"[get_credentials] Traceback: {traceback.format_exc()[:500]}")

    # Fallback to environment variables (.env file)
    if not all([client_id, client_secret, refresh_token]):
        logger.info("[get_credentials] Attempting fallback to environment variables")

        env_client_id = os.getenv("GOOGLE_CLIENT_ID")
        env_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        env_refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

        logger.debug(f"[get_credentials] Env has GOOGLE_CLIENT_ID: {bool(env_client_id)}")
        logger.debug(f"[get_credentials] Env has GOOGLE_CLIENT_SECRET: {bool(env_client_secret)}")
        logger.debug(f"[get_credentials] Env has GMAIL_REFRESH_TOKEN: {bool(env_refresh_token)}")

        client_id = client_id or env_client_id
        client_secret = client_secret or env_client_secret
        refresh_token = refresh_token or env_refresh_token

        if all([client_id, client_secret, refresh_token]):
            logger.info("✓ [get_credentials] Loaded Google credentials from environment variables (.env)")
        else:
            logger.warning("✗ [get_credentials] Incomplete credentials from environment variables")

    if not all([client_id, client_secret, refresh_token]):
        missing = []
        if not client_id: missing.append("client_id")
        if not client_secret: missing.append("client_secret")
        if not refresh_token: missing.append("refresh_token")

        error_msg = (
            f"Missing Gmail OAuth credentials: {', '.join(missing)}. "
            "Please set Google Workspace credentials in Supabase user_secrets table or .env file"
        )
        logger.error(f"✗ [get_credentials] {error_msg}")
        raise ValueError(error_msg)

    # Create credentials with refresh token
    logger.info("[get_credentials] Creating Google OAuth2 Credentials object")
    logger.debug(f"[get_credentials] Token URI: https://oauth2.googleapis.com/token")
    logger.debug(f"[get_credentials] Scopes: {', '.join(_SCOPES)}")

    creds = Credentials(
        token=None,  # Will be refreshed automatically
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=_SCOPES
    )

    logger.info("✓ [get_credentials] Successfully created credentials object")
    return creds


def extract_message_part(msg):
    """Recursively walk through the email parts to find message body."""
    if msg["mimeType"] == "text/plain":
        body_data = msg.get("body", {}).get("data")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8")
    elif msg["mimeType"] == "text/html":
        body_data = msg.get("body", {}).get("data")
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode("utf-8")
    if "parts" in msg:
        for part in msg["parts"]:
            body = extract_message_part(part)
            if body:
                return body
    return "No message body available."


def parse_time(send_time: str):
    try:
        parsed_time = parser.parse(send_time)
        return parsed_time
    except (ValueError, TypeError) as e:
        raise ValueError(f"Error parsing time: {send_time} - {e}")


def create_message(sender, to, subject, message_text, thread_id, original_message_id):
    message = MIMEMultipart()
    message["to"] = ", ".join(to)
    message["from"] = sender
    message["subject"] = subject
    message["In-Reply-To"] = original_message_id
    message["References"] = original_message_id
    message["Message-ID"] = email.utils.make_msgid()
    msg = MIMEText(message_text)
    message.attach(msg)
    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    return {"raw": raw, "threadId": thread_id}


def get_recipients(
    headers,
    email_address,
    addn_receipients=None,
):
    recipients = set(addn_receipients or [])
    sender = None
    for header in headers:
        if header["name"].lower() in ["to", "cc"]:
            recipients.update(header["value"].replace(" ", "").split(","))
        if header["name"].lower() == "from":
            sender = header["value"]
    if sender:
        recipients.add(sender)  # Ensure the original sender is included in the response
    for r in list(recipients):
        if email_address in r:
            recipients.remove(r)
    return list(recipients)


async def send_message(service, user_id, message):
    message = await asyncio.to_thread(
        lambda: service.users().messages().send(userId=user_id, body=message).execute()
    )
    return message


async def send_email(
    email_id,
    response_text,
    email_address,
    config: dict | None = None,
    gmail_token: str | None = None,
    gmail_secret: str | None = None,
    addn_receipients=None,
):
    creds = await get_credentials(email_address, config=config)

    service = await asyncio.to_thread(build, "gmail", "v1", credentials=creds)
    message = await asyncio.to_thread(
        lambda: service.users().messages().get(userId="me", id=email_id).execute()
    )

    headers = message["payload"]["headers"]
    message_id = next(
        header["value"] for header in headers if header["name"].lower() == "message-id"
    )
    thread_id = message["threadId"]

    # Get recipients and sender
    recipients = get_recipients(headers, email_address, addn_receipients)

    # Create the response
    subject = next(
        header["value"] for header in headers if header["name"].lower() == "subject"
    )
    response_subject = subject
    response_message = create_message(
        "me", recipients, response_subject, response_text, thread_id, message_id
    )
    # Send the response
    await send_message(service, "me", response_message)


async def fetch_group_emails(
    to_email,
    minutes_since: int = 30,
    config: dict | None = None,
    gmail_token: str | None = None,
    gmail_secret: str | None = None,
) -> Iterable[EmailData]:
    creds = await get_credentials(to_email, config=config)

    service = await asyncio.to_thread(build, "gmail", "v1", credentials=creds)
    after = int((datetime.now() - timedelta(minutes=minutes_since)).timestamp())

    query = f"(to:{to_email} OR from:{to_email}) after:{after}"
    messages = []
    nextPageToken = None
    # Fetch messages matching the query
    while True:
        results = await asyncio.to_thread(
            lambda: service.users()
            .messages()
            .list(userId="me", q=query, pageToken=nextPageToken)
            .execute()
        )
        if "messages" in results:
            messages.extend(results["messages"])
        nextPageToken = results.get("nextPageToken")
        if not nextPageToken:
            break

    count = 0
    for message in messages:
        try:
            msg = await asyncio.to_thread(
                lambda: service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            thread_id = msg["threadId"]
            payload = msg["payload"]
            headers = payload.get("headers")
            # Get the thread details
            thread = await asyncio.to_thread(
                lambda: service.users().threads().get(userId="me", id=thread_id).execute()
            )
            messages_in_thread = thread["messages"]
            # Check the last message in the thread
            last_message = messages_in_thread[-1]
            last_headers = last_message["payload"]["headers"]
            from_header = next(
                header["value"] for header in last_headers if header["name"] == "From"
            )
            last_from_header = next(
                header["value"]
                for header in last_message["payload"].get("headers")
                if header["name"] == "From"
            )
            if to_email in last_from_header:
                yield {
                    "id": message["id"],
                    "thread_id": message["threadId"],
                    "user_respond": True,
                }
            # Check if the last message was from you and if the current message is the last in the thread
            if to_email not in from_header and message["id"] == last_message["id"]:
                subject = next(
                    header["value"] for header in headers if header["name"] == "Subject"
                )
                from_email = next(
                    (header["value"] for header in headers if header["name"] == "From"),
                    "",
                ).strip()
                _to_email = next(
                    (header["value"] for header in headers if header["name"] == "To"),
                    "",
                ).strip()
                if reply_to := next(
                    (
                        header["value"]
                        for header in headers
                        if header["name"] == "Reply-To"
                    ),
                    "",
                ).strip():
                    from_email = reply_to
                send_time = next(
                    header["value"] for header in headers if header["name"] == "Date"
                )
                # Only process emails that are less than an hour old
                parsed_time = parse_time(send_time)
                body = extract_message_part(payload)
                yield {
                    "from_email": from_email,
                    "to_email": _to_email,
                    "subject": subject,
                    "page_content": body,
                    "id": message["id"],
                    "thread_id": message["threadId"],
                    "send_time": parsed_time.isoformat(),
                }
                count += 1
        except Exception:
            logger.info(f"Failed on {message}")

    logger.info(f"Found {count} emails.")


async def mark_as_read(
    message_id,
    user_email: str,
    config: dict | None = None,
    gmail_token: str | None = None,
    gmail_secret: str | None = None,
):
    creds = await get_credentials(user_email, config=config)

    service = await asyncio.to_thread(build, "gmail", "v1", credentials=creds)
    await asyncio.to_thread(
        lambda: service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    )


class CalInput(BaseModel):
    date_strs: list[str] = Field(
        description="The days for which to retrieve events. Each day should be represented by dd-mm-yyyy string."
    )


@tool(args_schema=CalInput)
async def get_events_for_days(date_strs: list[str]):
    """
    Retrieves events for a list of days. If you want to check for multiple days, call this with multiple inputs.

    Input in the format of ['dd-mm-yyyy', 'dd-mm-yyyy']

    Args:
    date_strs: The days for which to retrieve events (dd-mm-yyyy string).

    Returns: availability for those days.
    """
    import asyncio
    # Note: This function needs user_email from config - will be handled by calling code
    from .main.config import get_config
    from langchain_core.runnables.config import ensure_config

    config = ensure_config()
    user_config = await get_config(config)
    user_email = user_config["email"]

    creds = await get_credentials(user_email, config=config)
    service = await asyncio.to_thread(build, "calendar", "v3", credentials=creds)
    results = ""
    for date_str in date_strs:
        # Convert the date string to a datetime.date object
        day = datetime.strptime(date_str, "%d-%m-%Y").date()

        start_of_day = datetime.combine(day, time.min).isoformat() + "Z"
        end_of_day = datetime.combine(day, time.max).isoformat() + "Z"

        events_result = await asyncio.to_thread(
            lambda: service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        results += f"***FOR DAY {date_str}***\n\n" + print_events(events)
    return results


def format_datetime_with_timezone(dt_str, timezone="US/Pacific"):
    """
    Formats a datetime string with the specified timezone.

    Args:
    dt_str: The datetime string to format.
    timezone: The timezone to use for formatting.

    Returns:
    A formatted datetime string with the timezone abbreviation.
    """
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    tz = pytz.timezone(timezone)
    dt = dt.astimezone(tz)
    return dt.strftime("%Y-%m-%d %I:%M %p %Z")


def print_events(events):
    """
    Prints the events in a human-readable format.

    Args:
    events: List of events to print.
    """
    if not events:
        return "No events found for this day."

    result = ""

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        summary = event.get("summary", "No Title")

        if "T" in start:  # Only format if it's a datetime
            start = format_datetime_with_timezone(start)
            end = format_datetime_with_timezone(end)

        result += f"Event: {summary}\n"
        result += f"Starts: {start}\n"
        result += f"Ends: {end}\n"
        result += "-" * 40 + "\n"
    return result


async def send_calendar_invite(
    emails, title, start_time, end_time, email_address, config: dict | None = None, timezone="America/Toronto"
):
    creds = await get_credentials(email_address, config=config)
    service = await asyncio.to_thread(build, "calendar", "v3", credentials=creds)

    # Parse the start and end times
    start_datetime = datetime.fromisoformat(start_time)
    end_datetime = datetime.fromisoformat(end_time)
    emails = list(set(emails + [email_address]))
    event = {
        "summary": title,
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": timezone,
        },
        "attendees": [{"email": email} for email in emails],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 10},
            ],
        },
        "conferenceData": {
            "createRequest": {
                "requestId": f"{title}-{start_datetime.isoformat()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    try:
        await asyncio.to_thread(
            lambda: service.events().insert(
                calendarId="primary",
                body=event,
                sendNotifications=True,
                conferenceDataVersion=1,
            ).execute()
        )
        return True
    except Exception as e:
        logger.info(f"An error occurred while sending the calendar invite: {e}")
        return False
