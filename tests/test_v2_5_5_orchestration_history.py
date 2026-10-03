from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.orchestrator.history import OrchestrationHistoryStore


def test_history_is_append_only_hash_chained_and_persistent(tmp_path: Path) -> None:
    store = OrchestrationHistoryStore(tmp_path)
    first = store.append(event="plan_loaded", plan_digest_sha256="a" * 64)
    second = store.append(
        event="task_completed",
        plan_digest_sha256="a" * 64,
        task_id="inspect",
        task_digest_sha256="b" * 64,
        workspace_id="c" * 64,
        state="completed",
        evidence_digest_sha256="d" * 64,
    )

    records = store.records()
    assert records == (first, second)
    assert second.previous_digest_sha256 == first.digest_sha256
    assert store.path == tmp_path.resolve() / ".kodepoia" / "orchestration" / "history.jsonl"


def test_history_tampering_fails_closed(tmp_path: Path) -> None:
    store = OrchestrationHistoryStore(tmp_path)
    store.append(event="plan_loaded", plan_digest_sha256="a" * 64)

    line = json.loads(store.path.read_text(encoding="utf-8").strip())
    line["event"] = "tampered"
    store.path.write_text(json.dumps(line) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="digest mismatch"):
        store.records()
