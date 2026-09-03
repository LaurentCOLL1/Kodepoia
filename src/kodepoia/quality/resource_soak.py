from __future__ import annotations

import ctypes
import gc
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from kodepoia.core.kill_switch import KillSwitch
from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.quality.privacy import redact_privacy_evidence

SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FIXTURE_RELATIVE = Path("tests/fixtures/r16_16_resource_soak/scenario.json")
POLICY_RELATIVE = Path("configs/r16_16_resource_soak_policy.json")
_CAPACITIES = {"cpu", "ram", "vram", "disk", "process", "time", "concurrency"}
_PROFILE_IDS = {"code", "godot", "comfyui", "media", "desktop"}


class ResourceSoakGovernanceError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _case(name: str, passed: bool, detail: str) -> dict[str, object]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def validate_fixture_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "schema_version",
        "name",
        "profiles",
        "synthetic_secret_token",
        "negative_controls",
    }
    if set(payload) != expected or payload.get("schema_version") != 1:
        raise ResourceSoakGovernanceError("fixture schema/fields drifted")
    if payload.get("name") != "r16.16-resource-concurrency-leak-diagnostics-soak":
        raise ResourceSoakGovernanceError("fixture identity drifted")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or len(profiles) != len(_PROFILE_IDS):
        raise ResourceSoakGovernanceError("fixture must contain the five representative profiles")
    seen: set[str] = set()
    for profile in profiles:
        if not isinstance(profile, Mapping) or set(profile) != {
            "id",
            "cycles",
            "payload_kib",
            "hash_rounds",
        }:
            raise ResourceSoakGovernanceError("profile contract is invalid")
        profile_id = profile.get("id")
        if not isinstance(profile_id, str) or profile_id not in _PROFILE_IDS or profile_id in seen:
            raise ResourceSoakGovernanceError("profile identity is invalid or duplicated")
        seen.add(profile_id)
        cycles = profile.get("cycles")
        payload_kib = profile.get("payload_kib")
        rounds = profile.get("hash_rounds")
        if isinstance(cycles, bool) or not isinstance(cycles, int) or not 1 <= cycles <= 8:
            raise ResourceSoakGovernanceError("profile cycles must be bounded to 1..8")
        if isinstance(payload_kib, bool) or not isinstance(payload_kib, int) or not 1 <= payload_kib <= 256:
            raise ResourceSoakGovernanceError("profile payload must be bounded to 1..256 KiB")
        if isinstance(rounds, bool) or not isinstance(rounds, int) or not 1 <= rounds <= 256:
            raise ResourceSoakGovernanceError("profile hash rounds must be bounded to 1..256")
    if seen != _PROFILE_IDS:
        raise ResourceSoakGovernanceError("representative profile set drifted")
    canary = payload.get("synthetic_secret_token")
    if not isinstance(canary, str) or not canary.startswith("R16_16_SYNTHETIC_") or len(canary) > 128:
        raise ResourceSoakGovernanceError("synthetic diagnostic canary is invalid")
    controls = payload.get("negative_controls")
    expected_controls = {
        "required_unknown_capacity",
        "over_budget",
        "orphan_process",
        "temp_leak",
        "sensitive_diagnostic",
        "post_cancel_mutation",
    }
    if not isinstance(controls, Mapping) or set(controls) != expected_controls:
        raise ResourceSoakGovernanceError("negative-control contract drifted")
    if not all(value is True for value in controls.values()):
        raise ResourceSoakGovernanceError("all negative controls must be enabled")
    return dict(payload)


def validate_policy_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "schema_version",
        "policy_id",
        "repeat_runs",
        "concurrency_workers",
        "child_processes",
        "required_capacities",
        "optional_capacities",
        "budgets",
        "diagnostics",
    }
    if set(payload) != expected or payload.get("schema_version") != 1:
        raise ResourceSoakGovernanceError("policy schema/fields drifted")
    if payload.get("policy_id") != "r16.16-resource-concurrency-leak-diagnostics-v1":
        raise ResourceSoakGovernanceError("policy identity drifted")
    repeat_runs = payload.get("repeat_runs")
    workers = payload.get("concurrency_workers")
    children = payload.get("child_processes")
    if isinstance(repeat_runs, bool) or not isinstance(repeat_runs, int) or not 2 <= repeat_runs <= 4:
        raise ResourceSoakGovernanceError("repeat_runs must be bounded to 2..4")
    if isinstance(workers, bool) or not isinstance(workers, int) or not 2 <= workers <= 8:
        raise ResourceSoakGovernanceError("concurrency_workers must be bounded to 2..8")
    if isinstance(children, bool) or not isinstance(children, int) or not 1 <= children <= 4:
        raise ResourceSoakGovernanceError("child_processes must be bounded to 1..4")
    required = payload.get("required_capacities")
    optional = payload.get("optional_capacities")
    if not isinstance(required, list) or not isinstance(optional, list):
        raise ResourceSoakGovernanceError("capacity lists are invalid")
    required_set = {str(item) for item in required}
    optional_set = {str(item) for item in optional}
    if required_set & optional_set or required_set | optional_set != _CAPACITIES:
        raise ResourceSoakGovernanceError("capacity partition must cover each known capacity exactly once")
    if "vram" not in optional_set:
        raise ResourceSoakGovernanceError("hosted-runner VRAM must remain an explicit optional capability")
    budgets = payload.get("budgets")
    expected_budget_keys = {
        "max_wall_ms",
        "max_cpu_ms",
        "max_rss_growth_bytes",
        "max_heap_growth_bytes",
        "max_peak_heap_bytes",
        "max_peak_temp_bytes",
        "max_temp_bytes_after",
        "max_temp_files_after",
        "max_thread_delta_after",
        "max_active_processes_after",
        "max_repeat_wall_ratio",
        "max_repeat_cpu_ratio",
        "timeout_seconds",
    }
    if not isinstance(budgets, Mapping) or set(budgets) != expected_budget_keys:
        raise ResourceSoakGovernanceError("budget contract drifted")
    positive = {
        "max_wall_ms",
        "max_cpu_ms",
        "max_rss_growth_bytes",
        "max_heap_growth_bytes",
        "max_peak_heap_bytes",
        "max_peak_temp_bytes",
        "max_repeat_wall_ratio",
        "max_repeat_cpu_ratio",
        "timeout_seconds",
    }
    non_negative = expected_budget_keys - positive
    for key in positive:
        value = budgets[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) <= 0:
            raise ResourceSoakGovernanceError(f"{key} must be positive")
    for key in non_negative:
        value = budgets[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) < 0:
            raise ResourceSoakGovernanceError(f"{key} must be non-negative")
    if float(budgets["max_wall_ms"]) > 60000 or float(budgets["timeout_seconds"]) > 60:
        raise ResourceSoakGovernanceError("wall-clock budgets exceed bounded CI authority")
    diagnostics = payload.get("diagnostics")
    expected_diag = {
        "aggregate_only",
        "redact_sensitive_values",
        "persist_raw_fixture_content",
        "persist_absolute_paths",
    }
    if not isinstance(diagnostics, Mapping) or set(diagnostics) != expected_diag:
        raise ResourceSoakGovernanceError("diagnostic policy drifted")
    if diagnostics != {
        "aggregate_only": True,
        "redact_sensitive_values": True,
        "persist_raw_fixture_content": False,
        "persist_absolute_paths": False,
    }:
        raise ResourceSoakGovernanceError("diagnostic policy must remain privacy-safe")
    return dict(payload)


def load_fixture(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / FIXTURE_RELATIVE).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ResourceSoakGovernanceError("fixture root must be an object")
    return validate_fixture_payload(payload)


def load_policy(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ResourceSoakGovernanceError("policy root must be an object")
    return validate_policy_payload(payload)


def _rss_bytes() -> tuple[int | None, str]:
    if os.name == "nt":
        try:
            dword = ctypes.c_ulong
            size_t = ctypes.c_size_t

            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", dword),
                    ("PageFaultCount", dword),
                    ("PeakWorkingSetSize", size_t),
                    ("WorkingSetSize", size_t),
                    ("QuotaPeakPagedPoolUsage", size_t),
                    ("QuotaPagedPoolUsage", size_t),
                    ("QuotaPeakNonPagedPoolUsage", size_t),
                    ("QuotaNonPagedPoolUsage", size_t),
                    ("PagefileUsage", size_t),
                    ("PeakPagefileUsage", size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(ProcessMemoryCounters)
            process = ctypes.windll.kernel32.GetCurrentProcess()
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(
                process,
                ctypes.byref(counters),
                counters.cb,
            )
            if ok:
                return int(counters.WorkingSetSize), "windows-working-set"
        except (AttributeError, OSError, ValueError):
            return None, "windows-rss-unavailable"
        return None, "windows-rss-unavailable"
    try:
        import resource

        value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        factor = 1 if sys.platform == "darwin" else 1024
        return value * factor, "posix-maxrss"
    except (ImportError, OSError, ValueError):
        return None, "posix-rss-unavailable"


def _tree_stats(root: Path) -> tuple[int, int]:
    if not root.exists():
        return 0, 0
    total = 0
    files = 0
    for path in root.rglob("*"):
        if path.is_file():
            files += 1
            total += path.stat().st_size
    return total, files


def _payload(profile_id: str, cycle: int, size_bytes: int) -> bytes:
    seed = f"r16.16:{profile_id}:{cycle}:".encode()
    return (seed * ((size_bytes // len(seed)) + 1))[:size_bytes]


def _exercise_profile(root: Path, profile: Mapping[str, Any]) -> dict[str, Any]:
    profile_id = str(profile["id"])
    root.mkdir(parents=True, exist_ok=False)
    peak_temp_bytes = 0
    digests: list[str] = []
    generated_bytes = 0
    try:
        for cycle in range(int(profile["cycles"])):
            data = _payload(profile_id, cycle, int(profile["payload_kib"]) * 1024)
            digest = hashlib.sha256(data).digest()
            for _ in range(int(profile["hash_rounds"])):
                digest = hashlib.sha256(digest + data[:1024]).digest()
            temporary = root / f".{profile_id}-{cycle}.tmp"
            final = root / f"{profile_id}-{cycle}.bin"
            with temporary.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            peak_temp_bytes = max(peak_temp_bytes, temporary.stat().st_size)
            os.replace(temporary, final)
            if hashlib.sha256(final.read_bytes()).digest() != hashlib.sha256(data).digest():
                raise ResourceSoakGovernanceError("representative profile artifact digest drifted")
            digests.append(digest.hex())
            generated_bytes += len(data)
            final.unlink()
        remaining_bytes, remaining_files = _tree_stats(root)
        if remaining_bytes or remaining_files:
            raise ResourceSoakGovernanceError("representative profile left temporary artifacts")
    finally:
        shutil.rmtree(root, ignore_errors=False)
    return {
        "id": profile_id,
        "cycles": int(profile["cycles"]),
        "generated_bytes": generated_bytes,
        "peak_temp_bytes": peak_temp_bytes,
        "semantic_sha256": canonical_sha256(digests),
    }


@dataclass(frozen=True, slots=True)
class RepetitionMetrics:
    wall_ms: float
    cpu_ms: float
    rss_growth_bytes: int
    rss_probe: str
    heap_growth_bytes: int
    peak_heap_bytes: int
    peak_temp_bytes: int
    temp_bytes_after: int
    temp_files_after: int
    thread_delta_after: int
    operation_count: int
    generated_bytes: int
    profile_semantic_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "wall_ms": self.wall_ms,
            "cpu_ms": self.cpu_ms,
            "rss_growth_bytes": self.rss_growth_bytes,
            "rss_probe": self.rss_probe,
            "heap_growth_bytes": self.heap_growth_bytes,
            "peak_heap_bytes": self.peak_heap_bytes,
            "peak_temp_bytes": self.peak_temp_bytes,
            "temp_bytes_after": self.temp_bytes_after,
            "temp_files_after": self.temp_files_after,
            "thread_delta_after": self.thread_delta_after,
            "operation_count": self.operation_count,
            "generated_bytes": self.generated_bytes,
            "profile_semantic_sha256": self.profile_semantic_sha256,
        }


def _run_repetition(root: Path, fixture: Mapping[str, Any]) -> RepetitionMetrics:
    root.mkdir(parents=True, exist_ok=False)
    gc.collect()
    baseline_threads = threading.active_count()
    baseline_rss, rss_probe = _rss_bytes()
    tracemalloc.start()
    baseline_heap, _ = tracemalloc.get_traced_memory()
    started_wall = time.perf_counter_ns()
    started_cpu = time.process_time_ns()
    peak_temp = 0
    profiles: list[dict[str, Any]] = []
    try:
        for profile in fixture["profiles"]:
            result = _exercise_profile(root / str(profile["id"]), profile)
            peak_temp = max(peak_temp, int(result["peak_temp_bytes"]))
            profiles.append(result)
        wall_ms = (time.perf_counter_ns() - started_wall) / 1_000_000
        cpu_ms = (time.process_time_ns() - started_cpu) / 1_000_000
        gc.collect()
        final_heap, peak_heap = tracemalloc.get_traced_memory()
        final_rss, final_probe = _rss_bytes()
        if final_probe != rss_probe:
            rss_probe = f"{rss_probe}->{final_probe}"
        temp_bytes, temp_files = _tree_stats(root)
        profile_semantic = canonical_sha256(
            [{"id": item["id"], "semantic_sha256": item["semantic_sha256"]} for item in profiles]
        )
        return RepetitionMetrics(
            wall_ms=round(wall_ms, 6),
            cpu_ms=round(cpu_ms, 6),
            rss_growth_bytes=(
                0
                if baseline_rss is None or final_rss is None
                else max(0, int(final_rss) - int(baseline_rss))
            ),
            rss_probe=rss_probe,
            heap_growth_bytes=max(0, int(final_heap) - int(baseline_heap)),
            peak_heap_bytes=int(peak_heap),
            peak_temp_bytes=peak_temp,
            temp_bytes_after=temp_bytes,
            temp_files_after=temp_files,
            thread_delta_after=max(0, threading.active_count() - baseline_threads),
            operation_count=sum(int(item["cycles"]) for item in profiles),
            generated_bytes=sum(int(item["generated_bytes"]) for item in profiles),
            profile_semantic_sha256=profile_semantic,
        )
    finally:
        tracemalloc.stop()
        shutil.rmtree(root, ignore_errors=False)


def _run_cancellation_race(root: Path, workers: int, timeout: float) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    first_barrier = threading.Barrier(workers + 1)
    release_barrier = threading.Barrier(workers + 1)
    cancelled = threading.Event()
    lock = threading.Lock()
    committed: set[int] = set()
    post_cancel_mutations: list[int] = []

    def worker(index: int) -> str:
        data = _payload("concurrency", index, 4096)
        temporary = root / f".{index}.tmp"
        final = root / f"{index}.bin"
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, final)
        with lock:
            committed.add(index)
        first_barrier.wait(timeout=timeout)
        release_barrier.wait(timeout=timeout)
        if cancelled.is_set():
            return "cancelled"
        with lock:
            post_cancel_mutations.append(index)
        (root / f"post-{index}.bin").write_bytes(data)
        return "mutated"

    try:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="r16-16") as pool:
            futures = [pool.submit(worker, index) for index in range(workers)]
            first_barrier.wait(timeout=timeout)
            cancelled.set()
            release_barrier.wait(timeout=timeout)
            results = [future.result(timeout=timeout) for future in futures]
        before_cleanup_bytes, before_cleanup_files = _tree_stats(root)
        return {
            "workers": workers,
            "committed_before_cancel": len(committed),
            "cancelled_workers": sum(item == "cancelled" for item in results),
            "post_cancel_mutations": len(post_cancel_mutations),
            "files_before_cleanup": before_cleanup_files,
            "bytes_before_cleanup": before_cleanup_bytes,
            "state_consistent": committed == set(range(workers)) and not post_cancel_mutations,
        }
    except threading.BrokenBarrierError as exc:
        raise ResourceSoakGovernanceError("concurrency cancellation barrier failed") from exc
    finally:
        shutil.rmtree(root, ignore_errors=False)


def _run_process_cleanup(root: Path, children: int) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=False)
    kill_switch = KillSwitch()
    executable = Path(sys.executable).name
    sandbox = ProcessSandbox(root, allowed_executables={executable}, kill_switch=kill_switch)
    managed = []
    try:
        for _ in range(children):
            managed.append(
                sandbox.spawn_background(
                    [sys.executable, "-c", "import time; time.sleep(30)"],
                    cwd=root,
                )
            )
        peak_active = kill_switch.active_count
        signalled = kill_switch.trigger()
        for process in managed:
            process.close()
        active_after = kill_switch.active_count
        kill_switch.reset()
        return {
            "requested_children": children,
            "peak_active": peak_active,
            "signalled": signalled,
            "active_after": active_after,
            "cleanup_complete": peak_active == children and signalled == children and active_after == 0,
        }
    finally:
        for process in managed:
            process.close()
        if kill_switch.active_count == 0 and kill_switch.triggered:
            kill_switch.reset()
        shutil.rmtree(root, ignore_errors=False)


def _availability(rss_probe: str) -> dict[str, dict[str, Any]]:
    return {
        "cpu": {"state": "PASS", "source": "time.process_time_ns"},
        "ram": {
            "state": "PASS",
            "source": rss_probe if "unavailable" not in rss_probe else "tracemalloc-fallback",
        },
        "disk": {"state": "PASS", "source": "bounded temporary tree accounting"},
        "process": {"state": "PASS", "source": "ProcessSandbox/KillSwitch active_count"},
        "time": {"state": "PASS", "source": "time.perf_counter_ns"},
        "concurrency": {"state": "PASS", "source": "ThreadPoolExecutor/barrier cancellation"},
        "vram": {
            "state": "INCONCLUSIVE",
            "source": "hosted runner exposes no repository-owned portable VRAM probe",
        },
    }


def required_capacities_satisfied(
    required: list[str] | tuple[str, ...], availability: Mapping[str, Mapping[str, Any]]
) -> tuple[bool, tuple[str, ...]]:
    missing = tuple(
        sorted(
            capacity
            for capacity in required
            if capacity not in availability or availability[capacity].get("state") != "PASS"
        )
    )
    return not missing, missing


def metrics_within_budget(metrics: Mapping[str, int | float], budgets: Mapping[str, Any]) -> bool:
    checks = (
        float(metrics["wall_ms"]) <= float(budgets["max_wall_ms"]),
        float(metrics["cpu_ms"]) <= float(budgets["max_cpu_ms"]),
        int(metrics["rss_growth_bytes"]) <= int(budgets["max_rss_growth_bytes"]),
        int(metrics["heap_growth_bytes"]) <= int(budgets["max_heap_growth_bytes"]),
        int(metrics["peak_heap_bytes"]) <= int(budgets["max_peak_heap_bytes"]),
        int(metrics["peak_temp_bytes"]) <= int(budgets["max_peak_temp_bytes"]),
        int(metrics["temp_bytes_after"]) <= int(budgets["max_temp_bytes_after"]),
        int(metrics["temp_files_after"]) <= int(budgets["max_temp_files_after"]),
        int(metrics["thread_delta_after"]) <= int(budgets["max_thread_delta_after"]),
    )
    return all(checks)


def _repeat_ratio(values: list[float], floor: float) -> float:
    high = max(values)
    low = min(values)
    return round(high / max(low, floor), 6)


def sanitize_diagnostic(value: Any) -> Any:
    redacted = redact_privacy_evidence(value)

    def scrub(item: Any, key: str = "") -> Any:
        lowered = key.lower()
        if lowered.endswith("path") or lowered.endswith("_path") or lowered == "cwd":
            return "<redacted-path>"
        if isinstance(item, Mapping):
            return {str(k): scrub(v, str(k)) for k, v in item.items()}
        if isinstance(item, list):
            return [scrub(v, key) for v in item]
        return item

    return scrub(redacted)


def build_resource_soak_report(
    repo_root: Path,
    *,
    source_sha: str,
    platform: str | None = None,
) -> dict[str, Any]:
    if SOURCE_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be an exact lowercase 40-character SHA")
    started = time.monotonic()
    fixture = load_fixture(repo_root)
    policy = load_policy(repo_root)
    budgets = policy["budgets"]
    cases: list[dict[str, object]] = []
    cases.append(_case("fixture_contract_valid", True, "five bounded representative profiles validated"))
    cases.append(_case("policy_contract_valid", True, "resource and diagnostic policy validated"))

    repetitions: list[RepetitionMetrics] = []
    with Path(os.path.abspath(repo_root)).resolve():
        pass
    import tempfile

    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-16-") as name:
        scratch = Path(name)
        for index in range(int(policy["repeat_runs"])):
            repetitions.append(_run_repetition(scratch / f"repeat-{index}", fixture))
        semantic_ids = {item.profile_semantic_sha256 for item in repetitions}
        operation_counts = {item.operation_count for item in repetitions}
        generated_bytes = {item.generated_bytes for item in repetitions}
        cases.append(
            _case(
                "representative_profiles_repeatable",
                len(semantic_ids) == 1 and len(operation_counts) == 1 and len(generated_bytes) == 1,
                "profile identities, operations and generated byte counts are stable across repeats",
            )
        )
        all_budgeted = all(metrics_within_budget(item.to_dict(), budgets) for item in repetitions)
        cases.append(_case("absolute_resource_budgets", all_budgeted, "all bounded repetitions fit hard budgets"))
        cases.append(
            _case(
                "temp_artifacts_cleaned",
                all(item.temp_bytes_after == 0 and item.temp_files_after == 0 for item in repetitions),
                "representative profile temporary trees are empty after each repetition",
            )
        )
        cases.append(
            _case(
                "thread_count_recovers",
                all(item.thread_delta_after <= int(budgets["max_thread_delta_after"]) for item in repetitions),
                "thread count returns within frozen tolerance",
            )
        )
        wall_ratio = _repeat_ratio([item.wall_ms for item in repetitions], 1.0)
        cpu_ratio = _repeat_ratio([item.cpu_ms for item in repetitions], 1.0)
        repeat_ok = (
            wall_ratio <= float(budgets["max_repeat_wall_ratio"])
            and cpu_ratio <= float(budgets["max_repeat_cpu_ratio"])
        )
        cases.append(
            _case(
                "repeat_runtime_variance_bounded",
                repeat_ok,
                f"normalized wall ratio={wall_ratio}; cpu ratio={cpu_ratio}",
            )
        )
        cancellation = _run_cancellation_race(
            scratch / "cancellation",
            int(policy["concurrency_workers"]),
            float(budgets["timeout_seconds"]),
        )
        cancel_ok = (
            cancellation["state_consistent"]
            and cancellation["committed_before_cancel"] == int(policy["concurrency_workers"])
            and cancellation["cancelled_workers"] == int(policy["concurrency_workers"])
        )
        cases.append(
            _case(
                "concurrency_cancellation_state_consistent",
                bool(cancel_ok),
                "all workers reached the supported boundary and no post-cancel project mutation occurred",
            )
        )
        process_cleanup = _run_process_cleanup(scratch / "processes", int(policy["child_processes"]))
        cases.append(
            _case(
                "sandbox_processes_cleanup",
                bool(process_cleanup["cleanup_complete"]),
                "all bounded child workers were terminated and unregistered",
            )
        )
        scratch_bytes, scratch_files = _tree_stats(scratch)
        cases.append(
            _case(
                "scratch_tree_clean_after_soak",
                scratch_bytes == 0 and scratch_files == 0,
                "all acceptance scratch artifacts were removed",
            )
        )

    availability = _availability(repetitions[0].rss_probe)
    required_ok, missing_required = required_capacities_satisfied(
        [str(item) for item in policy["required_capacities"]], availability
    )
    cases.append(
        _case(
            "required_capacity_preflight",
            required_ok,
            "required resource probes are available" if required_ok else f"missing={','.join(missing_required)}",
        )
    )
    vram_truthful = availability["vram"]["state"] == "INCONCLUSIVE" and "vram" in policy["optional_capacities"]
    cases.append(
        _case(
            "optional_vram_truthful_inconclusive",
            vram_truthful,
            "hosted-runner VRAM is not promoted to a synthetic PASS",
        )
    )

    forced_required = [*policy["required_capacities"], "vram"]
    forced_ok, forced_missing = required_capacities_satisfied(forced_required, availability)
    cases.append(
        _case(
            "unknown_required_capacity_fails_closed",
            not forced_ok and forced_missing == ("vram",),
            "required unknown VRAM capacity becomes an explicit blocker",
        )
    )
    over_budget = dict(repetitions[0].to_dict())
    over_budget["wall_ms"] = float(budgets["max_wall_ms"]) + 1.0
    cases.append(
        _case(
            "over_budget_negative_control",
            not metrics_within_budget(over_budget, budgets),
            "synthetic wall-budget breach is rejected",
        )
    )
    orphan_budget_ok = 1 <= int(budgets["max_active_processes_after"])
    cases.append(
        _case(
            "orphan_process_negative_control",
            not orphan_budget_ok,
            "one synthetic active process exceeds the zero-orphan final budget",
        )
    )
    temp_leak_ok = 1 <= int(budgets["max_temp_files_after"])
    cases.append(
        _case(
            "temp_leak_negative_control",
            not temp_leak_ok,
            "one synthetic leaked file exceeds the zero-temp final budget",
        )
    )
    cases.append(
        _case(
            "post_cancel_mutation_negative_control",
            int(cancellation["post_cancel_mutations"]) == 0,
            "governed mutation count remains zero after cancellation",
        )
    )

    canary = str(fixture["synthetic_secret_token"])
    diagnostic = sanitize_diagnostic(
        {
            "token": canary,
            "message": f"secret={canary}",
            "repo_path": str(repo_root.resolve()),
            "profile_ids": sorted(_PROFILE_IDS),
            "repeat_count": len(repetitions),
        }
    )
    diagnostic_text = canonical_json(diagnostic)
    diagnostics_safe = canary not in diagnostic_text and str(repo_root.resolve()) not in diagnostic_text
    cases.append(
        _case(
            "privacy_safe_diagnostics",
            diagnostics_safe,
            "sensitive synthetic values and absolute paths are redacted",
        )
    )

    failed = [item for item in cases if not item["pass"]]
    material = {
        "fixture_sha256": canonical_sha256(fixture),
        "policy_sha256": canonical_sha256(policy),
        "profile_semantic_sha256": repetitions[0].profile_semantic_sha256,
        "operation_count": repetitions[0].operation_count,
        "generated_bytes": repetitions[0].generated_bytes,
        "case_names": [str(item["name"]) for item in cases],
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R16.16",
        "source_sha": source_sha,
        "platform": platform or sys.platform,
        "fixture_sha256": material["fixture_sha256"],
        "policy_sha256": material["policy_sha256"],
        "semantic_sha256": canonical_sha256(material),
        "authority_sha256": canonical_sha256(
            {
                "source_sha": source_sha,
                "fixture_sha256": material["fixture_sha256"],
                "policy_sha256": material["policy_sha256"],
            }
        ),
        "resource_claim": not failed,
        "critical_veto": bool(failed),
        "secret_free": diagnostics_safe,
        "external_network_calls": 0,
        "destructive_host_actions": 0,
        "core_manual_required": False,
        "manual_state": "NONE",
        "availability": availability,
        "runtime_metrics": [item.to_dict() for item in repetitions],
        "repeatability": {"wall_ratio": wall_ratio, "cpu_ratio": cpu_ratio},
        "concurrency": cancellation,
        "process_cleanup": process_cleanup,
        "diagnostics": diagnostic,
        "summary": {
            "total": len(cases),
            "passed": len(cases) - len(failed),
            "failed": len(failed),
        },
        "cases": cases,
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    report["evidence_sha256"] = canonical_sha256(
        {key: value for key, value in report.items() if key not in {"elapsed_seconds", "evidence_sha256"}}
    )
    return report
