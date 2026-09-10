from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from securesystemslib.signer import SSlibKey

from kodepoia.update.online_signing import OnlineSignerConfig, resolve_online_signers
from kodepoia.update.zero_cost_signing import (
    ZERO_COST_PROVIDER,
    GitHubEnvironmentSecretResolver,
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _config_from_public_manifest(role: str, entry: dict[str, object]) -> OnlineSignerConfig:
    public_key = entry.get("public_key")
    if not isinstance(public_key, dict):
        raise ValueError(f"missing public key for {role}")
    keyval = public_key.get("keyval")
    if not isinstance(keyval, dict) or not isinstance(keyval.get("public"), str):
        raise ValueError(f"invalid public key payload for {role}")
    crypto_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(keyval["public"]))
    sslib_key = SSlibKey.from_crypto(crypto_key)
    expected_keyid = entry.get("keyid")
    if sslib_key.keyid != expected_keyid:
        raise ValueError(f"public keyid mismatch for {role}")
    secret_name = entry.get("secret_name")
    if not isinstance(secret_name, str):
        raise ValueError(f"missing secret resource for {role}")
    return OnlineSignerConfig(
        role=role,
        provider=ZERO_COST_PROVIDER,
        resource=secret_name,
        public_key=sslib_key,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the two live R20.3 GitHub environment secrets without publication."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument(
        "--public-keys",
        type=Path,
        default=Path("docs/roadmap/R20_3_PUBLIC_KEYS.json"),
    )
    args = parser.parse_args()

    source_sha = args.source_sha.strip().lower()
    if not _SHA_RE.fullmatch(source_sha):
        raise SystemExit("source SHA must be exactly 40 lowercase hexadecimal characters")

    manifest = json.loads(args.public_keys.read_text(encoding="utf-8"))
    if manifest.get("provider") != ZERO_COST_PROVIDER:
        raise SystemExit("public manifest provider mismatch")
    if manifest.get("environment") != "tuf-production-signing":
        raise SystemExit("public manifest environment mismatch")

    snapshot = _config_from_public_manifest("snapshot", manifest["snapshot"])
    timestamp = _config_from_public_manifest("timestamp", manifest["timestamp"])
    resolved = resolve_online_signers(
        [snapshot, timestamp],
        GitHubEnvironmentSecretResolver(),
    )

    challenge = f"kodepoia-r20.3-live-signing-challenge:{source_sha}".encode("ascii")
    snapshot_signature = resolved.snapshot.sign(challenge)
    timestamp_signature = resolved.timestamp.sign(challenge)
    snapshot.public_key.verify_signature(snapshot_signature, challenge)
    timestamp.public_key.verify_signature(timestamp_signature, challenge)

    report = {
        "format": "kodepoia-r20-3-live-signing-challenge",
        "schema_version": 1,
        "source_sha": source_sha,
        "challenge_sha256": hashlib.sha256(challenge).hexdigest(),
        "snapshot": snapshot_signature.to_dict(),
        "timestamp": timestamp_signature.to_dict(),
        "snapshot_keyid": snapshot.keyid,
        "timestamp_keyid": timestamp.keyid,
        "distinct_online_keys": snapshot.keyid != timestamp.keyid,
        "signatures_verified": True,
        "secret_values_emitted": False,
        "artifact_storage_used": False,
        "production_effect": False,
        "status": "pass",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
