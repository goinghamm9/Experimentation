"""Plain-text/simple-markdown -> Atlassian Document Format.

Jira Cloud v3 rejects raw markdown in description fields; everything sent
there must be an ADF document. Supports paragraphs, '#'-headings and '-'/'*'
bullet lists, which covers what the model is told to produce.
"""


def _text_node(text: str) -> dict:
    return {"type": "text", "text": text}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "content": [_text_node(text)]}


def _heading(text: str, level: int) -> dict:
    return {"type": "heading", "attrs": {"level": min(level, 6)}, "content": [_text_node(text)]}


def _bullet_list(items: list[str]) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [_paragraph(item)]} for item in items
        ],
    }


def text_to_adf(text: str) -> dict:
    """Convert simple text to an ADF doc. Empty input becomes an empty doc."""
    content: list[dict] = []
    bullets: list[str] = []

    def flush_bullets():
        if bullets:
            content.append(_bullet_list(bullets.copy()))
            bullets.clear()

    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            flush_bullets()
            continue
        if line.startswith(("- ", "* ")):
            bullets.append(line[2:].strip())
            continue
        flush_bullets()
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading_text = line[level:].strip()
            if heading_text:
                content.append(_heading(heading_text, level))
                continue
        content.append(_paragraph(line))
    flush_bullets()

    return {"type": "doc", "version": 1, "content": content}


def candidate_description_adf(description: str, acceptance_criteria: list[str]) -> dict:
    """Full issue description: body text plus an Acceptance Criteria section."""
    doc = text_to_adf(description)
    if acceptance_criteria:
        doc["content"].append(_heading("Acceptance Criteria", 3))
        doc["content"].append(_bullet_list(acceptance_criteria))
    return doc
