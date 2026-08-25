from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.desktop.contracts import (
    DesktopArchitecture,
    DesktopFramework,
    DesktopOS,
    DesktopPackageKind,
)
from kodepoia.desktop.integrated_acceptance import WizardWindowsEvidence, canonical_sha256
from kodepoia.desktop.packaging import (
    DesktopVersion,
    SigningState,
    build_artifact_manifest,
    verify_artifact_tree,
)
from kodepoia.desktop.product_intent import apply_desktop_product_intent
from kodepoia.desktop.scaffold import (
    DesktopScaffoldEngine,
    DesktopTemplateManifest,
    ScaffoldLineage,
    TemplateValue,
    TemplateValueKind,
)
from kodepoia.desktop.workspace import DesktopWorkspaceService, DesktopWorkspaceState
from kodepoia.desktop.wpf import WpfAcceptanceResult, WpfAdapter
from kodepoia.product.spec import ProductSpec
from kodepoia.project.dna import Platform, ProjectType
from kodepoia.project.initializer import ProjectInitializer
from kodepoia.project.wizard import ProjectWizardState

ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bounded(path: Path) -> Path:
    resolved = path.resolve(strict=False)
    root = ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes repository root: {path}")
    return resolved


def _semantic_payload(
    *,
    source_sha: str,
    project_dna_sha256: str,
    product_sha256: str,
    workspace_manifest_sha256: str,
    model_sha256: str,
    package_manifest_sha256: str,
    artifact_count: int,
    build_returncode: int,
    test_returncode: int,
    test_sentinel: str,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_sha": source_sha,
        "project_type": "desktop_app",
        "platform": "windows",
        "framework": "wpf",
        "architecture": "x64",
        "package_kind": "archive",
        "project_dna_sha256": project_dna_sha256,
        "product_sha256": product_sha256,
        "workspace_manifest_sha256": workspace_manifest_sha256,
        "model_sha256": model_sha256,
        "package_manifest_sha256": package_manifest_sha256,
        "artifact_count": artifact_count,
        "build_returncode": build_returncode,
        "test_returncode": test_returncode,
        "test_sentinel": test_sentinel,
        "status": "pass",
        "blockers": [],
    }


def collect(*, source_sha: str, output: Path, work_root: Path) -> WizardWindowsEvidence:
    env_sha = os.environ.get("KODEPOIA_SOURCE_SHA")
    if env_sha and env_sha != source_sha:
        raise ValueError("--source-sha does not match KODEPOIA_SOURCE_SHA")

    work_root = _bounded(work_root)
    output = _bounded(output)
    if work_root == ROOT.resolve():
        raise ValueError("work root cannot be the repository root")
    if work_root.exists():
        shutil.rmtree(work_root)
    project_root = work_root / "project"
    staging_root = work_root / "staging"
    staging_root.mkdir(parents=True, exist_ok=True)

    dna = ProjectWizardState(
        name="R12IntegratedFixture",
        project_type=ProjectType.DESKTOP_APP,
        platforms=[Platform.WINDOWS],
        desktop_framework=DesktopFramework.WPF,
        desktop_architecture=DesktopArchitecture.X64,
        desktop_package_kind=DesktopPackageKind.ARCHIVE,
    ).build()
    if dna.desktop is None:
        raise RuntimeError("Project Wizard did not produce a desktop profile")

    product = ProductSpec(1, dna.name, "Canonical R12 Wizard-to-Windows integrated fixture")
    apply_desktop_product_intent(product, dna.desktop, dna.platforms)
    initialized = ProjectInitializer().initialize(project_root, dna, product)

    dna_sha = _sha(initialized.dna_path)
    product_sha = _sha(initialized.product_path)
    template = DesktopTemplateManifest.load(
        ROOT / "templates" / "r12" / "desktop" / "canonical" / "template.json"
    )
    values = {
        "name": TemplateValue(TemplateValueKind.IDENTIFIER, "R12IntegratedFixture"),
        "namespace": TemplateValue(TemplateValueKind.NAMESPACE, "Kodepoia.R12IntegratedFixture"),
        "description": TemplateValue(
            TemplateValueKind.TEXT,
            "Canonical R12 Wizard-to-Windows integrated fixture",
        ),
    }
    engine = DesktopScaffoldEngine()
    preview = engine.preview(
        project_root,
        template,
        values,
        ScaffoldLineage(dna_sha, product_sha),
    )
    if preview.has_conflicts:
        raise RuntimeError("canonical scaffold unexpectedly contains conflicts")
    workspace_manifest = engine.apply(project_root, preview)

    service = DesktopWorkspaceService(project_root, kill_switch=KillSwitch())
    status = service.status()
    validation = service.validate()
    if status.state is not DesktopWorkspaceState.READY:
        raise RuntimeError(f"Desktop workspace is not READY: {status.blockers}")
    if validation.state is not DesktopWorkspaceState.PASS:
        raise RuntimeError(f"Desktop Project DNA did not validate: {validation.blockers}")
    if status.framework != "wpf" or status.architecture != "x64":
        raise RuntimeError("Desktop workspace state drifted from Wizard intent")

    adapter = WpfAdapter(project_root, staging_root)
    result = adapter.run_acceptance(canonical_sample_app())
    if not isinstance(result, WpfAcceptanceResult):
        diagnostic = getattr(adapter, "last_diagnostic", "")
        raise RuntimeError(f"WPF integrated acceptance unavailable/failed: {result}; {diagnostic}")
    if result.build.returncode != 0 or result.test.returncode != 0:
        raise RuntimeError("WPF build/test did not return zero")
    sentinel = f"{WpfAdapter.SENTINEL}:{result.model_sha256}"
    if sentinel not in result.test.stdout:
        raise RuntimeError("WPF runtime test sentinel is missing")

    package_manifest = build_artifact_manifest(
        staging_root,
        package_id="kodepoia.r12.integrated.fixture",
        version=DesktopVersion(1, 0, 0),
        framework=DesktopFramework.WPF,
        platform=DesktopOS.WINDOWS,
        architecture=DesktopArchitecture.X64,
        package_kind=DesktopPackageKind.ARCHIVE,
        signing_state=SigningState.UNSIGNED,
    )
    verify_artifact_tree(staging_root, package_manifest)

    semantic = _semantic_payload(
        source_sha=source_sha,
        project_dna_sha256=dna_sha,
        product_sha256=product_sha,
        workspace_manifest_sha256=workspace_manifest.digest(),
        model_sha256=result.model_sha256,
        package_manifest_sha256=package_manifest.digest(),
        artifact_count=len(package_manifest.files),
        build_returncode=result.build.returncode,
        test_returncode=result.test.returncode,
        test_sentinel=sentinel,
    )
    evidence = WizardWindowsEvidence(
        schema_version=1,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        source_sha=source_sha,
        project_type="desktop_app",
        platform="windows",
        framework="wpf",
        architecture="x64",
        package_kind="archive",
        project_dna_sha256=dna_sha,
        product_sha256=product_sha,
        workspace_manifest_sha256=workspace_manifest.digest(),
        model_sha256=result.model_sha256,
        package_manifest_sha256=package_manifest.digest(),
        artifact_count=len(package_manifest.files),
        build_returncode=result.build.returncode,
        test_returncode=result.test.returncode,
        test_sentinel=sentinel,
        status="pass",
        blockers=(),
        evidence_sha256=canonical_sha256(semantic),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect R12.16 Wizard-to-Windows CI evidence")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument(
        "--output",
        default=".kodepoia/evidence/R12_16_WINDOWS_CI_ACCEPTANCE.json",
    )
    parser.add_argument(
        "--work-root",
        default=".kodepoia/r12_16_integrated",
    )
    args = parser.parse_args()
    evidence = collect(
        source_sha=args.source_sha,
        output=ROOT / args.output,
        work_root=ROOT / args.work_root,
    )
    print(json.dumps(evidence.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
