from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Protocol, Sequence

from PIL import Image

from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.intelligence.research.contracts import ResearchStatus
from kodepoia.kodecode.workspace import WorkspaceBoundary


MEDIA_SCHEMA_VERSION = 1
DEFAULT_WHISPER_MODEL = ".kodepoia/models/stt/ggml-base.en.bin"
EXPECTED_FIXTURE_SHA256 = "8b3ed015526fd4584309a3c661b9e267ac464315e2d1c9aeed5bea19f28bdcf7"
EXPECTED_FIXTURE_TOKENS = ("one", "two", "three", "four")
_EXPECTED_FIXTURE_CANONICAL = ("1", "2", "3", "4")
_NUMBER_CANONICAL = {"one": "1", "two": "2", "three": "3", "four": "4"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_TRANSCRIPT_TOKEN_RE = re.compile(r"[a-z]+|\d+")


class MediaProcessingError(RuntimeError):
    """Raised when bounded local-media processing cannot complete safely."""


class AcceptanceStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class MediaExecutionPolicy:
    max_input_bytes: int = 32 * 1024 * 1024
    max_temporary_bytes: int = 96 * 1024 * 1024
    ffmpeg_timeout_seconds: float = 60.0
    stt_timeout_seconds: float = 180.0
    frame_timestamps_ms: tuple[int, ...] = (500, 1500, 2500)
    frame_width: int = 320
    max_frame_pixels: int = 4_000_000

    def __post_init__(self) -> None:
        if not 1 <= self.max_input_bytes <= 512 * 1024 * 1024:
            raise ValueError("media input budget must be between 1 byte and 512 MiB")
        if not self.max_input_bytes <= self.max_temporary_bytes <= 2 * 1024 * 1024 * 1024:
            raise ValueError("media temporary-disk budget is invalid")
        if not 0.1 <= self.ffmpeg_timeout_seconds <= 600.0:
            raise ValueError("ffmpeg timeout must be between 0.1 and 600 seconds")
        if not 0.1 <= self.stt_timeout_seconds <= 1800.0:
            raise ValueError("STT timeout must be between 0.1 and 1800 seconds")
        if not self.frame_timestamps_ms or any(value < 0 for value in self.frame_timestamps_ms):
            raise ValueError("frame timestamps must be non-empty non-negative milliseconds")
        if len(set(self.frame_timestamps_ms)) != len(self.frame_timestamps_ms):
            raise ValueError("frame timestamps must be unique")
        if not 16 <= self.frame_width <= 4096:
            raise ValueError("frame width must be between 16 and 4096")
        if not 256 <= self.max_frame_pixels <= 33_554_432:
            raise ValueError("frame pixel budget is invalid")


@dataclass(frozen=True, slots=True)
class ToolCapability:
    name: str
    status: ResearchStatus
    executable_name: str = ""
    version: str = ""
    executable_sha256: str = ""
    contract_supported: bool = False
    reason: str = ""

    def __post_init__(self) -> None:
        if self.executable_sha256 and not _SHA256_RE.fullmatch(self.executable_sha256):
            raise ValueError("tool executable_sha256 must be lowercase SHA-256")


@dataclass(frozen=True, slots=True)
class SttModelCapability:
    engine: str
    status: ResearchStatus
    relative_path: str
    sha256: str = ""
    size_bytes: int = 0
    reason: str = ""

    def __post_init__(self) -> None:
        if self.sha256 and not _SHA256_RE.fullmatch(self.sha256):
            raise ValueError("STT model sha256 must be lowercase SHA-256")
        if self.size_bytes < 0:
            raise ValueError("STT model size cannot be negative")


@dataclass(frozen=True, slots=True)
class ResourceMeasurements:
    elapsed_ms: int
    input_bytes: int
    temporary_peak_bytes: int
    cpu_measurement_status: ResearchStatus = ResearchStatus.UNKNOWN
    ram_measurement_status: ResearchStatus = ResearchStatus.UNKNOWN

    def __post_init__(self) -> None:
        if min(self.elapsed_ms, self.input_bytes, self.temporary_peak_bytes) < 0:
            raise ValueError("resource measurements cannot be negative")


@dataclass(frozen=True, slots=True)
class MediaDoctorReport:
    schema_version: int
    generated_at: str
    source_sha: str
    ready: bool
    ffmpeg: ToolCapability
    stt: ToolCapability
    stt_model: SttModelCapability
    vision_status: ResearchStatus = ResearchStatus.UNAVAILABLE
    vision_reason: str = "no_accepted_local_vision_provider_configured"

    def to_dict(self) -> dict[str, object]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True)
class TranscriptSegment:
    start_ms: int
    end_ms: int
    text: str
    confidence: float | None = None

    def __post_init__(self) -> None:
        if self.start_ms < 0 or self.end_ms < self.start_ms:
            raise ValueError("invalid transcript segment timestamps")
        if not self.text.strip():
            raise ValueError("transcript segment text must not be empty")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("transcript confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class FrameEvidence:
    timestamp_ms: int
    sha256: str
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.timestamp_ms < 0:
            raise ValueError("frame timestamp cannot be negative")
        if not _SHA256_RE.fullmatch(self.sha256):
            raise ValueError("frame sha256 must be lowercase SHA-256")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("frame dimensions must be positive")


@dataclass(frozen=True, slots=True)
class AcceptanceCheck:
    check_id: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class FrameAnalysisResult:
    status: ResearchStatus
    provider: str
    summary: str = ""
    reason: str = ""


class FrameAnalysisProvider(Protocol):
    def analyze(self, image_path: Path, *, timestamp_ms: int) -> FrameAnalysisResult: ...


@dataclass(frozen=True, slots=True)
class UnavailableFrameAnalysisProvider:
    reason: str = "no_accepted_local_vision_provider_configured"

    def analyze(self, image_path: Path, *, timestamp_ms: int) -> FrameAnalysisResult:
        del image_path, timestamp_ms
        return FrameAnalysisResult(
            status=ResearchStatus.UNAVAILABLE,
            provider="none",
            reason=self.reason,
        )


@dataclass(frozen=True, slots=True)
class MediaAcceptanceReport:
    schema_version: int
    generated_at: str
    source_sha: str
    status: AcceptanceStatus
    fixture_relative_path: str
    fixture_sha256: str
    fixture_size_bytes: int
    ffmpeg: ToolCapability
    stt: ToolCapability
    stt_model: SttModelCapability
    transcript_segments: tuple[TranscriptSegment, ...]
    frames: tuple[FrameEvidence, ...]
    checks: tuple[AcceptanceCheck, ...]
    vision_status: ResearchStatus
    vision_reason: str
    resources: ResourceMeasurements
    cleanup_passed: bool

    def to_dict(self) -> dict[str, object]:
        return _jsonable(asdict(self))


class MediaProcessRunner(Protocol):
    def run(self, argv: Sequence[str], *, cwd: Path, timeout: float) -> SandboxResult: ...


@dataclass(slots=True)
class GovernedMediaRunner:
    guardian: KodeGuardian
    sandbox: ProcessSandbox

    def run(self, argv: Sequence[str], *, cwd: Path, timeout: float) -> SandboxResult:
        if not argv:
            raise ValueError("media argv cannot be empty")
        executable_name = Path(argv[0]).name.lower()
        decision = self.guardian.authorize(
            ActionRequest(
                action=ActionType.EXECUTE,
                actor="KodeResearch.Media",
                target=executable_name,
                project_root=self.sandbox.root,
                sandboxed=True,
                metadata={"executable": executable_name},
            )
        )
        if decision.kind is not DecisionKind.ALLOW:
            raise PermissionError(f"Guardian denied local media helper: {decision.reason}")
        return self.sandbox.run(argv, cwd=cwd, timeout=timeout)


def build_governed_media_runner(project_root: Path) -> GovernedMediaRunner:
    root = Path(project_root).resolve(strict=False)
    allowed = {"ffmpeg", "ffmpeg.exe", "whisper-cli", "whisper-cli.exe"}
    permissions = PermissionSet()
    permissions.grant(
        PermissionGrant(capability=Capability.PROCESS_EXECUTE, executables=tuple(sorted(allowed)))
    )
    return GovernedMediaRunner(
        KodeGuardian(permissions),
        ProcessSandbox(root, allowed_executables=allowed),
    )


def _jsonable(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path, *, max_bytes: int | None = None) -> str:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            total += len(block)
            if max_bytes is not None and total > max_bytes:
                raise MediaProcessingError("file exceeds configured byte budget")
            digest.update(block)
    return digest.hexdigest()


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:512]
    return ""


def _read_git_head(project_root: Path) -> str:
    git_dir = project_root / ".git"
    try:
        raw = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return "UNKNOWN"
    if _GIT_SHA_RE.fullmatch(raw):
        return raw
    if not raw.startswith("ref: "):
        return "UNKNOWN"
    ref_name = raw[5:].strip()
    if ".." in ref_name or ref_name.startswith(("/", "\\")):
        return "UNKNOWN"
    try:
        value = (git_dir / ref_name).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        value = ""
    if _GIT_SHA_RE.fullmatch(value):
        return value
    try:
        lines = (git_dir / "packed-refs").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return "UNKNOWN"
    suffix = f" {ref_name}"
    for line in lines:
        if not line.startswith(("#", "^")) and line.endswith(suffix):
            candidate = line.split(" ", 1)[0]
            if _GIT_SHA_RE.fullmatch(candidate):
                return candidate
    return "UNKNOWN"


def _resolve_model_path(boundary: WorkspaceBoundary, configured: str | None = None) -> tuple[Path, str]:
    model_value = configured or os.environ.get("KODEPOIA_WHISPER_MODEL", DEFAULT_WHISPER_MODEL)
    model_path = boundary.resolve(model_value, must_exist=False)
    return model_path, boundary.relative(model_path)


def _find_executable(name: str) -> Path | None:
    found = shutil.which(name)
    if not found and os.name == "nt" and not name.lower().endswith(".exe"):
        found = shutil.which(f"{name}.exe")
    return Path(found).resolve(strict=False) if found else None


def _probe_tool(
    *,
    name: str,
    executable: Path | None,
    runner: MediaProcessRunner,
    project_root: Path,
    version_args: tuple[str, ...],
    contract_args: tuple[str, ...] | None,
    required_markers: tuple[str, ...],
    timeout: float = 15.0,
) -> ToolCapability:
    if executable is None or not executable.exists() or not executable.is_file():
        return ToolCapability(name=name, status=ResearchStatus.UNAVAILABLE, reason="executable_not_found")
    executable_hash = _sha256_file(executable)
    version_result = runner.run((str(executable), *version_args), cwd=project_root, timeout=timeout)
    if version_result.timed_out or version_result.cancelled or version_result.returncode != 0:
        return ToolCapability(
            name=name,
            status=ResearchStatus.UNAVAILABLE,
            executable_name=executable.name,
            executable_sha256=executable_hash,
            reason="version_probe_failed",
        )
    version = _first_line(version_result.stdout or version_result.stderr)
    contract_text = f"{version_result.stdout}\n{version_result.stderr}"
    if contract_args is not None:
        contract_result = runner.run((str(executable), *contract_args), cwd=project_root, timeout=timeout)
        if contract_result.timed_out or contract_result.cancelled or contract_result.returncode != 0:
            return ToolCapability(
                name=name,
                status=ResearchStatus.UNAVAILABLE,
                executable_name=executable.name,
                version=version,
                executable_sha256=executable_hash,
                reason="contract_probe_failed",
            )
        contract_text = f"{contract_result.stdout}\n{contract_result.stderr}"
    supported = all(marker in contract_text for marker in required_markers)
    return ToolCapability(
        name=name,
        status=ResearchStatus.READY if supported else ResearchStatus.UNAVAILABLE,
        executable_name=executable.name,
        version=version,
        executable_sha256=executable_hash,
        contract_supported=supported,
        reason="" if supported else "required_cli_contract_missing",
    )


@dataclass(slots=True)
class MediaDoctor:
    project_root: Path
    runner: MediaProcessRunner
    ffmpeg_executable: Path | None = None
    whisper_executable: Path | None = None
    whisper_model: str | None = None
    _boundary: WorkspaceBoundary = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root).resolve(strict=False)
        self._boundary = WorkspaceBoundary(self.project_root)
        self.ffmpeg_executable = self.ffmpeg_executable or _find_executable("ffmpeg")
        self.whisper_executable = self.whisper_executable or _find_executable("whisper-cli")

    def run(self) -> MediaDoctorReport:
        ffmpeg = _probe_tool(
            name="ffmpeg",
            executable=self.ffmpeg_executable,
            runner=self.runner,
            project_root=self.project_root,
            version_args=("-version",),
            contract_args=None,
            required_markers=("ffmpeg version",),
        )
        stt = _probe_tool(
            name="whisper.cpp",
            executable=self.whisper_executable,
            runner=self.runner,
            project_root=self.project_root,
            version_args=("--version",),
            contract_args=("-h",),
            required_markers=("--output-json", "--output-json-full", "--output-file", "--no-gpu"),
        )
        model_path, model_relative = _resolve_model_path(self._boundary, self.whisper_model)
        if model_path.exists() and model_path.is_file():
            model = SttModelCapability(
                engine="whisper.cpp",
                status=ResearchStatus.READY,
                relative_path=model_relative,
                sha256=_sha256_file(model_path),
                size_bytes=model_path.stat().st_size,
            )
        else:
            model = SttModelCapability(
                engine="whisper.cpp",
                status=ResearchStatus.UNAVAILABLE,
                relative_path=model_relative,
                reason="model_not_found",
            )
        ready = all(item.status is ResearchStatus.READY for item in (ffmpeg, stt, model))
        return MediaDoctorReport(
            schema_version=MEDIA_SCHEMA_VERSION,
            generated_at=_utc_now(),
            source_sha=_read_git_head(self.project_root),
            ready=ready,
            ffmpeg=ffmpeg,
            stt=stt,
            stt_model=model,
        )


class WhisperCppAdapter:
    def __init__(
        self,
        *,
        runner: MediaProcessRunner,
        executable: Path,
        model_path: Path,
        project_root: Path,
        timeout_seconds: float,
    ) -> None:
        self.runner = runner
        self.executable = executable
        self.model_path = model_path
        self.project_root = project_root
        self.timeout_seconds = timeout_seconds

    def transcribe(self, audio_path: Path, output_base: Path) -> tuple[TranscriptSegment, ...]:
        result = self.runner.run(
            (
                str(self.executable),
                "-m", str(self.model_path),
                "-f", str(audio_path),
                "-l", "en",
                "-ng",
                "-np",
                "-oj",
                "-ojf",
                "-of", str(output_base),
            ),
            cwd=self.project_root,
            timeout=self.timeout_seconds,
        )
        _require_process_success(result, "whisper.cpp transcription")
        json_path = output_base.with_suffix(".json")
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise MediaProcessingError("whisper.cpp JSON output is missing or invalid") from exc
        segments = parse_whisper_json(payload)
        if not segments:
            raise MediaProcessingError("whisper.cpp produced no transcript segments")
        return segments


def parse_whisper_json(payload: object) -> tuple[TranscriptSegment, ...]:
    if not isinstance(payload, dict) or not isinstance(payload.get("transcription"), list):
        raise MediaProcessingError("whisper.cpp JSON is missing transcription array")
    segments: list[TranscriptSegment] = []
    for raw in payload["transcription"]:
        if not isinstance(raw, dict) or not isinstance(raw.get("offsets"), dict):
            continue
        text = str(raw.get("text", "")).strip()
        if not text:
            continue
        offsets = raw["offsets"]
        try:
            start_ms = int(offsets["from"])
            end_ms = int(offsets["to"])
        except (KeyError, TypeError, ValueError):
            continue
        confidence: float | None = None
        if raw.get("confidence") is not None:
            try:
                candidate = float(raw["confidence"])
            except (TypeError, ValueError):
                candidate = -1.0
            if 0.0 <= candidate <= 1.0:
                confidence = candidate
        segments.append(TranscriptSegment(start_ms, end_ms, text, confidence))
    return tuple(segments)


def _fixture_transcript_matches_expected(text: str) -> bool:
    canonical = tuple(
        _NUMBER_CANONICAL.get(token, token)
        for token in _TRANSCRIPT_TOKEN_RE.findall(text.lower())
    )
    width = len(_EXPECTED_FIXTURE_CANONICAL)
    return any(
        canonical[index:index + width] == _EXPECTED_FIXTURE_CANONICAL
        for index in range(max(0, len(canonical) - width + 1))
    )


def _materialize_fixture(
    boundary: WorkspaceBoundary,
    requested: str | Path,
    *,
    temp_dir: Path,
    max_bytes: int,
) -> tuple[Path, str]:
    logical = boundary.resolve(requested, must_exist=False)
    logical_relative = boundary.relative(logical)
    if logical.exists():
        if not logical.is_file():
            raise MediaProcessingError("media fixture must be a file")
        return logical, logical_relative
    encoded = boundary.resolve(f"{logical_relative}.b64", must_exist=True)
    if not encoded.is_file():
        raise MediaProcessingError("encoded media fixture must be a file")
    if encoded.stat().st_size > ((max_bytes * 4) // 3) + 4096:
        raise MediaProcessingError("encoded media fixture exceeds configured byte budget")
    try:
        raw = base64.b64decode(encoded.read_text(encoding="ascii").strip(), validate=True)
    except (OSError, UnicodeError, binascii.Error) as exc:
        raise MediaProcessingError("encoded media fixture is invalid base64") from exc
    if len(raw) > max_bytes:
        raise MediaProcessingError("decoded media fixture exceeds configured byte budget")
    materialized = temp_dir / logical.name
    materialized.write_bytes(raw)
    return materialized, logical_relative


def _directory_bytes(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


@dataclass(slots=True)
class LocalMediaAcceptance:
    project_root: Path
    runner: MediaProcessRunner
    doctor: MediaDoctor
    policy: MediaExecutionPolicy = field(default_factory=MediaExecutionPolicy)
    frame_analysis: FrameAnalysisProvider = field(default_factory=UnavailableFrameAnalysisProvider)
    _boundary: WorkspaceBoundary = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.project_root = Path(self.project_root).resolve(strict=False)
        self._boundary = WorkspaceBoundary(self.project_root)

    def run(self, fixture: str | Path) -> MediaAcceptanceReport:
        started = time.monotonic()
        checks: list[AcceptanceCheck] = []
        doctor_report = self.doctor.run()
        transcripts: tuple[TranscriptSegment, ...] = ()
        frames: tuple[FrameEvidence, ...] = ()
        cleanup_passed = False
        vision_status = ResearchStatus.UNAVAILABLE
        vision_reason = "no_accepted_local_vision_provider_configured"
        fixture_hash = "0" * 64
        fixture_size = 0
        fixture_relative = str(fixture).replace("\\", "/")
        temporary_peak = 0

        temp_root = self._boundary.resolve(".kodepoia/research/tmp", must_exist=False)
        temp_root.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix="r7_7_", dir=temp_root))
        try:
            fixture_path, fixture_relative = _materialize_fixture(
                self._boundary,
                fixture,
                temp_dir=temp_dir,
                max_bytes=self.policy.max_input_bytes,
            )
            fixture_size = fixture_path.stat().st_size
            fixture_hash = _sha256_file(fixture_path, max_bytes=self.policy.max_input_bytes)
            checks.extend(
                (
                    AcceptanceCheck("source_sha_exact", bool(_GIT_SHA_RE.fullmatch(doctor_report.source_sha)), doctor_report.source_sha),
                    AcceptanceCheck("fixture_budget", fixture_size <= self.policy.max_input_bytes, str(fixture_size)),
                    AcceptanceCheck("fixture_hash", fixture_hash == EXPECTED_FIXTURE_SHA256, fixture_hash),
                    AcceptanceCheck("ffmpeg_ready", doctor_report.ffmpeg.status is ResearchStatus.READY, doctor_report.ffmpeg.reason),
                    AcceptanceCheck("stt_ready", doctor_report.stt.status is ResearchStatus.READY, doctor_report.stt.reason),
                    AcceptanceCheck("stt_model_ready", doctor_report.stt_model.status is ResearchStatus.READY, doctor_report.stt_model.reason),
                )
            )
            if all(item.passed for item in checks):
                ffmpeg = self.doctor.ffmpeg_executable
                whisper = self.doctor.whisper_executable
                model_path, _ = _resolve_model_path(self._boundary, self.doctor.whisper_model)
                if ffmpeg is None or whisper is None:
                    raise MediaProcessingError("doctor reported READY without executable paths")

                audio_path = temp_dir / "audio.wav"
                audio_result = self.runner.run(
                    (
                        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                        "-i", str(fixture_path), "-vn", "-ac", "1", "-ar", "16000",
                        "-c:a", "pcm_s16le", str(audio_path),
                    ),
                    cwd=self.project_root,
                    timeout=self.policy.ffmpeg_timeout_seconds,
                )
                _require_process_success(audio_result, "ffmpeg audio extraction")
                checks.append(AcceptanceCheck("audio_extracted", audio_path.exists() and audio_path.stat().st_size > 44))
                temporary_peak = max(temporary_peak, _directory_bytes(temp_dir))

                transcripts = WhisperCppAdapter(
                    runner=self.runner,
                    executable=whisper,
                    model_path=model_path,
                    project_root=self.project_root,
                    timeout_seconds=self.policy.stt_timeout_seconds,
                ).transcribe(audio_path, temp_dir / "transcript")
                normalized = " ".join(segment.text.lower() for segment in transcripts)
                checks.append(AcceptanceCheck("transcript_tokens", _fixture_transcript_matches_expected(normalized), normalized[:256]))
                checks.append(AcceptanceCheck("transcript_timestamps", all(s.start_ms >= 0 and s.end_ms >= s.start_ms for s in transcripts), str(len(transcripts))))
                temporary_peak = max(temporary_peak, _directory_bytes(temp_dir))

                frame_items: list[FrameEvidence] = []
                analyses: list[FrameAnalysisResult] = []
                for index, timestamp_ms in enumerate(self.policy.frame_timestamps_ms, start=1):
                    frame_path = temp_dir / f"frame_{index:02d}.png"
                    frame_result = self.runner.run(
                        (
                            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                            "-ss", f"{timestamp_ms / 1000:.3f}", "-i", str(fixture_path),
                            "-an", "-frames:v", "1", "-vf", f"scale={self.policy.frame_width}:-2",
                            str(frame_path),
                        ),
                        cwd=self.project_root,
                        timeout=self.policy.ffmpeg_timeout_seconds,
                    )
                    _require_process_success(frame_result, f"ffmpeg frame extraction at {timestamp_ms}ms")
                    frame_items.append(_validate_frame(frame_path, timestamp_ms, self.policy.max_frame_pixels))
                    analyses.append(self.frame_analysis.analyze(frame_path, timestamp_ms=timestamp_ms))
                    temporary_peak = max(temporary_peak, _directory_bytes(temp_dir))
                    if temporary_peak > self.policy.max_temporary_bytes:
                        raise MediaProcessingError("temporary media exceeds configured disk budget")
                frames = tuple(frame_items)
                checks.append(AcceptanceCheck("frame_count", len(frames) == len(self.policy.frame_timestamps_ms), str(len(frames))))
                checks.append(AcceptanceCheck("frame_hashes_unique", len({item.sha256 for item in frames}) == len(frames)))
                checks.append(AcceptanceCheck("temporary_disk_budget", temporary_peak <= self.policy.max_temporary_bytes, str(temporary_peak)))
                if analyses and any(item.status is ResearchStatus.READY for item in analyses):
                    vision_status = ResearchStatus.READY
                    vision_reason = ""
                elif analyses:
                    vision_reason = analyses[0].reason
            else:
                checks.append(AcceptanceCheck("processing_prerequisites", False, "doctor_or_fixture_prerequisite_failed"))
        except (MediaProcessingError, OSError) as exc:
            checks.append(AcceptanceCheck("processing", False, str(exc)))
        finally:
            try:
                shutil.rmtree(temp_dir)
                cleanup_passed = not temp_dir.exists()
            except OSError:
                cleanup_passed = False
            checks.append(AcceptanceCheck("temporary_cleanup", cleanup_passed))

        elapsed_ms = max(0, int((time.monotonic() - started) * 1000))
        required_pass = all(check.passed for check in checks)
        status = AcceptanceStatus.PASS if required_pass and transcripts and frames else AcceptanceStatus.FAIL
        return MediaAcceptanceReport(
            schema_version=MEDIA_SCHEMA_VERSION,
            generated_at=_utc_now(),
            source_sha=doctor_report.source_sha,
            status=status,
            fixture_relative_path=fixture_relative,
            fixture_sha256=fixture_hash,
            fixture_size_bytes=fixture_size,
            ffmpeg=doctor_report.ffmpeg,
            stt=doctor_report.stt,
            stt_model=doctor_report.stt_model,
            transcript_segments=transcripts,
            frames=frames,
            checks=tuple(checks),
            vision_status=vision_status,
            vision_reason=vision_reason,
            resources=ResourceMeasurements(
                elapsed_ms=elapsed_ms,
                input_bytes=fixture_size,
                temporary_peak_bytes=temporary_peak,
            ),
            cleanup_passed=cleanup_passed,
        )


def _require_process_success(result: SandboxResult, label: str) -> None:
    if result.timed_out:
        raise MediaProcessingError(f"{label} timed out")
    if result.cancelled:
        raise MediaProcessingError(f"{label} was cancelled")
    if result.returncode != 0:
        raise MediaProcessingError(f"{label} failed")


def _validate_frame(path: Path, timestamp_ms: int, max_pixels: int) -> FrameEvidence:
    if not path.exists() or not path.is_file():
        raise MediaProcessingError("ffmpeg did not produce expected frame")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
    except Exception as exc:
        raise MediaProcessingError("extracted frame is not a valid image") from exc
    if width * height > max_pixels:
        raise MediaProcessingError("extracted frame exceeds pixel budget")
    return FrameEvidence(
        timestamp_ms=timestamp_ms,
        sha256=_sha256_file(path, max_bytes=16 * 1024 * 1024),
        width=width,
        height=height,
    )


def write_json_report(project_root: Path, relative_path: str | Path, payload: dict[str, object]) -> Path:
    boundary = WorkspaceBoundary(Path(project_root).resolve(strict=False))
    destination = boundary.resolve(relative_path, must_exist=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination
