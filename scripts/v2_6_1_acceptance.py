from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from kodepoia.release import CURRENT_RELEASE, ReleaseIdentity
from kodepoia.release.terminal_freeze import TERMINAL_RELEASE_FREEZE
from kodepoia.release.winget import WinGetInstallerEvidence, build_winget_bundle


def _check(name: str, condition: bool, detail: str) -> dict[str, str]:
    return {"name": name, "status": "PASS" if condition else "FAIL", "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source_sha = args.source_sha.strip().lower()
    observed_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip().lower()

    def read(path: str) -> str:
        return (root / path).read_text(encoding="utf-8")

    authority = read("docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md")
    state = read("docs/continuity/STATE.md")
    next_doc = read("docs/continuity/NEXT.md")
    v26 = read("docs/roadmap/V2_6_HARDENING_NEXT_PUBLIC_WINDOWS_RELEASE.md")
    rc8 = read("docs/release/RC8_WINDOWS_E2E_ACCEPTANCE.md")
    freeze_doc = read("docs/release/V2_6_1_TERMINAL_RELEASE_FREEZE.md")
    iss = read("packaging/windows/Kodepoia.iss")
    targets = read("update-repository/metadata/targets.json")
    authenticode_policy = read("docs/release/UPDATER_AUTHENTICODE_POLICY.md")
    r19_5_acceptance = read("scripts/r19_5_corrective_rc_acceptance.py")
    r20_5_tests = read("tests/test_r20_5_operations_health.py")
    root_metadata = json.loads(read("update-repository/metadata/root.json"))
    targets_metadata = json.loads(read("update-repository/metadata/targets.json"))
    snapshot_metadata = json.loads(read("update-repository/metadata/snapshot.json"))
    timestamp_metadata = json.loads(read("update-repository/metadata/timestamp.json"))
    python_core = read(".github/workflows/python-core.yml")

    freeze = TERMINAL_RELEASE_FREEZE
    target = freeze.successor_identity
    baseline = ReleaseIdentity(
        schema_version=1,
        product="Kodepoia",
        package="kodepoia",
        channel="beta",
        build_type="prerelease",
        source_binding="exact-head",
        major=1,
        minor=1,
        patch=0,
        stage="rc",
        serial=8,
    )
    freeze.assert_transition_from(baseline)

    preview = build_winget_bundle(
        WinGetInstallerEvidence(
            source_sha="a" * 40,
            installer_sha256="b" * 64,
        ),
        identity=target,
    )

    current_authority = (
        "V2.6.1 — Terminal V2 scope, release identity and compatibility freeze" in authority
        and "V2.6.1 — Terminal V2 scope, release identity and compatibility freeze" in state
        and "Current next action — V2.6.1 only" in next_doc
        and "V2.6.1 — Terminal V2 scope, release identity and compatibility freeze" in v26
    )

    checks = [
        _check("exact_head", source_sha == observed_sha, "acceptance runs the exact PR head"),
        _check(
            "current_authority",
            current_authority,
            "V2.6.1 is the only authorized implementation subdivision",
        ),
        _check(
            "later_scope_unauthorized",
            "V2.6.2 through V2.6.6 remain unauthorized" in authority
            and "V2.6.2 through V2.6.6 remain unauthorized" in next_doc,
            "V2.6.2-V2.6.6 remain outside this implementation scope",
        ),
        _check(
            "scope_base_exact",
            freeze.terminal_scope_base_sha
            == "6402041e6c86b21260c9b0fd7176141fff53a0ee",
            "terminal V2.6.1 scope begins at the normalized planning merge",
        ),
        _check(
            "public_baseline_rc8",
            baseline.public_version == "1.1.0-rc8"
            and freeze.public_baseline["public_version"] == "1.1.0-rc8"
            and freeze.public_baseline["source_sha"]
            == "fa787ab7ef76f2556b56ac1f058916a1425455af"
            and "37730750" in rc8
            and "6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422"
            in rc8,
            "installed/public rc8 baseline remains exact and unchanged",
        ),
        _check(
            "successor_identity",
            target.public_version == "1.1.0"
            and target.pep440_version == "1.1.0"
            and target.channel == "stable"
            and target.build_type == "release"
            and freeze.successor["tag"] == "v1.1.0",
            "terminal release identity is stable 1.1.0 / v1.1.0",
        ),
        _check(
            "monotonic_transition",
            target.is_newer_than(baseline)
            and baseline.can_transition_to(target)
            and freeze.transition["monotonic"] is True,
            "1.1.0 final is a valid monotonic transition from 1.1.0-rc8",
        ),
        _check(
            "candidate_source_not_preclaimed",
            freeze.successor["source_binding"] == "exact-head"
            and freeze.successor["candidate_source_freeze_phase"] == "V2.6.3"
            and freeze.successor["candidate_source_sha"] is None,
            "candidate SHA remains exact-head and is frozen only after V2.6.2",
        ),
        _check(
            "windows_identity",
            freeze.windows_installer["app_id"] in iss
            and '#define AppName "Kodepoia"' in iss
            and '#define AppExeName "KodepoiaStudio.exe"' in iss
            and "UsePreviousAppDir=yes" in iss
            and "DisableDirPage=no" in iss
            and "DefaultDirName={localappdata}\\Programs\\Kodepoia" in iss,
            "Windows install/upgrade identity and selectable directory remain compatible",
        ),
        _check(
            "stable_update_target",
            freeze.windows_installer["target_path_template"]
            == "channels/stable/windows-x86_64/1.1.0/{source_sha}/KodepoiaSetup.exe"
            and freeze.transition["rc8_to_stable_rehearsal_channel"] == "stable"
            and freeze.transition["beta_channel_behavior"]
            == "prerelease-feed-no-implicit-cross-channel-promotion",
            "stable target/channel behavior is explicit and no implicit beta promotion exists",
        ),
        _check(
            "installed_upgrade_baseline",
            freeze.transition["supported_installed_upgrade_baselines"] == ["1.1.0-rc8"]
            and freeze.transition["clean_install_supported"] is True,
            "installed updater support is frozen from rc8 plus clean install",
        ),
        _check(
            "authenticode_truth",
            freeze.authenticode["production_signing_verified"] is False
            and freeze.authenticode["production_signing_capability"] == "not-verified"
            and freeze.authenticode["production_signing_secret_provisioning_authorized"] is False
            and freeze.authenticode["unsigned_tuf_policy"] == "allow-unsigned"
            and freeze.authenticode["unsigned_policy_scope"] == "exact-target-only"
            and 'authenticode_policy: "allow-unsigned"' in authenticode_policy,
            "production signing is not fabricated and unsigned policy remains exact-target-scoped",
        ),
        _check(
            "production_tuf_freshness_observed",
            freeze.production_tuf_repository_observation["repository_metadata_fresh"] is False
            and freeze.production_tuf_repository_observation[
                "expired_roles_at_v2_6_1"
            ]
            == ["snapshot", "timestamp"]
            and freeze.production_tuf_repository_observation[
                "production_metadata_mutation_authorized"
            ]
            is False
            and freeze.production_tuf_repository_observation["resolution_phase"]
            == "V2.6.4"
            and root_metadata["signed"]["expires"]
            == freeze.production_tuf_repository_observation["root_expires"]
            and targets_metadata["signed"]["expires"]
            == freeze.production_tuf_repository_observation["targets_expires"]
            and snapshot_metadata["signed"]["expires"]
            == freeze.production_tuf_repository_observation["snapshot_expires"]
            and timestamp_metadata["signed"]["expires"]
            == freeze.production_tuf_repository_observation["timestamp_expires"]
            and "current_metadata_not_expired" not in r19_5_acceptance
            and "current_metadata_freshness" in r19_5_acceptance
            and "test_expired_or_unverifiable_metadata_is_critical_and_never_accepted"
            in r20_5_tests,
            (
                "expired repository metadata is observed without weakening updater "
                "rejection or authorizing a live refresh"
            ),
        ),
        _check(
            "winget_out",
            freeze.winget["decision"] == "out"
            and freeze.winget["public_submission_authorized"] is False
            and preview.readiness["publishable"] is False
            and "production_signing_not_verified" in preview.readiness["publication_blockers"],
            "WinGet is explicitly out and existing readiness logic remains non-publishable",
        ),
        _check(
            "release_note_contract",
            all(
                fragment in freeze_doc
                for fragment in (
                    "SmartScreen",
                    "stable update channel",
                    "WinGet publication is out",
                    "validation evidence",
                )
            ),
            "terminal release notes and known limitations are frozen",
        ),
        _check(
            "no_new_feature_freeze",
            freeze.no_new_feature_freeze["effective_after_v2_6_1_normalization"] is True
            and freeze.no_new_feature_freeze["new_product_capability_allowed"] is False
            and freeze.no_new_feature_freeze["v2_7_authorized"] is False
            and freeze.no_new_feature_freeze["r20_7_authorized"] is False,
            "post-V2.6.1 work is restricted to hardening and release closure",
        ),
        _check(
            "no_public_effects",
            all(value is False for value in freeze.effects.values())
            and "channels/stable/windows-x86_64/1.1.0/" not in targets,
            "V2.6.1 performs no public release/tag/TUF/updater/WinGet effect",
        ),
        _check(
            "runtime_identity_candidate_phase",
            target == CURRENT_RELEASE
            and '"channel": "stable"' in read("src/kodepoia/release/release_identity.json")
            and '"stage": "final"' in read("src/kodepoia/release/release_identity.json")
            and '"serial": 0' in read("src/kodepoia/release/release_identity.json")
            and 'version = "1.1.0"' in read("pyproject.toml"),
            "runtime canonical identity matches the frozen successor in the V2.6.3 candidate phase",
        ),
        _check(
            "ci_exact_head",
            "Run V2.6.1 terminal release freeze exact-head acceptance" in python_core
            and "v2-6-1-terminal-release-freeze" in python_core
            and "test_v2_6_1_terminal_release_freeze.py" in python_core,
            "Ubuntu/Windows exact-head acceptance is mandatory",
        ),
    ]

    passed = all(item["status"] == "PASS" for item in checks)
    payload: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.6.1",
        "title": "Terminal V2 scope, release identity and compatibility freeze",
        "source_sha": source_sha,
        "observed_sha": observed_sha,
        "target_release": target.to_dict(),
        "baseline_release": dict(freeze.public_baseline),
        "winget_decision": freeze.winget["decision"],
        "production_signing_verified": freeze.authenticode["production_signing_verified"],
        "checks": checks,
        "summary": {
            "passed": sum(item["status"] == "PASS" for item in checks),
            "total": len(checks),
        },
        "status": "PASS" if passed else "FAIL",
        "public_release_triggered": False,
        "public_tag_triggered": False,
        "production_tuf_mutation_triggered": False,
        "winget_submission_triggered": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["evidence_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
