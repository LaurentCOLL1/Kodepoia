from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contracts import sha256_hex, stable_id


@dataclass(frozen=True, slots=True)
class SynthesisCacheRecord:
    cache_key: str
    asset_revision_id: str
    output_sha256: str
    runtime_sha256: str
    model_sha256: str
    config_sha256: str

    def __post_init__(self) -> None:
        sha256_hex(self.cache_key, field="cache_key")
        stable_id(self.asset_revision_id, field="asset_revision_id")
        for name in ("output_sha256", "runtime_sha256", "model_sha256", "config_sha256"):
            sha256_hex(getattr(self, name), field=name)

    def canonical(self) -> dict[str, Any]:
        return {
            "cache_key": self.cache_key,
            "asset_revision_id": self.asset_revision_id,
            "output_sha256": self.output_sha256,
            "runtime_sha256": self.runtime_sha256,
            "model_sha256": self.model_sha256,
            "config_sha256": self.config_sha256,
        }


class SynthesisCacheIndex:
    """Identity-only cache index; physical bytes remain governed by the R8 Vault."""

    def __init__(self) -> None:
        self._records: dict[str, SynthesisCacheRecord] = {}

    def put(self, record: SynthesisCacheRecord) -> None:
        existing = self._records.get(record.cache_key)
        if existing is not None and existing != record:
            raise ValueError("cache key collision with different synthesis identity")
        self._records[record.cache_key] = record

    def resolve(
        self,
        cache_key: str,
        *,
        runtime_sha256: str,
        model_sha256: str,
        config_sha256: str,
    ) -> SynthesisCacheRecord | None:
        sha256_hex(cache_key, field="cache_key")
        sha256_hex(runtime_sha256, field="runtime_sha256")
        sha256_hex(model_sha256, field="model_sha256")
        sha256_hex(config_sha256, field="config_sha256")
        record = self._records.get(cache_key)
        if record is None:
            return None
        if (
            record.runtime_sha256 != runtime_sha256
            or record.model_sha256 != model_sha256
            or record.config_sha256 != config_sha256
        ):
            return None
        return record

    def canonical(self) -> list[dict[str, Any]]:
        return [self._records[key].canonical() for key in sorted(self._records)]
