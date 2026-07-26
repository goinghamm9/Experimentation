"""digital-ethnography: an ethics-first pipeline for digital ethnographic
user research over any digital system.

Public entry points:

    from ethnography import EthnographyPipeline, load_study
"""

from .config import LoadedStudy, load_study
from .pipeline import EthnographyPipeline, StudyResult
from .schema import (
    Corpus,
    DataCategory,
    Observation,
    ObservationKind,
    Participant,
    Provenance,
    Study,
)

__version__ = "0.1.0"

__all__ = [
    "EthnographyPipeline",
    "StudyResult",
    "LoadedStudy",
    "load_study",
    "Study",
    "Corpus",
    "Observation",
    "ObservationKind",
    "Participant",
    "DataCategory",
    "Provenance",
]
