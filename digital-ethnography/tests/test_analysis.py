from datetime import datetime, timedelta, timezone

from ethnography.analysis.coding import axial_code, open_code
from ethnography.analysis.journeys import friction_index, reconstruct
from ethnography.analysis.personas import synthesize
from ethnography.schema import (
    Corpus,
    DataCategory,
    Observation,
    ObservationKind,
    Participant,
    Study,
)


def _corpus():
    study = Study(id="s", title="t", purpose="p")
    base = datetime(2026, 6, 1, tzinfo=timezone.utc)
    obs = []
    for i, (pid, event, text) in enumerate(
        [
            ("p1", "checkout_start", None),
            ("p1", "payment_error", "the payment was broken and confusing"),
            ("p1", "payment_error", None),
            ("p2", "checkout_start", "love the smooth checkout, great"),
            ("p2", "purchase_complete", None),
            ("p3", "signup_start", "onboarding was confusing"),
        ]
    ):
        obs.append(
            Observation(
                id=f"o{i}",
                pid=pid,
                source="s",
                kind=ObservationKind.UTTERANCE if text else ObservationKind.EVENT,
                timestamp=base + timedelta(minutes=i),
                category=DataCategory.CONTENT if text else DataCategory.BEHAVIORAL,
                text=text,
                payload={"event": event},
            )
        )
    participants = {p: Participant(pid=p) for p in {"p1", "p2", "p3"}}
    return Corpus(study=study, participants=participants, observations=obs)


def test_open_coding_applies_codebook_and_emergent():
    corpus = _corpus()
    codes = open_code(corpus, min_emergent_freq=2)
    labels = {c.label for c in codes}
    assert any("checkout" in l for l in labels)
    assert any("error" in l or "payment" in l for l in labels)


def test_axial_coding_groups_related_codes():
    corpus = _corpus()
    codes = open_code(corpus, min_emergent_freq=2)
    themes = axial_code(codes, min_theme_size=1)
    assert len(themes) >= 1
    assert all(t.observation_ids for t in themes)


def test_journey_detects_repeated_error_friction():
    corpus = _corpus()
    journeys = reconstruct(corpus)
    p1 = next(j for j in journeys if j.pid == "p1")
    # payment_error appears twice + failure token -> friction detected.
    assert len(p1.friction) >= 1
    assert friction_index(journeys) > 0


def test_personas_respect_k_anonymity_floor():
    corpus = _corpus()
    codes = open_code(corpus, min_emergent_freq=2)
    personas = synthesize(corpus, codes, k_min=3)
    # Only 3 participants total; no persona of size < 3 should be published.
    assert all(p.size >= 3 for p in personas)
