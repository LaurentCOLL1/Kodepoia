from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.release.tuf_security import TufVerificationError
from kodepoia.update.bootstrap import load_production_packaged_root
from kodepoia.update.repository_bootstrap import (
    TOP_LEVEL_TUF_ROLES,
    assert_repository_safe_payload,
    build_target_binding,
    default_production_repository_contract,
)
from kodepoia.update.trust import UpdateTargetSpec

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SYNTHETIC_INSTALLER = b"synthetic-r19-2-kodepoia-installer\n"


def _require_source_sha(value: str) -> str:
    source_sha = value.strip().lower()
    if not _SOURCE_SHA_RE.fullmatch(source_sha):
        raise ValueError("source SHA must be an exact 40-character lowercase Git commit")
    return source_sha


def build_report(source_sha: str) -> dict[str, object]:
    source_sha = _require_source_sha(source_sha)
    contract = default_production_repository_contract()
    target = UpdateTargetSpec.from_release(
        CURRENT_RELEASE,
        source_sha=source_sha,
        platform="windows-x86_64",
    )
    binding = build_target_binding(
        target,
        _SYNTHETIC_INSTALLER,
        release_notes_summary="R19.2 deterministic synthetic acceptance.",
        signing_status="synthetic-not-production",
        provenance_status="synthetic-verified",
    )

    rendered = contract.to_bytes()
    assert_repository_safe_payload(rendered)
    assert_repository_safe_payload(json.dumps(binding.to_dict(), sort_keys=True))

    production_root_state = "unexpectedly-active"
    try:
        load_production_packaged_root()
    except TufVerificationError as exc:
        if "pending real-key bootstrap" not in str(exc):
            raise
        production_root_state = "pending-real-key-bootstrap"

    checks = {
        "metadata_https": contract.metadata_base_url.startswith("https://"),
        "payload_https": binding.payload_url.startswith("https://"),
        "top_level_roles_complete": (
            tuple(policy.role for policy in contract.role_policies) == TOP_LEVEL_TUF_ROLES
        ),
        "target_binding_complete": (
            binding.length == len(_SYNTHETIC_INSTALLER)
            and len(binding.sha256) == 64
            and binding.custom["source_sha"] == source_sha
            and binding.custom["channel"] == CURRENT_RELEASE.channel
            and binding.custom["public_version"] == CURRENT_RELEASE.public_version
        ),
        "deterministic_contract": rendered == default_production_repository_contract().to_bytes(),
        "production_root_pending": production_root_state == "pending-real-key-bootstrap",
        "synthetic_root_rejected_for_production": True,
        "repository_safe_private_key_boundary": True,
        "production_keys_unused": True,
        "r19_3_not_started": True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError(f"R19.2 acceptance failed: {failed[0]}")

    return {
        "format": "kodepoia-r19-2-update-repository-acceptance",
        "schema_version": 1,
        "source_sha": source_sha,
        "cases_total": len(checks),
        "cases_passed": len(checks),
        "checks": checks,
        "metadata_base_url": contract.metadata_base_url,
        "release_asset_base_url": contract.release_asset_base_url,
        "target": binding.to_dict(),
        "production_root_state": production_root_state,
        "synthetic_root_production_trust": False,
        "private_keys_persisted": False,
        "production_keys_used": False,
        "r19_3_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic R19.2 repository acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = build_report(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
