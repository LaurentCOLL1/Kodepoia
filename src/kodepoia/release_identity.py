from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Mapping

_ALLOWED_CHANNELS = ("stable", "beta", "nightly")
_ALLOWED_STAGES = ("dev", "a", "b", "rc", "final")
_STAGE_RANK = {stage: rank for rank, stage in enumerate(_ALLOWED_STAGES)}
_CHANNEL_RANK = {channel: rank for rank, channel in enumerate(("nightly", "beta", "stable"))}


@dataclass(frozen=True)
class ReleaseIdentity:
    schema_version: int
    product: str
    channel: str
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
        if self.channel not in _ALLOWED_CHANNELS:
            raise ValueError(f"unsupported release channel: {self.channel}")
        if self.stage not in _ALLOWED_STAGES:
            raise ValueError(f"unsupported release stage: {self.stage}")
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
    def display_version(self) -> str:
        if self.stage == "final":
            return self.base_version
        return f"{self.base_version}-{self.stage}{self.serial}"

    @property
    def precedence_key(self) -> tuple[int, int, int, int, int]:
        return (
            self.major,
            self.minor,
            self.patch,
            _STAGE_RANK[self.stage],
            self.serial,
        )

    def is_newer_than(self, other: ReleaseIdentity) -> bool:
        return self.precedence_key > other.precedence_key

    def can_transition_to(self, target: ReleaseIdentity) -> bool:
        if target.product != self.product or not target.is_newer_than(self):
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
            "channel": self.channel,
            "version": {
                "major": self.major,
                "minor": self.minor,
                "patch": self.patch,
                "stage": self.stage,
                "serial": self.serial,
            },
            "pep440_version": self.pep440_version,
            "display_version": self.display_version,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ReleaseIdentity:
        version = payload.get("version")
        if not isinstance(version, Mapping):
            raise ValueError("release identity requires a version object")
        return cls(
            schema_version=int(payload.get("schema_version", 0)),
            product=str(payload.get("product", "")),
            channel=str(payload.get("channel", "")),
            major=int(version.get("major", -1)),
            minor=int(version.get("minor", -1)),
            patch=int(version.get("patch", -1)),
            stage=str(version.get("stage", "")),
            serial=int(version.get("serial", -1)),
        )


def load_release_identity() -> ReleaseIdentity:
    resource = files("kodepoia").joinpath("release_identity.json")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("release identity root must be an object")
    return ReleaseIdentity.from_mapping(payload)


CURRENT_RELEASE = load_release_identity()


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the canonical Kodepoia release identity")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    if args.json:
        print(json.dumps(CURRENT_RELEASE.to_dict(), ensure_ascii=False, sort_keys=True))
    else:
        print(f"{CURRENT_RELEASE.product} {CURRENT_RELEASE.display_version} ({CURRENT_RELEASE.channel})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
