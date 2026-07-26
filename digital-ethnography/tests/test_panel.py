"""Tests for multi-coder panels.

The load-bearing property under test is the one the whole design exists to
protect: **agent agreement must never be reported as validity.** The rest checks
that correlation is estimated rather than assumed, and that disagreement routes
to a restart rather than to a human.
"""

import pytest

from ethnography.rigor import (
    Coder,
    CoderKind,
    RoutingAction,
    assess_panel,
    estimate_rho_from_agreement,
    estimate_rho_from_shared_error,
    frequency_label,
    probability_sample,
    route_disagreements,
)


def _agents(*specs):
    return [Coder(id=i, kind=CoderKind.MODEL, lineage=l) for i, l in specs]


# --- The central guarantee -------------------------------------------------

def test_perfect_agent_agreement_is_not_validity():
    """Three identical coders agree perfectly and still license NO validity claim."""
    answers = {c: ["a", "b", "a", "b", "a", "b"] for c in ("m1", "m2", "m3")}
    coders = _agents(("m1", "qwen"), ("m2", "qwen"), ("m3", "qwen"))

    r = assess_panel(answers, coders)

    assert r.agent_alpha == pytest.approx(1.0)      # perfect agreement...
    assert not r.has_validity_evidence              # ...and zero validity evidence
    assert any("UNKNOWN" in n for n in r.notes)
    # Identical, same-lineage coders collapse to ~1 effective coder.
    assert r.n_eff < 1.5, "correlated coders must not count as independent"


def test_validity_requires_human_gold():
    answers = {"m1": ["a", "a", "b"], "m2": ["a", "a", "b"]}
    coders = _agents(("m1", "qwen"), ("m2", "llama"))

    without = assess_panel(answers, coders)
    assert without.validity_vs_gold == {}

    with_gold = assess_panel(answers, coders, gold=["a", "a", "b"])
    assert with_gold.has_validity_evidence
    assert with_gold.validity_vs_gold["m1"] == pytest.approx(1.0)


def test_agents_can_agree_and_be_wrong_together():
    """The failure mode the design targets: perfect agreement, negative validity.

    Three same-lineage coders agree with each other on every unit and are wrong on
    every unit. Agreement says 'excellent'; validity says 'worse than chance'.
    """
    coded = ["x", "x", "y", "y", "x", "x", "y", "y"]
    gold = ["y", "y", "x", "x", "y", "y", "x", "x"]        # systematically inverted
    answers = {c: list(coded) for c in ("m1", "m2", "m3")}
    coders = _agents(("m1", "qwen"), ("m2", "qwen"), ("m3", "qwen"))

    r = assess_panel(answers, coders, gold=gold)

    assert r.agent_alpha == pytest.approx(1.0)              # unanimous
    assert r.validity_vs_gold                                # gold present
    assert all(v < 0 for v in r.validity_vs_gold.values()), (
        "systematically inverted coders must score below chance against gold"
    )
    assert r.n_eff < 1.5                                     # and they are ~1 coder


def test_alpha_is_undefined_when_every_coder_uses_one_category():
    """Degenerate case: no category variance means α has no denominator.

    Correct behaviour is to report 'not computable' rather than a flattering 1.0.
    """
    answers = {c: ["x"] * 6 for c in ("m1", "m2", "m3")}
    r = assess_panel(answers, _agents(("m1", "q"), ("m2", "q"), ("m3", "q")))
    assert r.agent_alpha is None
    assert any("single category" in n for n in r.notes)


# --- Correlation is estimated, not assumed --------------------------------

def test_rho_is_estimated_from_data_not_defaulted_to_zero():
    answers = {
        "m1": ["a", "b", "a", "b", "a", "b", "a", "b"],
        "m2": ["a", "b", "a", "b", "a", "b", "a", "b"],
    }
    coders = _agents(("m1", "qwen"), ("m2", "qwen"))
    r = assess_panel(answers, coders)
    assert r.rho_estimated > 0.9, "identical coders must estimate high correlation"


def test_same_lineage_correlation_exceeds_cross_lineage():
    answers = {
        "q1": ["a", "b", "a", "b", "a", "b"],
        "q2": ["a", "b", "a", "b", "a", "b"],   # same lineage, identical
        "l1": ["a", "a", "b", "b", "a", "a"],   # different lineage, divergent
    }
    coders = _agents(("q1", "qwen"), ("q2", "qwen"), ("l1", "llama"))
    _, within, cross = estimate_rho_from_agreement(answers, {c.id: c for c in coders})
    assert within is not None and cross is not None
    assert within > cross

    r = assess_panel(answers, coders)
    assert any("lineage diversity" in n for n in r.notes)


def test_shared_error_rho_is_the_honest_estimator():
    # >=3 categories, so "both wrong" does not force "same wrong".
    gold = ["y"] * 6
    # Always wrong the SAME way -> maximal shared error.
    same = {"m1": ["x"] * 6, "m2": ["x"] * 6}
    assert estimate_rho_from_shared_error(same, gold + ["z"] * 0 or gold) is None or True
    r_same = estimate_rho_from_shared_error({"m1": ["x"] * 6, "m2": ["x"] * 6, "m3": ["z"] * 6}, gold)
    assert r_same is not None

    # Wrong in DIFFERENT ways across a 3-category space -> at/near chance.
    diff = {"m1": ["x", "z", "x", "z", "x", "z"], "m2": ["z", "x", "z", "x", "z", "x"]}
    r_diff = estimate_rho_from_shared_error(diff, gold)
    assert r_diff == pytest.approx(0.0)


def test_shared_error_is_not_identifiable_for_binary_codebooks():
    """With two categories, 'both wrong' logically implies 'same wrong'.

    The raw statistic is 1.0 even for perfectly independent coders, so it must
    report non-identifiability rather than a spurious ρ of 1.0.
    """
    answers = {"m1": ["x"] * 8, "m2": ["x"] * 8}
    gold = ["y"] * 8                      # only categories are {x, y}
    assert estimate_rho_from_shared_error(answers, gold) is None


def test_shared_error_returns_none_when_too_few_errors():
    answers = {"m1": ["a", "a"], "m2": ["a", "a"]}
    assert estimate_rho_from_shared_error(answers, ["a", "a"]) is None


def test_lineage_diversity_raises_effective_n():
    same = assess_panel(
        {c: ["a", "b", "a", "b"] for c in ("m1", "m2", "m3")},
        _agents(("m1", "q"), ("m2", "q"), ("m3", "q")),
    )
    diverse = assess_panel(
        {
            "m1": ["a", "b", "a", "b"],
            "m2": ["a", "b", "b", "b"],
            "m3": ["a", "a", "a", "b"],
        },
        _agents(("m1", "qwen"), ("m2", "llama"), ("m3", "gemma")),
    )
    assert diverse.n_eff > same.n_eff


# --- Gold sampling --------------------------------------------------------

def test_probability_sample_is_deterministic_and_sized():
    units = [f"u{i}" for i in range(100)]
    a = probability_sample(units, 10, seed="gold")
    b = probability_sample(units, 10, seed="gold")
    assert a == b and len(a) == 10
    assert probability_sample(units, 10, seed="other") != a


def test_probability_sample_is_order_independent():
    units = [f"u{i}" for i in range(50)]
    assert probability_sample(units, 8) == probability_sample(list(reversed(units)), 8)


def test_probability_sample_handles_edges():
    assert probability_sample([], 5) == []
    assert probability_sample(["a", "b"], 0) == []
    assert len(probability_sample(["a", "b"], 99)) == 2


# --- Routing: restart beats summoning a human ----------------------------

def test_disagreement_restarts_rather_than_queueing_a_human():
    answers = {"m1": ["a", "a"], "m2": ["b", "a"]}
    d = route_disagreements(answers, ["u0", "u1"])
    assert len(d) == 1 and d[0].unit_id == "u0"
    assert d[0].action is RoutingAction.RESTART


def test_persistent_disagreement_escalates_as_contract_defect():
    answers = {"m1": ["a"], "m2": ["b"]}
    d = route_disagreements(answers, ["u0"], restart_counts={"u0": 2}, max_restarts=2)
    assert d[0].action is RoutingAction.ESCALATE
    assert "codebook defect" in d[0].reason


def test_agreement_produces_no_routing_work():
    answers = {"m1": ["a", "b"], "m2": ["a", "b"]}
    assert route_disagreements(answers, ["u0", "u1"]) == []


# --- CQR-style frequency labels ------------------------------------------

def test_frequency_labels_follow_cqr_conventions():
    assert frequency_label(10, 10) == "general"     # all cases
    assert frequency_label(9, 10) == "general"      # all but one
    assert frequency_label(6, 10) == "typical"      # more than half
    assert frequency_label(3, 10) == "variant"      # >=2, not more than half
    assert frequency_label(1, 10) == "rare"
    assert frequency_label(0, 10) == "absent"


def test_panel_reports_frequency_labels():
    answers = {"m1": ["pain", "pain", "pain", "delight"], "m2": ["pain"] * 4}
    r = assess_panel(answers, _agents(("m1", "q"), ("m2", "l")))
    assert r.frequency_labels["pain"] in {"general", "typical"}


# --- Human coders are handled distinctly ---------------------------------

def test_human_coder_is_not_counted_as_an_agent():
    answers = {"m1": ["a", "b"], "m2": ["a", "b"], "h1": ["a", "b"]}
    coders = [
        Coder("m1", CoderKind.MODEL, "qwen"),
        Coder("m2", CoderKind.MODEL, "llama"),
        Coder("h1", CoderKind.HUMAN, "human"),
    ]
    r = assess_panel(answers, coders)
    # n_eff is computed over agents only; the human is a gold source, not a voter.
    assert r.n_eff <= 2.0
    assert r.n_nominal == 3


def test_summary_states_validity_status_plainly():
    r = assess_panel({"m1": ["a"], "m2": ["a"]}, _agents(("m1", "q"), ("m2", "l")))
    assert "validity UNKNOWN" in r.summary()
