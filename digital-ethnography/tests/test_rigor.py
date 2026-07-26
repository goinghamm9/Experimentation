"""Tests for the rigor layer.

These estimators produce numbers a researcher will quote, so the tests check them
against hand-computable cases and known analytic properties rather than golden
values produced by the implementation itself.
"""

import math

import pytest

from ethnography.rigor import (
    SearchLedger,
    alpha_eff,
    assess_consensus,
    assess_reliability,
    assess_saturation,
    chao1,
    chao1_bias_corrected,
    cohens_kappa,
    competence_weighted_answer,
    detection_floor,
    fleiss_kappa,
    good_turing_unseen,
    krippendorff_alpha,
    marchenko_pastur_edge,
    max_spurious_correlation,
    n_eff_correlation,
    n_eff_tail,
    ppv,
    rule_of_three,
)


# --- Saturation -----------------------------------------------------------

def test_chao1_matches_hand_computation():
    # D=10, f1=4, f2=2  ->  10 + 16/4 = 14
    assert chao1(10, 4, 2) == pytest.approx(14.0)
    # bias-corrected: 10 + 4*3/(2*3) = 12
    assert chao1_bias_corrected(10, 4, 2) == pytest.approx(12.0)


def test_chao1_falls_back_when_f2_zero():
    # Classic estimator divides by zero; must degrade to bias-corrected form.
    assert chao1(5, 3, 0) == pytest.approx(chao1_bias_corrected(5, 3, 0))


def test_good_turing_is_singleton_rate():
    assert good_turing_unseen(4, 100) == pytest.approx(0.04)
    assert good_turing_unseen(0, 0) == 0.0


def test_no_singletons_means_nothing_projected_unseen():
    # Every code seen by 3+ participants -> f1 = 0 -> no unseen mass.
    code_to_units = {f"c{i}": {"p1", "p2", "p3"} for i in range(5)}
    r = assess_saturation(code_to_units, n_units=3)
    assert r.f1 == 0
    assert r.unseen_mass == 0.0
    assert r.projected_unseen == pytest.approx(0.0)
    assert r.is_saturated


def test_many_singletons_flags_unsaturated():
    code_to_units = {f"c{i}": {f"p{i}"} for i in range(10)}
    r = assess_saturation(code_to_units, n_units=10)
    assert r.f1 == 10
    assert r.unseen_mass == pytest.approx(1.0)
    assert not r.is_saturated
    assert r.projected_unseen > 0


# --- Reliability ----------------------------------------------------------

def test_krippendorff_alpha_is_one_on_perfect_agreement():
    units = [["a", "a"], ["b", "b"], ["a", "a"], ["b", "b"]]
    assert krippendorff_alpha(units) == pytest.approx(1.0)


def test_krippendorff_alpha_near_zero_on_chance_agreement():
    # Systematic disagreement -> alpha should be <= 0 (worse than chance).
    units = [["a", "b"], ["b", "a"], ["a", "b"], ["b", "a"]]
    alpha = krippendorff_alpha(units)
    assert alpha is not None and alpha < 0.05


def test_krippendorff_handles_missing_and_undefined():
    # Units with <2 ratings contribute nothing.
    assert krippendorff_alpha([["a", None], [None, None]]) is None
    # Zero expected disagreement (single category) -> undefined, not a crash.
    assert krippendorff_alpha([["a", "a"], ["a", "a"]]) is None


def test_cohens_kappa_perfect_and_chance():
    assert cohens_kappa(["a", "b", "a"], ["a", "b", "a"]) == pytest.approx(1.0)
    k = cohens_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])
    assert k is not None and abs(k) < 1e-9  # exactly chance


def test_fleiss_kappa_perfect_agreement():
    units = [["a", "a", "a"], ["b", "b", "b"], ["a", "a", "a"]]
    assert fleiss_kappa(units) == pytest.approx(1.0)


def test_n_eff_correlation_deflates_as_documented():
    assert n_eff_correlation(5, 0.0) == pytest.approx(5.0)      # independent
    assert n_eff_correlation(5, 1.0) == pytest.approx(1.0)      # identical

    # NOTE — discrepancy in the source corpus, resolved in favour of the formula.
    # Corpus §8.1 states the formula n_eff = k/(1+(k-1)rho) and then illustrates it
    # with "at rho = 0.6, five informants ... are worth about 1.7". The formula
    # actually gives 5/3.4 = 1.47; the value 1.67 corresponds to rho = 0.5.
    # The formula is the standard Kish design-effect result and is correct, so we
    # assert the formula and not the illustration.
    assert n_eff_correlation(5, 0.6) == pytest.approx(1.4706, abs=0.001)
    assert n_eff_correlation(5, 0.5) == pytest.approx(1.6667, abs=0.001)


def test_n_eff_tail_deflates_independently():
    # alpha=1.5, n=100 -> 100^(2*0.5/1.5) = 100^(2/3) ~= 21.5
    assert n_eff_tail(100, 1.5) == pytest.approx(21.5, abs=0.5)
    assert n_eff_tail(100, 3.0) == pytest.approx(100.0)  # thin tail, no deflation


def test_single_coder_reports_unknown_not_a_pass():
    r = assess_reliability(units=[], n_coders=1)
    assert r.alpha is None
    assert "UNKNOWN" in r.note
    assert r.interpretation() == "not computable"


# --- Consensus (CCT) ------------------------------------------------------

def test_cct_needs_three_coders():
    r = assess_consensus({"a": ["x"], "b": ["x"]})
    assert r.n_coders == 2
    assert "at least 3" in r.note


def test_cct_detects_single_shared_rubric():
    # Three coders who mostly agree -> one dominant eigenvalue.
    answers = {
        "c1": ["a", "b", "a", "b", "a", "b", "a", "b"],
        "c2": ["a", "b", "a", "b", "a", "b", "a", "a"],
        "c3": ["a", "b", "a", "b", "a", "b", "b", "b"],
    }
    r = assess_consensus(answers)
    assert r.eigenvalue_ratio is not None
    assert r.single_domain
    assert all(0.0 <= v <= 1.0 for v in r.competences.values())


def test_cct_flags_two_rubrics():
    # Two blocs that disagree across the split -> lambda2 is large.
    answers = {
        "a1": ["a", "a", "a", "a", "a", "a"],
        "a2": ["a", "a", "a", "a", "a", "a"],
        "b1": ["b", "b", "b", "b", "b", "b"],
        "b2": ["b", "b", "b", "b", "b", "b"],
    }
    r = assess_consensus(answers)
    assert not r.single_domain
    assert "MORE THAN ONE rubric" in r.note


def test_marchenko_pastur_edge_grows_with_aspect_ratio():
    # q -> 0 (many observations) => edge -> sigma^2
    assert marchenko_pastur_edge(4, 10_000) == pytest.approx(1.0, abs=0.1)
    # q = 1 => edge = 4*sigma^2
    assert marchenko_pastur_edge(100, 100) == pytest.approx(4.0)


def test_competence_weighting_beats_majority():
    # Two low-competence coders outvote one high-competence coder by headcount,
    # but competence weighting recovers the expert's answer (corpus 2.1).
    answers = {"expert": ["correct"], "n1": ["wrong"], "n2": ["wrong"]}
    competences = {"expert": 0.95, "n1": 0.15, "n2": 0.15}
    assert competence_weighted_answer(answers, competences, 0) == "correct"


# --- Base-rate honesty & search space ------------------------------------

def test_ppv_reproduces_the_corpus_worked_example():
    # sens .95, spec .99, prevalence .001 -> ~8.7% precision
    assert ppv(0.95, 0.99, 0.001) == pytest.approx(0.0868, abs=0.001)


def test_ppv_improves_with_prestratification():
    # Raising prevalence beats chasing specificity.
    assert ppv(0.95, 0.99, 0.10) > ppv(0.999, 0.999, 0.001) * 0.5


def test_rule_of_three():
    # 30 observations, zero occurrences -> prevalence still plausibly 10%
    assert rule_of_three(30) == pytest.approx(0.10)


def test_detection_floor_matches_documented_case():
    # 95% confident of catching anything held by >=30% -> 9 interviews
    assert detection_floor(0.30, 0.95) == 9


def test_alpha_eff_explodes_with_search():
    assert alpha_eff(0.05, 1) == pytest.approx(0.05)
    assert alpha_eff(0.05, 100) > 0.99


def test_max_spurious_correlation_matches_worked_example():
    # m=20,000 pairs at n=500 -> ~0.20
    assert max_spurious_correlation(20_000, 500) == pytest.approx(0.199, abs=0.01)


def test_max_spurious_correlation_is_clamped_to_a_possible_value():
    """The asymptotic formula exceeds 1 when m is large and n small.

    A correlation above 1 is impossible; reporting one destroys credibility. The
    clamped value means the search space has outgrown the sample entirely.
    """
    from ethnography.rigor.honesty import search_is_saturated

    assert max_spurious_correlation(105, 5) == pytest.approx(1.0)
    assert search_is_saturated(105, 5)
    assert not search_is_saturated(20_000, 500)


def test_search_ledger_accumulates_and_reports():
    led = SearchLedger()
    led.record("open_coding", 12)
    led.record("axial_coding", 3)
    assert led.hypotheses_considered == 15
    rep = led.report(n_observations=100)
    assert rep["m_hypotheses"] == 15
    assert rep["alpha_effective"] > 0.05
    assert "15 hypotheses" in led.summary(100)


# --- Jacobi eigensolver sanity -------------------------------------------

def test_jacobi_recovers_known_eigenvalues():
    from ethnography.rigor.consensus import jacobi_eigen

    # [[2,1],[1,2]] has eigenvalues 3 and 1.
    vals, _ = jacobi_eigen([[2.0, 1.0], [1.0, 2.0]])
    assert vals[0] == pytest.approx(3.0)
    assert vals[1] == pytest.approx(1.0)


def test_jacobi_is_stable_on_identity():
    from ethnography.rigor.consensus import jacobi_eigen

    vals, _ = jacobi_eigen([[1.0, 0.0], [0.0, 1.0]])
    assert all(v == pytest.approx(1.0) for v in vals)
    assert not any(math.isnan(v) for v in vals)
