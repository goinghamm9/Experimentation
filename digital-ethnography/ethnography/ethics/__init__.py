"""Ethics-by-design primitives: consent, redaction, governance, audit."""

from .audit import AuditEvent, AuditLog
from .consent import ConsentRecord, ConsentRegistry
from .governance import GateReport, GovernanceGate
from .redaction import Pseudonymizer, RedactionResult, redact_text

__all__ = [
    "AuditEvent",
    "AuditLog",
    "ConsentRecord",
    "ConsentRegistry",
    "GateReport",
    "GovernanceGate",
    "Pseudonymizer",
    "RedactionResult",
    "redact_text",
]
