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
from kodepoia.models import KodeModelRegistry

_SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
_APPROVAL = "I_REVIEWED_AND_APPROVE_THIS_VOICE_LICENSE"
_DEFAULT_MODEL_ID = "tts.piper.fr-FR.siwis-medium"


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
    parser.add_argument("--model-id", default=_DEFAULT_MODEL_ID, help="KodeModelRegistry id under repository-local models/")
    parser.add_argument("--repo-root", default=".", help="Kodepoia repository root containing models/registry/models.json")
    parser.add_argument("--speaker", type=int)
    parser.add_argument("--approval", required=True, help=f"Must equal {_APPROVAL}")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if _SOURCE_RE.fullmatch(args.source_sha) is None:
        raise SystemExit("--source-sha must be the exact lowercase 40-character candidate SHA")
    if args.approval != _APPROVAL:
        raise SystemExit(f"--approval must be exactly {_APPROVAL} after you review the voice/model license")

    piper = Path(args.piper).resolve(strict=True)
    if piper.name.lower() not in {"piper", "piper.exe"}:
        raise SystemExit("--piper must point to the piper or piper.exe console executable")

    registry = KodeModelRegistry(Path(args.repo_root))
    try:
        model_manifest = registry.manifest(args.model_id)
        model = registry.resolve_file(args.model_id, "model", verify=True)
        config = registry.resolve_file(args.model_id, "config", verify=True)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        raise SystemExit(f"KodeModelRegistry rejected local model {args.model_id!r}: {exc}") from exc

    if model_manifest.purpose != "tts" or model_manifest.backend != "piper-compatible":
        raise SystemExit("selected model manifest is not an accepted Piper-compatible TTS model")
    if model_manifest.locale is None:
        raise SystemExit("selected TTS model manifest must declare locale")
    if AllowedUse.INTERNAL.value not in model_manifest.allowed_uses:
        raise SystemExit("selected TTS model manifest does not permit internal acceptance use")

    model_sha = sha256_file(model)
    config_sha = sha256_file(config, max_bytes=16 * 1024 * 1024)
    manifest_digest = canonical_sha256(model_manifest.canonical())
    rights = RightsDeclaration(
        provenance_id=model_manifest.provenance_id,
        license_id=model_manifest.license_id,
        allowed_uses=(AllowedUse.INTERNAL,),
        source_uri_id=f"{model_manifest.provenance_id}.model-card",
    )
    binding = VoiceModelBinding(
        binding_id="binding.r11.5.local",
        backend_id="piper-compatible",
        model_sha256=model_sha,
        config_sha256=config_sha,
        locale=model_manifest.locale,
        rights=rights,
        speaker_id=None if args.speaker is None else f"speaker.{args.speaker}",
        display_label="R11.5 approved repository-local synthetic voice",
    )
    profile = VoiceProfile(
        profile_id="voice.r11.5.local",
        scope_id="acceptance.r11.5",
        locale=model_manifest.locale,
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
            "license_id": model_manifest.license_id,
            "provenance_id": model_manifest.provenance_id,
            "allowed_use": AllowedUse.INTERNAL.value,
            "locale": binding.locale,
        },
        "voice_identity": {
            "model_id": model_manifest.model_id,
            "manifest_digest": manifest_digest,
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
