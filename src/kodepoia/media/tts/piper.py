from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodepoia.core.sandbox import ProcessSandbox

from ..boundary import MediaRuntimeBoundary
from ..contracts import MediaRuntimeKind
from ..voice import VoiceModelBinding
from .contracts import SynthesisRequest, TTSBackendCapabilities

_REQUIRED_HELP_MARKERS = ("--model", "--config", "--output-file", "--speaker", "--length-scale")


def sha256_file(path: Path, *, max_bytes: int = 512 * 1024 * 1024) -> str:
    resolved = Path(path).resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("hash input must be a regular file")
    size = resolved.stat().st_size
    if size <= 0 or size > max_bytes:
        raise ValueError("hash input byte size is outside accepted bounds")
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class PiperCapabilityReport:
    executable_sha256: str
    help_sha256: str
    capabilities: TTSBackendCapabilities
    status: str
    blockers: tuple[str, ...] = ()

    def canonical(self) -> dict[str, Any]:
        return {
            "executable_sha256": self.executable_sha256,
            "help_sha256": self.help_sha256,
            "capabilities": self.capabilities.canonical(),
            "status": self.status,
            "blockers": list(self.blockers),
        }


class PiperAdapter:
    backend_id = "piper-compatible"

    def __init__(self, boundary: MediaRuntimeBoundary, sandbox: ProcessSandbox, *, model_root: Path) -> None:
        self.boundary = boundary
        self.sandbox = sandbox
        self.model_root = Path(model_root).resolve(strict=False)

    @property
    def capabilities(self) -> TTSBackendCapabilities:
        return TTSBackendCapabilities(
            backend_id=self.backend_id,
            supports_explicit_model_path=True,
            supports_explicit_config_path=True,
            supports_output_wav=True,
            supports_speaker_id=True,
            supports_length_scale=True,
            network_required=False,
        )

    def capability_probe(self, executable: Path, *, timeout_seconds: float = 15.0) -> PiperCapabilityReport:
        exe = self.boundary.validate_executable(MediaRuntimeKind.TTS, executable)
        runtime_sha = sha256_file(exe, max_bytes=128 * 1024 * 1024)
        result = self.sandbox.run((str(exe), "--help"), timeout=timeout_seconds)
        help_text = (result.stdout or "") + "\n" + (result.stderr or "")
        help_sha = hashlib.sha256(help_text.encode("utf-8", errors="replace")).hexdigest()
        blockers: list[str] = []
        if result.timed_out:
            blockers.append("runtime_probe_timeout")
        if result.cancelled:
            blockers.append("runtime_probe_cancelled")
        if result.returncode != 0:
            blockers.append("runtime_probe_nonzero")
        lowered = help_text.lower()
        for marker in _REQUIRED_HELP_MARKERS:
            if marker not in lowered:
                blockers.append(f"missing_capability_{marker[2:].replace('-', '_')}")
        return PiperCapabilityReport(runtime_sha, help_sha, self.capabilities, "pass" if not blockers else "fail", tuple(sorted(set(blockers))))

    def compile_synthesis_argv(
        self,
        executable: Path,
        model_path: Path,
        config_path: Path,
        output_path: Path,
        *,
        binding: VoiceModelBinding,
        request: SynthesisRequest,
    ) -> tuple[str, ...]:
        if binding.backend_id != self.backend_id:
            raise ValueError("voice binding backend does not match Piper adapter")
        if request.binding_digest != binding.digest():
            raise ValueError("synthesis request binding identity is stale")
        exe = self.boundary.validate_executable(MediaRuntimeKind.TTS, executable)
        model = self.boundary.validate_input(model_path, root=self.model_root, suffixes=frozenset({".onnx"}))
        config = self.boundary.validate_input(config_path, root=self.model_root, suffixes=frozenset({".json"}))
        output = self.boundary.validate_output(output_path, suffixes=frozenset({".wav"}))
        model_sha = sha256_file(model)
        config_sha = sha256_file(config, max_bytes=16 * 1024 * 1024)
        if model_sha != binding.model_sha256 or config_sha != binding.config_sha256:
            raise ValueError("voice model/config bytes do not match governed binding identity")
        argv: list[str] = [
            str(exe),
            "--model",
            str(model),
            "--config",
            str(config),
            "--output-file",
            str(output),
            "--length-scale",
            f"{float(request.length_scale):.8g}",
        ]
        if request.speaker_id is not None:
            argv.extend(("--speaker", str(request.speaker_id)))
        argv.extend(("--", request.text))
        return tuple(argv)
