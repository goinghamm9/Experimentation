"""TranscriptSource seam — FUTURE: automatically fetch Google Meet transcripts
from Google Drive. Interface only in v1.

v1 paths for meeting transcripts (no Drive API needed):
- Meet/Gemini transcript *emails* land in the watched Gmail label and flow
  through the normal poller (ingested with source_type="transcript").
- Drive-only transcripts are pasted into the dashboard's "Add transcript" form.
"""
from typing import Protocol


class TranscriptSource(Protocol):
    def fetch_new_transcripts(self, since_iso: str) -> list[dict]:
        """Return [{id, title, text, meeting_date}] for unseen transcripts."""
        ...
