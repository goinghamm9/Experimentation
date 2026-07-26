"""Journey reconstruction and friction detection.

Digital ethnography cares about *sequence in context*: not just that a user hit
an error, but that they hit it three screens into a checkout they then
abandoned. For each participant we order their behavioral observations in time
and flag friction points using deterministic heuristics:

* explicit failure signals in the event name (error/crash/fail)
* immediate repetition of the same event (a retry / stuck loop)
* rapid back-and-forth between two screens (thrash)
* negative-affect language in a co-occurring utterance
"""

from __future__ import annotations

from ..schema import Corpus, FrictionPoint, Journey, ObservationKind

_FAILURE_TOKENS = ("error", "crash", "fail", "denied", "timeout", "invalid")
_NEGATIVE_AFFECT = (
    "confusing", "frustrat", "annoy", "hate", "stuck", "gave up", "worst",
    "useless", "broken", "angry", "disappoint",
)


def reconstruct(corpus: Corpus) -> list[Journey]:
    journeys: list[Journey] = []
    for pid, participant in corpus.participants.items():
        obs = sorted(corpus.by_participant(pid), key=lambda o: o.timestamp)
        if not obs:
            continue
        journey = Journey(pid=pid, step_ids=[o.id for o in obs])
        journey.friction = _detect_friction(obs)
        journeys.append(journey)
    return journeys


def _event_name(payload: dict) -> str:
    return str(payload.get("event", "")).lower()


def _detect_friction(obs) -> list[FrictionPoint]:
    friction: list[FrictionPoint] = []
    prev_event: str | None = None
    prev_prev_event: str | None = None

    for o in obs:
        name = _event_name(o.payload)

        # Explicit failure signal.
        if o.kind == ObservationKind.EVENT and any(t in name for t in _FAILURE_TOKENS):
            friction.append(FrictionPoint(o.id, f"failure event: {name}", 0.9))

        # Immediate repetition (retry / stuck).
        elif name and name == prev_event:
            friction.append(FrictionPoint(o.id, f"repeated event: {name}", 0.5))

        # Thrash: A -> B -> A pattern.
        elif name and name == prev_prev_event and name != prev_event:
            friction.append(FrictionPoint(o.id, f"back-and-forth around: {name}", 0.4))

        # Negative affect in an utterance.
        if o.text:
            low = o.text.lower()
            if any(tok in low for tok in _NEGATIVE_AFFECT):
                friction.append(
                    FrictionPoint(o.id, "negative-affect language in feedback", 0.6)
                )

        prev_prev_event, prev_event = prev_event, name

    return friction


def friction_index(journeys: list[Journey]) -> float:
    """Mean friction points per journey — a single portable health signal."""
    if not journeys:
        return 0.0
    return sum(len(j.friction) for j in journeys) / len(journeys)
