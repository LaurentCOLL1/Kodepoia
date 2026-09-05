from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from kodepoia.release.signing import (
    SigningMode,
    SigningPolicy,
    SigningPolicyError,
    SubjectEvidence,
    build_signing_evidence,
    sha256_file,
    signtool_sign_args,
    signtool_verify_args,
)


def _run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _discover_signtool(explicit: str | None) -> str:
    if explicit:
        target = Path(explicit)
        if not target.is_file():
            raise SigningPolicyError(f"SignTool not found: {target}")
        return str(target)

    found = shutil.which("signtool.exe") or shutil.which("signtool")
    if found:
        return found

    roots: list[Path] = []
    for env_name in ("WindowsSdkDir", "ProgramFiles(x86)", "ProgramFiles"):
        value = os.environ.get(env_name)
        if value:
            root = Path(value)
            if env_name != "WindowsSdkDir":
                root = root / "Windows Kits" / "10" / "bin"
            roots.append(root)

    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        candidates.extend(item for item in root.glob("*/x64/signtool.exe") if item.is_file())
        direct = root / "x64" / "signtool.exe"
        if direct.is_file():
            candidates.append(direct)
    if not candidates:
        raise SigningPolicyError("Microsoft SignTool.exe was not found in PATH or Windows SDK locations")
    return str(sorted(set(candidates), key=lambda item: str(item), reverse=True)[0])


def _powershell_signature(subject: Path) -> dict[str, object]:
    escaped = str(subject.resolve()).replace("'", "''")
    script = (
        f"$s=Get-AuthenticodeSignature -LiteralPath '{escaped}'; "
        "[pscustomobject]@{"
        "status=[string]$s.Status;"
        "signer_subject=if($s.SignerCertificate){[string]$s.SignerCertificate.Subject}else{$null};"
        "signer_thumbprint=if($s.SignerCertificate){[string]$s.SignerCertificate.Thumbprint}else{$null};"
        "timestamp_subject=if($s.TimeStamperCertificate){[string]$s.TimeStamperCertificate.Subject}else{$null}"
        "}|ConvertTo-Json -Compress"
    )
    completed = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script])
    payload = json.loads(completed.stdout.strip())
    if not isinstance(payload, dict):
        raise SigningPolicyError(f"could not read Authenticode metadata for {subject}")
    return payload


def _signtool_version(signtool: str) -> str:
    escaped = str(Path(signtool).resolve()).replace("'", "''")
    script = f"(Get-Item -LiteralPath '{escaped}').VersionInfo.FileVersion"
    completed = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script])
    return completed.stdout.strip() or "unknown"


def _subject_evidence(
    signtool: str,
    subject: Path,
    *,
    require_signature: bool,
    pre_sign_sha256: str | None = None,
) -> SubjectEvidence:
    metadata = _powershell_signature(subject)
    verify = _run(signtool_verify_args(signtool, subject), check=False)
    verify_ok = verify.returncode == 0
    status = str(metadata.get("status") or "")
    timestamp_subject = metadata.get("timestamp_subject")
    timestamp_verified = bool(timestamp_subject) and verify_ok

    if require_signature and not verify_ok:
        raise SigningPolicyError(
            f"SignTool verification failed for {subject} with exit code {verify.returncode}: "
            f"{verify.stdout[-1200:]}"
        )
    if not require_signature and status.lower() != "notsigned":
        raise SigningPolicyError(f"unsigned subject unexpectedly reports Authenticode status {status!r}")

    return SubjectEvidence(
        filename=subject.name,
        sha256=sha256_file(subject),
        authenticode_status=status,
        signer_subject=(
            str(metadata["signer_subject"]) if metadata.get("signer_subject") is not None else None
        ),
        signer_thumbprint=(
            str(metadata["signer_thumbprint"]).replace(" ", "").upper()
            if metadata.get("signer_thumbprint") is not None
            else None
        ),
        timestamp_subject=(str(timestamp_subject) if timestamp_subject is not None else None),
        timestamp_verified=timestamp_verified,
        signtool_verified=verify_ok,
        pre_sign_sha256=pre_sign_sha256,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sign and verify exact-source Windows release subjects under the R18.4 policy."
    )
    parser.add_argument("--mode", choices=[mode.value for mode in SigningMode], required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--subject", action="append", required=True)
    parser.add_argument("--certificate-thumbprint")
    parser.add_argument("--timestamp-url")
    parser.add_argument("--signtool")
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-production", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    policy = SigningPolicy(
        SigningMode(args.mode),
        args.source_sha,
        timestamp_url=args.timestamp_url,
        certificate_thumbprint=args.certificate_thumbprint,
        production_enabled=args.allow_production,
    ).validated()

    subjects = [Path(value) for value in args.subject]
    for subject in subjects:
        if not subject.is_file() or subject.stat().st_size <= 0:
            raise SigningPolicyError(f"release signing subject is missing or empty: {subject}")

    signtool = _discover_signtool(args.signtool)
    pre_sign_digests: dict[Path, str] = {}

    if policy.mode is not SigningMode.UNSIGNED and not args.verify_only:
        for subject in subjects:
            resolved = subject.resolve()
            pre_sign_digests[resolved] = sha256_file(subject)
            completed = _run(signtool_sign_args(signtool, subject, policy), check=False)
            if completed.returncode != 0:
                raise SigningPolicyError(
                    f"SignTool signing failed for {subject} with exit code {completed.returncode}: "
                    f"{completed.stdout[-1200:]}"
                )

    evidence_subjects = [
        _subject_evidence(
            signtool,
            subject,
            require_signature=policy.mode is not SigningMode.UNSIGNED,
            pre_sign_sha256=pre_sign_digests.get(subject.resolve()),
        )
        for subject in subjects
    ]
    evidence = build_signing_evidence(
        policy,
        signtool_version=_signtool_version(signtool),
        subjects=evidence_subjects,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(evidence.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(evidence.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
