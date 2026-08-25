from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path

from jsonschema import Draft202012Validator

from kodepoia.mobile.android_device import (
    AndroidAdbState,
    AndroidDeviceAcceptanceEvidence,
    AndroidDeviceCapabilitySnapshot,
    AndroidDeviceLease,
    AndroidDeviceMatrixEntry,
    AndroidNetworkProfile,
    AndroidOrientation,
    build_adb_density_argv,
    build_adb_devices_argv,
    build_adb_emulator_kill_argv,
    build_adb_getprop_argv,
    build_adb_install_argv,
    build_adb_instrument_argv,
    build_adb_logcat_argv,
    build_adb_uninstall_argv,
    build_adb_wait_argv,
    parse_adb_devices,
    parse_instrumentation_output,
    select_single_online_emulator,
)
from kodepoia.mobile.contracts import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[1]
_METADATA = ".kodepoia/r13_6_device_metadata.json"
_SCHEMA = ROOT / "schemas/r13/android-device-evidence.schema.json"
_APP_ID = "com.kodepoia.r13acceptance"
_TEST_APP_ID = _APP_ID + ".test"
_RUNNER = "androidx.test.runner.AndroidJUnitRunner"
_COMPONENT = _TEST_APP_ID + "/" + _RUNNER
_TEST_SOURCE = "app/src/androidTest/java/com/kodepoia/r13acceptance/R13DeviceSmokeTest.kt"


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _tool(name: str) -> str:
    direct = shutil.which(name)
    if direct:
        return direct
    sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if sdk:
        suffix = ".exe" if os.name == "nt" else ""
        candidates: list[Path] = []
        if name == "adb":
            candidates.append(Path(sdk) / "platform-tools" / f"adb{suffix}")
        elif name == "emulator":
            candidates.append(Path(sdk) / "emulator" / f"emulator{suffix}")
        elif name == "avdmanager":
            bat = ".bat" if os.name == "nt" else ""
            candidates.append(Path(sdk) / "cmdline-tools" / "latest" / "bin" / f"avdmanager{bat}")
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
    raise SystemExit(f"required R13.6 Android tool is unavailable: {name}")


def _run(
    argv: tuple[str, ...] | list[str],
    *,
    timeout: int = 120,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        list(argv),
        input=None if input_text is None else input_text.encode("utf-8"),
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        raise SystemExit(f"fixed R13.6 command failed: {Path(argv[0]).name}")
    return completed


def _metadata_path(staging_root: Path) -> Path:
    return staging_root / _METADATA


def _controlled_overlay(staging_root: Path, source_sha: str) -> str:
    build_file = staging_root / "app/build.gradle.kts"
    if not build_file.is_file():
        raise SystemExit("R13.6 requires the exact R13.4 governed staging project")
    text = build_file.read_text(encoding="utf-8")
    runner_line = '        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"\n'
    if runner_line not in text:
        marker = "        targetSdk = 36\n"
        if text.count(marker) != 1:
            raise SystemExit("R13.6 could not identify the controlled targetSdk line")
        text = text.replace(marker, marker + runner_line, 1)
    deps_marker = "dependencies {\n"
    test_deps = (
        '    androidTestImplementation("androidx.test:runner:1.7.0")\n'
        '    androidTestImplementation("androidx.test.ext:junit:1.3.0")\n'
    )
    if test_deps not in text:
        if text.count(deps_marker) != 1:
            raise SystemExit("R13.6 could not identify the controlled dependencies block")
        text = text.replace(deps_marker, deps_marker + test_deps, 1)
    build_file.write_text(text, encoding="utf-8", newline="\n")

    test_path = staging_root / _TEST_SOURCE
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_source = f'''package {_APP_ID}

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class R13DeviceSmokeTest {{
    @Test
    fun packageContextIsCanonical() {{
        val appContext = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("{_APP_ID}", appContext.packageName)
    }}
}}
'''
    test_path.write_text(test_source, encoding="utf-8", newline="\n")

    files = []
    for relative in ("app/build.gradle.kts", _TEST_SOURCE):
        path = staging_root / relative
        files.append({"path": relative, "sha256": _sha(path.read_bytes())})
    payload = {
        "schema_version": 1,
        "source_sha": source_sha,
        "androidx_test_runner": "1.7.0",
        "androidx_test_ext_junit": "1.3.0",
        "files": files,
    }
    return _sha(canonical_json_bytes(payload))


def prepare(source_sha: str, staging_root: Path) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise SystemExit("source SHA must be exact lowercase 40-hex Git SHA")
    metadata_path = staging_root / ".kodepoia/r13_4_ci_metadata.json"
    if not metadata_path.is_file():
        raise SystemExit("R13.6 requires R13.4 exact-head staging metadata")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("source_sha") != source_sha:
        raise SystemExit("R13.4 staging source SHA does not match R13.6 source SHA")
    overlay_sha = _controlled_overlay(staging_root, source_sha)
    own = {
        "schema_version": 1,
        "source_sha": source_sha,
        "r13_4_overlay_manifest_sha256": metadata["overlay_manifest_sha256"],
        "test_overlay_sha256": overlay_sha,
        "application_id": _APP_ID,
        "test_application_id": _TEST_APP_ID,
        "instrumentation_component": _COMPONENT,
    }
    path = _metadata_path(staging_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(own, sort_keys=True), encoding="utf-8")
    print(json.dumps(own, indent=2))


def launch_emulator(avd_name: str, system_image: str, pid_file: Path, log_file: Path) -> None:
    if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", avd_name) is None:
        raise SystemExit("invalid bounded AVD name")
    if re.fullmatch(r"system-images;android-[0-9]+;google_apis;x86_64", system_image) is None:
        raise SystemExit("unsupported R13.6 system image identity")
    avdmanager = _tool("avdmanager")
    emulator = _tool("emulator")
    _run(
        [avdmanager, "create", "avd", "--force", "--name", avd_name, "--package", system_image],
        input_text="no\n",
        timeout=120,
    )
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("wb") as log_handle:
        process = subprocess.Popen(
            [
                emulator,
                "-avd",
                avd_name,
                "-no-window",
                "-no-audio",
                "-no-boot-anim",
                "-no-snapshot",
                "-wipe-data",
                "-gpu",
                "swiftshader_indirect",
            ],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(process.pid), encoding="ascii")
    print(json.dumps({"avd_name": avd_name, "pid": process.pid}))


def _discover_single_online_emulator(adb: str, timeout_seconds: int = 120):
    """Wait only for ADB registration; strict single-emulator selection remains enforced."""
    deadline = time.monotonic() + timeout_seconds
    last_states: tuple[str, ...] = ()
    while time.monotonic() < deadline:
        completed = _run(build_adb_devices_argv(adb), timeout=30, check=False)
        if completed.returncode == 0:
            observations = parse_adb_devices(completed.stdout.decode("utf-8", errors="replace"))
            online = [
                item
                for item in observations
                if item.virtual and item.state is AndroidAdbState.DEVICE
            ]
            if len(online) > 1:
                raise SystemExit("multiple online Android emulators detected during bounded discovery")
            if len(online) == 1:
                return select_single_online_emulator(observations)
            last_states = tuple(sorted(item.state.value for item in observations if item.virtual))
        time.sleep(1)
    state_text = ",".join(last_states) if last_states else "not-visible"
    raise SystemExit(f"R13.6 emulator did not register online in ADB: {state_text}")


def _getprop(adb: str, serial: str, prop: str) -> str:
    completed = _run(build_adb_getprop_argv(adb, serial, prop), timeout=30)
    return completed.stdout.decode("utf-8", errors="replace").strip()


def _wait_for_boot(adb: str, serial: str, timeout_seconds: int = 300) -> None:
    _run(build_adb_wait_argv(adb, serial), timeout=timeout_seconds)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _getprop(adb, serial, "sys.boot_completed") == "1":
            return
        time.sleep(2)
    raise SystemExit("R13.6 emulator did not complete boot within bounded timeout")


def _density(adb: str, serial: str) -> int:
    out = _run(build_adb_density_argv(adb, serial), timeout=30).stdout.decode(
        "utf-8", errors="replace"
    )
    matches = re.findall(r"[Dd]ensity:\s*([0-9]+)", out)
    if not matches:
        raise SystemExit("unable to parse bounded emulator density")
    return int(matches[-1])


def collect(staging_root: Path, output: Path) -> None:
    metadata = json.loads(_metadata_path(staging_root).read_text(encoding="utf-8"))
    source_sha = str(metadata["source_sha"])
    adb = _tool("adb")
    observation = _discover_single_online_emulator(adb)
    _wait_for_boot(adb, observation.serial)

    apk = staging_root / "app/build/outputs/apk/debug/app-debug.apk"
    test_apk = staging_root / "app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
    if not apk.is_file() or not test_apk.is_file():
        raise SystemExit("R13.6 requires main and instrumentation APK outputs")
    apk_sha = _sha(apk.read_bytes())
    test_apk_sha = _sha(test_apk.read_bytes())
    lease = AndroidDeviceLease(
        lease_id="r13.6-hosted-emulator",
        device_sha256=observation.device_sha256,
        artifact_sha256=apk_sha,
        timeout_seconds=300,
    )
    lease.assert_matches(observation, apk_sha)

    app_installed = False
    test_installed = False
    cleanup_complete = False
    instrumentation = None
    log_bytes = b""
    try:
        _run(build_adb_install_argv(adb, observation.serial, apk), timeout=120)
        app_installed = True
        lease.assert_matches(observation, apk_sha)
        _run(build_adb_install_argv(adb, observation.serial, test_apk), timeout=120)
        test_installed = True
        instrument = _run(
            build_adb_instrument_argv(adb, observation.serial, _COMPONENT),
            timeout=180,
            check=False,
        )
        instrumentation = parse_instrumentation_output(instrument.stdout + instrument.stderr)
        if instrument.returncode != 0 or not instrumentation.passed:
            raise SystemExit("R13.6 instrumentation did not pass")
        log_bytes = _run(
            build_adb_logcat_argv(adb, observation.serial, line_limit=500),
            timeout=30,
        ).stdout
    finally:
        test_ok = True
        app_ok = True
        if test_installed:
            test_ok = (
                _run(
                    build_adb_uninstall_argv(adb, observation.serial, _TEST_APP_ID),
                    timeout=60,
                    check=False,
                ).returncode
                == 0
            )
        if app_installed:
            app_ok = (
                _run(
                    build_adb_uninstall_argv(adb, observation.serial, _APP_ID),
                    timeout=60,
                    check=False,
                ).returncode
                == 0
            )
        cleanup_complete = test_ok and app_ok

    if instrumentation is None:
        raise SystemExit("R13.6 instrumentation result is unavailable")
    locale = _getprop(adb, observation.serial, "persist.sys.locale") or _getprop(
        adb, observation.serial, "ro.product.locale"
    )
    snapshot = AndroidDeviceCapabilitySnapshot(
        device_sha256=observation.device_sha256,
        state=AndroidAdbState.DEVICE,
        virtual=True,
        boot_completed=True,
        os_version=_getprop(adb, observation.serial, "ro.build.version.release"),
        model=_getprop(adb, observation.serial, "ro.product.model"),
        abi=_getprop(adb, observation.serial, "ro.product.cpu.abi"),
        locale=locale or "und",
        density_dpi=_density(adb, observation.serial),
    )
    matrix = (
        AndroidDeviceMatrixEntry(
            locale="en-US",
            orientation=AndroidOrientation.PORTRAIT,
            density_dpi=snapshot.density_dpi,
            network=AndroidNetworkProfile.DEFAULT,
        ),
    )
    evidence = AndroidDeviceAcceptanceEvidence(
        schema_version=1,
        source_sha=source_sha,
        runner_os=platform.system(),
        snapshot=snapshot,
        lease=lease,
        test_apk_sha256=test_apk_sha,
        test_overlay_sha256=str(metadata["test_overlay_sha256"]),
        matrix=matrix,
        instrumentation=instrumentation,
        logcat_sha256=_sha(log_bytes),
        logcat_lines=min(20_000, len(log_bytes.decode("utf-8", errors="replace").splitlines())),
        cleanup_complete=cleanup_complete,
        physical_device_claim=False,
    )
    payload = evidence.to_dict()
    if observation.serial in json.dumps(payload, sort_keys=True):
        raise SystemExit("raw ADB serial leaked into durable R13.6 evidence")
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(evidence.canonical_bytes() + b"\n")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def cleanup_emulator() -> None:
    adb = _tool("adb")
    completed = _run(build_adb_devices_argv(adb), timeout=30, check=False)
    if completed.returncode != 0:
        return
    try:
        observations = parse_adb_devices(completed.stdout.decode("utf-8", errors="replace"))
    except ValueError:
        return
    for observation in observations:
        if observation.virtual and observation.state is AndroidAdbState.DEVICE:
            _run(build_adb_emulator_kill_argv(adb, observation.serial), timeout=30, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.6 governed Android device acceptance")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--source-sha", required=True)
    p_prepare.add_argument("--staging-root", type=Path, required=True)

    p_launch = sub.add_parser("launch-emulator")
    p_launch.add_argument("--avd-name", required=True)
    p_launch.add_argument("--system-image", required=True)
    p_launch.add_argument("--pid-file", type=Path, required=True)
    p_launch.add_argument("--log-file", type=Path, required=True)

    p_collect = sub.add_parser("collect")
    p_collect.add_argument("--staging-root", type=Path, required=True)
    p_collect.add_argument("--output", type=Path, required=True)

    sub.add_parser("cleanup-emulator")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.source_sha, args.staging_root)
    elif args.command == "launch-emulator":
        launch_emulator(args.avd_name, args.system_image, args.pid_file, args.log_file)
    elif args.command == "collect":
        collect(args.staging_root, args.output)
    else:
        cleanup_emulator()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
