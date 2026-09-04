"""Compatibility shim for the canonical :mod:`kodepoia.release` identity API."""

from kodepoia.release.identity import (
    CURRENT_RELEASE,
    BoundReleaseIdentity,
    ReleaseIdentity,
    load_release_identity,
    main,
)

__all__ = [
    "BoundReleaseIdentity",
    "CURRENT_RELEASE",
    "ReleaseIdentity",
    "load_release_identity",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
