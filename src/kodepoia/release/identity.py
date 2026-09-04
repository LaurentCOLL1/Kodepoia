from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

_ALLOWED_CHANNELS = ("stable", "beta", "nightly")
_ALLOWED_STAGES = ("dev", "a", "b", "rc", "final")
_ALLOWED_BUILD_TYPES = ("release", "prerelease", "development")
_STAGE_RANK = {stage: rank for rank, stage in enumerate(_ALLOWED_STAGES)}
_CHANNEL_RANK = {channel: rank for rank, channel in enumerate(("nightly", "beta", "stable"))}
_SOURCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class BoundReleaseIdentity:
    release: ReleaseIdentity
    source_sha: str

    def __post_init__(self) -> None:
        normalized = self.source_sha.strip().lower()
        if not _SOURCE_SHA_RE.fullmatch(normalized):
            raise ValueError("source SHA must be an exact 40-character hexadecimal Git commit")
        object.__setattr__(self, "source_sha", normalized)

    def to_dict(self) -> dict[str, Any]:
        return {**self.release.to_dict(), "source_sha": self.source_sha}


@dataclass(frozen=True)
class ReleaseIdentity:
    schema_version: int
    product: str
    package: str
    channel: str
    build_type: str
    source_binding: str
    major: int
    minor: int
    patch: int
    stage: str
    serial: int

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported release identity schema version")
        if not self.product.strip():
            raise ValueError("release product must not be empty")
        if not self.package.strip():
            raise ValueError("release package must not be empty")
        if self.channel not in _ALLOWED_CHANNELS:
            raise ValueError(f"unsupported release channel: {self.channel}")
        if self.stage not in _ALLOWED_STAGES:
            raise ValueError(f"unsupported release stage: {self.stage}")
        if self.build_type not in _ALLOWED_BUILD_TYPES:
            raise ValueError(f"unsupported build type: {self.build_type}")
        if self.source_binding != "exact-head":
            raise ValueError("release identity source binding must be exact-head")
        if min(self.major, self.minor, self.patch) < 0:
            raise ValueError("release version components must be non-negative")
        if self.stage == "final":
            if self.serial != 0:
                raise ValueError("final releases require serial 0")
        elif self.serial < 1:
            raise ValueError("development and pre-releases require serial >= 1")

        valid_stage_for_channel = {
            "stable": self.stage == "final",
            "beta": self.stage in {"a", "b", "rc"},
            "nightly": self.stage == "dev",
        }
        if not valid_stage_for_channel[self.channel]:
            raise ValueError(
                f"channel {self.channel!r} is incompatible with stage {self.stage!r}"
            )

        expected_build_type = {
            "stable": "release",
            "beta": "prerelease",
            "nightly": "development",
        }[self.channel]
        if self.build_type != expected_build_type:
            raise ValueError(
                f"channel {self.channel!r} requires build type {expected_build_type!r}"
            )

    @property
    def base_version(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def pep440_version(self) -> str:
        if self.stage == "final":
            return self.base_version
        if self.stage == "dev":
            return f"{self.base_version}.dev{self.serial}"
        return f"{self.base_version}{self.stage}{self.serial}"

    @property
    def public_version(self) -> str:
        if self.stage == "final":
            return self.base_version
        return f"{self.base_version}-{self.stage}{self.serial}"

    @property
    def display_version(self) -> str:
        return self.public_version

    @property
    def installer_version(self) -> str:
        return self.public_version

    @property
    def precedence_key(self) -> tuple[int, int, int, int, int]:
        return (
            self.major,
            self.minor,
            self.patch,
            _STAGE_RANK[self.stage],
            self.serial,
        )

    def bind_source(self, source_sha: str) -> BoundReleaseIdentity:
        return BoundReleaseIdentity(release=self, source_sha=source_sha)

    def is_newer_than(self, other: ReleaseIdentity) -> bool:
        return self.precedence_key > other.precedence_key

    def can_transition_to(self, target: ReleaseIdentity) -> bool:
        if target.product != self.product or target.package != self.package:
            return False
        if not target.is_newer_than(self):
            return False
        source_base = (self.major, self.minor, self.patch)
        target_base = (target.major, target.minor, target.patch)
        if target_base > source_base:
            return True
        return _CHANNEL_RANK[target.channel] >= _CHANNEL_RANK[self.channel]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "product": self.product,
            "package": self.package,
            "channel": self.channel,
            "build_type": self.build_type,
            "source_binding": self.source_binding,
            "version": {
                "major": self.major,
                "minor": self.minor,
                "patch": self.patch,
                "stage": self.stage,
                "serial": self.serial,
            },
            "pep440_version": self.pep440_version,
            "public_version": self.public_version,
            "installer_version": self.installer_version,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ReleaseIdentity:
        version = payload.get("version")
        if not isinstance(version, Mapping):
            raise ValueError("release identity requires a version object")
        return cls(
            schema_version=int(payload.get("schema_version", 0)),
            product=str(payload.get("product", "")),
            package=str(payload.get("package", "")),
            channel=str(payload.get("channel", "")),
            build_type=str(payload.get("build_type", "")),
            source_binding=str(payload.get("source_binding", "")),
            major=int(version.get("major", -1)),
            minor=int(version.get("minor", -1)),
            patch=int(version.get("patch", -1)),
            stage=str(version.get("stage", "")),
            serial=int(version.get("serial", -1)),
        )


def load_release_identity() -> ReleaseIdentity:
    resource = files("kodepoia.release").joinpath("release_identity.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("release identity root must be an object")
    return ReleaseIdentity.from_mapping(payload)


CURRENT_RELEASE = load_release_identity()


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the canonical Kodepoia release identity")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--source-sha", help="bind the identity to an exact Git commit SHA")
    args = parser.parse_args()
    payload: dict[str, Any] = CURRENT_RELEASE.to_dict()
    if args.source_sha:
        payload = CURRENT_RELEASE.bind_source(args.source_sha).to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        suffix = f" @{args.source_sha[:12]}" if args.source_sha else ""
        print(
            f"{CURRENT_RELEASE.product} {CURRENT_RELEASE.public_version} "
            f"({CURRENT_RELEASE.channel}, {CURRENT_RELEASE.build_type}){suffix}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
