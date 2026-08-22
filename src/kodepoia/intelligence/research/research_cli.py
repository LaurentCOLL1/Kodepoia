from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.intelligence.research.contracts import ResearchSourceKind
from kodepoia.intelligence.research.service import (
    ResearchFetchRequest,
    ResearchOperationStatus,
    ResearchService,
)


_SUCCESS = frozenset({ResearchOperationStatus.READY, ResearchOperationStatus.STALE})


def _service(args: argparse.Namespace) -> ResearchService:
    return ResearchService(Path.cwd().resolve(strict=False), allow_network=bool(getattr(args, "allow_network", False)))


def _emit(service: ResearchService, result) -> int:
    print(service.serialized(result))
    return 0 if result.status in _SUCCESS else 2


def _query(args: argparse.Namespace) -> int:
    service = _service(args)
    sources = tuple(ResearchSourceKind(value) for value in (args.source or ()))
    return _emit(
        service,
        service.query(args.query, source_kinds=sources, limit=args.limit),
    )


def _fetch(args: argparse.Namespace) -> int:
    service = _service(args)
    result = service.fetch(
        ResearchFetchRequest(
            kind=ResearchSourceKind(args.kind),
            locator=args.locator,
            retrieved_at=args.retrieved_at,
            canonical_locator=args.canonical_locator,
            title=args.title,
            publisher=args.publisher,
            product=args.product,
            version=args.version,
            target_version=args.target_version,
        )
    )
    return _emit(service, result)


def _show(args: argparse.Namespace) -> int:
    service = _service(args)
    return _emit(service, service.show(args.identifier))


def _cache(args: argparse.Namespace) -> int:
    service = _service(args)
    return _emit(service, service.cache(args.cache_key, as_of=args.as_of))


def _status(args: argparse.Namespace) -> int:
    service = _service(args)
    return _emit(service, service.status())


def _media_capability(args: argparse.Namespace) -> int:
    service = _service(args)
    return _emit(service, service.media_capability())


def register_research_commands(commands: argparse._SubParsersAction) -> None:
    query = commands.add_parser(
        "research-query",
        help="Search validated persisted KodeResearch evidence without network side effects",
    )
    query.add_argument("--query", required=True)
    query.add_argument(
        "--source",
        action="append",
        choices=[kind.value for kind in ResearchSourceKind],
        default=[],
        help="optional source filter; repeat for multiple source classes",
    )
    query.add_argument("--limit", type=int, default=20)
    query.set_defaults(func=_query)

    fetch = commands.add_parser(
        "research-fetch",
        help="Fetch one typed local/official/Web research source through accepted R7 adapters",
    )
    fetch.add_argument(
        "--kind",
        required=True,
        choices=[
            ResearchSourceKind.LOCAL.value,
            ResearchSourceKind.OFFICIAL_DOCS.value,
            ResearchSourceKind.WEB.value,
        ],
    )
    fetch.add_argument("--locator", required=True)
    fetch.add_argument("--retrieved-at", default="")
    fetch.add_argument("--canonical-locator", default="")
    fetch.add_argument("--title", default="")
    fetch.add_argument("--publisher", default="")
    fetch.add_argument("--product", default="")
    fetch.add_argument("--version", default="")
    fetch.add_argument("--target-version", default="")
    fetch.add_argument(
        "--allow-network",
        action="store_true",
        help="explicitly grant only the NETWORK capability for this Web fetch; Guardian/R7.3 policies still apply",
    )
    fetch.set_defaults(func=_fetch)

    show = commands.add_parser(
        "research-show",
        help="Show a typed persisted research artifact or report by SHA-256 identifier",
    )
    show.add_argument("identifier")
    show.set_defaults(func=_show)

    cache = commands.add_parser(
        "research-cache",
        help="Inspect one R7.9 cache key and its explicit reuse/stale state",
    )
    cache.add_argument("cache_key")
    cache.add_argument("--as-of", default="")
    cache.set_defaults(func=_cache)

    status = commands.add_parser(
        "research-status",
        help="Show persisted evidence counts and explicit interactive provider capability states",
    )
    status.add_argument(
        "--allow-network",
        action="store_true",
        help="show the Web interactive capability with an explicit NETWORK grant for this invocation",
    )
    status.set_defaults(func=_status)

    media = commands.add_parser(
        "research-media-capability",
        help="Run the accepted R7.7 local media capability doctor without changing R7.7 evidence files",
    )
    media.set_defaults(func=_media_capability)
