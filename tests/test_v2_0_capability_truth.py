from __future__ import annotations

import json
from pathlib import Path

from kodepoia.capability_truth import (
    PUBLIC_DISTRIBUTION_SHA,
    PUBLIC_DISTRIBUTION_TAG,
    build_capability_matrix,
    capability_documentation_payload,
)
from kodepoia.kodestudio.research_panel import research_capability_rows


ROOT = Path(__file__).resolve().parents[1]


def _by_id(*, allow_network: bool = False, github_authenticated: bool = False):
    return {
        row["capability_id"]: row
        for row in build_capability_matrix(
            allow_network=allow_network,
            github_authenticated=github_authenticated,
        )
    }


def test_committed_capability_matrix_matches_runtime_truth() -> None:
    documented = json.loads(
        (ROOT / "docs" / "roadmap" / "V2_0_CAPABILITY_MATRIX.json").read_text(
            encoding="utf-8"
        )
    )
    assert documented == capability_documentation_payload()
    assert documented["public_distribution"] == {
        "tag": PUBLIC_DISTRIBUTION_TAG,
        "source_sha": PUBLIC_DISTRIBUTION_SHA,
    }


def test_kodestudio_research_rows_share_canonical_truth() -> None:
    runtime = [
        row
        for row in build_capability_matrix()
        if row["capability_id"].startswith("research.")
    ]
    assert list(research_capability_rows()) == runtime


def test_provider_failures_are_not_empty_result_states() -> None:
    rows = _by_id()
    assert rows["research.saved-reports-search"]["runtime_state"] == "ready"
    assert rows["research.web-discovery"]["runtime_state"] == "network-restricted"
    assert rows["research.github-authenticated-resource"]["runtime_state"] == "auth-required"
    assert rows["research.vision-provider"]["runtime_state"] == "unavailable"
    assert rows["research.explicit-web-fetch"]["runtime_state"] == "network-restricted"


def test_network_and_auth_transitions_are_explicit() -> None:
    network = _by_id(allow_network=True)
    assert network["research.explicit-web-fetch"]["runtime_state"] == "ready"
    assert network["research.web-discovery"]["runtime_state"] == "auth-required"
    assert network["research.github-discovery"]["runtime_state"] == "ready"
    assert network["research.github-known-resource"]["runtime_state"] == "ready"
    assert network["research.github-authenticated-resource"]["runtime_state"] == "auth-required"

    authenticated = _by_id(allow_network=True, github_authenticated=True)
    assert authenticated["research.github-authenticated-resource"]["runtime_state"] == "ready"
    assert authenticated["research.github-authenticated-resource"]["authentication_state"] == "authenticated"


def test_accelerator_policy_remains_conservative() -> None:
    rows = _by_id()
    kaggle = rows["accelerator.kaggle-t4x2"]
    tpu = rows["accelerator.tpu-v5e-8"]
    assert kaggle["accelerator_state"] == "priority"
    assert "acceptance-proven" in kaggle["classifications"]
    assert "public-validated" not in kaggle["classifications"]
    assert tpu["accelerator_state"] == "deferred"
    assert tpu["runtime_state"] == "not-implemented"
