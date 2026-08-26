from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

from kodepoia.mobile.android_signing import AndroidSigningState
from kodepoia.mobile.contracts import StoreReadinessState
from kodepoia.mobile.google_play import (
    PlayAabCandidate,
    PlayAssetKind,
    PlayContentRatingDeclaration,
    PlayDataSafetyDeclaration,
    PlayDeclarationState,
    PlayLocalizedListing,
    PlayPermissionDeclaration,
    PlayReleaseIntent,
    PlayReleaseKind,
    PlayReleaseTrack,
    PlaySdkDeclaration,
    PlayStoreAsset,
    PlayStoreMetadata,
    current_google_play_policy_snapshot,
    evaluate_google_play_readiness,
)

ROOT = Path(__file__).resolve().parents[1]
_SHA = re.compile(r"^[0-9a-f]{40}$")


def build_acceptance_payload(source_sha: str) -> dict[str, object]:
    if _SHA.fullmatch(source_sha) is None:
        raise ValueError("--source-sha must be an exact lowercase 40-hex Git SHA")
    policy = current_google_play_policy_snapshot()
    artifact_sha = "11" * 32
    candidate = PlayAabCandidate(
        application_id="com.kodepoia.r13acceptance",
        artifact_sha256=artifact_sha,
        target_sdk=36,
        build_evidence_sha256="22" * 32,
        signing_state=AndroidSigningState.PLAY_APP_SIGNING_READY,
        signing_artifact_sha256=artifact_sha,
    )
    metadata = PlayStoreMetadata(
        application_id=candidate.application_id,
        localizations=(
            PlayLocalizedListing(
                "en-US",
                "Kodepoia",
                "Governed mobile readiness",
                "Deterministic Google Play readiness evidence for Kodepoia.",
            ),
            PlayLocalizedListing(
                "fr-FR",
                "Kodepoia",
                "Préparation mobile gouvernée",
                "Preuve déterministe de préparation Google Play pour Kodepoia.",
            ),
        ),
        assets=(PlayStoreAsset(PlayAssetKind.ICON, "33" * 32),),
    )
    report = evaluate_google_play_readiness(
        source_sha=source_sha,
        evaluated_on="2026-08-31",
        policy=policy,
        release=PlayReleaseIntent(
            release_id="r13.7-hosted-dry-run",
            application_id=candidate.application_id,
            track=PlayReleaseTrack.CLOSED,
            release_kind=PlayReleaseKind.FIRST_RELEASE,
        ),
        candidate=candidate,
        metadata=metadata,
        data_safety=PlayDataSafetyDeclaration(
            PlayDeclarationState.COMPLETE,
            privacy_policy_url="https://example.invalid/privacy",
            third_party_sdks_reviewed=True,
        ),
        content_rating=PlayContentRatingDeclaration(
            PlayDeclarationState.COMPLETE,
            "44" * 32,
        ),
        permissions=(
            PlayPermissionDeclaration("android.permission.INTERNET"),
        ),
        sdks=(PlaySdkDeclaration("kodepoia.fixture", True, True),),
    )
    if report.store_status.readiness is not StoreReadinessState.STORE_READY:
        raise RuntimeError("canonical R13.7 dry-run fixture is not store-ready")
    if not report.dry_run or report.publish_attempted:
        raise RuntimeError("R13.7 acceptance must never publish")

    stale = evaluate_google_play_readiness(
        source_sha=source_sha,
        evaluated_on="2026-10-01",
        policy=policy,
        release=PlayReleaseIntent(
            release_id="r13.7-stale-policy",
            application_id=candidate.application_id,
            track=PlayReleaseTrack.CLOSED,
            release_kind=PlayReleaseKind.FIRST_RELEASE,
        ),
        candidate=candidate,
        metadata=metadata,
        data_safety=PlayDataSafetyDeclaration(
            PlayDeclarationState.COMPLETE,
            privacy_policy_url="https://example.invalid/privacy",
            third_party_sdks_reviewed=True,
        ),
        content_rating=PlayContentRatingDeclaration(
            PlayDeclarationState.COMPLETE,
            "44" * 32,
        ),
    )
    if stale.policy_freshness.value != "STALE":
        raise RuntimeError("stale policy snapshot was not detected")
    if stale.store_status.readiness is not StoreReadinessState.BLOCKED:
        raise RuntimeError("stale policy snapshot manufactured readiness")

    payload = report.to_dict()
    schema = json.loads(
        (ROOT / "schemas/r13/google-play-readiness.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="R13.7 Google Play dry-run acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = build_acceptance_payload(args.source_sha)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({
        "output": str(output),
        "source_sha": payload["source_sha"],
        "readiness": payload["store_status"]["readiness"],
        "policy_freshness": payload["policy_freshness"],
        "dry_run": payload["dry_run"],
        "publish_attempted": payload["publish_attempted"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
