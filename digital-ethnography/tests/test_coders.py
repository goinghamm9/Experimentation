"""Tests for the coder layer.

The load-bearing properties: a fabricated quote must not be able to move a
validity number, an invented code must not become a finding, a refusal must not
become an absence, and coders must be decorrelated by construction rather than by
assumption.
"""

import json
from datetime import datetime, timezone

import pytest

from ethnography.coders import (
    DEDUCTIVE,
    DEFAULT_VARIANTS,
    ELIMINATIVE,
    INDUCTIVE,
    CodedUnit,
    CodingResult,
    DeterministicCoder,
    LLMCoder,
    ModelSpec,
    coding_prompt,
    extract_json,
    looks_like_refusal,
    run_panel,
    verify_span,
)
from ethnography.schema import DataCategory, Observation, ObservationKind

CODEBOOK = {
    "checkout_flow": ["checkout", "payment"],
    "onboarding_friction": ["signup", "confusing"],
    "value_and_delight": ["love", "great"],
}


def _obs(i, text=None, event=None):
    return Observation(
        id=f"o{i}", pid=f"p{i}", source="reviews",
        kind=ObservationKind.UTTERANCE if text else ObservationKind.EVENT,
        timestamp=datetime(2026, 6, 1, tzinfo=timezone.utc),
        category=DataCategory.CONTENT if text else DataCategory.BEHAVIORAL,
        text=text, payload={"event": event} if event else {},
    )


class FakeClient:
    """Scripted client: one canned response per call, in order."""

    available = True

    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def complete(self, system, prompt):
        self.prompts.append(prompt)
        return self.responses.pop(0) if self.responses else ""


def _reply(label, evidence, confidence=0.9):
    return json.dumps({"label": label, "evidence": evidence, "confidence": confidence})


# --- Evidence verification: the hallucination gate ------------------------

def test_verify_span_accepts_exact_and_cosmetically_varied_quotes():
    src = "The checkout  was\nCONFUSING and slow"
    assert verify_span("checkout was confusing", src)     # whitespace + case folded
    assert verify_span("The checkout", src)


def test_verify_span_rejects_paraphrase_and_invention():
    src = "The checkout was confusing and slow"
    assert not verify_span("the checkout was hard to use", src)   # paraphrase
    assert not verify_span("I loved the checkout", src)           # invention
    assert not verify_span("", src)
    assert not verify_span("anything", None)


def test_fabricated_evidence_is_dropped_from_the_label_vector():
    client = FakeClient([_reply("checkout_flow", "a quote that was never written")])
    coder = LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, client)
    result = coder.code([_obs(1, "the payment step failed twice")])

    unit = result.units[0]
    assert unit.label == "checkout_flow"
    assert unit.span_verified is False
    # The label exists but must NOT reach the panel as evidence.
    assert result.label_vector(["o1"]) == [None]
    assert result.fabrication_rate == pytest.approx(1.0)
    assert any("fabricated evidence" in f for f in result.quality_flags())


def test_verified_evidence_survives_into_the_label_vector():
    client = FakeClient([_reply("checkout_flow", "payment step failed")])
    coder = LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, client)
    result = coder.code([_obs(1, "the payment step failed twice")])
    assert result.units[0].span_verified
    assert result.label_vector(["o1"]) == ["checkout_flow"]
    assert result.fabrication_rate == 0.0


# --- Out-of-contract output ----------------------------------------------

def test_invented_code_is_not_a_finding():
    client = FakeClient([_reply("brand_new_theme", "payment step failed")])
    coder = LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, client)
    result = coder.code([_obs(1, "the payment step failed twice")])
    assert result.units[0].label is None
    assert "not in codebook" in result.units[0].rationale


def test_uncertain_is_accepted_as_an_answer():
    client = FakeClient([_reply("UNCERTAIN", None)])
    coder = LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, client)
    result = coder.code([_obs(1, "something unrelated")])
    assert result.units[0].label is None
    assert result.units[0].refused is False
    assert result.uncertain_rate == pytest.approx(1.0)


def test_unparseable_response_becomes_uncertain_not_a_crash():
    client = FakeClient(["I think maybe checkout? hard to say"])
    coder = LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, client)
    result = coder.code([_obs(1, "the payment step failed")])
    assert result.units[0].label is None
    assert "unparseable" in result.units[0].rationale


# --- Refusals are counted, not swallowed ---------------------------------

def test_refusal_is_recorded_as_refusal():
    client = FakeClient(["I'm sorry, I can't help with analysing that content."])
    coder = LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, client)
    result = coder.code([_obs(1, "a sensitive account")])
    assert result.units[0].refused
    assert result.refusal_rate == pytest.approx(1.0)
    assert any("coverage loss" in f for f in result.quality_flags())


def test_refusal_detection_does_not_fire_on_ordinary_content():
    assert looks_like_refusal("I cannot assist with that")
    assert not looks_like_refusal(_reply("checkout_flow", "payment failed"))
    assert not looks_like_refusal("")


def test_absent_client_produces_nothing_rather_than_agreement():
    class Absent:
        available = False
        def complete(self, s, p): return ""

    coder = LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, Absent())
    result = coder.code([_obs(1, "text")])
    assert result.units == []
    assert any("absent coder, not an agreeing one" in n for n in result.notes)


# --- JSON extraction ------------------------------------------------------

def test_extract_json_handles_fences_prose_and_nesting():
    assert extract_json('```json\n{"label":"a"}\n```')["label"] == "a"
    assert extract_json('Sure! {"label":"b"} hope that helps')["label"] == "b"
    assert extract_json('{"label":"c","meta":{"x":1}}')["meta"] == {"x": 1}
    assert extract_json("no json here") is None
    assert extract_json("") is None
    assert extract_json('[1,2,3]') is None     # array is not a coding response


# --- Decorrelation is constructed, not assumed ---------------------------

def test_option_order_differs_across_coders_but_is_reproducible():
    labels = sorted(CODEBOOK)
    a1 = DEDUCTIVE.code_order(labels, "m1")
    a2 = DEDUCTIVE.code_order(labels, "m1")
    b = DEDUCTIVE.code_order(labels, "m2")
    assert a1 == a2, "same coder must get a stable order (auditability)"
    assert set(a1) == set(b) == set(labels)
    assert any(
        DEDUCTIVE.code_order(labels, f"m{i}") != a1 for i in range(3, 12)
    ), "option order must vary across coders"


def test_variants_ask_genuinely_different_questions():
    texts = {
        coding_prompt("t", "ctx", CODEBOOK, v, "m1").split("CODEBOOK")[0]
        for v in DEFAULT_VARIANTS
    }
    assert len(texts) == 3


def test_prompt_offers_uncertain_and_demands_verbatim_evidence():
    p = coding_prompt("some text", "ctx", CODEBOOK, INDUCTIVE, "m1")
    assert "UNCERTAIN" in p
    assert "VERBATIM" in p
    assert "rationale" in p                      # inductive asks for it
    assert "rationale" not in coding_prompt("t", "c", CODEBOOK, ELIMINATIVE, "m1")


# --- Deterministic baseline ----------------------------------------------

def test_deterministic_coder_matches_and_grounds():
    r = DeterministicCoder(CODEBOOK).code([_obs(1, "the checkout was confusing")])
    u = r.units[0]
    assert u.label in {"checkout_flow", "onboarding_friction"}
    assert u.span_verified and u.evidence


def test_deterministic_coder_returns_uncertain_when_nothing_matches():
    r = DeterministicCoder(CODEBOOK).code([_obs(1, "unrelated content here")])
    assert r.units[0].label is None


def test_behavioural_unit_codes_without_claiming_a_text_span():
    r = DeterministicCoder(CODEBOOK).code([_obs(1, None, event="checkout_start")])
    u = r.units[0]
    assert u.label == "checkout_flow"
    assert u.evidence is None and u.span_verified is False
    # No fabrication is claimed for a unit that had no text to quote.
    assert r.fabrication_rate == 0.0
    assert r.label_vector(["o1"]) == ["checkout_flow"]


# --- The panel run --------------------------------------------------------

def test_panel_run_reports_agreement_and_withholds_validity_without_gold():
    obs = [_obs(1, "the payment failed"), _obs(2, "I love this, great app")]
    c1 = FakeClient([_reply("checkout_flow", "payment failed"),
                     _reply("value_and_delight", "love this")])
    c2 = FakeClient([_reply("checkout_flow", "payment failed"),
                     _reply("value_and_delight", "love this")])

    run = run_panel(
        [LLMCoder(ModelSpec("m1", "qwen", variant=DEDUCTIVE), CODEBOOK, c1),
         LLMCoder(ModelSpec("m2", "llama", variant=INDUCTIVE), CODEBOOK, c2)],
        obs,
    )
    assert not run.report.has_validity_evidence
    assert run.ledger.hypotheses_considered == 2 * 2 * (len(CODEBOOK) + 1)
    assert "validity UNKNOWN" in run.report.summary()
    assert run.lineages == {"qwen", "llama"}


def test_panel_run_produces_validity_against_gold():
    obs = [_obs(1, "the payment failed"), _obs(2, "I love this, great app")]
    client = FakeClient([_reply("checkout_flow", "payment failed"),
                         _reply("value_and_delight", "love this")])
    run = run_panel(
        [LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, client)],
        obs,
        gold=["checkout_flow", "value_and_delight"],
    )
    assert run.report.has_validity_evidence
    assert run.report.validity_vs_gold["m1"] == pytest.approx(1.0)


def test_single_lineage_panel_is_flagged():
    obs = [_obs(1, "the payment failed")]
    run = run_panel(
        [LLMCoder(ModelSpec("m1", "qwen"), CODEBOOK, FakeClient([_reply("checkout_flow", "payment failed")])),
         LLMCoder(ModelSpec("m2", "qwen"), CODEBOOK, FakeClient([_reply("checkout_flow", "payment failed")]))],
        obs,
    )
    assert "share one lineage" in run.summary()


def test_deterministic_baseline_can_be_panelled_offline():
    obs = [_obs(1, "the checkout was confusing"), _obs(2, "I love it")]
    run = run_panel([DeterministicCoder(CODEBOOK)], obs, gold=["checkout_flow", "value_and_delight"])
    assert run.report.gold_units == 2
    assert run.total_cost_usd == 0.0
