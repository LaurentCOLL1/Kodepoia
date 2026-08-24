from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..audio.qa import AudioQAProfile, evaluate_wav
from ..audio.wav import AudioFormatError, inspect_wav_bytes
from ..contracts import MediaState
from ..voice import VoiceModelBinding
from .contracts import SynthesisLimits, SynthesisRequest
from .piper import PiperAdapter, PiperCapabilityReport, sha256_file


class TTSRunError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SynthesisManifest:
    source_sha: str
    request_digest: str
    text_sha256: str
    cache_key: str
    backend_id: str
    runtime_executable_sha256: str
    runtime_help_sha256: str
    model_sha256: str
    config_sha256: str
    output_sha256: str
    output_bytes: int
    wav_facts: dict[str, Any]
    qa: dict[str, Any]
    process: dict[str, Any]
    status: str
    blockers: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "source_sha": self.source_sha,
            "request_digest": self.request_digest,
            "text_sha256": self.text_sha256,
            "cache_key": self.cache_key,
            "backend_id": self.backend_id,
            "runtime_executable_sha256": self.runtime_executable_sha256,
            "runtime_help_sha256": self.runtime_help_sha256,
            "model_sha256": self.model_sha256,
            "config_sha256": self.config_sha256,
            "output_sha256": self.output_sha256,
            "output_bytes": self.output_bytes,
            "wav_facts": self.wav_facts,
            "qa": self.qa,
            "process": self.process,
            "status": self.status,
            "blockers": list(self.blockers),
        }


def synthesize_local(
    adapter: PiperAdapter,
    *,
    executable: Path,
    model_path: Path,
    config_path: Path,
    output_path: Path,
    binding: VoiceModelBinding,
    request: SynthesisRequest,
    source_sha: str,
    limits: SynthesisLimits | None = None,
    capability_report: PiperCapabilityReport | None = None,
) -> SynthesisManifest:
    active_limits = limits or SynthesisLimits()
    probe = capability_report or adapter.capability_probe(executable)
    if probe.status != "pass":
        raise TTSRunError("Piper capability probe failed")
    model_sha = sha256_file(model_path)
    config_sha = sha256_file(config_path, max_bytes=16 * 1024 * 1024)
    cache_key = request.cache_key(
        runtime_sha256=probe.executable_sha256,
        model_sha256=model_sha,
        config_sha256=config_sha,
    )
    argv = adapter.compile_synthesis_argv(
        executable,
        model_path,
        config_path,
        output_path,
        binding=binding,
        request=request,
    )
    result = adapter.sandbox.run(argv, timeout=active_limits.timeout_seconds)
    blockers: list[str] = []
    if result.timed_out:
        blockers.append("synthesis_timeout")
    if result.cancelled:
        blockers.append("synthesis_cancelled")
    if result.returncode != 0:
        blockers.append("synthesis_nonzero")
    if len(result.stdout.encode("utf-8", errors="replace")) > active_limits.max_stdout_bytes:
        blockers.append("stdout_budget")
    if len(result.stderr.encode("utf-8", errors="replace")) > active_limits.max_stderr_bytes:
        blockers.append("stderr_budget")

    output = Path(output_path).resolve(strict=False)
    output_bytes = b""
    facts_payload: dict[str, Any] = {}
    qa_payload: dict[str, Any] = {}
    output_sha = "0" * 64
    if not output.exists() or not output.is_file():
        blockers.append("output_missing")
    else:
        size = output.stat().st_size
        if size <= 0 or size > active_limits.max_output_bytes:
            blockers.append("output_byte_budget")
        else:
            output_bytes = output.read_bytes()
            output_sha = hashlib.sha256(output_bytes).hexdigest()
            try:
                facts = inspect_wav_bytes(
                    output_bytes,
                    max_bytes=active_limits.max_output_bytes,
                    max_duration_seconds=active_limits.max_duration_seconds,
                )
                facts_payload = facts.canonical()
                qa = evaluate_wav(
                    output_sha,
                    facts,
                    AudioQAProfile(
                        profile_id="tts.local.v1",
                        max_duration_seconds=active_limits.max_duration_seconds,
                    ),
                )
                qa_payload = qa.canonical()
                if qa.state not in {MediaState.PASS, MediaState.WARN}:
                    blockers.append("audio_qa_blocked")
            except AudioFormatError:
                blockers.append("wav_validation_failed")

    process_payload = {
        "returncode": result.returncode,
        "timed_out": result.timed_out,
        "cancelled": result.cancelled,
        "stdout_bytes": len(result.stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(result.stderr.encode("utf-8", errors="replace")),
    }
    return SynthesisManifest(
        source_sha=source_sha,
        request_digest=request.cache_key(
            runtime_sha256="0" * 64,
            model_sha256=binding.model_sha256,
            config_sha256=binding.config_sha256,
        ),
        text_sha256=request.text_sha256,
        cache_key=cache_key,
        backend_id=adapter.backend_id,
        runtime_executable_sha256=probe.executable_sha256,
        runtime_help_sha256=probe.help_sha256,
        model_sha256=model_sha,
        config_sha256=config_sha,
        output_sha256=output_sha,
        output_bytes=len(output_bytes),
        wav_facts=facts_payload,
        qa=qa_payload,
        process=process_payload,
        status="pass" if not blockers else "fail",
        blockers=tuple(sorted(set(blockers))),
    )
