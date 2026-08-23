from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]


def test_r10_6_local_runtime_mapping_uses_runner_manifest_shape() -> None:
    namespace = runpy.run_path(str(ROOT / "scripts/r10_6_local_acceptance.py"))
    runtime_evidence = namespace["runtime_evidence"]
    evidence, blockers = runtime_evidence(
        {
            "runtime": {"version": "5.2.0", "platform": "windows"},
            "probe": {"background": True, "online_access": False},
        }
    )
    assert blockers == []
    assert evidence == {
        "blender_version": "5.2.0",
        "platform": "windows",
        "background": True,
        "online_access": False,
    }


def test_r10_6_local_runtime_mapping_fails_closed_when_missing() -> None:
    namespace = runpy.run_path(str(ROOT / "scripts/r10_6_local_acceptance.py"))
    runtime_evidence = namespace["runtime_evidence"]
    evidence, blockers = runtime_evidence({"runtime": {}, "probe": {}})
    assert evidence == {
        "blender_version": None,
        "platform": None,
        "background": None,
        "online_access": None,
    }
    assert set(blockers) == {
        "runtime_version_missing_or_invalid",
        "runtime_platform_missing",
        "runtime_background_not_confirmed",
        "runtime_offline_not_confirmed",
    }


def test_r10_6_local_schema_rejects_null_runtime_evidence() -> None:
    schema = json.loads((ROOT / "schemas/r10-rig-local-acceptance-v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    payload = {
        "schema": "kodepoia.r10_6_local_acceptance",
        "version": 1,
        "source_sha": "a" * 40,
        "status": "pass",
        "blockers": [],
        "runtime": {
            "blender_version": "5.2.0",
            "platform": "windows",
            "background": True,
            "online_access": False,
        },
        "fixture": {},
        "rig": {},
        "evidence_digest": "b" * 64,
    }
    validator.validate(payload)
    payload["runtime"] = {
        "blender_version": None,
        "platform": None,
        "background": None,
        "online_access": None,
    }
    with pytest.raises(ValidationError):
        validator.validate(payload)
