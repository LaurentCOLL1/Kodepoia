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


def _row(
    capability_id: str,
    label: str,
    classifications: list[str],
    runtime_state: str,
    network_state: str,
    authentication_state: str,
    action: str,
    details: str,
    live_source_paths: list[str],
    *,
    accelerator_state: str | None = None,
    public: bool = False,
    evidence: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "label": label,
        "classifications": classifications,
        "runtime_state": runtime_state,
        "network_state": network_state,
        "authentication_state": authentication_state,
        "accelerator_state": accelerator_state,
        "action": action,
        "details": details,
        "live_source_paths": live_source_paths,
        "public_distribution": PUBLIC_DISTRIBUTION_TAG if public else "",
        "public_source_sha": PUBLIC_DISTRIBUTION_SHA if public else "",
        "evidence": evidence or [],
    }


_BASELINE: tuple[dict[str, Any], ...] = (
    _row(
        "research.saved-reports-search",
        "Saved project research search",
        ["public-validated", "source-available", "acceptance-proven"],
        "ready", "not-required", "not-required",
        "Search persisted project research reports. Zero matches is a successful local result.",
        "This KodeStudio Search path does not run Internet discovery.",
        ["src/kodepoia/intelligence/research/service.py", "src/kodepoia/kodestudio/research_panel.py"],
        public=True,
        evidence=[_evidence("docs/roadmap/R7_10_ACCEPTANCE.md", "cfd0f7ba02af04b456993f686827f10810b3a61a", "Shared ResearchService and KodeStudio local query path accepted.")],
    ),
    _row(
        "research.local-document-fetch",
        "Local and official-document acquisition",
        ["public-validated", "source-available", "acceptance-proven"],
        "ready", "not-required", "not-required",
        "Provide a project-relative local document or accepted offline official snapshot.",
        "Local acquisition is distinct from external discovery.",
        ["src/kodepoia/intelligence/research/documents.py", "src/kodepoia/intelligence/research/service.py"],
        public=True,
        evidence=[_evidence("docs/roadmap/R7_2_ACCEPTANCE.md", "9101e686a32b24bb33a23d7ac578bf25570e115e", "Local/offline official documentation research accepted.")],
    ),
    _row(
        "research.explicit-web-fetch",
        "Guarded explicit-URL Web fetch",
        ["public-validated", "source-available", "acceptance-proven"],
        "network-restricted", "restricted", "not-required",
        "Enable NETWORK for this explicit fetch and provide an HTTP(S) locator.",
        "GET-only governed acquisition for an explicit locator; this is not Web discovery.",
        ["src/kodepoia/intelligence/research/web.py", "src/kodepoia/intelligence/research/service.py"],
        public=True,
        evidence=[_evidence("docs/roadmap/R7_3_ACCEPTANCE.md", "4efd2cb016e774fa3ef06590ffda377606d875e9", "Governed GET-only Web research accepted.")],
    ),
    _row(
        "research.web-discovery",
        "Question-driven general Web discovery",
        ["source-available", "experimental"],
        "network-restricted", "restricted", "required",
        "Enable NETWORK and configure brave/search_api_key to include general Web candidates.",
        "V2.1.2 source code provides Brave Search discovery. Returned rows are descriptor-only candidates and are never fetched evidence.",
        ["src/kodepoia/intelligence/research/discovery.py", "src/kodepoia/kodestudio/research_panel.py"],
    ),
    _row(
        "research.github-known-resource",
        "GitHub known-resource acquisition",
        ["public-validated", "source-available", "acceptance-proven"],
        "network-restricted", "restricted", "optional",
        "Enable NETWORK and provide a structured repository/resource selector.",
        "Read-only typed acquisition for known GitHub resources; distinct from discovery.",
        ["src/kodepoia/intelligence/research/github.py"],
        public=True,
        evidence=[_evidence("docs/roadmap/R7_4_ACCEPTANCE.md", "be6f1d5d2f7d9a16c1c295a51905fcd22e9835be", "Typed read-only GitHub adapter accepted for public unauthenticated behavior.")],
    ),
    _row(
        "research.github-authenticated-resource",
        "Authenticated/private GitHub acquisition",
        ["source-available", "experimental"],
        "auth-required", "restricted", "required",
        "Configure a least-privilege read-only GitHub credential through KodeSecrets and run explicit authenticated acceptance.",
        "Credential plumbing exists, but public rc8 did not prove private/authenticated hosted access.",
        ["src/kodepoia/intelligence/research/github.py"],
    ),
    _row(
        "research.github-discovery",
        "Question-driven GitHub discovery",
        ["source-available", "experimental"],
        "network-restricted", "restricted", "optional",
        "Enable NETWORK to search public repositories; configure github/api_token optionally for a larger authenticated budget.",
        "V2.1.2 uses the official GitHub REST repository search endpoint and emits descriptor-only candidates.",
        ["src/kodepoia/intelligence/research/discovery.py", "src/kodepoia/intelligence/research/github.py"],
    ),
    _row(
        "research.community-normalization",
        "Community-source normalization",
        ["public-validated", "source-available", "acceptance-proven"],
        "ready", "not-required", "not-required",
        "Normalize already acquired community content as untrusted evidence.",
        "Normalization is accepted; question-driven community discovery is not implied.",
        ["src/kodepoia/intelligence/research/community.py"],
        public=True,
        evidence=[_evidence("docs/roadmap/R7_5_ACCEPTANCE.md", "12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5", "Community-source normalization accepted.")],
    ),
    _row(
        "research.youtube-transcript",
        "YouTube metadata/transcript acquisition",
        ["public-validated", "source-available", "acceptance-proven"],
        "network-restricted", "restricted", "not-required",
        "Enable NETWORK and provide an explicit YouTube locator.",
        "Accepted explicit-locator media acquisition; not question-driven YouTube discovery.",
        ["src/kodepoia/intelligence/research/media.py"],
        public=True,
        evidence=[_evidence("docs/roadmap/R7_6_ACCEPTANCE.md", "b623836b8f5bd39fce101eca7fe4653a996a9562", "YouTube metadata/transcript path accepted.")],
    ),
    _row(
        "research.vision-provider",
        "Research vision provider",
        ["public-validated", "source-available", "acceptance-proven", "unavailable"],
        "unavailable", "not-required", "not-required",
        "Keep vision unavailable until a concrete provider is configured and separately accepted.",
        "R7.7 explicitly preserved UNAVAILABLE when no accepted vision provider exists.",
        ["src/kodepoia/intelligence/research/media.py"],
        public=True,
        evidence=[_evidence("docs/roadmap/R7_7_ACCEPTANCE.md", "04cef94c82fdacafe7313d27c8cf516e8e765295", "Fail-closed vision unavailability accepted.")],
    ),
    _row(
        "accelerator.kaggle-t4x2",
        "Kaggle GPU T4 x2",
        ["source-available", "acceptance-proven"],
        "auth-required", "restricted", "required",
        "Authenticate the Kaggle CLI, enable network access, verify quota, then run the governed R15 remote-training flow.",
        "Priority remote accelerator: two separate 16 GiB GPUs, never one 32 GiB pool.",
        ["src/kodepoia/tuning/kaggle_remote.py", "docs/user/KAGGLE_REMOTE_TRAINING.md", ".github/workflows/r15-kaggle-remote-training.yml"],
        accelerator_state="priority",
        evidence=[_evidence(".github/workflows/r15-kaggle-remote-training.yml", "b99c65d5113026d66993ff419bb44dc71923a2ea", "PR #470 exact-head Kaggle acceptance completed/success.")],
    ),
    _row(
        "accelerator.tpu-v5e-8",
        "TPU v5e-8",
        ["experimental", "unavailable"],
        "not-implemented", "restricted", "required",
        "Do not implement XLA unless a benchmark demonstrates a material Kodepoia advantage.",
        "Deferred; no qualified JAX/PyTorch-XLA backend exists.",
        [],
        accelerator_state="deferred",
    ),
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
    brave_authenticated: bool = False,
) -> list[dict[str, Any]]:
    rows = deepcopy(list(_BASELINE))
    by_id = {row["capability_id"]: row for row in rows}

    if allow_network:
        for capability_id in (
            "research.explicit-web-fetch",
            "research.github-known-resource",
            "research.github-discovery",
            "research.youtube-transcript",
        ):
            row = by_id[capability_id]
            row["runtime_state"] = "ready"
            row["network_state"] = "allowed"
        by_id["research.web-discovery"]["network_state"] = "allowed"
        by_id["research.web-discovery"]["runtime_state"] = "ready" if brave_authenticated else "auth-required"
        by_id["research.github-authenticated-resource"]["network_state"] = "allowed"
        by_id["accelerator.kaggle-t4x2"]["network_state"] = "allowed"

    auth_row = by_id["research.github-authenticated-resource"]
    if github_authenticated:
        auth_row["authentication_state"] = "authenticated"
        auth_row["runtime_state"] = "ready" if allow_network else "network-restricted"
    web_row = by_id["research.web-discovery"]
    if brave_authenticated:
        web_row["authentication_state"] = "authenticated"
        if not allow_network:
            web_row["runtime_state"] = "network-restricted"

    _validate(rows)
    return sorted(rows, key=lambda row: row["capability_id"])


def capability_matrix_payload(
    *,
    allow_network: bool = False,
    github_authenticated: bool = False,
    brave_authenticated: bool = False,
) -> dict[str, Any]:
    return {
        "schema": "kodepoia.v2.capability-matrix",
        "schema_version": 1,
        "public_distribution": {"tag": PUBLIC_DISTRIBUTION_TAG, "source_sha": PUBLIC_DISTRIBUTION_SHA},
        "runtime_context": {
            "network_allowed": allow_network,
            "github_authenticated": github_authenticated,
            "brave_authenticated": brave_authenticated,
        },
        "capabilities": build_capability_matrix(
            allow_network=allow_network,
            github_authenticated=github_authenticated,
            brave_authenticated=brave_authenticated,
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
        "capabilities": [{field: row[field] for field in fields} for row in full["capabilities"]],
    }
