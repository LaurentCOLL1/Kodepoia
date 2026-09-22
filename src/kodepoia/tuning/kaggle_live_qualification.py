from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .contracts import canonical_sha256
from .kaggle_remote import CommandResult, CommandRunner, SubprocessCommandRunner
from .strategy import MIN_REPLICATED_THROUGHPUT_SPEEDUP_RATIO

LIVE_REQUEST_SCHEMA = "kodepoia.v2.4.5.kaggle-live-qualification-request"
LIVE_REPORT_SCHEMA = "kodepoia.v2.4.5.kaggle-live-qualification-report"
LIVE_SCHEMA_VERSION = 1
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+@-]{0,255}$")
_SECRET_KEYS = {
    "access_token",
    "api_key",
    "credential",
    "credentials",
    "kaggle_api_token",
    "kaggle_key",
    "password",
    "refresh_token",
    "secret",
    "token",
}


class KaggleLiveQualificationError(ValueError):
    """Invalid or incomplete V2.4.5 live-provider evidence."""


def _digest(label: str, value: str) -> str:
    value = value.strip().lower()
    if _HEX64.fullmatch(value) is None:
        raise KaggleLiveQualificationError(f"{label} must be a 64-character lowercase digest")
    return value


def _source_sha(value: str) -> str:
    value = value.strip().lower()
    if _HEX40.fullmatch(value) is None:
        raise KaggleLiveQualificationError("source_sha must be a full 40-character Git SHA")
    return value


def _safe_id(label: str, value: str) -> str:
    value = value.strip()
    if _SAFE_ID.fullmatch(value) is None or ".." in value.split("/"):
        raise KaggleLiveQualificationError(f"{label} must be a bounded safe identifier")
    return value


def _assert_no_secrets(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).casefold() in _SECRET_KEYS:
                raise KaggleLiveQualificationError("live qualification evidence contains a secret-like field")
            _assert_no_secrets(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_secrets(item)


@dataclass(frozen=True, slots=True)
class KaggleLiveQualificationRequest:
    source_sha: str
    training_plan_digest: str
    topology_report_digest: str
    topology_digest: str
    single_strategy_plan_digest: str
    replicated_strategy_plan_digest: str
    benchmark_report_digest: str
    execution_plan_digest: str
    recovery_plan_digest: str
    kernel_id: str
    requested_shape: str = "NvidiaTeslaT4"
    expected_device_count: int = 2
    schema: str = LIVE_REQUEST_SCHEMA
    schema_version: int = LIVE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_sha", _source_sha(self.source_sha))
        for label in (
            "training_plan_digest",
            "topology_report_digest",
            "topology_digest",
            "single_strategy_plan_digest",
            "replicated_strategy_plan_digest",
            "benchmark_report_digest",
            "execution_plan_digest",
            "recovery_plan_digest",
        ):
            object.__setattr__(self, label, _digest(label, getattr(self, label)))
        object.__setattr__(self, "kernel_id", _safe_id("kernel_id", self.kernel_id))
        if self.requested_shape != "NvidiaTeslaT4":
            raise KaggleLiveQualificationError("V2.4.5 production qualification requires NvidiaTeslaT4")
        if self.expected_device_count != 2:
            raise KaggleLiveQualificationError("V2.4.5 expects exactly two T4 devices")

    def descriptor(self) -> dict[str, object]:
        return {
            "benchmark_report_digest": self.benchmark_report_digest,
            "execution_plan_digest": self.execution_plan_digest,
            "expected_device_count": self.expected_device_count,
            "kernel_id": self.kernel_id,
            "recovery_plan_digest": self.recovery_plan_digest,
            "replicated_strategy_plan_digest": self.replicated_strategy_plan_digest,
            "requested_shape": self.requested_shape,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "single_strategy_plan_digest": self.single_strategy_plan_digest,
            "source_sha": self.source_sha,
            "topology_digest": self.topology_digest,
            "topology_report_digest": self.topology_report_digest,
            "training_plan_digest": self.training_plan_digest,
        }

    @property
    def digest(self) -> str:
        return canonical_sha256(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "request_digest": self.digest}


def build_private_probe_bundle(
    request: KaggleLiveQualificationRequest,
    output_root: Path,
) -> Path:
    root = Path(output_root).resolve(strict=False)
    root.mkdir(parents=True, exist_ok=True)
    request_path = root / "qualification-request.json"
    request_path.write_text(
        json.dumps(request.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    script = root / "probe_kaggle_t4x2.py"
    script.write_text(
        """from __future__ import annotations
import json
import platform
from pathlib import Path

import torch

request = json.loads(
    Path("qualification-request.json").read_text(encoding="utf-8")
)
count = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
devices = []
for index in range(count):
    props = torch.cuda.get_device_properties(index)
    try:
        free, total = torch.cuda.mem_get_info(index)
    except Exception:
        free = total = None
    devices.append(
        {
            "backend_type": "cuda",
            "index": index,
            "name": str(props.name),
            "vram_free_bytes": free,
            "vram_total_bytes": total,
        }
    )
payload = {
    "schema": "kodepoia.v2.4.5.kaggle-provider-probe",
    "schema_version": 1,
    "source_sha": request["source_sha"],
    "request_digest": request["request_digest"],
    "requested_shape": request["requested_shape"],
    "kernel_id": request["kernel_id"],
    "private_kernel": True,
    "backend_type": "cuda",
    "device_count": count,
    "devices": devices,
    "framework_versions": {
        "python": platform.python_version(),
        "torch": str(torch.__version__),
        "cuda": str(torch.version.cuda),
    },
}
Path("provider-probe.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\\n",
    encoding="utf-8",
)
print(json.dumps({"device_count": count, "source_sha": request["source_sha"]}))
""",
        encoding="utf-8",
    )
    metadata = {
        "code_file": script.name,
        "competition_sources": [],
        "dataset_sources": [],
        "enable_gpu": True,
        "enable_internet": False,
        "id": request.kernel_id,
        "is_private": True,
        "kernel_sources": [],
        "kernel_type": "script",
        "language": "python",
        "machine_shape": request.requested_shape,
        "model_sources": [],
        "title": "Kodepoia V2.4.5 exact-source provider probe",
    }
    _assert_no_secrets(metadata)
    (root / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "files": {
            request_path.name: hashlib.sha256(request_path.read_bytes()).hexdigest(),
            script.name: hashlib.sha256(script.read_bytes()).hexdigest(),
        },
        "private": True,
        "request_digest": request.digest,
        "schema": "kodepoia.v2.4.5.kaggle-live-probe-bundle",
        "schema_version": 1,
        "source_sha": request.source_sha,
    }
    _assert_no_secrets(manifest)
    (root / "bundle-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root


class KaggleLiveProbeClient:
    """Fixed-argv provider probe lifecycle; never accepts caller shell/env arguments."""

    def __init__(
        self,
        *,
        runner: CommandRunner | None = None,
        kaggle_executable: str | None = None,
    ) -> None:
        self.runner = runner or SubprocessCommandRunner()
        self.kaggle_executable = kaggle_executable or shutil.which("kaggle") or "kaggle"

    def push(self, bundle_root: Path) -> CommandResult:
        root = Path(bundle_root).resolve(strict=True)
        metadata = json.loads((root / "kernel-metadata.json").read_text(encoding="utf-8"))
        if not isinstance(metadata, dict) or metadata.get("is_private") is not True:
            raise KaggleLiveQualificationError("live probe kernel must be private")
        return self._checked(
            [self.kaggle_executable, "kernels", "push", "--path", str(root)],
            timeout=300.0,
        )

    def status(self, request: KaggleLiveQualificationRequest) -> CommandResult:
        return self._checked(
            [self.kaggle_executable, "kernels", "status", request.kernel_id],
            timeout=120.0,
        )

    def fetch_probe(
        self,
        request: KaggleLiveQualificationRequest,
        output_root: Path,
    ) -> dict[str, object]:
        output = Path(output_root).resolve(strict=False)
        output.mkdir(parents=True, exist_ok=True)
        self._checked(
            [
                self.kaggle_executable,
                "kernels",
                "output",
                request.kernel_id,
                "--path",
                str(output),
            ],
            timeout=3600.0,
        )
        matches = list(output.rglob("provider-probe.json"))
        if len(matches) != 1:
            raise KaggleLiveQualificationError(
                "Kaggle output must contain exactly one provider-probe.json"
            )
        payload = json.loads(matches[0].read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise KaggleLiveQualificationError("provider probe root must be an object")
        _assert_no_secrets(payload)
        if payload.get("schema") != "kodepoia.v2.4.5.kaggle-provider-probe":
            raise KaggleLiveQualificationError("provider probe schema mismatch")
        if str(payload.get("source_sha", "")).lower() != request.source_sha:
            raise KaggleLiveQualificationError("provider probe source SHA mismatch")
        if payload.get("request_digest") != request.digest:
            raise KaggleLiveQualificationError("provider probe request digest mismatch")
        if payload.get("kernel_id") != request.kernel_id:
            raise KaggleLiveQualificationError("provider probe kernel identity mismatch")
        if payload.get("private_kernel") is not True:
            raise KaggleLiveQualificationError("provider probe did not prove private kernel")
        return payload

    def _checked(self, argv: list[str], *, timeout: float) -> CommandResult:
        result = self.runner.run(argv, timeout=timeout)
        if result.returncode != 0:
            raise KaggleLiveQualificationError(
                f"Kaggle CLI probe command failed ({result.returncode}): "
                f"{result.stderr.strip()[:4096]}"
            )
        return result


def _run_blockers(
    label: str,
    run: Mapping[str, object],
    *,
    request: KaggleLiveQualificationRequest,
    expected_strategy: str,
) -> list[str]:
    blockers: list[str] = []
    if str(run.get("strategy", "")) != expected_strategy:
        blockers.append(f"{label}_strategy_mismatch")
    if str(run.get("training_plan_digest", "")) != request.training_plan_digest:
        blockers.append(f"{label}_training_plan_mismatch")
    expected_strategy_digest = (
        request.single_strategy_plan_digest
        if expected_strategy == "single_gpu"
        else request.replicated_strategy_plan_digest
    )
    if str(run.get("strategy_plan_digest", "")) != expected_strategy_digest:
        blockers.append(f"{label}_strategy_plan_mismatch")
    if str(run.get("topology_digest", "")) != request.topology_digest:
        blockers.append(f"{label}_topology_mismatch")
    if run.get("state") != "completed":
        blockers.append(f"{label}_not_completed")
    if run.get("run_integrity") is not True:
        blockers.append(f"{label}_run_integrity_failed")
    if run.get("checkpoint_integrity") is not True:
        blockers.append(f"{label}_checkpoint_integrity_failed")
    return blockers


def validate_live_evidence(
    request: KaggleLiveQualificationRequest,
    evidence: Mapping[str, object],
) -> dict[str, object]:
    _assert_no_secrets(evidence)
    blockers: list[str] = []
    if str(evidence.get("source_sha", "")).lower() != request.source_sha:
        blockers.append("source_sha_mismatch")
    if str(evidence.get("request_digest", "")) != request.digest:
        blockers.append("request_digest_mismatch")
    provider = evidence.get("provider")
    provider_map = provider if isinstance(provider, Mapping) else {}
    if provider_map.get("authenticated") is not True:
        blockers.append("provider_auth_unavailable")
    if provider_map.get("private_kernel") is not True:
        blockers.append("private_kernel_not_proven")
    if str(provider_map.get("requested_shape", "")) != request.requested_shape:
        blockers.append("provider_shape_mismatch")
    if str(provider_map.get("kernel_id", "")) != request.kernel_id:
        blockers.append("kernel_identity_mismatch")

    topology = evidence.get("topology")
    topology_map = topology if isinstance(topology, Mapping) else {}
    devices = topology_map.get("devices")
    device_rows = devices if isinstance(devices, list) else []
    if str(topology_map.get("backend_type", "")) != "cuda":
        blockers.append("cuda_topology_not_proven")
    if topology_map.get("device_count") != 2 or len(device_rows) != 2:
        blockers.append("two_device_topology_not_proven")
    indexes: list[int] = []
    for item in device_rows:
        if not isinstance(item, Mapping):
            blockers.append("device_evidence_invalid")
            continue
        try:
            index = int(item.get("index", -1))
        except (TypeError, ValueError):
            index = -1
        indexes.append(index)
        if "T4" not in str(item.get("name", "")).upper():
            blockers.append("device_not_t4")
        free = item.get("vram_free_bytes")
        total = item.get("vram_total_bytes")
        if not isinstance(free, int) or not isinstance(total, int) or free < 0 or total <= 0 or free > total:
            blockers.append("device_vram_invalid")
    if sorted(indexes) != [0, 1]:
        blockers.append("device_ordinals_invalid")

    runs = evidence.get("runs")
    runs_map = runs if isinstance(runs, Mapping) else {}
    single = runs_map.get("single_gpu")
    replicated = runs_map.get("replicated_data_parallel")
    single_map = single if isinstance(single, Mapping) else {}
    replicated_map = replicated if isinstance(replicated, Mapping) else {}
    blockers.extend(
        _run_blockers("single", single_map, request=request, expected_strategy="single_gpu")
    )
    blockers.extend(
        _run_blockers(
            "replicated",
            replicated_map,
            request=request,
            expected_strategy="replicated_data_parallel",
        )
    )
    if replicated_map.get("execution_plan_digest") != request.execution_plan_digest:
        blockers.append("execution_plan_mismatch")
    if evidence.get("recovery_plan_digest") != request.recovery_plan_digest:
        blockers.append("recovery_plan_mismatch")

    same_config = (
        single_map.get("benchmark_config_digest")
        and single_map.get("benchmark_config_digest") == replicated_map.get("benchmark_config_digest")
    )
    if not same_config:
        blockers.append("paired_benchmark_config_mismatch")
    if single_map.get("effective_global_batch_size") != replicated_map.get(
        "effective_global_batch_size"
    ):
        blockers.append("effective_global_batch_mismatch")
    if single_map.get("processed_samples") != replicated_map.get("processed_samples"):
        blockers.append("processed_samples_mismatch")

    try:
        single_throughput = float(single_map.get("throughput_samples_per_second", 0.0))
        replicated_throughput = float(
            replicated_map.get("throughput_samples_per_second", 0.0)
        )
    except (TypeError, ValueError):
        single_throughput = replicated_throughput = 0.0
    speedup = 0.0 if single_throughput <= 0 else replicated_throughput / single_throughput
    if speedup < MIN_REPLICATED_THROUGHPUT_SPEEDUP_RATIO:
        blockers.append("throughput_gain_below_threshold")

    try:
        single_eval = float(single_map["eval_loss"])
        replicated_eval = float(replicated_map["eval_loss"])
    except (KeyError, TypeError, ValueError):
        single_eval = replicated_eval = float("nan")
        blockers.append("eval_loss_missing")
    if single_eval == single_eval and replicated_eval == replicated_eval and replicated_eval > single_eval:
        blockers.append("eval_loss_regression")
    if evidence.get("critical_regression_pass") is not True:
        blockers.append("critical_regression_veto")
    if evidence.get("download_revalidated") is not True:
        blockers.append("download_revalidation_missing")
    if evidence.get("secret_scan_pass") is not True:
        blockers.append("secret_scan_not_proven")

    blockers = sorted(set(blockers))
    payload: dict[str, object] = {
        "blockers": blockers,
        "production_qualified": not blockers,
        "provider": dict(provider_map),
        "request_digest": request.digest,
        "schema": LIVE_REPORT_SCHEMA,
        "schema_version": LIVE_SCHEMA_VERSION,
        "source_sha": request.source_sha,
        "status": "qualified" if not blockers else "blocked",
        "throughput_speedup_ratio": speedup,
        "topology": dict(topology_map),
        "lineage": {
            "benchmark_report_digest": request.benchmark_report_digest,
            "execution_plan_digest": request.execution_plan_digest,
            "recovery_plan_digest": request.recovery_plan_digest,
            "replicated_strategy_plan_digest": request.replicated_strategy_plan_digest,
            "single_strategy_plan_digest": request.single_strategy_plan_digest,
            "topology_digest": request.topology_digest,
            "topology_report_digest": request.topology_report_digest,
            "training_plan_digest": request.training_plan_digest,
        },
    }
    payload["report_digest"] = canonical_sha256(payload)
    return payload


def save_live_report(path: Path, report: Mapping[str, object]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(dict(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


__all__ = [
    "KaggleLiveQualificationError",
    "KaggleLiveQualificationRequest",
    "KaggleLiveProbeClient",
    "LIVE_REPORT_SCHEMA",
    "LIVE_REQUEST_SCHEMA",
    "build_private_probe_bundle",
    "save_live_report",
    "validate_live_evidence",
]
