from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from kodepoia.tuning.r15_ux import (
    R15UXService,
    R15WorkflowMode,
    R15WorkflowRequest,
)

CURATION_SCHEMA = "kodepoia.v2.3.2.model-lab-curation"
_MAX_JSON_BYTES = 4 * 1024 * 1024
_MAX_JSON_FILES = 512
_AUTHORIZATION_FIELDS = ("source_scope", "consent", "provenance", "license", "privacy")
_TERMINAL_BLOCKED_STATES = {"rejected", "quarantined", "revoked", "expired"}
_DATASET_SCHEMA = "kodepoia.experience.dataset-manifest"
_DATASET_CARD_SCHEMA = "kodepoia.experience.dataset-card"
_CAPTURE_SCHEMA = "kodepoia.experience.capture"
_RECORD_SCHEMA = "kodepoia.experience.record"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        return "<external-path>"


def _bounded_json(path: Path) -> tuple[dict[str, object] | None, str, int | None]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        return None, f"unavailable:{exc}", None
    if size > _MAX_JSON_BYTES:
        return None, "oversized", size
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"invalid:{exc}", size
    if not isinstance(payload, dict):
        return None, "invalid:root_not_object", size
    return payload, "ready", size


def _auth_blockers(record: Mapping[str, object]) -> list[str]:
    authorization = record.get("authorization")
    if not isinstance(authorization, Mapping):
        return ["authorization:missing"]
    blockers: list[str] = []
    for field in _AUTHORIZATION_FIELDS:
        value = str(authorization.get(field, "unknown")).strip().lower()
        if value != "allow":
            blockers.append(f"authorization:{field}:{value or 'unknown'}")
    return blockers


def _experience_blockers(
    record: Mapping[str, object],
    *,
    integrity: str,
) -> tuple[list[str], list[str]]:
    common: list[str] = []
    if integrity != "ready":
        common.append(f"integrity:{integrity}")
    state = str(record.get("state", "unknown")).strip().lower()
    if state in _TERMINAL_BLOCKED_STATES:
        common.append(f"state:{state}")
    common.extend(_auth_blockers(record))

    provenance = record.get("provenance")
    license_expression = (
        provenance.get("license_expression")
        if isinstance(provenance, Mapping)
        else None
    )
    if not isinstance(license_expression, str) or not license_expression.strip():
        common.append("license:missing")

    if bool(record.get("benchmark_protected")):
        common.append("benchmark_protected")

    sanitization = record.get("sanitization")
    sanitization_status = (
        str(sanitization.get("status", "not_run")).strip().lower()
        if isinstance(sanitization, Mapping)
        else "missing"
    )

    curation = list(common)
    if state != "sanitized":
        curation.append(f"curation_state:{state or 'unknown'}")
    if sanitization_status != "passed":
        curation.append(f"sanitization:{sanitization_status}")

    dataset = list(common)
    if state != "curated":
        dataset.append(f"dataset_state:{state or 'unknown'}")
    if sanitization_status != "passed":
        dataset.append(f"sanitization:{sanitization_status}")

    return sorted(set(curation)), sorted(set(dataset))


def _experience_summary(
    record: Mapping[str, object],
    *,
    path: str,
    expected_digest: str | None,
) -> dict[str, object]:
    observed_digest = _sha256_json(record)
    integrity = "ready"
    if expected_digest is None:
        integrity = "unverified"
    elif expected_digest != observed_digest:
        integrity = "tampered"

    provenance = record.get("provenance")
    provenance_map = provenance if isinstance(provenance, Mapping) else {}
    authorization = record.get("authorization")
    authorization_map = authorization if isinstance(authorization, Mapping) else {}
    sanitization = record.get("sanitization")
    sanitization_map = sanitization if isinstance(sanitization, Mapping) else {}
    content = record.get("content")
    content_map = content if isinstance(content, Mapping) else {}

    curation_blockers, dataset_blockers = _experience_blockers(
        record,
        integrity=integrity,
    )
    return {
        "experience_id": str(record.get("experience_id", "")),
        "workspace_id": str(record.get("workspace_id", "")),
        "project_id": str(record.get("project_id", "")),
        "task": str(record.get("task_label", "")),
        "domain": str(record.get("domain_label", "")),
        "state": str(record.get("state", "unknown")),
        "outcome": str(record.get("outcome", "unknown")),
        "source_type": str(provenance_map.get("source_type", "")),
        "source_id": str(provenance_map.get("source_id", "")),
        "origin_digest": str(provenance_map.get("origin_digest", "")),
        "project_scope": str(provenance_map.get("project_scope", "")),
        "license_expression": provenance_map.get("license_expression"),
        "authorization": {
            field: str(authorization_map.get(field, "unknown"))
            for field in _AUTHORIZATION_FIELDS
        },
        "sanitization": {
            "status": str(sanitization_map.get("status", "not_run")),
            "categories": [
                str(item)
                for item in sanitization_map.get("categories", [])
                if isinstance(item, str)
            ],
            "finding_count": int(sanitization_map.get("finding_count", 0) or 0),
            "sanitizer_digest": sanitization_map.get("sanitizer_digest"),
        },
        "benchmark_protected": bool(record.get("benchmark_protected")),
        "content": {
            "sha256": content_map.get("sha256"),
            "byte_length": content_map.get("byte_length"),
            "media_type": content_map.get("media_type"),
            "payload_read": False,
        },
        "record_digest": observed_digest,
        "expected_record_digest": expected_digest,
        "integrity": integrity,
        "curation_ready": not curation_blockers,
        "curation_blockers": curation_blockers,
        "dataset_eligible": not dataset_blockers,
        "dataset_blockers": dataset_blockers,
        "path": path,
    }


def _dataset_summary(payload: Mapping[str, object], *, path: str) -> dict[str, object]:
    core = {
        "dedup_policy_digest": payload.get("dedup_policy_digest"),
        "entries": payload.get("entries", []),
        "export_digests": payload.get("export_digests", {}),
        "policy": payload.get("policy", {}),
        "policy_digest": payload.get("policy_digest"),
        "representation_version": payload.get("representation_version"),
        "selection_summary": payload.get("selection_summary", {}),
        "split_stats": payload.get("split_stats", {}),
    }
    expected = str(payload.get("dataset_digest", ""))
    observed = _sha256_json(core)
    dataset_id = str(payload.get("dataset_id", ""))
    integrity = (
        "ready"
        if expected == observed and dataset_id == f"ds_{expected}"
        else "tampered"
    )

    entries = payload.get("entries")
    entries_list = entries if isinstance(entries, list) else []
    licenses = sorted(
        {
            str(entry.get("license_expression"))
            for entry in entries_list
            if isinstance(entry, Mapping)
            and isinstance(entry.get("license_expression"), str)
            and str(entry.get("license_expression")).strip()
        }
    )
    domains = sorted(
        {
            str(entry.get("domain"))
            for entry in entries_list
            if isinstance(entry, Mapping) and str(entry.get("domain", "")).strip()
        }
    )
    tasks = sorted(
        {
            str(entry.get("task"))
            for entry in entries_list
            if isinstance(entry, Mapping) and str(entry.get("task", "")).strip()
        }
    )
    selection = payload.get("selection_summary")
    selection_map = selection if isinstance(selection, Mapping) else {}
    split_stats = payload.get("split_stats")
    split_map = split_stats if isinstance(split_stats, Mapping) else {}
    export_digests = payload.get("export_digests")
    export_map = export_digests if isinstance(export_digests, Mapping) else {}

    return {
        "dataset_id": dataset_id,
        "dataset_digest": expected,
        "observed_dataset_digest": observed,
        "policy_digest": payload.get("policy_digest"),
        "dedup_policy_digest": payload.get("dedup_policy_digest"),
        "integrity": integrity,
        "rows": len(entries_list),
        "selected_records": selection_map.get("selected_records"),
        "selected_groups": selection_map.get("selected_groups"),
        "excluded_by_reason": dict(selection_map.get("excluded_by_reason", {}))
        if isinstance(selection_map.get("excluded_by_reason"), Mapping)
        else {},
        "split_stats": {
            str(key): dict(value) if isinstance(value, Mapping) else {}
            for key, value in sorted(split_map.items(), key=lambda item: str(item[0]))
        },
        "export_digests": {
            str(key): str(value)
            for key, value in sorted(export_map.items(), key=lambda item: str(item[0]))
        },
        "licenses": licenses,
        "domains": domains,
        "tasks": tasks,
        "path": path,
        "payload_rows_read": False,
    }


class ModelLabCurationService:
    """Structured V2.3.2 facade over accepted R15 experience/dataset contracts.

    Snapshot inspection never reads raw experience payloads or dataset JSONL rows.
    Curation and dataset-build mutations are delegated exclusively to R15UXService.
    """

    schema = CURATION_SCHEMA

    def __init__(
        self,
        project_root: Path,
        *,
        r15_service: R15UXService | None = None,
    ) -> None:
        self.root = Path(project_root).resolve(strict=False)
        self.r15 = r15_service or R15UXService.for_project(self.root)
        if self.r15.root != self.root:
            raise ValueError("R15 UX service project root does not match curation project root")

    @classmethod
    def for_project(cls, project_root: Path) -> "ModelLabCurationService":
        return cls(project_root)

    def _experience_evidence(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        root = self.root / ".kodepoia" / "experience"
        if not root.is_dir():
            return [], []
        experiences: list[dict[str, object]] = []
        reports: list[dict[str, object]] = []
        files = sorted(
            (path for path in root.rglob("*.json") if path.is_file()),
            key=lambda path: path.as_posix(),
        )[:_MAX_JSON_FILES]
        for path in files:
            payload, read_state, _size = _bounded_json(path)
            relative = _relative(self.root, path)
            if payload is None:
                reports.append(
                    {
                        "kind": "invalid_json",
                        "path": relative,
                        "state": read_state,
                    }
                )
                continue
            schema = str(payload.get("schema", ""))
            if schema == _CAPTURE_SCHEMA:
                record = payload.get("record")
                if isinstance(record, Mapping):
                    experiences.append(
                        _experience_summary(
                            record,
                            path=relative,
                            expected_digest=(
                                str(payload.get("record_digest"))
                                if isinstance(payload.get("record_digest"), str)
                                else None
                            ),
                        )
                    )
                continue
            if schema == _RECORD_SCHEMA:
                experiences.append(
                    _experience_summary(
                        payload,
                        path=relative,
                        expected_digest=None,
                    )
                )
                continue
            if {
                "policy_digest",
                "quarantined_item_ids",
                "contaminated_group_ids",
                "findings",
            } <= set(payload):
                raw_findings = payload.get("findings")
                findings = raw_findings if isinstance(raw_findings, list) else []
                safe_findings: list[dict[str, object]] = []
                for finding in findings:
                    if not isinstance(finding, Mapping):
                        continue
                    safe_findings.append(
                        {
                            "item_id": str(finding.get("item_id", "")),
                            "holdout_id": str(finding.get("holdout_id", "")),
                            "group_id": str(finding.get("group_id", "")),
                            "match_type": str(finding.get("match_type", "")),
                            "similarity": finding.get("similarity"),
                            "threshold": finding.get("threshold"),
                            "review_required": bool(finding.get("review_required")),
                        }
                    )
                reports.append(
                    {
                        "kind": "contamination",
                        "path": relative,
                        "state": "ready",
                        "policy_digest": payload.get("policy_digest"),
                        "finding_count": len(safe_findings),
                        "findings": safe_findings,
                        "match_types": sorted(
                            {
                                str(item.get("match_type"))
                                for item in safe_findings
                                if str(item.get("match_type", "")).strip()
                            }
                        ),
                        "quarantined_item_ids": [
                            str(item)
                            for item in payload.get("quarantined_item_ids", [])
                            if isinstance(item, str)
                        ],
                        "contaminated_group_ids": [
                            str(item)
                            for item in payload.get("contaminated_group_ids", [])
                            if isinstance(item, str)
                        ],
                    }
                )
                continue
            if {"policy_digest", "clusters"} <= set(payload):
                raw_clusters = payload.get("clusters")
                clusters = raw_clusters if isinstance(raw_clusters, list) else []
                safe_clusters: list[dict[str, object]] = []
                for cluster in clusters:
                    if not isinstance(cluster, Mapping):
                        continue
                    safe_clusters.append(
                        {
                            "group_id": str(cluster.get("group_id", "")),
                            "member_ids": [
                                str(item)
                                for item in cluster.get("member_ids", [])
                                if isinstance(item, str)
                            ],
                            "representative_id": str(
                                cluster.get("representative_id", "")
                            ),
                        }
                    )
                reports.append(
                    {
                        "kind": "dedup",
                        "path": relative,
                        "state": "ready",
                        "policy_digest": payload.get("policy_digest"),
                        "cluster_count": len(safe_clusters),
                        "clusters": safe_clusters,
                        "member_count": sum(
                            len(item["member_ids"]) for item in safe_clusters
                        ),
                    }
                )
        return experiences, reports

    def _dataset_evidence(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        root = self.root / ".kodepoia" / "datasets"
        if not root.is_dir():
            return [], []
        datasets: list[dict[str, object]] = []
        cards: list[dict[str, object]] = []
        files = sorted(
            (path for path in root.rglob("*.json") if path.is_file()),
            key=lambda path: path.as_posix(),
        )[:_MAX_JSON_FILES]
        for path in files:
            payload, read_state, _size = _bounded_json(path)
            relative = _relative(self.root, path)
            if payload is None:
                cards.append(
                    {
                        "kind": "invalid_json",
                        "path": relative,
                        "state": read_state,
                    }
                )
                continue
            schema = str(payload.get("schema", ""))
            if schema == _DATASET_SCHEMA:
                datasets.append(_dataset_summary(payload, path=relative))
            elif schema == _DATASET_CARD_SCHEMA:
                cards.append(
                    {
                        "kind": "dataset_card",
                        "dataset_id": str(payload.get("dataset_id", "")),
                        "dataset_digest": str(payload.get("dataset_digest", "")),
                        "policy_digest": str(payload.get("policy_digest", "")),
                        "licenses": [
                            str(item)
                            for item in payload.get("licenses", [])
                            if isinstance(item, str)
                        ],
                        "domains": [
                            str(item)
                            for item in payload.get("domains", [])
                            if isinstance(item, str)
                        ],
                        "tasks": [
                            str(item)
                            for item in payload.get("tasks", [])
                            if isinstance(item, str)
                        ],
                        "split_stats": payload.get("split_stats", {}),
                        "path": relative,
                        "state": "ready",
                    }
                )
        return datasets, cards

    def snapshot(self) -> dict[str, object]:
        experiences, reports = self._experience_evidence()
        datasets, cards = self._dataset_evidence()

        latest_by_id: dict[str, dict[str, object]] = {}
        state_rank = {
            "observed": 0,
            "eligible": 1,
            "sanitized": 2,
            "curated": 3,
            "dataset_included": 4,
            "rejected": 5,
            "quarantined": 5,
            "revoked": 6,
            "expired": 6,
        }
        for item in experiences:
            experience_id = str(item.get("experience_id", ""))
            if not experience_id:
                continue
            previous = latest_by_id.get(experience_id)
            if previous is None or state_rank.get(str(item.get("state", "")), -1) >= state_rank.get(
                str(previous.get("state", "")),
                -1,
            ):
                latest_by_id[experience_id] = item

        latest = sorted(
            latest_by_id.values(),
            key=lambda item: (
                str(item.get("project_id", "")),
                str(item.get("experience_id", "")),
            ),
        )
        contamination = [item for item in reports if item.get("kind") == "contamination"]
        quarantined_ids = {
            item_id
            for report in contamination
            for item_id in report.get("quarantined_item_ids", [])
            if isinstance(item_id, str)
        }
        for item in latest:
            if str(item.get("experience_id")) in quarantined_ids:
                blockers = set(item.get("dataset_blockers", []))
                blockers.add("benchmark_contamination")
                item["dataset_blockers"] = sorted(blockers)
                item["dataset_eligible"] = False

        handlers = set(self.r15.handlers)
        return {
            "schema": self.schema,
            "status": "ok",
            "project_root": ".",
            "raw_payloads_exposed": False,
            "project_knowledge_auto_ingest": False,
            "experiences": latest,
            "experience_revision_count": len(experiences),
            "dedup_and_contamination": reports,
            "datasets": sorted(
                datasets,
                key=lambda item: str(item.get("dataset_id", "")),
            ),
            "dataset_cards": sorted(
                cards,
                key=lambda item: (
                    str(item.get("dataset_id", "")),
                    str(item.get("path", "")),
                ),
            ),
            "summary": {
                "experience_count": len(latest),
                "curation_ready": sum(bool(item.get("curation_ready")) for item in latest),
                "dataset_eligible": sum(bool(item.get("dataset_eligible")) for item in latest),
                "quarantined_or_revoked": sum(
                    str(item.get("state", "")) in {"quarantined", "revoked"}
                    for item in latest
                ),
                "dataset_count": len(datasets),
            },
            "actions": {
                "experience_curate": {
                    "available": "experience.curate" in handlers,
                    "typed_backend": "experience.curate",
                    "dry_run_required_before_ui_apply": True,
                    "confirmation_required": True,
                },
                "dataset_build": {
                    "available": "dataset.build" in handlers,
                    "typed_backend": "dataset.build",
                    "dry_run_required_before_ui_apply": True,
                    "confirmation_required": True,
                },
                "training": False,
                "conversion": False,
                "promotion": False,
                "rollback": False,
            },
        }

    def preview_curation(self, experience_id: str) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="experience",
                action="curate",
                mode=R15WorkflowMode.DRY_RUN,
                identifier=experience_id,
            )
        )

    def apply_curation(
        self,
        experience_id: str,
        *,
        confirmed: bool,
    ) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="experience",
                action="curate",
                mode=R15WorkflowMode.APPLY,
                identifier=experience_id,
                confirmed=confirmed,
            )
        )

    def dataset_preview_summary(
        self,
        snapshot: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        current = dict(snapshot or self.snapshot())
        experiences = current.get("experiences")
        records = experiences if isinstance(experiences, list) else []
        eligible = [
            item
            for item in records
            if isinstance(item, Mapping) and bool(item.get("dataset_eligible"))
        ]

        exclusions: dict[str, int] = {}
        for item in records:
            if not isinstance(item, Mapping) or bool(item.get("dataset_eligible")):
                continue
            blockers = item.get("dataset_blockers")
            for blocker in blockers if isinstance(blockers, list) else []:
                key = str(blocker)
                exclusions[key] = exclusions.get(key, 0) + 1

        def counts(field: str) -> dict[str, int]:
            result: dict[str, int] = {}
            for item in eligible:
                value = item.get(field)
                if value is None or not str(value).strip():
                    continue
                key = str(value)
                result[key] = result.get(key, 0) + 1
            return dict(sorted(result.items()))

        latest_policy: Mapping[str, object] | None = None
        datasets = current.get("datasets")
        dataset_list = datasets if isinstance(datasets, list) else []
        if dataset_list:
            latest = dataset_list[-1]
            path = self.root / str(latest.get("path", ""))
            payload, state, _size = _bounded_json(path)
            if state == "ready" and isinstance(payload, Mapping):
                policy = payload.get("policy")
                if isinstance(policy, Mapping):
                    latest_policy = policy

        split_summary: dict[str, object]
        if latest_policy is None:
            split_summary = {
                "state": "policy_unavailable",
                "detail": (
                    "split assignment remains authoritative in the configured "
                    "R15 dataset-build backend"
                ),
            }
        else:
            split_summary = {
                "state": "reference_policy_available",
                "train_weight": latest_policy.get("train_weight"),
                "validation_weight": latest_policy.get("validation_weight"),
                "test_weight": latest_policy.get("test_weight"),
                "policy_version": latest_policy.get("version"),
                "detail": (
                    "reference weights are shown for explainability; the build "
                    "backend remains authoritative"
                ),
            }

        return {
            "candidate_rows": len(eligible),
            "excluded_rows": max(0, len(records) - len(eligible)),
            "excluded_by_reason": dict(sorted(exclusions.items())),
            "licenses": counts("license_expression"),
            "domains": counts("domain"),
            "tasks": counts("task"),
            "split_summary": split_summary,
            "raw_payloads_read": False,
        }

    def preview_dataset_build(self) -> dict[str, object]:
        dry_run = self.r15.execute(
            R15WorkflowRequest(
                domain="dataset",
                action="build",
                mode=R15WorkflowMode.DRY_RUN,
            )
        )
        return {
            **dry_run,
            "preview": self.dataset_preview_summary(),
        }

    def apply_dataset_build(self, *, confirmed: bool) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="dataset",
                action="build",
                mode=R15WorkflowMode.APPLY,
                confirmed=confirmed,
            )
        )

    def inspect_dataset(self, dataset_id: str) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="dataset",
                action="inspect",
                mode=R15WorkflowMode.INSPECT,
                identifier=dataset_id,
            )
        )


__all__ = ["CURATION_SCHEMA", "ModelLabCurationService"]
