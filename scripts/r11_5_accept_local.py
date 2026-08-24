from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.media.boundary import MediaRuntimeBoundary
from kodepoia.media.serialization import canonical_sha256
from kodepoia.media.tts import PiperAdapter, SynthesisLimits, SynthesisRequest, synthesize_local
from kodepoia.media.tts.piper import sha256_file
from kodepoia.media.voice import AllowedUse, RightsDeclaration, VoiceModelBinding, VoiceProfile

_SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
_APPROVAL = "I_REVIEWED_AND_APPROVE_THIS_VOICE_LICENSE"


def _fixture_text(locale: str) -> str:
    language = locale.replace("_", "-").split("-", 1)[0].lower()
    if language == "fr":
        return "Kodepoia vérifie une synthèse vocale locale, reproductible et hors ligne."
    if language == "en":
        return "Kodepoia verifies local, reproducible, offline speech synthesis."
    return "Kodepoia local TTS acceptance, version one."


def _evidence_digest(payload: dict[str, object]) -> str:
    without_digest = {key: value for key, value in payload.items() if key != "evidence_digest"}
    return canonical_sha256(without_digest)


def main() -> int:
    parser = argparse.ArgumentParser(description="R11.5 real local Piper-compatible TTS acceptance collector")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--piper", required=True, help="Exact existing piper/piper.exe executable path; never downloaded by this script")
    parser.add_argument("--model", required=True, help="Existing approved .onnx voice model")
    parser.add_argument("--config", required=True, help="Exact approved <model>.onnx.json sibling")
    parser.add_argument("--locale", required=True, help="Locale such as fr-FR")
    parser.add_argument("--license-id", required=True, help="Reviewed per-voice/model license identifier, e.g. cc-by-4.0")
    parser.add_argument("--provenance-id", required=True, help="Stable provenance identifier for the reviewed voice package")
    parser.add_argument("--speaker", type=int)
    parser.add_argument("--approval", required=True, help=f"Must equal {_APPROVAL}")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if _SOURCE_RE.fullmatch(args.source_sha) is None:
        raise SystemExit("--source-sha must be the exact lowercase 40-character candidate SHA")
    if args.approval != _APPROVAL:
        raise SystemExit(f"--approval must be exactly {_APPROVAL} after you review the voice/model license")

    piper = Path(args.piper).resolve(strict=True)
    model = Path(args.model).resolve(strict=True)
    config = Path(args.config).resolve(strict=True)
    if piper.name.lower() not in {"piper", "piper.exe"}:
        raise SystemExit("--piper must point to the piper or piper.exe console executable")
    if model.suffix.lower() != ".onnx":
        raise SystemExit("--model must be an existing .onnx file")
    if config.suffix.lower() != ".json":
        raise SystemExit("--config must be an existing .json file")
    expected_config = model.with_name(model.name + ".json")
    if config != expected_config:
        raise SystemExit("--config must be the exact <model>.onnx.json sibling next to --model")

    model_sha = sha256_file(model)
    config_sha = sha256_file(config, max_bytes=16 * 1024 * 1024)
    rights = RightsDeclaration(
        provenance_id=args.provenance_id,
        license_id=args.license_id,
        allowed_uses=(AllowedUse.INTERNAL,),
        source_uri_id=f"{args.provenance_id}.model-card",
    )
    binding = VoiceModelBinding(
        binding_id="binding.r11.5.local",
        backend_id="piper-compatible",
        model_sha256=model_sha,
        config_sha256=config_sha,
        locale=args.locale,
        rights=rights,
        speaker_id=None if args.speaker is None else f"speaker.{args.speaker}",
        display_label="R11.5 approved local synthetic voice",
    )
    profile = VoiceProfile(
        profile_id="voice.r11.5.local",
        scope_id="acceptance.r11.5",
        locale=args.locale,
        display_name="R11.5 local acceptance voice",
    )
    request = SynthesisRequest.from_profile(
        request_id="tts.r11.5.local.acceptance",
        profile=profile,
        binding=binding,
        text=_fixture_text(binding.locale),
        speaker_id=args.speaker,
        allowed_use=AllowedUse.INTERNAL,
    )

    output = Path(args.output).resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    blockers: list[str] = []
    manifest_payload: dict[str, object] = {}
    capability_payload: dict[str, object] = {}

    with tempfile.TemporaryDirectory(prefix="kodepoia-r11-5-") as temp:
        staging = Path(temp).resolve()
        boundary = MediaRuntimeBoundary(allowed_roots=(piper.parent,), staging_root=staging)
        sandbox = ProcessSandbox(staging, allowed_executables={"piper", "piper.exe"})
        adapter = PiperAdapter(boundary, sandbox, model_root=model.parent)
        probe = adapter.capability_probe(piper)
        capability_payload = probe.canonical()
        if probe.status != "pass":
            blockers.extend(probe.blockers or ("runtime_probe_failed",))
        if not blockers:
            manifest = synthesize_local(
                adapter,
                executable=piper,
                model_path=model,
                config_path=config,
                output_path=staging / "r11_5_acceptance.wav",
                binding=binding,
                request=request,
                source_sha=args.source_sha,
                limits=SynthesisLimits(timeout_seconds=90.0, max_output_bytes=32 * 1024 * 1024, max_duration_seconds=30.0),
                capability_report=probe,
            )
            manifest_payload = manifest.canonical()
            blockers.extend(manifest.blockers)
            if manifest.status != "pass":
                blockers.append("synthesis_manifest_failed")
            qa = manifest.qa
            if qa.get("state") != "PASS":
                blockers.append("audio_qa_not_pass")
            facts = manifest.wav_facts
            if not isinstance(facts.get("duration_seconds"), (int, float)) or float(facts["duration_seconds"]) <= 0.05:
                blockers.append("audio_duration_too_short")

    evidence: dict[str, object] = {
        "schema": "kodepoia.r11_5_local_acceptance",
        "version": 1,
        "source_sha": args.source_sha,
        "status": "pass" if not blockers else "fail",
        "blockers": sorted(set(blockers)),
        "approval": {
            "license_reviewed": True,
            "license_id": args.license_id,
            "provenance_id": args.provenance_id,
            "allowed_use": AllowedUse.INTERNAL.value,
            "locale": binding.locale,
        },
        "voice_identity": {
            "model_sha256": model_sha,
            "config_sha256": config_sha,
            "binding_digest": binding.digest(),
            "profile_digest": profile.digest(),
        },
        "capability": capability_payload,
        "synthesis": manifest_payload,
        "privacy": {
            "private_recording_used": False,
            "voice_clone_used": False,
            "network_download_performed_by_collector": False,
            "audio_retained": False,
        },
    }
    evidence["evidence_digest"] = _evidence_digest(evidence)
    output.write_text(json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if not blockers else 17


if __name__ == "__main__":
    raise SystemExit(main())
