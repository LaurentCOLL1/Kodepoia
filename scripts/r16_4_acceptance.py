from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.core.secret_guard import (
    ArtifactLeakScanner,
    EphemeralSecretResolver,
    SecretAwareProcessSandbox,
    SecretDestinationPolicy,
    SecretTaintGuard,
)
from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend
from kodepoia.exceptions import PolicyDenied

ROOT = Path(__file__).resolve().parents[1]
CANARY = "KODEPOIA_SYNTHETIC_SECRET_R16_4_ACCEPTANCE_f1d2d2f924e9"
ROTATED = "KODEPOIA_SYNTHETIC_SECRET_R16_4_ROTATED_4a44dc153642"


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip().lower()


def _sha256_json(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _case(case_id: str, passed: bool, observed: str) -> dict[str, object]:
    return {
        "id": case_id,
        "passed": bool(passed),
        "observed": observed,
        "critical": True,
    }


def build_acceptance(source_sha: str) -> dict[str, object]:
    source = source_sha.strip().lower()
    actual = _git_head()
    if actual != source:
        raise ValueError(f"exact-source mismatch: expected {source}, got {actual}")

    secrets = KodeSecrets(MemorySecretBackend())
    secrets.store("r16.4", "acceptance", CANARY)
    guard = SecretTaintGuard(secrets)
    ref = secrets.ref("r16.4", "acceptance")
    cases: list[dict[str, object]] = []

    encoded = base64.b64encode(CANARY.encode()).decode()
    double_encoded = base64.b64encode(encoded.encode()).decode()
    redacted = guard.redact_text(f"raw={CANARY};b64={encoded};double={double_encoded}")
    cases.append(
        _case(
            "R16.4.ACC.ENCODED_REDACTION",
            CANARY not in redacted and encoded not in redacted and double_encoded not in redacted,
            "raw+encoded-redacted",
        )
    )

    sanitized_payload = guard.sanitize_payload(
        {
            "credential_ref": ref,
            "api_key": "unregistered-sensitive-field",
            "message": f"failure {CANARY}",
        }
    )
    serialized_payload = json.dumps(sanitized_payload, sort_keys=True)
    cases.append(
        _case(
            "R16.4.ACC.DURABLE_REF_ONLY",
            CANARY not in serialized_payload
            and sanitized_payload["credential_ref"] == {"namespace": "r16.4", "key": "acceptance"}
            and sanitized_payload["api_key"] == "<redacted-secret>",
            "reference-preserved-material-redacted",
        )
    )

    argv_denied = False
    try:
        guard.assert_safe_argv(["tool", "--token", CANARY])
    except PolicyDenied:
        argv_denied = True
    cases.append(_case("R16.4.ACC.ARGV_DENY", argv_denied, "denied" if argv_denied else "allowed"))

    env_denied = False
    try:
        guard.assert_safe_environment({"TOKEN": CANARY})
    except PolicyDenied:
        env_denied = True
    cases.append(_case("R16.4.ACC.ENV_DENY", env_denied, "denied" if env_denied else "allowed"))

    destination_policy = SecretDestinationPolicy(approved_hosts=["api.example.test"])
    exfil_denied = False
    try:
        destination_policy.authorize(
            "https://unapproved.example.test/upload",
            {"payload": CANARY},
            guard,
            allow_secret_payload=True,
        )
    except PolicyDenied:
        exfil_denied = True
    cases.append(
        _case(
            "R16.4.ACC.EXFIL_DESTINATION_DENY",
            exfil_denied,
            "denied" if exfil_denied else "allowed",
        )
    )

    approved_delivery = True
    try:
        destination_policy.authorize(
            "https://api.example.test/upload",
            {"payload": CANARY},
            guard,
            allow_secret_payload=True,
        )
    except PolicyDenied:
        approved_delivery = False
    cases.append(
        _case(
            "R16.4.ACC.EXPLICIT_APPROVED_DELIVERY",
            approved_delivery,
            "authorized" if approved_delivery else "denied",
        )
    )

    resolver = EphemeralSecretResolver(secrets, guard)
    first = resolver.resolve(ref)
    secrets.backend.set("r16.4", "acceptance", ROTATED)
    second = resolver.resolve(ref)
    rotated_redaction = guard.redact_text(f"old={first};new={second}")
    cases.append(
        _case(
            "R16.4.ACC.ROTATION_REFRESH",
            first == CANARY
            and second == ROTATED
            and CANARY not in rotated_redaction
            and ROTATED not in rotated_redaction,
            "resolver-refreshes-and-redacts-old+new",
        )
    )

    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-4-") as temp:
        root = Path(temp)
        executable = Path(sys.executable).name.lower()
        protected = SecretAwareProcessSandbox(
            ProcessSandbox(root, allowed_executables={executable}),
            secrets,
            guard,
        )
        process = protected.run(
            [
                sys.executable,
                "-c",
                "import os,sys; v=os.environ['R16_SECRET']; print(v); print(v, file=sys.stderr)",
            ],
            secret_env={"R16_SECRET": ref},
        )
        process_clean = (
            process.returncode == 0
            and CANARY not in process.stdout
            and CANARY not in process.stderr
            and ROTATED not in process.stdout
            and ROTATED not in process.stderr
            and "<redacted-secret>" in process.stdout
            and "<redacted-secret>" in process.stderr
        )
        cases.append(
            _case(
                "R16.4.ACC.NARROW_PROCESS_RESOLUTION",
                process_clean,
                "captured-output-redacted" if process_clean else "secret-visible",
            )
        )

        (root / "clean.json").write_text('{"status":"ok"}\n', encoding="utf-8")
        (root / "leaky.log").write_text(
            base64.b64encode(ROTATED.encode()).decode() + "\n",
            encoding="utf-8",
        )
        report = ArtifactLeakScanner(guard).scan(root)
        report_text = json.dumps(report.to_dict(), sort_keys=True)
        artifact_safe_evidence = (
            not report.clean
            and any(item.location == "leaky.log" for item in report.leaks)
            and CANARY not in report_text
            and ROTATED not in report_text
        )
        cases.append(
            _case(
                "R16.4.ACC.ARTIFACT_LEAK_SCAN",
                artifact_safe_evidence,
                "leak-location-only" if artifact_safe_evidence else "unsafe-artifact-evidence",
            )
        )

    exception_text = guard.sanitize_exception(RuntimeError(f"credential={ROTATED}"))
    cases.append(
        _case(
            "R16.4.ACC.FAILURE_DIAGNOSTICS",
            exception_text.startswith("RuntimeError:") and ROTATED not in exception_text,
            "useful-redacted-diagnostic",
        )
    )

    passed = all(bool(item["passed"]) for item in cases)
    payload: dict[str, object] = {
        "schema_version": 1,
        "phase": "R16.4",
        "title": "Secrets, privacy and exfiltration hardening",
        "source_sha": source,
        "manual_state": "NONE",
        "synthetic_only": True,
        "live_secrets": False,
        "destructive_actions": False,
        "network_calls_performed": False,
        "security_claim": True,
        "critical_veto": not passed,
        "status": "PASS" if passed else "FAIL",
        "cases": cases,
    }
    payload["semantic_sha256"] = _sha256_json(payload)
    serialized = json.dumps(payload, sort_keys=True)
    if CANARY in serialized or ROTATED in serialized:
        raise RuntimeError("synthetic secret canary leaked into durable acceptance payload")
    if not passed:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit exact-source R16.4 secret-hardening acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = build_acceptance(args.source_sha)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
