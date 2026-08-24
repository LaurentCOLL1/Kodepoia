from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..audio.qa import AudioQAProfile, evaluate_wav
from ..audio.wav import AudioFormatError, inspect_wav_bytes
from ..contracts import MediaState
from ..serialization import canonical_sha256
from ..voice import VoiceModelBinding
from .contracts import SynthesisLimits, SynthesisRequest
from .piper import PiperAdapter, PiperCapabilityReport, sha256_file

_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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


def _tts_clipping_budget(frame_count: int, channels: int) -> int:
    """Allow isolated full-scale samples without weakening generic R11.2 audio QA.

    R11.2 counts a 16-bit sample at either full-scale endpoint as clipped. For
    local neural TTS, a single isolated endpoint sample is not sufficient by
    itself to establish an audibly flattened waveform. Keep the exception tiny:
    at most 10 ppm of samples, with an absolute cap of 16.
    """

    sample_count = max(1, int(frame_count) * max(1, int(channels)))
    return max(1, min(16, sample_count // 100_000))


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
    if not isinstance(source_sha, str) or _SOURCE_SHA_RE.fullmatch(source_sha) is None:
        raise ValueError("source_sha must be the exact lowercase 40-character candidate SHA")
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
    request_digest = canonical_sha256({"schema_version": 1, "request": request.canonical()})

    output = adapter.boundary.validate_output(output_path, suffixes=frozenset({".wav"}))
    input_path = output.with_suffix(".input.txt")
    adapter.boundary.validate_output(input_path, suffixes=frozenset({".txt"}))
    if output.exists():
        output.unlink()
    if input_path.exists():
        input_path.unlink()
    input_path.write_text(request.text + "\n", encoding="utf-8", newline="\n")

    try:
        argv = adapter.compile_synthesis_argv(
            executable,
            model_path,
            config_path,
            input_path,
            output,
            binding=binding,
            request=request,
        )
        result = adapter.sandbox.run(argv, timeout=active_limits.timeout_seconds)
    finally:
        try:
            input_path.unlink(missing_ok=True)
        except OSError:
            pass

    blockers: list[str] = []
    if result.timed_out:
        blockers.append("synthesis_timeout")
    if result.cancelled:
        blockers.append("synthesis_cancelled")
    if result.returncode != 0:
        blockers.append("synthesis_nonzero")
    stdout_bytes = len(result.stdout.encode("utf-8", errors="replace"))
    stderr_bytes = len(result.stderr.encode("utf-8", errors="replace"))
    if stdout_bytes > active_limits.max_stdout_bytes:
        blockers.append("stdout_budget")
    if stderr_bytes > active_limits.max_stderr_bytes:
        blockers.append("stderr_budget")

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
                        profile_id="tts.local.v2",
                        max_duration_seconds=active_limits.max_duration_seconds,
                        max_clipped_samples=_tts_clipping_budget(facts.frame_count, facts.channels),
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
        "stdout_bytes": stdout_bytes,
        "stderr_bytes": stderr_bytes,
        "text_passed_via_argv": False,
        "ephemeral_input_deleted": not input_path.exists(),
    }
    return SynthesisManifest(
        source_sha=source_sha,
        request_digest=request_digest,
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
