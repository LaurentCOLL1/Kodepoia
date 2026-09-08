from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from kodepoia.update.bootstrap import load_production_packaged_root
from kodepoia.update.network import (
    DEFAULT_METADATA_BASE_URL,
    DEFAULT_RELEASE_ASSET_BASE_URL,
    DEFAULT_TARGET_REDIRECT_HOSTS,
    TOP_LEVEL_METADATA,
    NetworkTransportPolicy,
    NetworkUpdateTransport,
)
from kodepoia.update.startup import PowerShellAuthenticodeVerifier, build_packaged_update_services
from kodepoia.update.trust import UpdateTransportError

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ROOT_SHA256 = "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"


class _Response:
    def __init__(self, status: int, data: bytes = b"", headers: dict[str, str] | None = None):
        self.status = status
        self.headers = {key.lower(): value for key, value in (headers or {}).items()}
        self.data = data
        self.offset = 0

    def read(self, amount: int, *, decode_content: bool = False) -> bytes:
        del decode_content
        chunk = self.data[self.offset : self.offset + amount]
        self.offset += len(chunk)
        return chunk

    def release_conn(self) -> None:
        return None


class _Pool:
    def __init__(self, responses: list[_Response] | None = None):
        self.responses = list(responses or [])
        self.requests: list[str] = []

    def request(self, method: str, url: str, **kwargs):
        assert method == "GET"
        assert kwargs["redirect"] is False
        self.requests.append(url)
        if not self.responses:
            raise AssertionError("unexpected network request")
        return self.responses.pop(0)


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run_acceptance(source_sha: str) -> dict[str, object]:
    actual = _git_head()
    if actual != source_sha:
        raise RuntimeError(f"exact-source mismatch: expected {source_sha}, got {actual}")

    contract = json.loads((ROOT / "configs/update_transport_r19_3.json").read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}

    root = load_production_packaged_root()
    checks["production_root_active"] = root.production_trust_claim and not root.private_keys_persisted
    checks["production_root_exact_sha256"] = (
        hashlib.sha256(root.root_bytes).hexdigest() == PRODUCTION_ROOT_SHA256
    )
    checks["metadata_base_exact"] = contract["metadata_base_url"] == DEFAULT_METADATA_BASE_URL
    checks["release_asset_base_exact"] = (
        contract["release_asset_base_url"] == DEFAULT_RELEASE_ASSET_BASE_URL
    )
    checks["metadata_allowlist_exact"] = sorted(TOP_LEVEL_METADATA) == sorted(contract["metadata_names"])
    checks["redirect_hosts_exact"] = sorted(DEFAULT_TARGET_REDIRECT_HOSTS) == sorted(
        contract["target_redirect_hosts"]
    )

    no_network_pool = _Pool()
    services = build_packaged_update_services(
        state_dir=ROOT / ".r19-3-acceptance-state",
        platform_name="win32",
        transport_factory=lambda policy: NetworkUpdateTransport(policy, pool=no_network_pool),
    )
    checks["startup_zero_network"] = no_network_pool.requests == []
    checks["startup_discovery_wired"] = services.discovery is not None
    checks["windows_verified_install_wired"] = services.installer is not None
    checks["startup_exact_root_pin"] = services.discovery.verifier.root_pin.sha256 == PRODUCTION_ROOT_SHA256

    policy = NetworkTransportPolicy(max_metadata_bytes=8, max_target_bytes=16)
    redirected = (
        "https://release-assets.githubusercontent.com/github-production-release-asset/1/"
        "KodepoiaSetup.exe?sp=r"
    )
    target_path = "channels/beta/windows-x86_64/1.1.0-rc2/" + "a" * 40 + "/KodepoiaSetup.exe"
    pool = _Pool(
        [
            _Response(302, headers={"Location": redirected}),
            _Response(200, b"installer"),
        ]
    )
    transport = NetworkUpdateTransport(policy, pool=pool)
    checks["explicit_github_redirect_supported"] = transport.fetch_target(target_path) == b"installer"

    escaped = _Pool([_Response(302, headers={"Location": "https://example.invalid/root.json"})])
    escaped_transport = NetworkUpdateTransport(policy, pool=escaped)
    try:
        escaped_transport.fetch_metadata("root.json")
    except UpdateTransportError:
        checks["metadata_redirect_escape_rejected"] = True
    else:
        checks["metadata_redirect_escape_rejected"] = False

    try:
        transport.fetch_metadata("../root.json")
    except UpdateTransportError:
        checks["metadata_traversal_rejected"] = True
    else:
        checks["metadata_traversal_rejected"] = False

    def runner(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess([], 0, "Valid|Signature verified", "")

    auth = PowerShellAuthenticodeVerifier(runner=runner).verify(ROOT / "pyproject.toml")
    checks["authenticode_valid_gate"] = auth.verified and auth.status == "valid"
    checks["silent_install_not_authorized"] = contract["silent_install_authorized"] is False
    checks["r19_4_not_included"] = contract["r19_4_behavior_included"] is False

    failed = [name for name, passed in checks.items() if not passed]
    report = {
        "phase": "R19.3",
        "source_sha": source_sha,
        "checks": checks,
        "passed": len(checks) - len(failed),
        "total": len(checks),
        "failed": failed,
    }
    if failed:
        raise RuntimeError(json.dumps(report, sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    report = run_acceptance(args.source_sha)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
