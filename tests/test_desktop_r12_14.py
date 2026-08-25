from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from kodepoia.desktop.contracts import (
    DesktopArchitecture,
    DesktopFramework,
    DesktopOS,
    DesktopPackageKind,
)
from kodepoia.desktop.packaging import (
    ArtifactFile,
    ArtifactManifest,
    ArtifactRole,
    DesktopVersion,
    LocalUpdateEngine,
    PackageCapabilityState,
    PackageDefinition,
    PackageIntegrityError,
    SigningIdentity,
    SigningState,
    UpdateApplyState,
    UpdateManifest,
    UpdatePolicy,
    UpdateRejectedError,
    build_artifact_manifest,
    package_capability,
    validate_update_candidate,
    verify_artifact_tree,
)


def _write_tree(root: Path, *, app: bytes, config: bytes = b"{}") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "bin").mkdir(exist_ok=True)
    (root / "assets").mkdir(exist_ok=True)
    (root / "bin" / "app.exe").write_bytes(app)
    (root / "assets" / "config.json").write_bytes(config)


def _manifest(
    root: Path,
    version: str,
    *,
    architecture: DesktopArchitecture = DesktopArchitecture.X64,
    signing_state: SigningState = SigningState.UNSIGNED,
    signing_identity: SigningIdentity | None = None,
) -> ArtifactManifest:
    return build_artifact_manifest(
        root,
        package_id="kodepoia.fixture",
        version=DesktopVersion.parse(version),
        framework=DesktopFramework.WINUI3,
        platform=DesktopOS.WINDOWS,
        architecture=architecture,
        package_kind=DesktopPackageKind.ARCHIVE,
        signing_state=signing_state,
        signing_identity=signing_identity,
        executable_paths=("bin/app.exe",),
    )


def _policy(**overrides: object) -> UpdatePolicy:
    values: dict[str, object] = {
        "policy_id": "stable-policy",
        "channel": "stable",
        "accepted_signing_states": (SigningState.UNSIGNED,),
    }
    values.update(overrides)
    return UpdatePolicy(**values)  # type: ignore[arg-type]


def test_desktop_version_is_bounded_and_comparable() -> None:
    assert DesktopVersion.parse("1.2.3").canonical() == "1.2.3.0"
    assert DesktopVersion.parse("1.2.3.4") > DesktopVersion.parse("1.2.3.3")
    with pytest.raises(ValueError):
        DesktopVersion.parse("1.2")
    with pytest.raises(ValueError):
        DesktopVersion(70000, 0, 0, 0)


def test_artifact_manifest_is_semantic_and_order_independent() -> None:
    first = ArtifactFile("bin/app.exe", 3, "a" * 64, ArtifactRole.EXECUTABLE)
    second = ArtifactFile("assets/config.json", 2, "b" * 64, ArtifactRole.METADATA)
    left = ArtifactManifest(
        package_id="kodepoia.fixture",
        version=DesktopVersion.parse("1.0.0"),
        framework=DesktopFramework.WINUI3,
        platform=DesktopOS.WINDOWS,
        architecture=DesktopArchitecture.X64,
        package_kind=DesktopPackageKind.ARCHIVE,
        signing_state=SigningState.UNSIGNED,
        files=(first, second),
    )
    right = replace(left, files=(second, first))
    assert left.canonical() == right.canonical()
    assert left.digest() == right.digest()


def test_manifest_rejects_path_escape_duplicate_and_secret_like_signer() -> None:
    with pytest.raises(ValueError):
        ArtifactFile("../escape.exe", 1, "a" * 64)
    duplicate = ArtifactFile("same.txt", 1, "a" * 64)
    with pytest.raises(ValueError):
        ArtifactManifest(
            package_id="fixture",
            version=DesktopVersion.parse("1.0.0"),
            framework=DesktopFramework.WPF,
            platform=DesktopOS.WINDOWS,
            architecture=DesktopArchitecture.X64,
            package_kind=DesktopPackageKind.ARCHIVE,
            signing_state=SigningState.UNSIGNED,
            files=(duplicate, duplicate),
        )
    with pytest.raises(ValueError):
        SigningIdentity("private key=.pfx", "b" * 64, False)


def test_signing_state_identity_contract_is_fail_closed() -> None:
    production = SigningIdentity("CN=Kodepoia Production", "a" * 64, True)
    test = SigningIdentity("CN=Kodepoia Test", "b" * 64, False)
    file = ArtifactFile("app.exe", 1, "c" * 64)

    with pytest.raises(ValueError):
        ArtifactManifest(
            package_id="fixture",
            version=DesktopVersion.parse("1.0.0"),
            framework=DesktopFramework.WPF,
            platform=DesktopOS.WINDOWS,
            architecture=DesktopArchitecture.X64,
            package_kind=DesktopPackageKind.ARCHIVE,
            signing_state=SigningState.SIGNED,
            signing_identity=test,
            files=(file,),
        )
    signed = ArtifactManifest(
        package_id="fixture",
        version=DesktopVersion.parse("1.0.0"),
        framework=DesktopFramework.WPF,
        platform=DesktopOS.WINDOWS,
        architecture=DesktopArchitecture.X64,
        package_kind=DesktopPackageKind.ARCHIVE,
        signing_state=SigningState.SIGNED,
        signing_identity=production,
        files=(file,),
    )
    assert signed.signing_identity is production


def test_framework_package_capability_is_truthful_not_install_claim() -> None:
    assert (
        package_capability(DesktopFramework.WINUI3, DesktopOS.WINDOWS, DesktopPackageKind.MSIX)
        is PackageCapabilityState.TOOLCHAIN_REQUIRED
    )
    assert (
        package_capability(DesktopFramework.TAURI2, DesktopOS.WINDOWS, DesktopPackageKind.MSI)
        is PackageCapabilityState.TOOLCHAIN_REQUIRED
    )
    assert (
        package_capability(DesktopFramework.QT6, DesktopOS.WINDOWS, DesktopPackageKind.ARCHIVE)
        is PackageCapabilityState.SUPPORTED_DEFINITION
    )
    assert (
        package_capability(DesktopFramework.WPF, DesktopOS.LINUX, DesktopPackageKind.MSIX)
        is PackageCapabilityState.UNSUPPORTED
    )


def test_package_definition_rejects_unsupported_framework_format() -> None:
    with pytest.raises(ValueError):
        PackageDefinition(
            definition_id="wpf-linux-msix",
            package_id="fixture",
            version=DesktopVersion.parse("1.0.0"),
            framework=DesktopFramework.WPF,
            platform=DesktopOS.LINUX,
            architecture=DesktopArchitecture.X64,
            package_kind=DesktopPackageKind.MSIX,
            signing_state=SigningState.UNSIGNED,
        )


def test_build_and_verify_artifact_tree_detects_tampering(tmp_path: Path) -> None:
    root = tmp_path / "artifact"
    _write_tree(root, app=b"v1")
    manifest = _manifest(root, "1.0.0")
    verify_artifact_tree(root, manifest)
    (root / "bin" / "app.exe").write_bytes(b"tampered")
    with pytest.raises(PackageIntegrityError, match="digest mismatch|size mismatch"):
        verify_artifact_tree(root, manifest)


def test_update_manifest_accepts_exact_higher_version(tmp_path: Path) -> None:
    current_root = tmp_path / "current"
    target_root = tmp_path / "target"
    _write_tree(current_root, app=b"v1")
    _write_tree(target_root, app=b"v2")
    current = _manifest(current_root, "1.0.0")
    target = _manifest(target_root, "2.0.0")
    update = UpdateManifest.from_manifests(
        update_id="fixture-2", channel="stable", source=current, target=target
    )
    result = validate_update_candidate(
        current=current, target=target, update=update, policy=_policy()
    )
    assert result.accepted
    assert result.blockers == ()


def test_update_rejects_downgrade_wrong_arch_and_channel(tmp_path: Path) -> None:
    current_root = tmp_path / "current"
    target_root = tmp_path / "target"
    _write_tree(current_root, app=b"v2")
    _write_tree(target_root, app=b"v1")
    current = _manifest(current_root, "2.0.0")
    target = _manifest(
        target_root, "1.0.0", architecture=DesktopArchitecture.X86
    )
    update = UpdateManifest.from_manifests(
        update_id="fixture-1", channel="beta", source=current, target=target
    )
    result = validate_update_candidate(
        current=current, target=target, update=update, policy=_policy()
    )
    assert not result.accepted
    assert "downgrade_forbidden" in result.blockers
    assert "architecture_mismatch" in result.blockers
    assert "channel_mismatch" in result.blockers


def test_explicit_downgrade_policy_can_authorize_only_compatible_downgrade(tmp_path: Path) -> None:
    current_root = tmp_path / "current"
    target_root = tmp_path / "target"
    _write_tree(current_root, app=b"v2")
    _write_tree(target_root, app=b"v1")
    current = _manifest(current_root, "2.0.0")
    target = _manifest(target_root, "1.0.0")
    update = UpdateManifest.from_manifests(
        update_id="fixture-1", channel="stable", source=current, target=target
    )
    result = validate_update_candidate(
        current=current,
        target=target,
        update=update,
        policy=_policy(allow_downgrade=True),
    )
    assert result.accepted


def test_signing_state_and_signer_substitution_are_rejected(tmp_path: Path) -> None:
    current_root = tmp_path / "current"
    target_root = tmp_path / "target"
    _write_tree(current_root, app=b"v1")
    _write_tree(target_root, app=b"v2")
    current = _manifest(current_root, "1.0.0")
    target = _manifest(target_root, "2.0.0")
    update = UpdateManifest.from_manifests(
        update_id="fixture-2", channel="stable", source=current, target=target
    )
    substituted = replace(
        update,
        signing_state=SigningState.TEST_SIGNED,
        signer_fingerprint_sha256="d" * 64,
    )
    result = validate_update_candidate(
        current=current, target=target, update=substituted, policy=_policy()
    )
    assert not result.accepted
    assert "signing_state_substitution" in result.blockers
    assert "signer_identity_substitution" in result.blockers


def test_signer_rotation_requires_explicit_policy(tmp_path: Path) -> None:
    current_root = tmp_path / "current"
    target_root = tmp_path / "target"
    _write_tree(current_root, app=b"v1")
    _write_tree(target_root, app=b"v2")
    first = SigningIdentity("CN=Test A", "a" * 64, False)
    second = SigningIdentity("CN=Test B", "b" * 64, False)
    current = _manifest(
        current_root,
        "1.0.0",
        signing_state=SigningState.TEST_SIGNED,
        signing_identity=first,
    )
    target = _manifest(
        target_root,
        "2.0.0",
        signing_state=SigningState.TEST_SIGNED,
        signing_identity=second,
    )
    update = UpdateManifest.from_manifests(
        update_id="fixture-2", channel="stable", source=current, target=target
    )
    denied = validate_update_candidate(
        current=current,
        target=target,
        update=update,
        policy=_policy(accepted_signing_states=(SigningState.TEST_SIGNED,)),
    )
    assert "signer_rotation_forbidden" in denied.blockers
    allowed = validate_update_candidate(
        current=current,
        target=target,
        update=update,
        policy=_policy(
            accepted_signing_states=(SigningState.TEST_SIGNED,),
            allow_signer_rotation=True,
        ),
    )
    assert allowed.accepted


def test_local_update_promotes_only_verified_candidate(tmp_path: Path) -> None:
    current_root = tmp_path / "installed"
    target_root = tmp_path / "candidate"
    _write_tree(current_root, app=b"v1")
    _write_tree(target_root, app=b"v2", config=b'{"v":2}')
    current = _manifest(current_root, "1.0.0")
    target = _manifest(target_root, "2.0.0")
    update = UpdateManifest.from_manifests(
        update_id="fixture-2", channel="stable", source=current, target=target
    )

    result = LocalUpdateEngine(tmp_path).apply(
        current_root=current_root,
        candidate_root=target_root,
        current_manifest=current,
        target_manifest=target,
        update=update,
        policy=_policy(),
    )

    assert result.state is UpdateApplyState.APPLIED
    assert (current_root / "bin" / "app.exe").read_bytes() == b"v2"
    verify_artifact_tree(current_root, target)
    assert [event.sequence for event in result.audit] == list(range(1, len(result.audit) + 1))


def test_failed_local_update_rolls_back_to_prior_verified_state(tmp_path: Path) -> None:
    current_root = tmp_path / "installed"
    target_root = tmp_path / "candidate"
    _write_tree(current_root, app=b"v1")
    _write_tree(target_root, app=b"v2")
    current = _manifest(current_root, "1.0.0")
    target = _manifest(target_root, "2.0.0")
    update = UpdateManifest.from_manifests(
        update_id="fixture-2", channel="stable", source=current, target=target
    )

    result = LocalUpdateEngine(tmp_path).apply(
        current_root=current_root,
        candidate_root=target_root,
        current_manifest=current,
        target_manifest=target,
        update=update,
        policy=_policy(),
        inject_failure_after_promotion=True,
    )

    assert result.state is UpdateApplyState.ROLLED_BACK
    assert result.error == "injected post-promotion failure"
    assert (current_root / "bin" / "app.exe").read_bytes() == b"v1"
    verify_artifact_tree(current_root, current)
    assert result.audit[-1].action == "rollback_verified"


def test_update_engine_rejects_workspace_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    candidate = workspace / "candidate"
    _write_tree(outside, app=b"v1")
    _write_tree(candidate, app=b"v2")
    current = _manifest(outside, "1.0.0")
    target = _manifest(candidate, "2.0.0")
    update = UpdateManifest.from_manifests(
        update_id="fixture-2", channel="stable", source=current, target=target
    )
    with pytest.raises(ValueError, match="escapes workspace"):
        LocalUpdateEngine(workspace).apply(
            current_root=outside,
            candidate_root=candidate,
            current_manifest=current,
            target_manifest=target,
            update=update,
            policy=_policy(),
        )


def test_tampered_candidate_is_rejected_before_any_backup(tmp_path: Path) -> None:
    current_root = tmp_path / "installed"
    target_root = tmp_path / "candidate"
    _write_tree(current_root, app=b"v1")
    _write_tree(target_root, app=b"v2")
    current = _manifest(current_root, "1.0.0")
    target = _manifest(target_root, "2.0.0")
    update = UpdateManifest.from_manifests(
        update_id="fixture-2", channel="stable", source=current, target=target
    )
    (target_root / "bin" / "app.exe").write_bytes(b"tampered")
    with pytest.raises(PackageIntegrityError):
        LocalUpdateEngine(tmp_path).apply(
            current_root=current_root,
            candidate_root=target_root,
            current_manifest=current,
            target_manifest=target,
            update=update,
            policy=_policy(),
        )
    assert (current_root / "bin" / "app.exe").read_bytes() == b"v1"
    assert not (tmp_path / ".kodepoia-r12-update-backup").exists()
