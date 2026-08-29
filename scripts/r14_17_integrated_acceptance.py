from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from kodepoia.backend.auth import AuthClientKind, AuthClientPolicy, AuthRealmIdentity, LocalAuthProvider
from kodepoia.backend.contracts import BackendEnvironmentKind, canonical_sha256


SERVICE_SCRIPTS = (
    ("postgres", "scripts/r14_5_postgres_acceptance.py"),
    ("authority", "scripts/r14_6_authority_acceptance.py"),
    ("matchmaking", "scripts/r14_7_matchmaking_acceptance.py"),
    ("cloud_save", "scripts/r14_8_cloud_save_acceptance.py"),
    ("progression", "scripts/r14_9_progression_acceptance.py"),
    ("entitlements", "scripts/r14_10_entitlements_acceptance.py"),
    ("remote_config", "scripts/r14_11_remote_config_acceptance.py"),
    ("content_delivery", "scripts/r14_12_content_delivery_acceptance.py"),
    ("event_pipeline", "scripts/r14_13_event_pipeline_acceptance.py"),
    ("liveops", "scripts/r14_14_liveops_acceptance.py"),
    ("resilience", "scripts/r14_15_resilience_acceptance.py"),
    ("liveops_ux", "scripts/r14_16_liveops_ux_acceptance.py"),
)

# Immutable semantic anchors accepted by the prior normalized subdivisions. R14.17
# re-runs the services on its own exact technical SHA; these anchors make drift visible
# without treating old PASS strings as fresh evidence.
FROZEN_ACCEPTANCE_DIGESTS: dict[str, dict[str, str]] = {
    "postgres": {
        "migration_plan": "b96484ae6d56fe54b013b975572310d8daf44cf43116c5c43edc73845856b71b",
        "restore": "bcc5ae8b707231568263e0f52c8426dd956a67e4e131bcf97becb4b45ccb9f6e",
    },
    "authority": {
        "state": "59c1afb567245df4f3521052564d0bdfbaa4a5423eb7db7997c1e20160a988a3",
        "events": "3adad95a513ee4812126d7d9695cc297d2f57287263a5686ee1ee5c08a15e4a1",
        "trace": "839f65c4ffbe019c43f6aad988ee8258945c328f348135ffef9320955102f178",
    },
    "matchmaking": {
        "state": "ae9ecc0893537e5c12cc8a78247197ed53d094b1a811c386c17161fac10c0c19",
        "reservation": "e8423de1a2d1a92873bbfa466111ab4a07168adeafca4bde4d62c64a70a9f690",
        "trace": "5f25c8f15da7e4f9dd45fbf072dd72101d3f32deef349c28069beeb83d954bd3",
    },
    "cloud_save": {
        "state": "984bf5fc88d5ca537cd3a4d938c0aa6d890e8f1794f5485467726331331ce345",
        "revision": "4603e4e2a7d7d708cf689eb6cd4502b9809993b7245fc3ac64bf05eee1f34d7e",
        "conflict": "be2d6808b13bd40aa4a04d003d8d47df315a4461a67647746b87b26d1e6c0eca",
    },
    "progression": {
        "definition": "0ff0b8c2215dabf637f852f3d049959a02dbd7cb3e8e26c5cf2fa680682cb686",
        "state": "a8d7bed52649c7f6cea1d2f07793a011058afbdd2973e568ade69f7b3811d49d",
        "trace": "c1180c3bc5326a6fd268dc6bd54f9bd13c99bba837a7bc931d1b55c206d9bec3",
    },
    "entitlements": {
        "catalog": "029829e18972971f3551f3a0a99e3e641e55ab7a2fb6cb374f6b4645b482389c",
        "state": "3a526baa050763c8b5453c7970f750ce205ef57d864a612986b43488ab9f0154",
        "trace": "1333f7f917742d6a0f93028466e0f1c8e771b9442dfe5403c22184764e1edbeb",
        "provider_event": "57962e7fddd666146ebb90aa4fed26eb20a287346995bb37f552179780ea447d",
    },
    "remote_config": {
        "snapshot": "70397539d8e0fd41102387f32a29f947f29b629cbbfddbd9b20b660b40ca27c4",
        "state": "5343df1b58f0f595133261cdff705d720dc2e2c561e6d01cd69263060680a0c9",
        "trace": "4f45743cdc5af05bbdb795026d2e15a76c502c37d46c649a5ba08347efd00509",
        "rollout": "24df98a3b2058d746bbbec24af41299acc9d84ea2b3d102cee4efbb56de69a98",
    },
    "content_delivery": {
        "bundle": "2c424688f078fce0d936ef7ec1a5a366c0f8a227601154c0d9f21f0f3cad4aea",
        "channel": "3727bd7357173626e7e8adc7c9847cd04c34ee84674a1cc817558503f35da9f7",
        "state": "777e94990f33d32d7a03095957ea0a200dec4c9a4ff8241c1bea6bf3e9b19c62",
        "trace": "f017e23985f805856801b613904d272cb71396daa5692688159f2366a2c43711",
    },
    "event_pipeline": {
        "event": "41475424fc7aff50871beeca5335e30e520e0855e7769daea7e42990eb4b77ec",
        "checkpoint": "f08c139275b3256f368253f7f7937e3da8d77e356e9cd066b01e0dca5a48df21",
        "state": "8efdb02adaa57c732d492b0d54eebe8b4a581877864bff3a352fa651c85439c7",
        "trace": "9437f5415724c4f299bcea79da5201a46b59c17b250d2c4a40d4bf18410c4d9a",
    },
    "liveops": {
        "season": "b248ec4595a757731318705d498d7275aa25cb80416308025b7bf5d318d67e34",
        "campaign": "f8a37a0dcd545f3fae4d13092c4e443d753dba96e6cdd6d6f0e6452ca6295183",
        "state": "d24bfdaec041971f4270c46d8ffe60740432bf6805ea63d69857abe6d65f7aa5",
        "trace": "1c0d7d7fd2cb50397c5783faf29ed518a7dea15a39b9463889f5db91129f43e5",
    },
    "resilience": {
        "degraded_health": "6013bc39f146bc5e564f62cfa9367c9cbde619214dd391879204e43f13df838d",
        "backup": "53141385e61fcd1054ab58bb3339777034f058573e9da6f03fbda1eb26445747",
        "restore": "464b5105d0113d69ecf6ad47618e7e47e4930cd690e606a5f7e6701212a3a6cf",
        "operations": "81f49a0c335a0f6dacd94017dcd82a74bc2eb9825e26c98bb1ca7d1c58532718",
    },
    "liveops_ux": {
        "catalog": "f0ac90c20d06d7e6ffdff22756bf65499c5e9d839098fb51ec8a7f1738dc351b",
        "preview": "ff1089d254637027bd959a669cae6b3cc6f82252c2c1883cb24c1878fe418719",
        "authorized_mutation": "c809c93458f425b48a7546afc78bd21dff3b412a6a17c3ba203d1c615cdc8c13",
    },
}


def _validate_sha(source_sha: str) -> None:
    if len(source_sha) != 40 or any(ch not in "0123456789abcdef" for ch in source_sha):
        raise SystemExit("source SHA must be a lowercase 40-character Git SHA")


def _auth_fixture() -> bool:
    realm = AuthRealmIdentity(
        realm_id="r14-17-test",
        issuer="http://127.0.0.1:9417",
        environment=BackendEnvironmentKind.TEST,
    )
    client = AuthClientPolicy(
        client_id="r14-17-native",
        client_kind=AuthClientKind.NATIVE_PUBLIC,
        redirect_uris=("http://127.0.0.1:9417/callback",),
        allowed_audiences=("kodepoia-r14",),
    )
    provider = LocalAuthProvider(
        realm,
        client,
        fixture_secret=b"r14.17 deterministic local fixture secret only",
    )
    account = provider.account_for_subject("integrated-player")
    session = provider.create_session(account, now=2_000_000)
    safe = json.dumps(
        {"account": account.canonical(), "session": session.safe_canonical()},
        sort_keys=True,
    )
    return (
        account.realm_id == realm.realm_id
        and session.account_id == account.account_id
        and "fixture secret" not in safe
        and "bearer" not in safe.lower()
    )


def _run_service(root: Path, label: str, relative_script: str, source_sha: str, output_dir: Path) -> dict[str, Any]:
    output = output_dir / f"{label}.json"
    env = os.environ.copy()
    completed = subprocess.run(
        [sys.executable, str(root / relative_script), "--source-sha", source_sha, "--output", str(output)],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"integrated service acceptance failed: {label}")
    payload = json.loads(output.read_text(encoding="utf-8"))
    if payload.get("source_sha") != source_sha or payload.get("status") != "pass":
        raise RuntimeError(f"integrated service evidence mismatch: {label}")
    checks = payload.get("checks")
    if not isinstance(checks, dict) or not checks or any(value is not True for value in checks.values()):
        raise RuntimeError(f"integrated service checks are incomplete: {label}")
    for forbidden_flag in (
        "provider_live_claim",
        "secrets_exposed",
        "pii_exposed",
        "raw_payloads_exposed",
        "internet_scale_claim",
        "multi_region_claim",
        "automatic_production_publish",
    ):
        if payload.get(forbidden_flag) is True:
            raise RuntimeError(f"integrated service overclaim: {label}:{forbidden_flag}")
    return payload


def _assert_pinned_runtime_digests(reports: dict[str, dict[str, Any]]) -> None:
    postgres = reports["postgres"]
    if postgres.get("migration_plan_digest") != FROZEN_ACCEPTANCE_DIGESTS["postgres"]["migration_plan"]:
        raise RuntimeError("PostgreSQL migration semantic digest drift")
    if postgres.get("restore_digest") != FROZEN_ACCEPTANCE_DIGESTS["postgres"]["restore"]:
        raise RuntimeError("PostgreSQL restore semantic digest drift")

    authority = reports["authority"]
    if authority.get("final_state", {}).get("digest") != FROZEN_ACCEPTANCE_DIGESTS["authority"]["state"]:
        raise RuntimeError("authority state semantic digest drift")
    if authority.get("events", {}).get("digest") != FROZEN_ACCEPTANCE_DIGESTS["authority"]["events"]:
        raise RuntimeError("authority event semantic digest drift")
    if authority.get("trace_digest") != FROZEN_ACCEPTANCE_DIGESTS["authority"]["trace"]:
        raise RuntimeError("authority trace semantic digest drift")

    matchmaking = reports["matchmaking"]
    for field, key in (("state_digest", "state"), ("reservation_digest", "reservation"), ("trace_digest", "trace")):
        if matchmaking.get(field) != FROZEN_ACCEPTANCE_DIGESTS["matchmaking"][key]:
            raise RuntimeError(f"matchmaking semantic digest drift: {field}")

    cloud = reports["cloud_save"]
    for field, key in (
        ("state_digest", "state"),
        ("current_revision_digest", "revision"),
        ("resolved_conflict_digest", "conflict"),
    ):
        if cloud.get(field) != FROZEN_ACCEPTANCE_DIGESTS["cloud_save"][key]:
            raise RuntimeError(f"cloud-save semantic digest drift: {field}")

    progression = reports["progression"]
    for field, key in (("definition_digest", "definition"), ("state_digest", "state"), ("trace_digest", "trace")):
        if progression.get(field) != FROZEN_ACCEPTANCE_DIGESTS["progression"][key]:
            raise RuntimeError(f"progression semantic digest drift: {field}")

    entitlements = reports["entitlements"]
    for field, key in (
        ("catalog_digest", "catalog"),
        ("state_digest", "state"),
        ("trace_digest", "trace"),
        ("provider_event_digest", "provider_event"),
    ):
        if entitlements.get(field) != FROZEN_ACCEPTANCE_DIGESTS["entitlements"][key]:
            raise RuntimeError(f"entitlement semantic digest drift: {field}")


def build(source_sha: str, root: Path) -> dict[str, Any]:
    _validate_sha(source_sha)
    auth_ok = _auth_fixture()
    # Nested subdivision acceptance scripts are repository-governed and some (R14.16)
    # explicitly refuse output paths outside the workspace. Keep ephemeral evidence
    # inside the checked-out repository and remove it atomically with the temporary dir.
    with tempfile.TemporaryDirectory(prefix=".r14-17-integrated-", dir=root) as directory:
        output_dir = Path(directory)
        reports = {
            label: _run_service(root, label, script, source_sha, output_dir)
            for label, script in SERVICE_SCRIPTS
        }
    _assert_pinned_runtime_digests(reports)

    service_runs = {
        label: {
            "status": "pass",
            "check_count": len(payload["checks"]),
            "all_checks_pass": all(payload["checks"].values()),
        }
        for label, payload in reports.items()
    }
    checks = {
        "local_auth_account_session": auth_ok,
        "postgresql_authoritative_persistence": service_runs["postgres"]["all_checks_pass"],
        "authoritative_server_boundary": service_runs["authority"]["all_checks_pass"],
        "lobby_reservation_reconnect": service_runs["matchmaking"]["all_checks_pass"],
        "cloud_save_conflict_rollback": service_runs["cloud_save"]["all_checks_pass"],
        "progression_authoritative_events": service_runs["progression"]["all_checks_pass"],
        "billing_duplicate_out_of_order": service_runs["entitlements"]["all_checks_pass"],
        "stable_feature_rollout_rollback": service_runs["remote_config"]["all_checks_pass"],
        "immutable_content_cache_rollback": service_runs["content_delivery"]["all_checks_pass"],
        "event_dedupe_checkpoint_replay": service_runs["event_pipeline"]["all_checks_pass"],
        "liveops_preview_activate_pause_rollback": service_runs["liveops"]["all_checks_pass"],
        "dependency_failure_recovery": service_runs["resilience"]["all_checks_pass"],
        "governed_cli_kodestudio_surface": service_runs["liveops_ux"]["all_checks_pass"],
        "provider_live_and_sensitive_claims_fail_closed": all(
            report.get("provider_live_claim") is not True
            and report.get("secrets_exposed") is not True
            and report.get("pii_exposed") is not True
            for report in reports.values()
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"R14.17 integrated checks failed: {[name for name, ok in checks.items() if not ok]}")

    frozen_digest = canonical_sha256(FROZEN_ACCEPTANCE_DIGESTS)
    return {
        "schema_version": 1,
        "status": "pass",
        "source_sha": source_sha,
        "checks": checks,
        "service_runs": service_runs,
        "frozen_acceptance_digests": FROZEN_ACCEPTANCE_DIGESTS,
        "frozen_acceptance_digest": frozen_digest,
        "manual_state": "conditional_not_triggered",
        "provider_live_claim": False,
        "external_provider_required": False,
        "secrets_exposed": False,
        "pii_exposed": False,
        "production_publish_claim": False,
        "internet_scale_claim": False,
        "multi_region_claim": False,
        "blockers": [],
    }


def _sanitized_failure(source_sha: str, exc: Exception) -> dict[str, Any]:
    message = str(exc).strip() or exc.__class__.__name__
    # All raised integration messages are deliberately label/digest-only. Defense in
    # depth still suppresses URL-like or credential-shaped diagnostics.
    lowered = message.lower()
    if "://" in message or any(token in lowered for token in ("password", "secret", "token=", "dsn=")):
        message = exc.__class__.__name__
    return {
        "schema_version": 1,
        "status": "fail",
        "source_sha": source_sha,
        "manual_state": "conditional_not_triggered",
        "provider_live_claim": False,
        "external_provider_required": False,
        "secrets_exposed": False,
        "pii_exposed": False,
        "production_publish_claim": False,
        "internet_scale_claim": False,
        "multi_region_claim": False,
        "blockers": [message[:512]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exact-head R14.17 integrated adversarial acceptance.")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)

    return_code = 0
    try:
        payload = build(args.source_sha, root)
    except Exception as exc:
        payload = _sanitized_failure(args.source_sha, exc)
        return_code = 1

    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "source_sha": payload["source_sha"],
        "blockers": payload.get("blockers", []),
        "check_count": len(payload.get("checks", {})),
        "frozen_acceptance_digest": payload.get("frozen_acceptance_digest"),
        "output": output.relative_to(root).as_posix(),
    }, indent=2, sort_keys=True))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
