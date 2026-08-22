from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping

from kodepoia.assets.contracts import AssetRevisionId, AssetRole, ReuseScope
from kodepoia.assets.serialization import canonical_json
from kodepoia.assets.store import VaultStore
from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.license_bom import (
    BomComponent,
    BomReport,
    ComponentKind,
    ComponentResolution,
    DependencyRequirement,
    IntegrityEvidence,
    IntegrityStatus,
    LicenseAssertion,
    LicenseAssertionState,
    LicensePolicy,
    LicensePolicyAction,
    LicenseReport,
)


class AssetGovernanceOutcome(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class AssetLicenseEvidence:
    revision_id: AssetRevisionId
    assertions: tuple[LicenseAssertion, ...] = ()
    creator: str = ""
    publisher: str = ""
    attribution: str = ""
    notice: str = ""
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        refs = tuple(dict.fromkeys(item.strip() for item in self.evidence_refs if item.strip()))
        object.__setattr__(self, "evidence_refs", refs)

    @property
    def conflict(self) -> bool:
        return len({item.spdx_token for item in self.assertions}) > 1

    @property
    def concluded(self) -> LicenseAssertion:
        if not self.assertions:
            return LicenseAssertion(
                state=LicenseAssertionState.NOASSERTION,
                evidence_source="vault-governance:missing-license-evidence",
                rationale="No authoritative license evidence is recorded for this asset revision.",
            )
        if self.conflict:
            return LicenseAssertion(
                state=LicenseAssertionState.NOASSERTION,
                evidence_source="vault-governance:conflicting-license-evidence",
                rationale="Conflicting license assertions remain unresolved and are not auto-reconciled.",
            )
        return self.assertions[0]


@dataclass(frozen=True, slots=True)
class AssetGovernanceDecision:
    revision_id: AssetRevisionId
    license_token: str
    policy_action: LicensePolicyAction
    outcome: AssetGovernanceOutcome
    effective_reuse_scope: ReuseScope
    reasons: tuple[str, ...]

    @property
    def blocking(self) -> bool:
        return self.outcome is AssetGovernanceOutcome.BLOCK

    def to_dict(self) -> dict[str, object]:
        return {
            "revision_id": str(self.revision_id),
            "license_token": self.license_token,
            "policy_action": self.policy_action.value,
            "outcome": self.outcome.value,
            "effective_reuse_scope": self.effective_reuse_scope.value,
            "reasons": list(self.reasons),
            "blocking": self.blocking,
        }


@dataclass(frozen=True, slots=True)
class AssetExportPlan:
    project_id: str
    decisions: tuple[AssetGovernanceDecision, ...]
    blockers: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return not self.blockers


@dataclass(frozen=True, slots=True)
class AssetExportReport:
    project_id: str
    destination: str
    exported_revision_ids: tuple[str, ...]
    bom_evidence_sha256: str
    license_evidence_sha256: str
    notice_sha256: str
    manifest_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "project_id": self.project_id,
            "destination": self.destination,
            "exported_revision_ids": list(self.exported_revision_ids),
            "bom_evidence_sha256": self.bom_evidence_sha256,
            "license_evidence_sha256": self.license_evidence_sha256,
            "notice_sha256": self.notice_sha256,
            "manifest_sha256": self.manifest_sha256,
        }


class AssetGovernanceService:
    """Bridge immutable R8 Vault evidence into the accepted R6 BOM/license policy engine."""

    def __init__(self, store: VaultStore, policy: LicensePolicy) -> None:
        self.store = store
        self.policy = policy

    @staticmethod
    def _safe_provenance_locator(locator: str) -> str:
        value = locator.strip()
        if value.startswith(("https://", "http://", "git+", "research:")):
            return value
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return f"local-locator-sha256:{digest}"

    def _revision(self, revision_id: AssetRevisionId):
        return self.store._load_revision_manifest(revision_id)

    def evidence_or_unknown(
        self,
        revision_id: AssetRevisionId,
        evidence_by_revision: Mapping[AssetRevisionId, AssetLicenseEvidence],
    ) -> AssetLicenseEvidence:
        evidence = evidence_by_revision.get(revision_id)
        if evidence is not None:
            if evidence.revision_id != revision_id:
                raise ValueError("Asset license evidence revision identity mismatch")
            return evidence
        return AssetLicenseEvidence(revision_id)

    def decision(
        self,
        revision_id: AssetRevisionId,
        evidence: AssetLicenseEvidence,
    ) -> AssetGovernanceDecision:
        revision = self._revision(revision_id)
        concluded = evidence.concluded
        action, source = self.policy.evaluate(concluded)
        reasons: list[str] = []
        if evidence.conflict:
            outcome = AssetGovernanceOutcome.BLOCK
            reasons.append("conflicting-license-evidence")
        elif action is LicensePolicyAction.DENY:
            outcome = AssetGovernanceOutcome.BLOCK
            reasons.append(f"license-policy-deny:{source}")
        elif action is LicensePolicyAction.UNKNOWN:
            outcome = AssetGovernanceOutcome.BLOCK
            reasons.append("license-policy-unknown")
        elif action is LicensePolicyAction.WARN:
            outcome = AssetGovernanceOutcome.WARN
            reasons.append(f"license-policy-warn:{source}")
        else:
            outcome = AssetGovernanceOutcome.ALLOW
            reasons.append(f"license-policy-allow:{source}")

        effective_scope = revision.reuse_scope
        if outcome is AssetGovernanceOutcome.BLOCK:
            effective_scope = ReuseScope.PROJECT_ONLY
        return AssetGovernanceDecision(
            revision_id=revision_id,
            license_token=concluded.spdx_token,
            policy_action=action,
            outcome=outcome,
            effective_reuse_scope=effective_scope,
            reasons=tuple(reasons),
        )

    def bom_component(
        self,
        revision_id: AssetRevisionId,
        evidence: AssetLicenseEvidence,
    ) -> BomComponent:
        revision = self._revision(revision_id)
        requirements = tuple(
            DependencyRequirement(
                group="asset-lineage",
                requirement=str(item.input_revision_id),
                source=f"vault-lineage:{revision_id}",
            )
            for item in revision.lineage
        )
        provenance_chain = [
            {
                "source_kind": item.source_kind,
                "locator": self._safe_provenance_locator(item.locator),
                "evidence_sha256": item.evidence_sha256,
            }
            for item in revision.provenance
        ]
        details = {
            "asset_revision_id": str(revision_id),
            "asset_id": str(revision.asset_id),
            "role": revision.role.value,
            "reuse_scope": revision.reuse_scope.value,
            "creator": evidence.creator,
            "publisher": evidence.publisher,
            "attribution": evidence.attribution,
            "notice": evidence.notice,
            "evidence_refs": list(evidence.evidence_refs),
            "license_assertions": [item.spdx_token for item in evidence.assertions],
            "license_conflict": evidence.conflict,
            "provenance_chain": provenance_chain,
        }
        return BomComponent(
            id=f"asset:{str(revision_id).replace('_', '-')}",
            name=str(revision.asset_id),
            kind=ComponentKind.ASSET,
            resolution=ComponentResolution.RESOLVED,
            version=str(revision_id),
            source_locator=f"vault:{revision_id}",
            provenance_source="canonical R8 Vault revision manifest",
            source_sha256=revision.content_sha256,
            integrity=IntegrityEvidence(
                status=IntegrityStatus.RECORDED,
                source=f"vault-content:{revision_id}",
                digest=revision.content_sha256,
            ),
            declared_license=evidence.assertions[0] if len(evidence.assertions) == 1 else None,
            concluded_license=evidence.concluded,
            requirements=requirements,
            details=details,
        )

    def project_bom(
        self,
        project_id: str,
        evidence_by_revision: Mapping[AssetRevisionId, AssetLicenseEvidence],
    ) -> BomReport:
        rows = self.store.db.execute(
            "SELECT DISTINCT revision_id FROM project_refs WHERE project_id = ? ORDER BY revision_id",
            (project_id,),
        ).fetchall()
        components = []
        for row in rows:
            revision_id = AssetRevisionId(str(row["revision_id"]))
            evidence = self.evidence_or_unknown(revision_id, evidence_by_revision)
            components.append(self.bom_component(revision_id, evidence))
        return BomReport.build(
            project_name=project_id,
            inventory_scope="vault-project-references",
            components=components,
            inventory_complete=True,
            inventory_review_source="AssetGovernanceService deterministic project_refs enumeration",
        )

    def project_license_report(
        self,
        project_id: str,
        evidence_by_revision: Mapping[AssetRevisionId, AssetLicenseEvidence],
    ) -> LicenseReport:
        return LicenseReport.build(self.project_bom(project_id, evidence_by_revision), self.policy)

    def plan_export(
        self,
        project_id: str,
        evidence_by_revision: Mapping[AssetRevisionId, AssetLicenseEvidence],
    ) -> AssetExportPlan:
        rows = self.store.db.execute(
            "SELECT DISTINCT revision_id FROM project_refs WHERE project_id = ? ORDER BY revision_id",
            (project_id,),
        ).fetchall()
        decisions: list[AssetGovernanceDecision] = []
        blockers: list[str] = []
        for row in rows:
            revision_id = AssetRevisionId(str(row["revision_id"]))
            evidence = self.evidence_or_unknown(revision_id, evidence_by_revision)
            decision = self.decision(revision_id, evidence)
            decisions.append(decision)
            revision = self._revision(revision_id)
            if decision.blocking:
                blockers.append(f"governance:{revision_id}")
            if revision.reuse_scope is not ReuseScope.EXPORTABLE:
                blockers.append(f"reuse-scope:{revision_id}:{revision.reuse_scope.value}")
        return AssetExportPlan(project_id, tuple(decisions), tuple(sorted(set(blockers))))

    def export_project(
        self,
        project_id: str,
        evidence_by_revision: Mapping[AssetRevisionId, AssetLicenseEvidence],
        *,
        export_boundary: WorkspaceBoundary,
        target_dir: str,
    ) -> AssetExportReport:
        plan = self.plan_export(project_id, evidence_by_revision)
        if not plan.allowed:
            raise PermissionError("Asset export blocked: " + ", ".join(plan.blockers))

        target = export_boundary.resolve(target_dir)
        if target.exists():
            raise FileExistsError(target)
        stage_rel = f".kodepoia-export-stage-{uuid.uuid4().hex}"
        stage = export_boundary.resolve(stage_rel)
        stage.mkdir(parents=True, exist_ok=False)
        stage_boundary = WorkspaceBoundary(stage)
        exported: list[str] = []
        try:
            rows = self.store.db.execute(
                "SELECT revision_id, target_path FROM project_refs WHERE project_id = ? ORDER BY revision_id, target_path",
                (project_id,),
            ).fetchall()
            used_targets: set[str] = set()
            for row in rows:
                revision_id = AssetRevisionId(str(row["revision_id"]))
                relative = str(row["target_path"] or f"assets/{revision_id}").replace("\\", "/")
                if relative in used_targets:
                    continue
                used_targets.add(relative)
                self.store.materialize(
                    revision_id,
                    project_boundary=stage_boundary,
                    target_path=relative,
                    overwrite=False,
                )
                exported.append(str(revision_id))

            bom = self.project_bom(project_id, evidence_by_revision)
            license_report = LicenseReport.build(bom, self.policy)
            notice_lines = [f"Kodepoia asset export notices — {project_id}", ""]
            for revision_id in sorted({AssetRevisionId(value) for value in exported}, key=str):
                evidence = self.evidence_or_unknown(revision_id, evidence_by_revision)
                notice_lines.append(f"[{revision_id}] {evidence.concluded.spdx_token}")
                if evidence.creator:
                    notice_lines.append(f"Creator: {evidence.creator}")
                if evidence.publisher:
                    notice_lines.append(f"Publisher: {evidence.publisher}")
                if evidence.attribution:
                    notice_lines.append(f"Attribution: {evidence.attribution}")
                if evidence.notice:
                    notice_lines.append(f"Notice: {evidence.notice}")
                notice_lines.append("")
            notice_text = "\n".join(notice_lines).rstrip() + "\n"
            notice_bytes = notice_text.encode("utf-8")
            notice_sha = hashlib.sha256(notice_bytes).hexdigest()
            (stage / "ASSET_NOTICES.txt").write_bytes(notice_bytes)

            manifest_payload = {
                "schema_version": 1,
                "project_id": project_id,
                "exported_revision_ids": sorted(set(exported)),
                "decisions": [item.to_dict() for item in plan.decisions],
                "bom": bom.to_dict(),
                "license_report": license_report.to_dict(),
                "notice_sha256": notice_sha,
            }
            manifest_bytes = (canonical_json(manifest_payload) + "\n").encode("utf-8")
            manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
            (stage / "ASSET_EXPORT_MANIFEST.json").write_bytes(manifest_bytes)

            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage, target)
            return AssetExportReport(
                project_id=project_id,
                destination=export_boundary.relative(target),
                exported_revision_ids=tuple(sorted(set(exported))),
                bom_evidence_sha256=bom.evidence_sha256,
                license_evidence_sha256=license_report.evidence_sha256,
                notice_sha256=notice_sha,
                manifest_sha256=manifest_sha,
            )
        except Exception:
            if stage.exists():
                shutil.rmtree(stage)
            raise
