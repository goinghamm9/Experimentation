from datetime import datetime, timedelta, timezone

import pytest

from ethnography.ethics.audit import AuditLog
from ethnography.ethics.consent import ConsentRecord, ConsentRegistry
from ethnography.ethics.governance import GovernanceGate
from ethnography.ethics.redaction import Pseudonymizer, redact_text
from ethnography.schema import (
    DataCategory,
    Observation,
    ObservationKind,
    Study,
    utcnow,
)


def _obs(pid, category=DataCategory.CONTENT, text=None, when=None, event=None):
    return Observation(
        id=f"{pid}:{id(text)}",
        pid=pid,
        source="test",
        kind=ObservationKind.UTTERANCE if text else ObservationKind.EVENT,
        timestamp=when or utcnow(),
        category=category,
        text=text,
        payload={"event": event} if event else {},
    )


def _study(**kw):
    defaults = dict(
        id="s1",
        title="t",
        purpose="research",
        allowed_categories={DataCategory.BEHAVIORAL, DataCategory.CONTENT},
        retention_days=90,
    )
    defaults.update(kw)
    return Study(**defaults)


def _consent(pid, study, **kw):
    reg = ConsentRegistry()
    reg.grant(
        ConsentRecord(
            pid=pid,
            study_id=study.id,
            purposes=kw.get("purposes", {study.purpose}),
            categories=kw.get("categories", {DataCategory.BEHAVIORAL, DataCategory.CONTENT}),
            granted_at=kw.get("granted_at", datetime(2020, 1, 1, tzinfo=timezone.utc)),
            expires_at=kw.get("expires_at"),
            withdrawn=kw.get("withdrawn", False),
        )
    )
    return reg


# --- Pseudonymization -------------------------------------------------------

def test_pseudonymizer_is_deterministic_and_non_identifying():
    p = Pseudonymizer("super-secret-salt")
    assert p.pid("alice@example.com") == p.pid("alice@example.com")
    assert p.pid("alice@example.com") != p.pid("bob@example.com")
    assert "alice" not in p.pid("alice@example.com")


def test_pseudonymizer_rejects_weak_salt():
    with pytest.raises(ValueError):
        Pseudonymizer("short")


# --- Redaction --------------------------------------------------------------

def test_redaction_scrubs_common_pii():
    r = redact_text("Email me at jane@doe.com or 415-555-0199, SSN 123-45-6789")
    assert "jane@doe.com" not in r.text
    assert "[EMAIL]" in r.text
    assert "[PHONE]" in r.text
    assert "[SSN]" in r.text
    assert r.anything_redacted


def test_redaction_noop_on_clean_text():
    r = redact_text("the checkout was smooth and delightful")
    assert not r.anything_redacted


# --- Consent ----------------------------------------------------------------

def test_consent_gate_permits_only_matching_purpose_and_category():
    study = _study()
    reg = _consent("p1", study)
    assert reg.permits("p1", study, DataCategory.CONTENT)
    # Wrong purpose -> denied.
    other = _study(id="s1", purpose="marketing")
    assert not reg.permits("p1", other, DataCategory.CONTENT)


def test_consent_withdrawal_revokes_access():
    study = _study()
    reg = _consent("p1", study)
    assert reg.permits("p1", study, DataCategory.CONTENT)
    assert reg.withdraw("p1", study.id)
    assert not reg.permits("p1", study, DataCategory.CONTENT)


def test_consent_expiry_revokes_access():
    study = _study()
    reg = _consent("p1", study, expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc))
    assert not reg.permits("p1", study, DataCategory.CONTENT)


# --- Governance gate --------------------------------------------------------

def test_gate_drops_non_consenting_participants():
    study = _study()
    reg = _consent("p1", study)
    audit = AuditLog()
    gate = GovernanceGate(reg, audit)
    obs = [_obs("p1", text="hi"), _obs("p2", text="no consent")]
    corpus, report = gate.apply(study, obs, {})
    assert report.kept == 1
    assert report.dropped_no_consent == 1
    assert "p2" not in corpus.participants


def test_gate_enforces_minimization():
    study = _study(allowed_categories={DataCategory.BEHAVIORAL})
    reg = _consent("p1", study)
    audit = AuditLog()
    gate = GovernanceGate(reg, audit)
    obs = [_obs("p1", category=DataCategory.CONTENT, text="text not allowed")]
    _, report = gate.apply(study, obs, {})
    assert report.kept == 0
    assert report.dropped_minimization == 1


def test_gate_enforces_retention():
    study = _study(retention_days=30)
    reg = _consent("p1", study)
    audit = AuditLog()
    gate = GovernanceGate(reg, audit)
    old = utcnow() - timedelta(days=100)
    corpus, report = gate.apply(study, [_obs("p1", when=old, text="old")], {})
    assert report.dropped_retention == 1
    assert report.kept == 0


def test_gate_redacts_before_retention():
    study = _study()
    reg = _consent("p1", study)
    audit = AuditLog()
    gate = GovernanceGate(reg, audit)
    corpus, report = gate.apply(study, [_obs("p1", text="reach me a@b.com")], {})
    assert report.redacted == 1
    assert "a@b.com" not in corpus.observations[0].text
    assert corpus.observations[0].redacted


def test_gate_refuses_sensitive_unless_allowed():
    study = _study()  # SENSITIVE not in allowed_categories
    reg = _consent("p1", study, categories={DataCategory.SENSITIVE})
    audit = AuditLog()
    gate = GovernanceGate(reg, audit)
    obs = [_obs("p1", category=DataCategory.SENSITIVE, text="sensitive")]
    _, report = gate.apply(study, obs, {})
    assert report.dropped_minimization + report.dropped_sensitive == 1
    assert report.kept == 0


def test_erasure_removes_all_participant_traces():
    study = _study()
    reg = _consent("p1", study)
    audit = AuditLog()
    gate = GovernanceGate(reg, audit)
    corpus, _ = gate.apply(study, [_obs("p1", text="a"), _obs("p1", text="b")], {})
    removed = gate.erase_participant(corpus, "p1")
    assert removed == 2
    assert corpus.by_participant("p1") == []
    assert "p1" not in corpus.participants


# --- Audit ------------------------------------------------------------------

def test_audit_chain_verifies_and_detects_tampering():
    log = AuditLog()
    log.record("keep", "o1")
    log.record("drop", "o2", reason="no_consent")
    assert log.verify()
    # Tamper with a recorded event.
    log.events()[0].detail["reason"] = "tampered"
    assert not log.verify()
