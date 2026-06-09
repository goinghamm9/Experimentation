"""Visualizer seam — FUTURE: render JQL results into Mermaid architecture /
user-flow diagrams. Interface only; do not implement in v1."""
from typing import Protocol


class Visualizer(Protocol):
    def render_jql(self, jql: str, diagram_type: str) -> str:
        """Return Mermaid source for the issues matching a JQL query."""
        ...
