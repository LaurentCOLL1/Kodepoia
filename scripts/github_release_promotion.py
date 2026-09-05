from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from kodepoia.release.promotion import (
    DEFAULT_REPOSITORY,
    ReleasePromotionError,
    build_publish_request,
    stage_release_archive,
    verify_published_release,
)


def _read_object(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleasePromotionError(f"unable to read JSON object {target}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleasePromotionError(f"JSON root must be an object: {target}")
    return payload


def _write_object(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "R18.5 GitHub Release staging contract. "
            "This command performs no GitHub write operation."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    stage = sub.add_parser("stage", help="verify an exact release bundle and stage metadata")
    stage.add_argument("--bundle", required=True)
    stage.add_argument("--source-sha", required=True)
    stage.add_argument("--repository", default=DEFAULT_REPOSITORY)
    stage.add_argument("--signing-evidence", required=True)
    stage.add_argument("--attestation-receipt", required=True)
    stage.add_argument("--tag-state", required=True)
    stage.add_argument("--output", required=True)

    prepare = sub.add_parser(
        "prepare-draft",
        help="build a create-draft-only GitHub REST request from an exact staged digest",
    )
    prepare.add_argument("--staged", required=True)
    prepare.add_argument("--approved-stage-digest", required=True)
    prepare.add_argument("--output", required=True)

    verify = sub.add_parser(
        "verify-published",
        help="verify a read-only GitHub release snapshot against staged authority",
    )
    verify.add_argument("--staged", required=True)
    verify.add_argument("--release-snapshot", required=True)
    verify.add_argument("--require-immutable", action="store_true")
    verify.add_argument("--output", required=True)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        if args.command == "stage":
            payload = stage_release_archive(
                archive_path=args.bundle,
                source_sha=args.source_sha,
                repository=args.repository,
                signing_evidence=_read_object(args.signing_evidence),
                attestation_receipt=_read_object(args.attestation_receipt),
                tag_state=_read_object(args.tag_state),
            )
        elif args.command == "prepare-draft":
            payload = build_publish_request(
                _read_object(args.staged),
                approved_stage_digest=args.approved_stage_digest,
            )
        else:
            payload = verify_published_release(
                _read_object(args.staged),
                release_snapshot=_read_object(args.release_snapshot),
                require_immutable=args.require_immutable,
            )
    except ReleasePromotionError as exc:
        raise SystemExit(f"R18.5 promotion contract rejected input: {exc}") from exc

    _write_object(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
