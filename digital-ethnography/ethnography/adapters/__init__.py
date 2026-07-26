"""Pluggable ingest adapters. Add one to support a new digital system."""

from .base import RawRecord, SourceAdapter, to_observations
from .events import EventLogAdapter
from .qualitative import QualitativeAdapter

__all__ = [
    "RawRecord",
    "SourceAdapter",
    "to_observations",
    "EventLogAdapter",
    "QualitativeAdapter",
]
