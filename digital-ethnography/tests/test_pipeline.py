from pathlib import Path

from ethnography.config import load_study
from ethnography.pipeline import EthnographyPipeline

CONFIG = Path(__file__).resolve().parents[1] / "config" / "study.example.yaml"


def _run():
    loaded = load_study(CONFIG)
    pipeline = EthnographyPipeline(
        study=loaded.study,
        consent=loaded.consent,
        salt=loaded.salt,
        codebook=loaded.codebook,
    )
    return loaded, pipeline.run(loaded.adapters)


def test_end_to_end_runs_and_produces_report():
    _, result = _run()
    assert result.report_markdown.startswith("# Digital Ethnography Field Report")
    assert "Ethics & Data Governance" in result.report_markdown
    assert result.audit.verify()


def test_non_consenting_users_are_absent_from_corpus():
    loaded, result = _run()
    # u_dave (events only) and u_frank (review only) never consented.
    dave = pid_for(loaded, "u_dave")
    frank = pid_for(loaded, "u_frank")
    assert dave not in result.corpus.participants
    assert frank not in result.corpus.participants
    # Consenting users are present.
    assert pid_for(loaded, "u_alice") in result.corpus.participants


def test_pii_is_redacted_in_corpus():
    _, result = _run()
    blob = " ".join(o.text or "" for o in result.corpus.observations)
    assert "alice@example.com" not in blob
    assert "415-555-0199" not in blob
    assert "[EMAIL]" in blob or "[PHONE]" in blob


def test_frank_ssn_never_enters_corpus():
    # u_frank did not consent, so their SSN-bearing review is dropped entirely.
    _, result = _run()
    blob = " ".join(o.text or "" for o in result.corpus.observations)
    assert "123-45-6789" not in blob


def test_themes_and_journeys_present():
    _, result = _run()
    assert len(result.themes) >= 1
    # Bob hit repeated payment errors -> friction should be detected.
    assert any(j.friction for j in result.journeys)


def test_deterministic_run_has_no_review_queue():
    # Deterministic core only (llm_enrichment: false) -> nothing needs review.
    _, result = _run()
    assert result.review_queue == []


def pid_for(loaded, raw):
    from ethnography.ethics.redaction import Pseudonymizer

    return Pseudonymizer(loaded.salt).pid(raw)
