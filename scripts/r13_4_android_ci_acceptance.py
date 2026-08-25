from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

from jsonschema import Draft202012Validator

from kodepoia.desktop.app_model import canonical_sample_app
from kodepoia.mobile.android_build import (
    AndroidArtifactKind,
    AndroidBuildEvidence,
    AndroidBuildRequest,
    AndroidBuildStatus,
    AndroidBuildToolchainEvidence,
    inspect_android_artifact,
    prepare_build_staging,
)
from kodepoia.mobile.android_scaffold import (
    AndroidDependencyEvidence,
    AndroidScaffoldDefinition,
    AndroidScaffoldEngine,
    AndroidScaffoldLineage,
)
from kodepoia.mobile.contracts import MobileFormFactor, MobilePackageKind, MobileSourceKind
from kodepoia.project.dna import MobileProjectProfile, Platform, ProjectDNA, ProjectType

ROOT = Path(__file__).resolve().parents[1]
_METADATA = ".kodepoia/r13_4_ci_metadata.json"


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _toolchain() -> AndroidBuildToolchainEvidence:
    # Hosted stable SDK repositories used by acceptance currently expose API 36
    # but not platforms;android-37. Keep R13.3 source lineage intact and apply a
    # dated, deterministic build overlay that is still Google-Play ready.
    return AndroidBuildToolchainEvidence(
        evidence_id="android.build.hosted-stable.2026-08-25",
        android_gradle_plugin="9.3.1",
        gradle_version="9.5.0",
        kotlin_version="2.3.21",
        compose_bom="2026.06.00",
        compile_sdk=36,
        build_tools_version="36.0.0",
        jdk_major=17,
        observed_on="2026-08-25",
        source_urls=(
            "https://developer.android.com/build/releases/agp-9-3-0-release-notes",
            "https://developer.android.com/google/play/requirements/target-sdk",
            "https://developer.android.com/develop/ui/compose/bom",
            "https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler",
        ),
    )


def _source_dependency() -> AndroidDependencyEvidence:
    # This is the already accepted R13.3 source definition. R13.4 verifies it
    # byte-for-byte before applying the compatibility overlay in isolated staging.
    return AndroidDependencyEvidence(
        evidence_id="android.compose.r13-3",
        android_gradle_plugin="9.1.2",
        compose_bom="2026.08.00",
        compile_sdk=37,
        observed_on="2026-08-25",
        source_urls=(
            "https://developer.android.com/build/releases/about-agp",
            "https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler",
        ),
    )


def _dna() -> ProjectDNA:
    return ProjectDNA(
        schema_version=1,
        name="Kodepoia R13 Android Acceptance",
        project_type=ProjectType.MOBILE_APP,
        platforms=[Platform.ANDROID],
        mobile=MobileProjectProfile(
            source_kind=MobileSourceKind.NATIVE,
            form_factors=(MobileFormFactor.PHONE, MobileFormFactor.TABLET),
            android_application_id="com.kodepoia.r13acceptance",
            android_min_api=26,
            android_target_api=36,
            package_kinds=(MobilePackageKind.APK, MobilePackageKind.AAB),
        ),
    )


def prepare(source_sha: str, source_root: Path, staging_root: Path) -> None:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("source SHA must be exact lowercase 40-hex Git SHA")
    model = canonical_sample_app()
    definition = AndroidScaffoldDefinition.from_project(_dna(), model, _source_dependency())
    lineage = AndroidScaffoldLineage(
        _sha(b"r13.4-canonical-dna"),
        _sha(b"r13.4-canonical-product"),
    )
    engine = AndroidScaffoldEngine()
    preview = engine.preview(source_root, definition, model, lineage)
    manifest = engine.apply(source_root, preview)
    toolchain = _toolchain()
    overlay = prepare_build_staging(source_root, staging_root, toolchain)
    request = AndroidBuildRequest(
        source_workspace_manifest_sha256=manifest.digest(),
        application_id=definition.application_id,
        min_sdk=definition.min_sdk,
        target_sdk=definition.target_sdk,
    )
    metadata = {
        "source_sha": source_sha,
        "source_workspace_manifest_sha256": manifest.digest(),
        "overlay_manifest_sha256": overlay.digest(),
        "started_at": time.time(),
        "argv": list(request.argv()),
    }
    metadata_path = staging_root / _METADATA
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
    print(json.dumps({"staging": str(staging_root), "argv": list(request.argv())}, indent=2))


def collect(staging_root: Path, output: Path) -> None:
    metadata = json.loads((staging_root / _METADATA).read_text(encoding="utf-8"))
    toolchain = _toolchain()
    request = AndroidBuildRequest(
        source_workspace_manifest_sha256=str(metadata["source_workspace_manifest_sha256"]),
        application_id="com.kodepoia.r13acceptance",
        min_sdk=26,
        target_sdk=36,
    )
    if list(request.argv()) != metadata.get("argv"):
        raise SystemExit("fixed Gradle argv drifted between prepare and collect")

    apk = staging_root / "app/build/outputs/apk/debug/app-debug.apk"
    aab = staging_root / "app/build/outputs/bundle/release/app-release.aab"
    artifacts = (
        inspect_android_artifact(apk, AndroidArtifactKind.APK, max_bytes=request.max_artifact_bytes),
        inspect_android_artifact(aab, AndroidArtifactKind.AAB, max_bytes=request.max_artifact_bytes),
    )
    evidence = AndroidBuildEvidence(
        schema_version=1,
        source_sha=str(metadata["source_sha"]),
        runner_os=platform.system(),
        source_workspace_manifest_sha256=request.source_workspace_manifest_sha256,
        overlay_manifest_sha256=str(metadata["overlay_manifest_sha256"]),
        toolchain=toolchain,
        request=request,
        status=AndroidBuildStatus.PASS,
        duration_seconds=max(0.0, time.time() - float(metadata["started_at"])),
        artifacts=artifacts,
    )
    payload = evidence.to_dict()
    schema = json.loads((ROOT / "schemas/r13/android-build-evidence.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(evidence.canonical_bytes() + b"\n")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.4 hosted Android acceptance collector")
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--source-sha", required=True)
    p_prepare.add_argument("--source-root", type=Path, required=True)
    p_prepare.add_argument("--staging-root", type=Path, required=True)
    p_collect = sub.add_parser("collect")
    p_collect.add_argument("--staging-root", type=Path, required=True)
    p_collect.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.source_sha, args.source_root, args.staging_root)
    else:
        collect(args.staging_root, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
