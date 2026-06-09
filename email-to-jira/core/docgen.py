"""DocGenerator seam — FUTURE: turn a sprint's tickets into a client-facing
wrap-up and export to Google Drive. Interface only; do not implement in v1."""
from typing import Protocol


class DocGenerator(Protocol):
    def generate_sprint_wrapup(self, project_key: str, sprint_id: str) -> str:
        """Return a client-facing document for the sprint."""
        ...

    def export_to_drive(self, document: str, folder_id: str) -> str:
        """Upload the document; return its Drive URL."""
        ...
