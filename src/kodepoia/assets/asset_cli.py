from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from kodepoia.assets.contracts import AssetId, AssetKind, AssetRole, ReuseScope
from kodepoia.assets.search import SearchFilters
from kodepoia.assets.service import AssetService, jsonable


def _emit(value: Any) -> int:
    print(json.dumps(jsonable(value), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _service(args: argparse.Namespace) -> AssetService:
    return AssetService(Path(args.project_root))


def _status(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.status())


def _doctor(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.doctor())


def _ingest(args: argparse.Namespace) -> int:
    identity = AssetId(args.asset_id) if args.asset_id else None
    with _service(args) as service:
        detail = service.ingest(
            args.source,
            kind=AssetKind(args.kind),
            display_name=args.name,
            asset_id=identity,
            project_id=args.project_id,
            target_path=args.target_path,
            reuse_scope=ReuseScope(args.reuse_scope),
        )
        return _emit(detail)


def _list(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.list_assets())


def _show(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.show(args.revision_id))


def _filters(args: argparse.Namespace) -> SearchFilters:
    return SearchFilters(
        kind=AssetKind(args.kind) if args.kind else None,
        role=AssetRole(args.role) if args.role else None,
        reuse_scope=ReuseScope(args.reuse_scope) if args.reuse_scope else None,
        project_id=args.project_id,
        license_state=args.license_state,
        tool_lineage=args.tool_lineage,
        include_blocked=bool(args.include_blocked),
    )


def _search(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.search(args.query, filters=_filters(args), limit=args.limit))


def _duplicates(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.duplicate_candidates(threshold=args.threshold))


def _lineage(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.lineage(args.revision_id))


def _rebuild(args: argparse.Namespace) -> int:
    with _service(args) as service:
        result = service.rebuild()
        _emit(result)
        return 0 if result.state.value == "ready" else 2


def _materialize(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(
            service.materialize(
                args.revision_id,
                args.target,
                overwrite=args.overwrite,
                confirmed=args.confirm,
            )
        )


def _delete_plan(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.deletion_plan(args.revision_id))


def _delete(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.delete_revision(args.revision_id, confirmed=args.confirm))


def _export_plan(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.export_plan(args.project_id))


def _export(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.export_project(args.project_id, args.target, confirmed=args.confirm))


def _vcs_status(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.vcs_status())


def _lfs_doctor(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.lfs_doctor())


def _repository_evidence(args: argparse.Namespace) -> int:
    with _service(args) as service:
        return _emit(service.repository_evidence(args.revision_id))


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-root",
        default=".",
        help="authorized Kodepoia project root (default: current directory)",
    )


def register_asset_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    asset = commands.add_parser("asset", help="Governed R8 Vault/asset operations")
    sub = asset.add_subparsers(dest="asset_command", required=True)

    status = sub.add_parser("status", help="Show Vault/VCS/LFS status")
    _common(status)
    status.set_defaults(func=_status)

    doctor = sub.add_parser("doctor", help="Show Vault/search/VCS/LFS diagnostic state")
    _common(doctor)
    doctor.set_defaults(func=_doctor)

    ingest = sub.add_parser("ingest", help="Ingest one project-relative source into the Vault")
    _common(ingest)
    ingest.add_argument("source")
    ingest.add_argument("--kind", choices=[item.value for item in AssetKind], default=AssetKind.GENERIC.value)
    ingest.add_argument("--name")
    ingest.add_argument("--asset-id")
    ingest.add_argument("--project-id")
    ingest.add_argument("--target-path")
    ingest.add_argument("--reuse-scope", choices=[item.value for item in ReuseScope], default=ReuseScope.PROJECT_ONLY.value)
    ingest.set_defaults(func=_ingest)

    listing = sub.add_parser("list", help="List canonical assets")
    _common(listing)
    listing.set_defaults(func=_list)

    show = sub.add_parser("show", help="Show one exact asset revision")
    _common(show)
    show.add_argument("revision_id")
    show.set_defaults(func=_show)

    search = sub.add_parser("search", help="Search the rebuildable asset index")
    _common(search)
    search.add_argument("query")
    search.add_argument("--kind", choices=[item.value for item in AssetKind])
    search.add_argument("--role", choices=[item.value for item in AssetRole])
    search.add_argument("--reuse-scope", choices=[item.value for item in ReuseScope])
    search.add_argument("--project-id")
    search.add_argument("--license-state")
    search.add_argument("--tool-lineage")
    search.add_argument("--include-blocked", action="store_true")
    search.add_argument("--limit", type=int, default=50)
    search.set_defaults(func=_search)

    duplicates = sub.add_parser("duplicates", help="List exact and near-duplicate candidates")
    _common(duplicates)
    duplicates.add_argument("--threshold", type=float, default=0.90)
    duplicates.set_defaults(func=_duplicates)

    lineage = sub.add_parser("lineage", help="Show source/derived lineage for one revision")
    _common(lineage)
    lineage.add_argument("revision_id")
    lineage.set_defaults(func=_lineage)

    rebuild = sub.add_parser("rebuild", help="Rebuild canonical and search indexes")
    _common(rebuild)
    rebuild.set_defaults(func=_rebuild)

    materialize = sub.add_parser("materialize", help="Materialize one Vault revision into the project")
    _common(materialize)
    materialize.add_argument("revision_id")
    materialize.add_argument("target")
    materialize.add_argument("--overwrite", action="store_true")
    materialize.add_argument("--confirm", action="store_true", help="required when overwriting an existing target")
    materialize.set_defaults(func=_materialize)

    delete_plan = sub.add_parser("delete-plan", help="Preview deletion without mutating the Vault")
    _common(delete_plan)
    delete_plan.add_argument("revision_id")
    delete_plan.set_defaults(func=_delete_plan)

    delete = sub.add_parser("delete", help="Delete an unprotected revision after explicit confirmation")
    _common(delete)
    delete.add_argument("revision_id")
    delete.add_argument("--confirm", action="store_true", required=True)
    delete.set_defaults(func=_delete)

    export_plan = sub.add_parser("export-plan", help="Preview governed project asset export")
    _common(export_plan)
    export_plan.add_argument("project_id")
    export_plan.set_defaults(func=_export_plan)

    export = sub.add_parser("export", help="Execute a preflight-governed asset export")
    _common(export)
    export.add_argument("project_id")
    export.add_argument("target")
    export.add_argument("--confirm", action="store_true", required=True)
    export.set_defaults(func=_export)

    vcs = sub.add_parser("vcs-status", help="Show structured local Git status")
    _common(vcs)
    vcs.set_defaults(func=_vcs_status)

    lfs = sub.add_parser("lfs-doctor", help="Show Git LFS capability/tracking diagnostics")
    _common(lfs)
    lfs.set_defaults(func=_lfs_doctor)

    evidence = sub.add_parser("repository-evidence", help="Show VCS/LFS evidence for one materialized revision")
    _common(evidence)
    evidence.add_argument("revision_id")
    evidence.set_defaults(func=_repository_evidence)
