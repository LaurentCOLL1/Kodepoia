from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from kodepoia.mobile.android_device import AndroidAdbState, parse_adb_devices


def _tool(name: str) -> str:
    direct = shutil.which(name)
    if direct:
        return direct
    sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if sdk:
        suffix = ".exe" if os.name == "nt" else ""
        candidates = {
            "adb": Path(sdk) / "platform-tools" / f"adb{suffix}",
            "emulator": Path(sdk) / "emulator" / f"emulator{suffix}",
            "avdmanager": Path(sdk)
            / "cmdline-tools"
            / "latest"
            / "bin"
            / f"avdmanager{'.bat' if os.name == 'nt' else ''}",
        }
        candidate = candidates.get(name)
        if candidate is not None and candidate.is_file():
            return str(candidate)
    raise SystemExit(f"required R13.6 Android tool is unavailable: {name}")


def _run(
    argv: list[str],
    *,
    timeout: int = 120,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        argv,
        input=None if input_text is None else input_text.encode("utf-8"),
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        detail = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
        bounded = "\n".join(detail.splitlines()[-40:])
        if bounded:
            print(bounded)
        raise SystemExit(f"fixed R13.6 command failed: {Path(argv[0]).name}")
    return completed


def _bounded_log_tail(log_file: Path, line_limit: int = 80) -> str:
    if not log_file.is_file():
        return "<emulator log unavailable>"
    text = log_file.read_text(encoding="utf-8", errors="replace")
    return "\n".join(text.splitlines()[-line_limit:])


def _controlled_avd_home() -> Path:
    raw = os.environ.get("ANDROID_AVD_HOME")
    if not raw:
        raise SystemExit("R13.6 requires an explicit ANDROID_AVD_HOME")
    home = Path(raw).expanduser().resolve()
    home.mkdir(parents=True, exist_ok=True)
    return home


def probe_acceleration() -> None:
    emulator = _tool("emulator")
    completed = _run([emulator, "-accel-check"], timeout=30, check=False)
    text = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
    bounded = "\n".join(text.splitlines()[-20:])
    if bounded:
        print(bounded)
    if completed.returncode != 0:
        raise SystemExit("R13.6 hosted Android acceleration probe failed")
    lowered = text.lower()
    if "usable" not in lowered and "installed" not in lowered:
        raise SystemExit("R13.6 acceleration probe did not confirm a usable hypervisor")


def launch_and_wait(
    avd_name: str,
    system_image: str,
    pid_file: Path,
    log_file: Path,
    timeout_seconds: int = 120,
) -> None:
    if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", avd_name) is None:
        raise SystemExit("invalid bounded AVD name")
    if re.fullmatch(r"system-images;android-[0-9]+;google_apis;x86_64", system_image) is None:
        raise SystemExit("unsupported R13.6 system image identity")

    avd_home = _controlled_avd_home()
    user_home_raw = os.environ.get("ANDROID_USER_HOME")
    if not user_home_raw:
        raise SystemExit("R13.6 requires an explicit ANDROID_USER_HOME")
    Path(user_home_raw).expanduser().resolve().mkdir(parents=True, exist_ok=True)

    probe_acceleration()
    avdmanager = _tool("avdmanager")
    emulator = _tool("emulator")
    adb = _tool("adb")
    _run(
        [
            avdmanager,
            "create",
            "avd",
            "--force",
            "--name",
            avd_name,
            "--package",
            system_image,
            "--path",
            str(avd_home / f"{avd_name}.avd"),
        ],
        input_text="no\n",
        timeout=120,
    )

    listed = _run([emulator, "-list-avds"], timeout=30)
    avd_names = {
        line.strip()
        for line in listed.stdout.decode("utf-8", errors="replace").splitlines()
        if line.strip()
    }
    if avd_name not in avd_names:
        bounded = ", ".join(sorted(avd_names)[:20]) or "<none>"
        raise SystemExit(f"R13.6 created AVD is not discoverable by emulator: {bounded}")

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
                "-gpu",
                "software",
                "-accel",
                "on",
            ],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(process.pid), encoding="ascii")

    deadline = time.monotonic() + timeout_seconds
    last_state = "not-visible"
    while time.monotonic() < deadline:
        returncode = process.poll()
        if returncode is not None:
            tail = _bounded_log_tail(log_file)
            if tail:
                print(tail)
            raise SystemExit(f"R13.6 emulator exited before ADB registration: {returncode}")

        completed = _run([adb, "devices", "-l"], timeout=30, check=False)
        if completed.returncode == 0:
            listing = completed.stdout.decode("utf-8", errors="replace")
            try:
                observations = parse_adb_devices(listing)
            except ValueError as exc:
                raise SystemExit(f"R13.6 invalid ADB device listing: {exc}") from exc
            emulators = [item for item in observations if item.virtual]
            online = [item for item in emulators if item.state is AndroidAdbState.DEVICE]
            if len(online) > 1:
                raise SystemExit("multiple online Android emulators detected during bounded launch")
            if len(online) == 1:
                print(json.dumps({"avd_name": avd_name, "pid": process.pid, "adb": "online"}))
                return
            if emulators:
                last_state = emulators[0].state.value
        time.sleep(1)

    tail = _bounded_log_tail(log_file)
    if tail:
        print(tail)
    raise SystemExit(f"R13.6 emulator did not become visible in ADB: {last_state}")


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.6 hosted emulator CI seam")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("probe")
    launch = sub.add_parser("launch")
    launch.add_argument("--avd-name", required=True)
    launch.add_argument("--system-image", required=True)
    launch.add_argument("--pid-file", type=Path, required=True)
    launch.add_argument("--log-file", type=Path, required=True)
    launch.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()

    if args.command == "probe":
        probe_acceleration()
    else:
        launch_and_wait(
            args.avd_name,
            args.system_image,
            args.pid_file,
            args.log_file,
            args.timeout_seconds,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
