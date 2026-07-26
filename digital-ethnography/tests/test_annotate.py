"""Tests for the human gold-coding surface.

The load-bearing property is **blindness**: if a machine label can reach the
annotator, the gold set measures agreement with the model rather than truth, and
every validity number downstream becomes circular.
"""

import json
from datetime import datetime, timezone

import pytest

from ethnography.annotate import Annotation, GoldStore, build_session
from ethnography.annotate.server import _handler_factory  # noqa: F401  (import smoke)
from ethnography.schema import (
    Corpus,
    DataCategory,
    Observation,
    ObservationKind,
    Participant,
    Study,
)


def _corpus(n=20):
    study = Study(id="s", title="Test Study", purpose="p")
    obs, parts = [], {}
    for i in range(n):
        pid = f"p{i % 5}"
        parts[pid] = Participant(pid=pid)
        obs.append(Observation(
            id=f"o{i}", pid=pid, source="reviews",
            kind=ObservationKind.UTTERANCE,
            timestamp=datetime(2026, 6, 1, tzinfo=timezone.utc),
            category=DataCategory.CONTENT,
            text=f"utterance number {i}",
            payload={"event": "review", "rating": i % 5},
        ))
    return Corpus(study=study, participants=parts, observations=obs)


CODEBOOK = {"friction": ["stuck", "error"], "delight": ["love", "great"]}


def _session(tmp_path, n=6, annotator="r1"):
    return build_session(
        corpus=_corpus(),
        codebook=CODEBOOK,
        gold_path=tmp_path / "gold.jsonl",
        annotator=annotator,
        sample_size=n,
    )


# --- Blindness: the central guarantee -------------------------------------

def test_units_sent_to_the_browser_contain_no_machine_label(tmp_path):
    payload = _session(tmp_path).units_payload()
    assert payload
    for u in payload:
        keys = set(u)
        assert "label" not in keys
        assert "code" not in keys
        assert "prediction" not in keys
        assert keys <= {"id", "text", "source", "kind", "timestamp", "payload"}


def test_serialised_units_never_mention_a_code_label(tmp_path):
    blob = json.dumps(_session(tmp_path).units_payload())
    for label in CODEBOOK:
        assert label not in blob, f"machine code '{label}' leaked into the annotator view"


# --- Sampling -------------------------------------------------------------

def test_sample_is_a_reproducible_probability_sample(tmp_path):
    a = _session(tmp_path).unit_ids()
    b = _session(tmp_path).unit_ids()
    assert a == b and len(a) == 6


def test_units_payload_matches_and_orders_by_sample(tmp_path):
    s = _session(tmp_path)
    assert [u["id"] for u in s.units_payload()] == s.unit_ids()


def test_codebook_version_changes_with_the_codebook(tmp_path):
    v1 = _session(tmp_path).codebook_version()
    other = build_session(
        corpus=_corpus(), codebook={**CODEBOOK, "trust": ["privacy"]},
        gold_path=tmp_path / "g2.jsonl", annotator="r1", sample_size=6,
    )
    assert other.codebook_version() != v1


# --- Store ----------------------------------------------------------------

def test_store_round_trips_and_resumes(tmp_path):
    p = tmp_path / "gold.jsonl"
    s = GoldStore(p)
    s.add(Annotation("o1", "friction", "r1", "v1", 4.2))
    s.add(Annotation("o2", None, "r1", "v1", 3.0))       # uncertain
    reopened = GoldStore(p)
    assert len(reopened) == 2
    assert reopened.completed_units("r1") == {"o1", "o2"}
    assert reopened.latest_by_unit("r1")["o2"].is_uncertain


def test_recoding_a_unit_supersedes_the_earlier_record(tmp_path):
    s = GoldStore(tmp_path / "g.jsonl")
    s.add(Annotation("o1", "friction", "r1", "v1", 5.0))
    s.add(Annotation("o1", "delight", "r1", "v1", 9.0))
    assert s.latest_by_unit("r1")["o1"].label == "delight"


def test_gold_vector_aligns_and_treats_uncertain_as_missing(tmp_path):
    s = GoldStore(tmp_path / "g.jsonl")
    s.add(Annotation("o1", "friction", "r1", "v1", 4.0))
    s.add(Annotation("o2", None, "r1", "v1", 4.0))
    assert s.gold_vector(["o1", "o2", "o3"], "r1") == ["friction", None, None]


def test_quality_flags_catch_implausibly_fast_coding(tmp_path):
    s = GoldStore(tmp_path / "g.jsonl")
    for i in range(5):
        s.add(Annotation(f"o{i}", "friction", "speedy", "v1", 0.3))
    flags = s.quality_flags()
    assert any("implausibly fast" in f for f in flags)


def test_quality_flags_catch_a_codebook_that_does_not_fit(tmp_path):
    s = GoldStore(tmp_path / "g.jsonl")
    for i in range(10):
        s.add(Annotation(f"o{i}", None if i < 6 else "friction", "r1", "v1", 8.0))
    assert any("codebook may not fit" in f for f in s.quality_flags())


def test_multiple_annotators_are_tracked_separately(tmp_path):
    s = GoldStore(tmp_path / "g.jsonl")
    s.add(Annotation("o1", "friction", "r1", "v1", 4.0))
    s.add(Annotation("o1", "delight", "r2", "v1", 4.0))
    assert s.annotators() == ["r1", "r2"]
    assert s.gold_vector(["o1"], "r1") == ["friction"]
    assert s.gold_vector(["o1"], "r2") == ["delight"]


# --- Gold feeds the panel -------------------------------------------------

def test_gold_flows_into_a_validity_claim(tmp_path):
    from ethnography.rigor import Coder, CoderKind, assess_panel

    s = GoldStore(tmp_path / "g.jsonl")
    units = ["o1", "o2", "o3", "o4"]
    for u, lab in zip(units, ["friction", "friction", "delight", "delight"]):
        s.add(Annotation(u, lab, "r1", "v1", 6.0))

    machine = ["friction", "friction", "delight", "friction"]  # 3/4 correct
    panel = assess_panel(
        {"m1": machine},
        [Coder("m1", CoderKind.MODEL, "qwen"), Coder("r1", CoderKind.HUMAN, "human")],
        unit_ids=units,
        gold=s.gold_vector(units, "r1"),
    )
    assert panel.has_validity_evidence
    assert 0 < panel.validity_vs_gold["m1"] < 1.0


# --- Safety ---------------------------------------------------------------

def test_server_refuses_to_bind_publicly_without_acknowledgement(tmp_path):
    from ethnography.annotate import serve

    with pytest.raises(ValueError, match="participant data"):
        serve(_session(tmp_path), host="0.0.0.0", open_browser=False)


def test_rendered_page_is_self_contained(tmp_path):
    from ethnography.annotate.ui import render_page

    page = render_page("T", "r1", "[]", "[]", '"r1"', '"v1"', "{}")
    assert "<script src=" not in page and "cdn" not in page.lower()
    assert "@media (prefers-color-scheme: dark)" in page
