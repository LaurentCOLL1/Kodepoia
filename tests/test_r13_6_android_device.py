from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from kodepoia.mobile.android_device import (
    AndroidAdbState,
    AndroidDeviceAcceptanceEvidence,
    AndroidDeviceCapabilitySnapshot,
    AndroidDeviceLease,
    AndroidDeviceMatrixEntry,
    AndroidDeviceObservation,
    AndroidInstrumentationResult,
    AndroidNetworkProfile,
    AndroidOrientation,
    build_adb_getprop_argv,
    build_adb_instrument_argv,
    build_adb_logcat_argv,
    parse_adb_devices,
    parse_instrumentation_output,
    select_single_online_emulator,
)

ROOT = Path(__file__).resolve().parents[1]
A = "11" * 32
B = "22" * 32
C = "33" * 32


def _observation(serial: str = "emulator-5554", state: AndroidAdbState = AndroidAdbState.DEVICE):
    return AndroidDeviceObservation(
        serial=serial,
        state=state,
        product="sdk_phone_x86_64",
        model="sdk_gphone64_x86_64",
        device="emu64xa",
        transport_id="1",
    )


def _snapshot(device_sha: str) -> AndroidDeviceCapabilitySnapshot:
    return AndroidDeviceCapabilitySnapshot(
        device_sha256=device_sha,
        state=AndroidAdbState.DEVICE,
        virtual=True,
        boot_completed=True,
        os_version="16",
        model="sdk_gphone64_x86_64",
        abi="x86_64",
        locale="en-US",
        density_dpi=420,
    )


def test_r13_6_adb_listing_parses_state_and_redacts_serial() -> None:
    output = """List of devices attached
emulator-5554 device product:sdk_phone_x86_64 model:sdk_gphone64_x86_64 device:emu64xa transport_id:1
physical123 offline product:foo model:bar device:baz transport_id:2
"""
    devices = parse_adb_devices(output)
    assert len(devices) == 2
    emulator = next(item for item in devices if item.virtual)
    assert emulator.state is AndroidAdbState.DEVICE
    assert emulator.public_dict()["device_sha256"] == emulator.device_sha256
    assert "serial" not in emulator.public_dict()
    assert "emulator-5554" not in json.dumps(emulator.public_dict(), sort_keys=True)


def test_r13_6_requires_exactly_one_online_emulator() -> None:
    selected = select_single_online_emulator((_observation(),))
    assert selected.serial == "emulator-5554"
    with pytest.raises(ValueError, match="exactly one"):
        select_single_online_emulator((_observation(), _observation("emulator-5556")))
    with pytest.raises(ValueError, match="exactly one"):
        select_single_online_emulator((_observation(state=AndroidAdbState.OFFLINE),))


def test_r13_6_lease_rejects_stale_wrong_device_and_artifact_substitution() -> None:
    observed = _observation()
    lease = AndroidDeviceLease("r13.6-lease", observed.device_sha256, A)
    lease.assert_matches(observed, A)
    with pytest.raises(ValueError, match="stale/offline"):
        lease.assert_matches(_observation(state=AndroidAdbState.OFFLINE), A)
    with pytest.raises(ValueError, match="wrong-device"):
        lease.assert_matches(_observation("emulator-5556"), A)
    with pytest.raises(ValueError, match="artifact substitution"):
        lease.assert_matches(observed, B)


def test_r13_6_adb_argv_is_typed_and_shell_surface_is_fixed() -> None:
    instrument = build_adb_instrument_argv(
        "/opt/android/platform-tools/adb",
        "emulator-5554",
        "com.kodepoia.r13acceptance.test/androidx.test.runner.AndroidJUnitRunner",
    )
    assert instrument[-5:] == (
        "am",
        "instrument",
        "-w",
        "-r",
        "com.kodepoia.r13acceptance.test/androidx.test.runner.AndroidJUnitRunner",
    )
    assert instrument[3:5] == ("shell", "am")
    with pytest.raises(ValueError, match="property is not allowlisted"):
        build_adb_getprop_argv("adb", "emulator-5554", "ro.evil.inject")
    with pytest.raises(ValueError, match="component is invalid"):
        build_adb_instrument_argv("adb", "emulator-5554", "sh -c whoami")
    with pytest.raises(ValueError, match="line limit"):
        build_adb_logcat_argv("adb", "emulator-5554", line_limit=50_000)


def test_r13_6_instrumentation_parser_is_fail_closed() -> None:
    passed = parse_instrumentation_output(b"Time: 0.321\n\nOK (1 test)\nINSTRUMENTATION_CODE: -1\n")
    assert passed.passed is True
    assert passed.tests_run == 1
    failed = parse_instrumentation_output(b"FAILURES!!!\nTests run: 1, Failures: 1\n")
    assert failed.passed is False
    assert failed.tests_run == 0


def test_r13_6_evidence_cannot_claim_physical_device_from_emulator() -> None:
    observed = _observation()
    snapshot = _snapshot(observed.device_sha256)
    lease = AndroidDeviceLease("r13.6-hosted", observed.device_sha256, A)
    instrumentation = AndroidInstrumentationResult(True, 1, B)
    matrix = (
        AndroidDeviceMatrixEntry(
            "en-US",
            AndroidOrientation.PORTRAIT,
            420,
            AndroidNetworkProfile.DEFAULT,
        ),
    )
    evidence = AndroidDeviceAcceptanceEvidence(
        schema_version=1,
        source_sha="a" * 40,
        runner_os="Linux",
        snapshot=snapshot,
        lease=lease,
        test_apk_sha256=C,
        test_overlay_sha256=B,
        matrix=matrix,
        instrumentation=instrumentation,
        logcat_sha256=A,
        logcat_lines=20,
        cleanup_complete=True,
    )
    assert evidence.to_dict()["physical_device_claim"] is False
    with pytest.raises(ValueError, match="physical-device claim"):
        AndroidDeviceAcceptanceEvidence(
            schema_version=1,
            source_sha="a" * 40,
            runner_os="Linux",
            snapshot=snapshot,
            lease=lease,
            test_apk_sha256=C,
            test_overlay_sha256=B,
            matrix=matrix,
            instrumentation=instrumentation,
            logcat_sha256=A,
            logcat_lines=20,
            cleanup_complete=True,
            physical_device_claim=True,
        )


def test_r13_6_evidence_schema_is_strict_and_matches_model() -> None:
    schema = json.loads(
        (ROOT / "schemas/r13/android-device-evidence.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    observed = _observation()
    payload = AndroidDeviceAcceptanceEvidence(
        schema_version=1,
        source_sha="b" * 40,
        runner_os="Linux",
        snapshot=_snapshot(observed.device_sha256),
        lease=AndroidDeviceLease("r13.6-hosted", observed.device_sha256, A),
        test_apk_sha256=C,
        test_overlay_sha256=B,
        matrix=(AndroidDeviceMatrixEntry("en-US", AndroidOrientation.PORTRAIT, 420),),
        instrumentation=AndroidInstrumentationResult(True, 1, B),
        logcat_sha256=A,
        logcat_lines=10,
        cleanup_complete=True,
    ).to_dict()
    Draft202012Validator(schema).validate(payload)
    payload["raw_serial"] = "emulator-5554"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)
