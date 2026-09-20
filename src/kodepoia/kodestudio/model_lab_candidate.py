from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from kodepoia.kodestudio.model_lab import ModelLabInventoryService
from kodepoia.tuning.r15_ux import R15UXService, R15WorkflowMode, R15WorkflowRequest

CANDIDATE_WORKSPACE_SCHEMA = "kodepoia.v2.3.5.model-lab-candidate-lifecycle"
_EVALUATION_SCHEMA = "kodepoia.r15.10.candidate-evaluation"
_EXPORT_SCHEMA = "kodepoia.r15.11.model-export"
_GGUF_SCHEMA = "kodepoia.r15.12.gguf-conversion"
_OLLAMA_SCHEMA = "kodepoia.r15.13.ollama-package"
_MAX_JSON_BYTES = 4 * 1024 * 1024
_MAX_JSON_FILES = 512
_EVIDENCE_ROOTS = (".kodepoia/benchmarks", ".kodepoia/tuning")


class CandidateLifecycleUXError(RuntimeError):
    """Raised when V2.3.5 cannot prove a governed candidate transition."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _digest_ready(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        return "<external-path>"


def _bounded_json(path: Path) -> tuple[dict[str, object] | None, str]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        return None, f"unavailable:{type(exc).__name__}"
    if size > _MAX_JSON_BYTES:
        return None, "oversized"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"invalid:{type(exc).__name__}"
    if not isinstance(value, dict):
        return None, "invalid:root_not_object"
    return value, "ready"


def _integrity(payload: Mapping[str, object], digest_key: str) -> tuple[str, str]:
    descriptor = dict(payload)
    claimed = descriptor.pop(digest_key, None)
    observed = _sha256_json(descriptor)
    if claimed == observed and _digest_ready(claimed):
        return "ready", observed
    return "tampered", observed


class ModelLabCandidateLifecycleService:
    """V2.3.5 projection and guarded actions over accepted R15.10-R15.14 contracts."""

    schema = CANDIDATE_WORKSPACE_SCHEMA

    def __init__(
        self,
        project_root: Path,
        *,
        r15_service: R15UXService | None = None,
    ) -> None:
        self.root = Path(project_root).resolve(strict=False)
        self.r15 = r15_service or R15UXService.for_project(self.root)
        if self.r15.root != self.root:
            raise ValueError(
                "R15 UX service project root does not match Candidate lifecycle workspace project root"
            )

    @classmethod
    def for_project(cls, project_root: Path) -> "ModelLabCandidateLifecycleService":
        return cls(project_root)

    def _files(self) -> list[Path]:
        files: list[Path] = []
        remaining = _MAX_JSON_FILES
        for relative_root in _EVIDENCE_ROOTS:
            root = self.root / relative_root
            if not root.is_dir() or remaining <= 0:
                continue
            found = sorted(
                (path for path in root.rglob("*.json") if path.is_file()),
                key=lambda path: path.as_posix(),
            )[:remaining]
            files.extend(found)
            remaining -= len(found)
        return files

    @staticmethod
    def _evaluation(payload: Mapping[str, object], path: str) -> dict[str, object]:
        binding = _mapping(payload.get("binding"))
        aggregate = _mapping(payload.get("aggregate"))
        integrity, observed = _integrity(payload, "evaluation_digest")
        return {
            "candidate_id": str(binding.get("candidate_id", "")),
            "candidate_model_ref": str(binding.get("candidate_model_ref", "")),
            "candidate_model_digest": binding.get("candidate_model_digest"),
            "base_model_ref": str(binding.get("base_model_ref", "")),
            "base_model_digest": binding.get("base_model_digest"),
            "adapter_digest": binding.get("adapter_digest"),
            "training_plan_digest": binding.get("training_plan_digest"),
            "dataset_digest": binding.get("dataset_digest"),
            "evaluation_digest": payload.get("evaluation_digest"),
            "observed_evaluation_digest": observed,
            "integrity": integrity,
            "disposition": str(payload.get("disposition", "unknown")),
            "can_export": payload.get("can_export") is True,
            "suite_digest": payload.get("suite_digest"),
            "config_digest": payload.get("config_digest"),
            "protection_manifest_digest": payload.get("protection_manifest_digest"),
            "aggregate": dict(aggregate),
            "task_deltas": dict(_mapping(payload.get("task_deltas"))),
            "domain_deltas": dict(_mapping(payload.get("domain_deltas"))),
            "critical_regressions": [str(item) for item in _list(payload.get("critical_regressions"))],
            "reasons": [str(item) for item in _list(payload.get("reasons"))],
            "training_loss": dict(_mapping(payload.get("training_loss"))),
            "resources": dict(_mapping(payload.get("resources"))),
            "overfit_risk": payload.get("overfit_risk") is True,
            "path": path,
        }

    @staticmethod
    def _export(payload: Mapping[str, object], path: str) -> dict[str, object]:
        binding = _mapping(payload.get("binding"))
        integrity, observed = _integrity(payload, "manifest_digest")
        adapter = _mapping(payload.get("adapter"))
        merge = _mapping(payload.get("merge"))
        return {
            "candidate_id": str(binding.get("candidate_id", "")),
            "evaluation_digest": binding.get("evaluation_digest"),
            "training_plan_digest": binding.get("training_plan_digest"),
            "dataset_digest": binding.get("dataset_digest"),
            "adapter_digest": binding.get("adapter_digest"),
            "base_model_ref": binding.get("base_model_ref"),
            "base_model_digest": binding.get("base_model_digest"),
            "manifest_digest": payload.get("manifest_digest"),
            "observed_manifest_digest": observed,
            "integrity": integrity,
            "adapter_tree_digest": adapter.get("tree_digest"),
            "adapter_files": list(_list(adapter.get("files"))),
            "merge_disposition": str(merge.get("disposition", "unknown")),
            "merged_files": list(_list(merge.get("files"))),
            "source_overwritten": payload.get("source_overwritten"),
            "path": path,
        }

    @staticmethod
    def _conversion(payload: Mapping[str, object], path: str) -> dict[str, object]:
        binding = _mapping(payload.get("binding"))
        integrity, observed = _integrity(payload, "report_digest")
        variants: list[dict[str, object]] = []
        for raw in _list(payload.get("variants")):
            if not isinstance(raw, Mapping):
                continue
            artifact = _mapping(raw.get("artifact"))
            output = _mapping(artifact.get("output"))
            quality = _mapping(raw.get("quality"))
            variants.append(
                {
                    "quant_type": artifact.get("quant_type"),
                    "artifact_sha256": output.get("sha256"),
                    "size_bytes": output.get("size_bytes"),
                    "quality": str(quality.get("disposition", "unknown")),
                    "aggregate_loss": quality.get("aggregate_loss"),
                    "critical_regressions": [
                        str(item) for item in _list(quality.get("critical_regressions"))
                    ],
                }
            )
        variants.sort(key=lambda item: str(item.get("quant_type")))
        return {
            "candidate_id": str(binding.get("candidate_id", "")),
            "evaluation_digest": binding.get("evaluation_digest"),
            "export_manifest_digest": binding.get("export_manifest_digest"),
            "source_digest": binding.get("source_digest"),
            "source_kind": binding.get("source_kind"),
            "source_precision": binding.get("source_precision"),
            "report_digest": payload.get("report_digest"),
            "observed_report_digest": observed,
            "integrity": integrity,
            "high_precision": dict(_mapping(payload.get("high_precision"))),
            "variants": variants,
            "accepted_variants": sum(item.get("quality") == "accept" for item in variants),
            "path": path,
        }

    @staticmethod
    def _package(payload: Mapping[str, object], path: str) -> dict[str, object]:
        binding = _mapping(payload.get("binding"))
        quality = _mapping(payload.get("quality"))
        integrity, observed = _integrity(payload, "report_digest")
        return {
            "candidate_id": str(binding.get("candidate_id", "")),
            "artifact_kind": binding.get("artifact_kind"),
            "artifact_sha256": binding.get("artifact_sha256"),
            "evaluation_digest": binding.get("evaluation_digest"),
            "export_manifest_digest": binding.get("export_manifest_digest"),
            "gguf_report_digest": binding.get("gguf_report_digest"),
            "report_digest": payload.get("report_digest"),
            "observed_report_digest": observed,
            "integrity": integrity,
            "candidate_tag": payload.get("candidate_tag"),
            "model_digest": payload.get("model_digest"),
            "ollama_version": payload.get("ollama_version"),
            "quality": str(quality.get("disposition", "unknown")),
            "aggregate_loss": quality.get("aggregate_loss"),
            "critical_regressions": [
                str(item) for item in _list(quality.get("critical_regressions"))
            ],
            "behavior": dict(_mapping(payload.get("behavior"))),
            "provider_live_claim": payload.get("provider_live_claim"),
            "public_push": payload.get("public_push"),
            "path": path,
        }

    def _evidence(self) -> tuple[
        list[dict[str, object]],
        list[dict[str, object]],
        list[dict[str, object]],
        list[dict[str, object]],
        list[dict[str, object]],
    ]:
        evaluations: list[dict[str, object]] = []
        exports: list[dict[str, object]] = []
        conversions: list[dict[str, object]] = []
        packages: list[dict[str, object]] = []
        invalid: list[dict[str, object]] = []
        for path in self._files():
            payload, state = _bounded_json(path)
            relative = _relative(self.root, path)
            if payload is None:
                invalid.append({"path": relative, "state": state})
                continue
            schema = payload.get("schema")
            if schema == _EVALUATION_SCHEMA:
                evaluations.append(self._evaluation(payload, relative))
            elif schema == _EXPORT_SCHEMA:
                exports.append(self._export(payload, relative))
            elif schema == _GGUF_SCHEMA:
                conversions.append(self._conversion(payload, relative))
            elif schema == _OLLAMA_SCHEMA:
                packages.append(self._package(payload, relative))
        key_map = (
            (evaluations, "evaluation_digest"),
            (exports, "manifest_digest"),
            (conversions, "report_digest"),
            (packages, "report_digest"),
        )
        for rows, key in key_map:
            rows.sort(key=lambda item: (str(item.get("candidate_id")), str(item.get(key))))
        invalid.sort(key=lambda item: str(item.get("path")))
        return evaluations, exports, conversions, packages, invalid

    def _action_state(self, domain: str, action: str) -> dict[str, object]:
        spec = self.r15.action(domain, action)
        return {
            "workflow": spec.key,
            "mutation": spec.mutation,
            "available": spec.key in self.r15.handlers,
            "terminal_mode": spec.terminal_mode.value,
            "identifier_required": spec.identifier_required,
        }

    def snapshot(self) -> dict[str, object]:
        evaluations, exports, conversions, packages, invalid = self._evidence()
        registry = ModelLabInventoryService(self.root).snapshot()["registry"]
        candidate_ids = sorted(
            {
                str(item.get("candidate_id"))
                for rows in (evaluations, exports, conversions, packages)
                for item in rows
                if str(item.get("candidate_id", "")).strip()
            }
            | {
                str(item.get("candidate_id"))
                for item in _list(_mapping(registry).get("records"))
                if isinstance(item, Mapping) and str(item.get("candidate_id", "")).strip()
            }
        )
        candidates: list[dict[str, object]] = []
        for candidate_id in candidate_ids:
            candidate_evaluations = [
                item for item in evaluations if item.get("candidate_id") == candidate_id
            ]
            candidate_exports = [item for item in exports if item.get("candidate_id") == candidate_id]
            candidate_conversions = [
                item for item in conversions if item.get("candidate_id") == candidate_id
            ]
            candidate_packages = [
                item for item in packages if item.get("candidate_id") == candidate_id
            ]
            dispositions = sorted(
                {
                    str(item.get("disposition"))
                    for item in candidate_evaluations
                    if item.get("integrity") == "ready"
                }
            )
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "evaluation_dispositions": dispositions,
                    "evaluation_count": len(candidate_evaluations),
                    "export_count": len(candidate_exports),
                    "conversion_count": len(candidate_conversions),
                    "package_count": len(candidate_packages),
                    "critical_regression": any(
                        bool(item.get("critical_regressions")) for item in candidate_evaluations
                    ),
                    "promotable_evaluation": any(
                        item.get("integrity") == "ready"
                        and item.get("disposition") == "promote_to_export"
                        and item.get("can_export") is True
                        for item in candidate_evaluations
                    ),
                    "accepted_package": any(
                        item.get("integrity") == "ready" and item.get("quality") == "accept"
                        for item in candidate_packages
                    ),
                }
            )
        return {
            "schema": self.schema,
            "status": "ok",
            "project_root": ".",
            "candidates": candidates,
            "evaluations": evaluations,
            "exports": exports,
            "conversions": conversions,
            "packages": packages,
            "registry": registry,
            "invalid_evidence": invalid,
            "actions": {
                "compare": self._action_state("bench", "compare"),
                "export_status": self._action_state("export", "status"),
                "export_run": self._action_state("export", "run"),
                "conversion_status": self._action_state("conversion", "status"),
                "conversion_run": self._action_state("conversion", "run"),
                "ollama_status": self._action_state("ollama", "status"),
                "ollama_package": self._action_state("ollama", "package"),
                "registry_candidates": self._action_state("registry", "candidates"),
                "registry_promote": self._action_state("registry", "promote"),
                "registry_rollback": self._action_state("registry", "rollback"),
            },
            "reference_context": {
                "state": "data_only",
                "project_knowledge": "reference_only",
                "research_packs": "reference_only",
                "retrieved_context": "reference_only",
                "instruction_authority": False,
                "promotion_authority": False,
                "registry_instruction_authority": False,
            },
            "boundaries": {
                "public_model_upload": False,
                "arbitrary_shell": False,
                "arbitrary_argv": False,
                "arbitrary_environment": False,
                "package_install": False,
                "silent_model_replacement": False,
                "silent_tokenizer_replacement": False,
                "silent_routing_replacement": False,
                "v2_3_6": False,
            },
        }

    @staticmethod
    def _single(
        rows: list[dict[str, object]],
        *,
        label: str,
        candidate_id: str,
    ) -> dict[str, object]:
        matched = [
            item
            for item in rows
            if item.get("candidate_id") == candidate_id and item.get("integrity") == "ready"
        ]
        if len(matched) != 1:
            raise CandidateLifecycleUXError(
                f"{label} requires exactly one integrity-ready evidence item for candidate"
            )
        return matched[0]

    def _chain(
        self,
        candidate_id: str,
        *,
        require_export: bool = False,
        require_conversion: bool = False,
        require_package: bool = False,
    ) -> dict[str, dict[str, object]]:
        snapshot = self.snapshot()
        evaluation = self._single(
            snapshot["evaluations"], label="candidate evaluation", candidate_id=candidate_id
        )
        if evaluation.get("disposition") != "promote_to_export" or evaluation.get("can_export") is not True:
            raise CandidateLifecycleUXError(
                "candidate evaluation is not PROMOTE_TO_EXPORT; export and promotion remain blocked"
            )
        if evaluation.get("critical_regressions"):
            raise CandidateLifecycleUXError("critical-regression veto blocks candidate lifecycle mutation")
        result = {"evaluation": evaluation}
        if not require_export:
            return result
        export = self._single(snapshot["exports"], label="model export", candidate_id=candidate_id)
        if export.get("evaluation_digest") != evaluation.get("evaluation_digest"):
            raise CandidateLifecycleUXError("export evaluation lineage does not match accepted evaluation")
        if export.get("source_overwritten") is not False:
            raise CandidateLifecycleUXError("export source immutability evidence is invalid")
        result["export"] = export
        if not require_conversion:
            return result
        conversion = self._single(
            snapshot["conversions"], label="GGUF conversion", candidate_id=candidate_id
        )
        if (
            conversion.get("evaluation_digest") != evaluation.get("evaluation_digest")
            or conversion.get("export_manifest_digest") != export.get("manifest_digest")
        ):
            raise CandidateLifecycleUXError("conversion lineage does not match evaluation/export evidence")
        if int(conversion.get("accepted_variants") or 0) <= 0:
            raise CandidateLifecycleUXError("no accepted GGUF quality variant is available")
        result["conversion"] = conversion
        if not require_package:
            return result
        package = self._single(
            snapshot["packages"], label="Ollama package", candidate_id=candidate_id
        )
        if (
            package.get("evaluation_digest") != evaluation.get("evaluation_digest")
            or package.get("export_manifest_digest") != export.get("manifest_digest")
            or package.get("gguf_report_digest") != conversion.get("report_digest")
        ):
            raise CandidateLifecycleUXError("package lineage does not match evaluation/export/conversion evidence")
        if package.get("quality") != "accept":
            raise CandidateLifecycleUXError("packaged candidate quality is not accepted")
        if package.get("public_push") is not False or package.get("provider_live_claim") is not False:
            raise CandidateLifecycleUXError("package evidence contains an unauthorized public/provider claim")
        result["package"] = package
        return result

    def promotion_preflight(self, candidate_id: str, role: str) -> dict[str, object]:
        chain = self._chain(
            candidate_id,
            require_export=True,
            require_conversion=True,
            require_package=True,
        )
        snapshot = self.snapshot()
        registry = _mapping(snapshot.get("registry"))
        if registry.get("state") != "ready":
            raise CandidateLifecycleUXError("specialized model registry is unavailable or invalid")
        records = [
            item
            for item in _list(registry.get("records"))
            if isinstance(item, Mapping) and item.get("candidate_id") == candidate_id
        ]
        if len(records) != 1:
            raise CandidateLifecycleUXError(
                "promotion requires exactly one immutable registry entry for candidate"
            )
        record = dict(records[0])
        if record.get("state") != "candidate":
            raise CandidateLifecycleUXError("registry entry is not in candidate state")
        if record.get("disposition") != "PROMOTE_TO_EXPORT":
            raise CandidateLifecycleUXError("registry disposition does not authorize promotion")
        normalized_role = role.strip().lower()
        if normalized_role not in {str(item) for item in _list(record.get("roles"))}:
            raise CandidateLifecycleUXError("candidate is not eligible for requested role")
        lineage_digests = {
            str(edge.get("digest"))
            for edge in _list(record.get("lineage"))
            if isinstance(edge, Mapping)
        }
        required_digests = {
            str(chain["evaluation"].get("evaluation_digest")),
            str(chain["export"].get("manifest_digest")),
            str(chain["conversion"].get("report_digest")),
            str(chain["package"].get("report_digest")),
        }
        if not required_digests <= lineage_digests:
            raise CandidateLifecycleUXError(
                "registry lineage does not bind accepted evaluation/export/conversion/package evidence"
            )
        preferred = str(record.get("preferred_variant", ""))
        variants = [
            dict(item) for item in _list(record.get("variants")) if isinstance(item, Mapping)
        ]
        selected = [item for item in variants if item.get("kind") == preferred]
        if len(selected) != 1 or not _digest_ready(selected[0].get("digest")):
            raise CandidateLifecycleUXError("preferred registry artifact identity is unavailable")
        active_roles = _mapping(registry.get("active_roles"))
        return {
            "candidate_id": candidate_id,
            "version_id": record.get("version_id"),
            "role": normalized_role,
            "artifact": selected[0],
            "current_mapping": active_roles.get(normalized_role),
            "proposed_mapping": record.get("version_id"),
            "evaluation_digest": chain["evaluation"].get("evaluation_digest"),
            "export_manifest_digest": chain["export"].get("manifest_digest"),
            "conversion_report_digest": chain["conversion"].get("report_digest"),
            "package_report_digest": chain["package"].get("report_digest"),
            "registry_record_digest": record.get("record_digest"),
            "blockers": [],
        }

    def rollback_preflight(self, role: str) -> dict[str, object]:
        snapshot = self.snapshot()
        registry = _mapping(snapshot.get("registry"))
        if registry.get("state") != "ready":
            raise CandidateLifecycleUXError("specialized model registry is unavailable or invalid")
        normalized_role = role.strip().lower()
        active = _mapping(registry.get("active_roles")).get(normalized_role)
        point = _mapping(_mapping(registry.get("rollback_roles")).get(normalized_role))
        if not point:
            raise CandidateLifecycleUXError("no immutable rollback point exists for requested role")
        if active != point.get("promoted_version_id"):
            raise CandidateLifecycleUXError("active mapping no longer matches immutable rollback point")
        prior = point.get("prior_version_id")
        records = {
            str(item.get("version_id")): item
            for item in _list(registry.get("records"))
            if isinstance(item, Mapping)
        }
        if prior is not None and str(prior) not in records:
            raise CandidateLifecycleUXError("rollback target registry entry is missing")
        return {
            "role": normalized_role,
            "current_mapping": active,
            "prior_mapping": prior,
            "transaction_id": point.get("transaction_id"),
            "current_record": records.get(str(active)),
            "prior_record": None if prior is None else records.get(str(prior)),
            "blockers": [],
        }

    def inspect_evaluation(self, candidate_id: str) -> dict[str, object]:
        chain = self._chain(candidate_id)
        return self.r15.execute(
            R15WorkflowRequest(
                domain="bench",
                action="compare",
                mode=R15WorkflowMode.INSPECT,
                identifier=str(chain["evaluation"]["evaluation_digest"]),
            )
        )

    def preview_export(self, candidate_id: str) -> dict[str, object]:
        chain = self._chain(candidate_id)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="export",
                action="run",
                mode=R15WorkflowMode.DRY_RUN,
                identifier=candidate_id,
            )
        )
        return {"preflight": chain, "request": request}

    def export_candidate(self, candidate_id: str, *, confirmed: bool = False) -> dict[str, object]:
        chain = self._chain(candidate_id)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="export",
                action="run",
                mode=R15WorkflowMode.APPLY,
                identifier=candidate_id,
                confirmed=confirmed,
            )
        )
        return {"preflight": chain, "request": request}

    def preview_conversion(self, candidate_id: str) -> dict[str, object]:
        chain = self._chain(candidate_id, require_export=True)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="conversion",
                action="run",
                mode=R15WorkflowMode.DRY_RUN,
                identifier=candidate_id,
            )
        )
        return {"preflight": chain, "request": request}

    def run_conversion(self, candidate_id: str, *, confirmed: bool = False) -> dict[str, object]:
        chain = self._chain(candidate_id, require_export=True)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="conversion",
                action="run",
                mode=R15WorkflowMode.APPLY,
                identifier=candidate_id,
                confirmed=confirmed,
            )
        )
        return {"preflight": chain, "request": request}

    def inspect_ollama(self) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(domain="ollama", action="status", mode=R15WorkflowMode.INSPECT)
        )

    def preview_package(self, candidate_id: str) -> dict[str, object]:
        chain = self._chain(candidate_id, require_export=True, require_conversion=True)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="ollama",
                action="package",
                mode=R15WorkflowMode.DRY_RUN,
                identifier=candidate_id,
            )
        )
        return {"preflight": chain, "request": request}

    def package_candidate(self, candidate_id: str, *, confirmed: bool = False) -> dict[str, object]:
        chain = self._chain(candidate_id, require_export=True, require_conversion=True)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="ollama",
                action="package",
                mode=R15WorkflowMode.APPLY,
                identifier=candidate_id,
                confirmed=confirmed,
            )
        )
        return {"preflight": chain, "request": request}

    def preview_promotion(self, candidate_id: str, role: str) -> dict[str, object]:
        preflight = self.promotion_preflight(candidate_id, role)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="registry",
                action="promote",
                mode=R15WorkflowMode.DRY_RUN,
                identifier=str(preflight["version_id"]),
                role=str(preflight["role"]),
            )
        )
        return {"preflight": preflight, "request": request}

    def promote(
        self,
        candidate_id: str,
        role: str,
        *,
        confirmed: bool = False,
    ) -> dict[str, object]:
        preflight = self.promotion_preflight(candidate_id, role)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="registry",
                action="promote",
                mode=R15WorkflowMode.APPLY,
                identifier=str(preflight["version_id"]),
                role=str(preflight["role"]),
                confirmed=confirmed,
            )
        )
        return {"preflight": preflight, "request": request}

    def preview_rollback(self, role: str) -> dict[str, object]:
        preflight = self.rollback_preflight(role)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="registry",
                action="rollback",
                mode=R15WorkflowMode.DRY_RUN,
                identifier=str(preflight["current_mapping"]),
                role=str(preflight["role"]),
            )
        )
        return {"preflight": preflight, "request": request}

    def rollback(self, role: str, *, confirmed: bool = False) -> dict[str, object]:
        preflight = self.rollback_preflight(role)
        request = self.r15.execute(
            R15WorkflowRequest(
                domain="registry",
                action="rollback",
                mode=R15WorkflowMode.ROLLBACK,
                identifier=str(preflight["current_mapping"]),
                role=str(preflight["role"]),
                confirmed=confirmed,
            )
        )
        return {"preflight": preflight, "request": request}


__all__ = [
    "CANDIDATE_WORKSPACE_SCHEMA",
    "CandidateLifecycleUXError",
    "ModelLabCandidateLifecycleService",
]
