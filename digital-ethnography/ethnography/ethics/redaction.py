"""PII detection, redaction, and pseudonymization.

Two responsibilities:

1. **Pseudonymization** of participant identifiers. The raw identifier a source
   provides (an email, a user id, a device id) is turned into a salted hash and
   thrown away. Downstream, nothing can re-identify a participant without the
   salt, and the salt lives only in the study's runtime config.

2. **Redaction** of personally identifying information that leaks into free
   text (an interview transcript, a support message). We use conservative
   regex detectors; anything matched is replaced with a typed placeholder so
   the *shape* of the data survives for analysis while the identity does not.

This is intentionally dependency-free and offline. A production deployment
would layer an NER model on top, but the regex floor is the safety net that
always runs.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# Ordered so that more specific patterns win before broad ones.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ \-]*?){13,16}\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("PHONE", re.compile(r"\b(?:\+?\d{1,3}[ \-.]?)?(?:\(?\d{3}\)?[ \-.]?)\d{3}[ \-.]?\d{4}\b")),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("URL", re.compile(r"https?://[^\s]+")),
    ("HANDLE", re.compile(r"(?<!\w)@[A-Za-z0-9_]{2,}")),
]


@dataclass
class RedactionResult:
    text: str
    counts: dict[str, int]

    @property
    def anything_redacted(self) -> bool:
        return any(self.counts.values())


def redact_text(text: str | None) -> RedactionResult:
    """Replace detected PII with typed placeholders like ``[EMAIL]``."""
    if not text:
        return RedactionResult(text or "", {})
    counts: dict[str, int] = {}
    out = text
    for label, pattern in _PATTERNS:
        # Credit-card pattern is greedy; require it to look card-like after strip.
        if label == "CREDIT_CARD":
            def _sub(m: re.Match[str]) -> str:
                digits = re.sub(r"\D", "", m.group(0))
                if 13 <= len(digits) <= 16:
                    counts[label] = counts.get(label, 0) + 1
                    return f"[{label}]"
                return m.group(0)
            out = pattern.sub(_sub, out)
        else:
            found = pattern.findall(out)
            if found:
                counts[label] = counts.get(label, 0) + len(found)
                out = pattern.sub(f"[{label}]", out)
    return RedactionResult(out, counts)


class Pseudonymizer:
    """Deterministically maps a raw identifier to a stable pseudonymous id.

    Deterministic so that the same participant across two data sources maps to
    the same ``pid`` (enabling journey stitching) without ever storing the raw
    identifier. The salt makes the mapping non-reversible by an outside party.
    """

    def __init__(self, salt: str) -> None:
        if not salt or len(salt) < 8:
            raise ValueError("Pseudonymization salt must be at least 8 characters.")
        self._salt = salt

    def pid(self, raw_identifier: str) -> str:
        digest = hashlib.sha256(f"{self._salt}:{raw_identifier}".encode("utf-8")).hexdigest()
        return f"p_{digest[:16]}"
