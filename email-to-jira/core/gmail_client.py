"""Gmail poller source: read messages under the configured label.

Read-only scope on purpose — idempotency lives in the database (unique
gmail_message_id), so we never need to mutate the inbox. OAuth tokens are
stored locally at GMAIL_TOKEN_PATH and never logged.
"""
import base64
from pathlib import Path

from core.config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Google Meet / Gemini transcript emails get ingested as transcripts so the
# model extracts decisions/commitments instead of treating them as requests.
TRANSCRIPT_SENDERS = ("meet-recordings-noreply@google.com", "gemini-notes")
TRANSCRIPT_SUBJECT_HINTS = ("transcript", "notes from", "meeting notes")


def classify_source(sender: str, subject: str) -> str:
    sender_l, subject_l = sender.lower(), subject.lower()
    if any(s in sender_l for s in TRANSCRIPT_SENDERS):
        return "transcript"
    if any(h in subject_l for h in TRANSCRIPT_SUBJECT_HINTS):
        return "transcript"
    return "email"


class GmailPoller:
    def __init__(self, credentials_path: str | None = None, token_path: str | None = None,
                 label: str | None = None):
        self.credentials_path = credentials_path or settings.gmail_credentials_path
        self.token_path = token_path or settings.gmail_token_path
        self.label = label or settings.gmail_label
        self._service = None

    def _get_service(self):
        if self._service is not None:
            return self._service
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        if Path(self.token_path).exists():
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            Path(self.token_path).write_text(creds.to_json())
        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def fetch_labeled_messages(self, max_results: int = 50) -> list[dict]:
        """Return normalized messages under the label:
        {gmail_message_id, thread_id, sender, subject, body, source_type, attachments_meta}
        """
        service = self._get_service()
        listing = service.users().messages().list(
            userId="me", q=f"label:{self.label}", maxResults=max_results
        ).execute()
        messages = []
        for ref in listing.get("messages", []):
            full = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
            messages.append(_normalize(full))
        return messages


def _normalize(message: dict) -> dict:
    payload = message.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    sender = headers.get("from", "")
    subject = headers.get("subject", "")
    body = _extract_text(payload)
    attachments = [
        {"filename": part.get("filename"), "mime_type": part.get("mimeType"),
         "size": part.get("body", {}).get("size", 0)}
        for part in _walk_parts(payload) if part.get("filename")
    ]
    return {
        "gmail_message_id": message["id"],
        "thread_id": message.get("threadId", ""),
        "sender": sender,
        "subject": subject,
        "body": body,
        "source_type": classify_source(sender, subject),
        "attachments_meta": attachments,
    }


def _walk_parts(payload: dict):
    yield payload
    for part in payload.get("parts", []) or []:
        yield from _walk_parts(part)


def _extract_text(payload: dict) -> str:
    for part in _walk_parts(payload):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return ""
