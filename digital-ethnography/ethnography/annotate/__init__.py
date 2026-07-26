"""Human gold coding — the annotation surface and its store.

Gold annotations are the only source of validity evidence in the system. Agreement
among machine coders is a disagreement router; agreement with a human on a
probability sample is the validity claim.
"""

from .server import AnnotationSession, build_session, serve
from .store import Annotation, GoldStore

__all__ = ["Annotation", "GoldStore", "AnnotationSession", "build_session", "serve"]
