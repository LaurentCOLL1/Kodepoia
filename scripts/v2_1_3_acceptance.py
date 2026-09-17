from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFreshness,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.evidence import (
    EvidenceLifecycle,
    EvidenceSelection,
    EvidenceSelectionStore,
    EvidenceWorkspace,
    canonical_source_identity_id,
    canonicalize_evidence_locator,
)
from kodepoia.intelligence.research.service import ResearchOperationStatus, ResearchViewItem
from kodepoia.intelligence.research.store import ResearchStore


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _candidate(locator: str, provider: str) -> ResearchViewItem:
    return ResearchViewItem(
        source_kind="web",
        source_id=_sha(f"{provider}:{locator}"),
        locator=locator,
        status=ResearchOperationStatus.READY,
        freshness="unfetched",
        trust="candidate-only",
        title="candidate",
        reason=f"descriptor_only_not_fetched:{provider}:rank=1",
    )


def _artifact(retrieved_at: str, content: str, version: str) -> ResearchArtifact:
    return ResearchArtifact.from_content(
        source=ResearchSource(
            kind=ResearchSourceKind.WEB,
            locator="https://example.com/docs",
            status=ResearchStatus.READY,
            title="Evidence",
            product="Example",
            version=version,
            updated_at="2026-09-16T00:00:00Z",
        ),
        content=content,
        retrieved_at=retrieved_at,
        freshness=ResearchFreshness.CURRENT,
    )


def _view(artifact: ResearchArtifact) -> ResearchViewItem:
    return ResearchViewItem(
        source_kind=artifact.source.kind.value,
        source_id=artifact.source.source_id,
        locator=artifact.source.locator,
        status=ResearchOperationStatus.READY,
        freshness=artifact.freshness.value,
        trust=artifact.trust.value,
        title=artifact.source.title,
        version=artifact.source.version,
        retrieved_at=artifact.retrieved_at,
        updated_at=artifact.source.updated_at or "",
        artifact_id=artifact.artifact_id,
    )


def _check(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def run(source_sha: str) -> dict[str, object]:
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    checks: list[dict[str, str]] = []
    checks.append(
        _check(
            "exact-head",
            actual == source_sha,
            f"Acceptance checkout is pinned to {source_sha}.",
        )
    )

    left = "HTTPS://Example.COM/docs/?b=2&a=1#fragment"
    right = "https://example.com/docs?a=1&b=2"
    checks.append(
        _check(
            "canonical-source-identity",
            canonicalize_evidence_locator(left) == canonicalize_evidence_locator(right)
            and canonical_source_identity_id(left) == canonical_source_identity_id(right),
            "Equivalent provider locators normalize to one stable canonical source identity.",
        )
    )

    candidates = EvidenceWorkspace.project(
        (_candidate("https://example.com/docs/", "brave-web"), _candidate("https://example.com/docs#top", "github-public"))
    )
    candidate = candidates.rows[0]
    checks.append(
        _check(
            "candidate-boundary",
            len(candidates.rows) == 1
            and candidate.lifecycle is EvidenceLifecycle.CANDIDATE_ONLY
            and candidate.selection is EvidenceSelection.NOT_APPLICABLE
            and not candidate.artifact_id,
            "Duplicate discovery descriptors stay candidate-only and never become fetched evidence.",
        )
    )
    checks.append(
        _check(
            "provider-provenance",
            candidate.provider_ids == ("brave-web", "github-public"),
            "Canonical dedupe retains provider provenance instead of discarding the second provider.",
        )
    )

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / ".kodepoia").mkdir()
        selection_store = EvidenceSelectionStore(root)
        selection_rejected = False
        try:
            selection_store.set("", EvidenceSelection.INCLUDED)
        except ValueError:
            selection_rejected = True
        selection_store.set("a" * 64, EvidenceSelection.EXCLUDED)
        checks.append(
            _check(
                "selection-boundary",
                selection_rejected and selection_store.load().get("a" * 64) is EvidenceSelection.EXCLUDED,
                "Include/exclude is persisted only against fetched artifact IDs.",
            )
        )

        store = ResearchStore(root)
        first_same = _artifact("2026-09-16T10:00:00Z", "same content", "1.0.0")
        second_same = _artifact("2026-09-17T10:00:00Z", "same content", "1.0.0")
        store.save_artifact(first_same)
        store.save_artifact(second_same)
        same_revisions = store.list_evidence_revisions()
        checks.append(
            _check(
                "refetch-lineage",
                first_same.artifact_id == second_same.artifact_id
                and len(same_revisions) == 2
                and same_revisions[0].revision_id != same_revisions[1].revision_id,
                "A refetch with unchanged content creates a distinct inspectable retrieval revision.",
            )
        )

        older = _artifact("2026-09-15T10:00:00Z", "version one", "1.0.0")
        newer = _artifact("2026-09-17T11:00:00Z", "version two", "2.0.0")
        store.save_artifact(older)
        store.save_artifact(newer)
        workspace = EvidenceWorkspace.project(
            (_view(newer),),
            revisions=store.list_evidence_revisions(),
            selections={newer.artifact_id: EvidenceSelection.EXCLUDED},
        )
        fetched = workspace.rows[0]
        checks.append(
            _check(
                "fetched-selection",
                fetched.lifecycle is EvidenceLifecycle.FETCHED
                and fetched.selection is EvidenceSelection.EXCLUDED
                and fetched.artifact_id == newer.artifact_id,
                "Fetched evidence exposes persisted include/exclude state without deleting the artifact.",
            )
        )
        checks.append(
            _check(
                "visible-lineage",
                older.artifact_id in fetched.lineage_artifact_ids
                and newer.artifact_id in fetched.lineage_artifact_ids
                and len(fetched.lineage_revision_ids) >= 2,
                "Fetched rows expose immutable retrieval lineage across refetches.",
            )
        )
        checks.append(
            _check(
                "version-conflict-visibility",
                fetched.has_version_conflict
                and "1.0.0" in fetched.conflicting_versions
                and "2.0.0" in fetched.conflicting_versions,
                "Conflicting source versions remain simultaneously visible instead of being silently collapsed.",
            )
        )

    panel = Path("src/kodepoia/kodestudio/research_panel.py").read_text(encoding="utf-8")
    checks.append(
        _check(
            "ui-evidence-workspace",
            "researchEvidenceIncludeButton" in panel
            and "researchEvidenceExcludeButton" in panel
            and "Canonical locator" in panel
            and "EvidenceWorkspace.project" in panel,
            "KodeStudio exposes lifecycle, canonical locator, lineage and fetched-evidence selection controls.",
        )
    )
    checks.append(
        _check(
            "raw-json-secondary",
            panel.index("researchResultsTable") < panel.index("researchDetails"),
            "Structured evidence rows precede raw technical JSON details in the Research page.",
        )
    )
    authority = Path("docs/roadmap/V2_1_RESEARCH_WORKSPACE.md").read_text(encoding="utf-8")
    checks.append(
        _check(
            "workspace-scope",
            "V2.1.3" in authority and "CURRENT" in authority and "V2.1.4" in authority,
            "Authority keeps V2.1.3 current and cited-answer synthesis deferred to V2.1.4.",
        )
    )

    failed = [item["name"] for item in checks if item["status"] != "PASS"]
    return {
        "schema": "kodepoia.v2.1.3.acceptance",
        "schema_version": 1,
        "source_sha": source_sha,
        "status": "PASS" if not failed else "FAIL",
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = run(args.source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
