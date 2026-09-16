from __future__ import annotations

from copy import deepcopy
from enum import StrEnum
from typing import Any

PUBLIC_DISTRIBUTION_TAG = "v1.1.0-rc8"
PUBLIC_DISTRIBUTION_SHA = "fa787ab7ef76f2556b56ac1f058916a1425455af"


class CapabilityClassification(StrEnum):
    PUBLIC_VALIDATED = "public-validated"
    SOURCE_AVAILABLE = "source-available"
    ACCEPTANCE_PROVEN = "acceptance-proven"
    EXPERIMENTAL = "experimental"
    UNAVAILABLE = "unavailable"


class ProviderRuntimeState(StrEnum):
    READY = "ready"
    UNAVAILABLE = "unavailable"
    AUTH_REQUIRED = "auth-required"
    NETWORK_RESTRICTED = "network-restricted"
    NOT_IMPLEMENTED = "not-implemented"


class NetworkRuntimeState(StrEnum):
    NOT_REQUIRED = "not-required"
    ALLOWED = "allowed"
    RESTRICTED = "restricted"


class AuthenticationRuntimeState(StrEnum):
    NOT_REQUIRED = "not-required"
    OPTIONAL = "optional"
    AUTHENTICATED = "authenticated"
    REQUIRED = "required"


class AcceleratorRuntimeState(StrEnum):
    PRIORITY = "priority"
    AVAILABLE = "available"
    EXPERIMENTAL = "experimental"
    DEFERRED = "deferred"
    UNSUPPORTED = "unsupported"


def _evidence(path: str, sha: str, note: str) -> dict[str, str]:
    return {"path": path, "accepted_source_sha": sha, "note": note}


_BASELINE: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "research.saved-reports-search",
        "label": "Saved project research search",
        "classifications": ["public-validated", "source-available", "acceptance-proven"],
        "runtime_state": "ready",
        "network_state": "not-required",
        "authentication_state": "not-required",
        "accelerator_state": None,
        "action": "Search persisted project research reports. Zero matches is a successful local result.",
        "details": "This KodeStudio Search path does not run Internet discovery.",
        "live_source_paths": [
            "src/kodepoia/intelligence/research/service.py",
            "src/kodepoia/kodestudio/research_panel.py",
        ],
        "public_distribution": PUBLIC_DISTRIBUTION_TAG,
        "public_source_sha": PUBLIC_DISTRIBUTION_SHA,
        "evidence": [
            _evidence(
                "docs/roadmap/R7_10_ACCEPTANCE.md",
                "cfd0f7ba02af04b456993f686827f10810b3a61a",
                "Shared ResearchService and KodeStudio local query path accepted.",
            )
        ],
    },
    {
        "capability_id": "research.local-document-fetch",
        "label": "Local and official-document acquisition",
        "classifications": ["public-validated", "source-available", "acceptance-proven"],
        "runtime_state": "ready",
        "network_state": "not-required",
        "authentication_state": "not-required",
        "accelerator_state": None,
        "action": "Provide a project-relative local document or accepted offline official snapshot.",
        "details": "Local acquisition is distinct from external discovery.",
        "live_source_paths": [
            "src/kodepoia/intelligence/research/documents.py",
            "src/kodepoia/intelligence/research/service.py",
        ],
        "public_distribution": PUBLIC_DISTRIBUTION_TAG,
        "public_source_sha": PUBLIC_DISTRIBUTION_SHA,
        "evidence": [
            _evidence(
                "docs/roadmap/R7_2_ACCEPTANCE.md",
                "9101e686a32b24bb33a23d7ac578bf25570e115e",
                "Local/offline official documentation research accepted.",
            )
        ],
    },
    {
        "capability_id": "research.explicit-web-fetch",
        "label": "Guarded explicit-URL Web fetch",
        "classifications": ["public-validated", "source-available", "acceptance-proven"],
        "runtime_state": "network-restricted",
        "network_state": "restricted",
        "authentication_state": "not-required",
        "accelerator_state": None,
        "action": "Enable NETWORK for this explicit fetch and provide an HTTP(S) locator.",
        "details": "GET-only governed acquisition for an explicit locator; this is not Web discovery.",
        "live_source_paths": [
            "src/kodepoia/intelligence/research/web.py",
            "src/kodepoia/intelligence/research/service.py",
        ],
        "public_distribution": PUBLIC_DISTRIBUTION_TAG,
        "public_source_sha": PUBLIC_DISTRIBUTION_SHA,
        "evidence": [
            _evidence(
                "docs/roadmap/R7_3_ACCEPTANCE.md",
                "4efd2cb016e774fa3ef06590ffda377606d875e9",
                "Governed GET-only Web research accepted.",
            )
        ],
    },
    {
        "capability_id": "research.web-discovery",
        "label": "Question-driven general Web discovery",
        "classifications": ["unavailable"],
        "runtime_state": "not-implemented",
        "network_state": "restricted",
        "authentication_state": "not-required",
        "accelerator_state": None,
        "action": "Use saved research or explicit-URL fetch until V2.1.2 qualifies discovery providers.",
        "details": "No current provider turns a natural-language question into Web search results.",
        "live_source_paths": [],
        "public_distribution": "",
        "public_source_sha": "",
        "evidence": [],
    },
    {
        "capability_id": "research.github-known-resource",
        "label": "GitHub known-resource acquisition",
        "classifications": ["public-validated", "source-available", "acceptance-proven"],
        "runtime_state": "network-restricted",
        "network_state": "restricted",
        "authentication_state": "optional",
        "accelerator_state": None,
        "action": "Enable NETWORK and provide a structured repository/resource selector.",
        "details": "Read-only typed acquisition for known GitHub resources; not question-driven discovery.",
        "live_source_paths": ["src/kodepoia/intelligence/research/github.py"],
        "public_distribution": PUBLIC_DISTRIBUTION_TAG,
        "public_source_sha": PUBLIC_DISTRIBUTION_SHA,
        "evidence": [
            _evidence(
                "docs/roadmap/R7_4_ACCEPTANCE.md",
                "be6f1d5d2f7d9a16c1c295a51905fcd22e9835be",
                "Typed read-only GitHub adapter accepted for public unauthenticated behavior.",
            )
        ],
    },
    {
        "capability_id": "research.github-authenticated-resource",
        "label": "Authenticated/private GitHub acquisition",
        "classifications": ["source-available", "experimental"],
        "runtime_state": "auth-required",
        "network_state": "restricted",
        "authentication_state": "required",
        "accelerator_state": None,
        "action": (
            "Configure a least-privilege read-only GitHub credential through KodeSecrets "
            "and run explicit authenticated acceptance."
        ),
        "details": "Credential plumbing exists, but R7.4 did not run real private/authenticated hosted proof.",
        "live_source_paths": ["src/kodepoia/intelligence/research/github.py"],
        "public_distribution": "",
        "public_source_sha": "",
        "evidence": [
            _evidence(
                "docs/roadmap/R7_4_ACCEPTANCE.md",
                "be6f1d5d2f7d9a16c1c295a51905fcd22e9835be",
                "Conditional private/authenticated manual gate was not triggered.",
            )
        ],
    },
    {
        "capability_id": "research.github-discovery",
        "label": "Question-driven GitHub discovery",
        "classifications": ["unavailable"],
        "runtime_state": "not-implemented",
        "network_state": "restricted",
        "authentication_state": "optional",
        "accelerator_state": None,
        "action": "Use typed known-resource GitHub acquisition until V2.1.2 qualifies GitHub discovery.",
        "details": "The accepted GitHub adapter resolves known resources; it is not a search provider.",
        "live_source_paths": [],
        "public_distribution": "",
        "public_source_sha": "",
        "evidence": [],
    },
    {
        "capability_id": "research.community-normalization",
        "label": "Community-source normalization",
        "classifications": ["public-validated", "source-available", "acceptance-proven"],
        "runtime_state": "ready",
        "network_state": "not-required",
        "authentication_state": "not-required",
        "accelerator_state": None,
        "action": "Normalize already acquired community content as untrusted evidence.",
        "details": "Normalization is accepted; question-driven community discovery is not implied.",
        "live_source_paths": ["src/kodepoia/intelligence/research/community.py"],
        "public_distribution": PUBLIC_DISTRIBUTION_TAG,
        "public_source_sha": PUBLIC_DISTRIBUTION_SHA,
        "evidence": [
            _evidence(
                "docs/roadmap/R7_5_ACCEPTANCE.md",
                "12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5",
                "Community-source normalization accepted.",
            )
        ],
    },
    {
        "capability_id": "research.youtube-transcript",
        "label": "YouTube metadata/transcript acquisition",
        "classifications": ["public-validated", "source-available", "acceptance-proven"],
        "runtime_state": "network-restricted",
        "network_state": "restricted",
        "authentication_state": "not-required",
        "accelerator_state": None,
        "action": "Enable NETWORK and provide an explicit YouTube locator.",
        "details": "Accepted explicit-locator media acquisition; not question-driven YouTube discovery.",
        "live_source_paths": ["src/kodepoia/intelligence/research/media.py"],
        "public_distribution": PUBLIC_DISTRIBUTION_TAG,
        "public_source_sha": PUBLIC_DISTRIBUTION_SHA,
        "evidence": [
            _evidence(
                "docs/roadmap/R7_6_ACCEPTANCE.md",
                "b623836b8f5bd39fce101eca7fe4653a996a9562",
                "YouTube metadata/transcript path accepted.",
            )
        ],
    },
    {
        "capability_id": "research.vision-provider",
        "label": "Research vision provider",
        "classifications": [
            "public-validated",
            "source-available",
            "acceptance-proven",
            "unavailable",
        ],
        "runtime_state": "unavailable",
        "network_state": "not-required",
        "authentication_state": "not-required",
        "accelerator_state": None,
        "action": "Keep vision unavailable until a concrete provider is configured and separately accepted.",
        "details": "R7.7 explicitly preserved UNAVAILABLE when no accepted vision provider exists.",
        "live_source_paths": ["src/kodepoia/intelligence/research/media.py"],
        "public_distribution": PUBLIC_DISTRIBUTION_TAG,
        "public_source_sha": PUBLIC_DISTRIBUTION_SHA,
        "evidence": [
            _evidence(
                "docs/roadmap/R7_7_ACCEPTANCE.md",
                "04cef94c82fdacafe7313d27c8cf516e8e765295",
                "Fail-closed vision unavailability accepted.",
            )
        ],
    },
    {
        "capability_id": "accelerator.kaggle-t4x2",
        "label": "Kaggle GPU T4 x2",
        "classifications": ["source-available", "acceptance-proven"],
        "runtime_state": "auth-required",
        "network_state": "restricted",
        "authentication_state": "required",
        "accelerator_state": "priority",
        "action": (
            "Authenticate the Kaggle CLI, enable network access, verify quota, "
            "then run the governed R15 remote-training flow."
        ),
        "details": "Priority remote accelerator: two separate 16 GiB GPUs, never one 32 GiB pool.",
        "live_source_paths": [
            "src/kodepoia/tuning/kaggle_remote.py",
            "docs/user/KAGGLE_REMOTE_TRAINING.md",
            ".github/workflows/r15-kaggle-remote-training.yml",
        ],
        "public_distribution": "",
        "public_source_sha": "",
        "evidence": [
            _evidence(
                ".github/workflows/r15-kaggle-remote-training.yml",
                "b99c65d5113026d66993ff419bb44dc71923a2ea",
                "PR #470 final exact head; Kaggle acceptance run 35001867739 completed/success.",
            )
        ],
    },
    {
        "capability_id": "accelerator.tpu-v5e-8",
        "label": "TPU v5e-8",
        "classifications": ["experimental", "unavailable"],
        "runtime_state": "not-implemented",
        "network_state": "restricted",
        "authentication_state": "required",
        "accelerator_state": "deferred",
        "action": "Do not implement XLA unless a benchmark demonstrates a material Kodepoia advantage.",
        "details": "Deferred; no qualified JAX/PyTorch-XLA backend exists.",
        "live_source_paths": [],
        "public_distribution": "",
        "public_source_sha": "",
        "evidence": [],
    },
)


def _validate(rows: list[dict[str, Any]]) -> None:
    sha40 = __import__("re").compile(r"^[0-9a-f]{40}$")
    for row in rows:
        classifications = set(row["classifications"])
        if "source-available" in classifications and not row["live_source_paths"]:
            raise ValueError(f"source-available without live source: {row['capability_id']}")
        if "acceptance-proven" in classifications:
            if not row["evidence"]:
                raise ValueError(f"acceptance-proven without evidence: {row['capability_id']}")
            for evidence in row["evidence"]:
                if not sha40.fullmatch(evidence["accepted_source_sha"]):
                    raise ValueError(f"non exact acceptance SHA: {row['capability_id']}")
        if "public-validated" in classifications:
            if row["public_distribution"] != PUBLIC_DISTRIBUTION_TAG:
                raise ValueError(f"invalid public tag: {row['capability_id']}")
            if row["public_source_sha"] != PUBLIC_DISTRIBUTION_SHA:
                raise ValueError(f"invalid public SHA: {row['capability_id']}")


def build_capability_matrix(
    *,
    allow_network: bool = False,
    github_authenticated: bool = False,
) -> list[dict[str, Any]]:
    rows = deepcopy(list(_BASELINE))
    by_id = {row["capability_id"]: row for row in rows}

    if allow_network:
        for capability_id in (
            "research.explicit-web-fetch",
            "research.github-known-resource",
            "research.youtube-transcript",
        ):
            row = by_id[capability_id]
            row["runtime_state"] = "ready"
            row["network_state"] = "allowed"
        by_id["research.github-authenticated-resource"]["network_state"] = "allowed"
        by_id["accelerator.kaggle-t4x2"]["network_state"] = "allowed"

    auth_row = by_id["research.github-authenticated-resource"]
    if github_authenticated:
        auth_row["authentication_state"] = "authenticated"
        auth_row["runtime_state"] = "ready" if allow_network else "network-restricted"

    _validate(rows)
    return sorted(rows, key=lambda row: row["capability_id"])


def capability_matrix_payload(
    *,
    allow_network: bool = False,
    github_authenticated: bool = False,
) -> dict[str, Any]:
    return {
        "schema": "kodepoia.v2.capability-matrix",
        "schema_version": 1,
        "public_distribution": {
            "tag": PUBLIC_DISTRIBUTION_TAG,
            "source_sha": PUBLIC_DISTRIBUTION_SHA,
        },
        "runtime_context": {
            "network_allowed": allow_network,
            "github_authenticated": github_authenticated,
        },
        "capabilities": build_capability_matrix(
            allow_network=allow_network,
            github_authenticated=github_authenticated,
        ),
    }


def capability_documentation_payload() -> dict[str, Any]:
    full = capability_matrix_payload()
    fields = (
        "capability_id",
        "classifications",
        "runtime_state",
        "network_state",
        "authentication_state",
        "accelerator_state",
    )
    return {
        "schema": "kodepoia.v2.capability-matrix.documentation",
        "schema_version": 1,
        "public_distribution": full["public_distribution"],
        "runtime_context": full["runtime_context"],
        "capabilities": [
            {field: row[field] for field in fields}
            for row in full["capabilities"]
        ],
    }
