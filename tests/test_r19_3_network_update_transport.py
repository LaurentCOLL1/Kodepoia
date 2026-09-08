from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from kodepoia.update.network import NetworkTransportPolicy, NetworkUpdateTransport
from kodepoia.update.startup import (
    PowerShellAuthenticodeVerifier,
    build_packaged_update_services,
)
from kodepoia.update.trust import UpdateTransportError, UpdateTransportOffline

SOURCE_SHA = "a" * 40
TARGET_PATH = f"channels/beta/windows-x86_64/1.1.0-rc2/{SOURCE_SHA}/KodepoiaSetup.exe"
PRODUCTION_ROOT_SHA256 = "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"


class FakeResponse:
    def __init__(self, status: int, data: bytes = b"", *, headers: dict[str, str] | None = None):
        self.status = status
        self.headers = {key.lower(): value for key, value in (headers or {}).items()}
        self._data = data
        self._offset = 0
        self.released = False

    def read(self, amount: int, *, decode_content: bool = False) -> bytes:
        del decode_content
        if self._offset >= len(self._data):
            return b""
        chunk = self._data[self._offset : self._offset + amount]
        self._offset += len(chunk)
        return chunk

    def release_conn(self) -> None:
        self.released = True


class FakePool:
    def __init__(self, responses: list[FakeResponse | Exception] | None = None) -> None:
        self.responses = list(responses or [])
        self.requests: list[str] = []

    def request(self, method: str, url: str, **kwargs):
        assert method == "GET"
        assert kwargs["redirect"] is False
        assert kwargs["preload_content"] is False
        assert kwargs["retries"] is False
        self.requests.append(url)
        if not self.responses:
            raise AssertionError("unexpected network request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def policy(**kwargs) -> NetworkTransportPolicy:
    defaults = {
        "metadata_base_url": "https://updates.example.test/metadata/",
        "release_asset_base_url": "https://github.com/LaurentCOLL1/Kodepoia/releases/download/",
        "max_metadata_bytes": 64,
        "max_target_bytes": 128,
    }
    defaults.update(kwargs)
    return NetworkTransportPolicy(**defaults)


def test_metadata_allowlist_and_exact_url() -> None:
    pool = FakePool([FakeResponse(200, b"{}")])
    transport = NetworkUpdateTransport(policy(), pool=pool)
    assert transport.fetch_metadata("timestamp.json") == b"{}"
    assert pool.requests == ["https://updates.example.test/metadata/timestamp.json"]
    with pytest.raises(UpdateTransportError, match="not authorized"):
        transport.fetch_metadata("../targets.json")


def test_target_path_maps_only_to_canonical_release_asset() -> None:
    pool = FakePool([FakeResponse(200, b"installer")])
    transport = NetworkUpdateTransport(policy(), pool=pool)
    assert transport.fetch_target(TARGET_PATH) == b"installer"
    assert pool.requests == [
        "https://github.com/LaurentCOLL1/Kodepoia/releases/download/v1.1.0-rc2/KodepoiaSetup.exe"
    ]
    with pytest.raises(UpdateTransportError, match="canonical"):
        transport.fetch_target("../KodepoiaSetup.exe")


def test_metadata_redirect_cannot_escape_authorized_origin() -> None:
    pool = FakePool(
        [FakeResponse(302, headers={"Location": "https://evil.example.test/timestamp.json"})]
    )
    transport = NetworkUpdateTransport(policy(), pool=pool)
    with pytest.raises(UpdateTransportError, match="escaped"):
        transport.fetch_metadata("timestamp.json")


def test_github_asset_redirect_is_explicitly_allowed() -> None:
    redirected = (
        "https://release-assets.githubusercontent.com/github-production-release-asset/1/"
        "KodepoiaSetup.exe?sp=r"
    )
    pool = FakePool(
        [
            FakeResponse(302, headers={"Location": redirected}),
            FakeResponse(200, b"installer", headers={"Content-Length": "9"}),
        ]
    )
    transport = NetworkUpdateTransport(policy(), pool=pool)
    assert transport.fetch_target(TARGET_PATH) == b"installer"
    assert pool.requests[-1] == redirected


def test_size_ceilings_apply_to_declared_and_streamed_bytes() -> None:
    too_large = FakePool([FakeResponse(200, b"x", headers={"Content-Length": "65"})])
    transport = NetworkUpdateTransport(policy(), pool=too_large)
    with pytest.raises(UpdateTransportError, match="size ceiling"):
        transport.fetch_metadata("root.json")

    streamed = FakePool([FakeResponse(200, b"x" * 129)])
    transport = NetworkUpdateTransport(policy(), pool=streamed)
    with pytest.raises(UpdateTransportError, match="size ceiling"):
        list(transport.iter_target(TARGET_PATH, chunk_size=17))


def test_connect_timeout_maps_to_offline_state() -> None:
    from urllib3.exceptions import ConnectTimeoutError

    pool = FakePool([ConnectTimeoutError(None, "connect timed out")])
    transport = NetworkUpdateTransport(policy(), pool=pool)
    with pytest.raises(UpdateTransportOffline, match="offline or timed out"):
        transport.fetch_metadata("timestamp.json")


def test_packaged_service_construction_performs_zero_network_requests(tmp_path: Path) -> None:
    pool = FakePool()
    services = build_packaged_update_services(
        state_dir=tmp_path,
        platform_name="linux",
        transport_factory=lambda transport_policy: NetworkUpdateTransport(
            transport_policy,
            pool=pool,
        ),
    )
    assert pool.requests == []
    assert services.transport is not None
    assert services.discovery is not None
    assert services.installer is None
    assert services.discovery.verifier.root_pin.sha256 == PRODUCTION_ROOT_SHA256


def test_windows_packaged_startup_constructs_verified_install_service(tmp_path: Path) -> None:
    pool = FakePool()
    services = build_packaged_update_services(
        state_dir=tmp_path,
        platform_name="win32",
        transport_factory=lambda transport_policy: NetworkUpdateTransport(
            transport_policy,
            pool=pool,
        ),
    )
    assert pool.requests == []
    assert services.installer is not None
    assert services.installer.transport is services.transport


def test_powershell_authenticode_requires_valid_status(tmp_path: Path) -> None:
    path = tmp_path / "KodepoiaSetup.exe"
    path.write_bytes(b"fixture")

    def valid_runner(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess([], 0, "Valid|Signature verified", "")

    valid = PowerShellAuthenticodeVerifier(runner=valid_runner).verify(path)
    assert valid.verified is True
    assert valid.status == "valid"

    def invalid_runner(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess([], 0, "NotSigned|No signature", "")

    invalid = PowerShellAuthenticodeVerifier(runner=invalid_runner).verify(path)
    assert invalid.verified is False
    assert invalid.status == "notsigned"
