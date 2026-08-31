from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from kodepoia.quality.redteam import (
    CasePolarity,
    ExpectedDecision,
    HarnessStatus,
    RedTeamCorpus,
    RedTeamRunner,
    load_redteam_corpus,
    policy_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "r16" / "redteam-corpus.json"
SOURCE_SHA = "1" * 40
POLICY_SHA = policy_sha256(
    {
        "instruction_data_separation": True,
        "least_privilege": True,
        "memory_is_not_policy": True,
        "recovery_before_continuation": True,
    }
)


def _load() -> RedTeamCorpus:
    return load_redteam_corpus(CORPUS, repository_root=ROOT)


def test_canonical_corpus_is_immutable_synthetic_and_complete() -> None:
    corpus = _load()

    assert corpus.metadata["synthetic_only"] is True
    assert corpus.metadata["immutable"] is True
    assert len(corpus.boundaries) == 14
    assert len(corpus.cases) == 28
    assert corpus.corpus_sha256 == corpus.declared_sha256
    assert corpus.case_set_sha256
    assert all(item["benign"] >= 1 for item in corpus.coverage().values())
    assert all(item["adversarial"] >= 1 for item in corpus.coverage().values())


def test_canonical_order_and_digest_are_deterministic() -> None:
    first = _load()
    second = _load()

    assert [item.id for item in first.boundaries] == sorted(item.id for item in first.boundaries)
    assert [item.id for item in first.cases] == sorted(item.id for item in first.cases)
    assert first.corpus_sha256 == second.corpus_sha256
    assert first.case_set_sha256 == second.case_set_sha256


def test_payloads_cover_frozen_attack_classes_without_live_secrets() -> None:
    corpus = _load()
    tags = {tag for case in corpus.cases for tag in case.tags}
    required = {
        "authority-spoofing",
        "corrupted-state",
        "destructive-command",
        "direct",
        "excessive-agency",
        "exfiltration",
        "indirect",
        "malicious-metadata",
        "memory-poisoning",
        "path-traversal",
        "resource-exhaustion",
        "secret-bait",
        "symlink",
        "tool-description-injection",
    }

    assert required <= tags
    assert all("BEGIN PRIVATE KEY" not in case.payload for case in corpus.cases)
    assert all("ghp_" not in case.payload for case in corpus.cases)
    assert any("[SYNTHETIC_SECRET:NEVER_REAL]" in case.payload for case in corpus.cases)


def test_loader_rejects_outside_repository(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text(CORPUS.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(ValueError, match="inside repository_root"):
        load_redteam_corpus(outside, repository_root=ROOT)


@pytest.mark.skipif(os.name == "nt", reason="symlink creation is not reliably available on Windows runners")
def test_loader_rejects_symlink_fixture(tmp_path: Path) -> None:
    link = tmp_path / "corpus.json"
    link.symlink_to(CORPUS)

    with pytest.raises(ValueError, match="cannot be a symlink"):
        load_redteam_corpus(link, repository_root=tmp_path)


def test_loader_rejects_digest_tampering(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    candidate = repo / "corpus.json"
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    payload["cases"][0]["payload"] += " tampered"
    candidate.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="digest mismatch"):
        load_redteam_corpus(candidate, repository_root=repo)


def test_loader_rejects_live_secret_shaped_values(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    candidate = repo / "corpus.json"
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    payload["cases"][0]["payload"] = "leaked ghp_123456789012345678901234567890"
    candidate.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="live-secret-shaped"):
        load_redteam_corpus(candidate, repository_root=repo)


def test_critical_boundary_requires_benign_and_adversarial_controls(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    candidate = repo / "corpus.json"
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    boundary = payload["boundaries"][0]["id"]
    payload["cases"] = [
        case
        for case in payload["cases"]
        if not (
            case["boundary_id"] == boundary
            and case["polarity"] == CasePolarity.ADVERSARIAL.value
        )
    ]
    payload_without_digest = {key: value for key, value in payload.items() if key != "corpus_sha256"}
    import hashlib

    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload["corpus_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    candidate.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="requires benign and adversarial coverage"):
        load_redteam_corpus(candidate, repository_root=repo)


def test_mutation_free_baseline_binds_source_corpus_and_policy() -> None:
    corpus = _load()
    report = RedTeamRunner(corpus).run(
        source_sha=SOURCE_SHA,
        policy_sha256=POLICY_SHA,
    )

    assert report.status is HarnessStatus.PASS
    assert report.mode == "mutation-free-contract"
    assert report.security_claim is False
    assert report.critical_veto is False
    assert report.source_sha == SOURCE_SHA
    assert report.corpus_sha256 == corpus.corpus_sha256
    assert report.case_set_sha256 == corpus.case_set_sha256
    assert report.policy_sha256 == POLICY_SHA
    assert all(item.actual_decision is None for item in report.results)
    assert all(item.passed is None for item in report.results)
    assert report.semantic_sha256 == RedTeamRunner(_load()).run(
        source_sha=SOURCE_SHA,
        policy_sha256=POLICY_SHA,
    ).semantic_sha256


def test_negative_control_boundary_bypass_cannot_silently_pass() -> None:
    corpus = _load()

    def bypass(case):
        if case.polarity is CasePolarity.ADVERSARIAL:
            return ExpectedDecision.ALLOW
        return case.expected_decision

    report = RedTeamRunner(corpus).run(
        source_sha=SOURCE_SHA,
        policy_sha256=POLICY_SHA,
        evaluator=bypass,
    )

    assert report.status is HarnessStatus.FAIL
    assert report.security_claim is True
    assert report.critical_veto is True
    assert any(item.critical and item.passed is False for item in report.results)


def test_exact_expected_decisions_produce_evaluation_pass_without_mutation() -> None:
    corpus = _load()
    report = RedTeamRunner(corpus).run(
        source_sha=SOURCE_SHA,
        policy_sha256=POLICY_SHA,
        evaluator=lambda case: case.expected_decision,
    )

    assert report.status is HarnessStatus.PASS
    assert report.security_claim is True
    assert report.critical_veto is False
    assert all(item.passed is True for item in report.results)


def test_source_and_policy_digests_are_fail_closed() -> None:
    runner = RedTeamRunner(_load())

    with pytest.raises(ValueError, match="40-hex"):
        runner.run(source_sha="main", policy_sha256=POLICY_SHA)
    with pytest.raises(ValueError, match="SHA-256"):
        runner.run(source_sha=SOURCE_SHA, policy_sha256="unknown")
