from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from PIL import Image

from kodepoia.assets.contracts import AssetKind, AssetRevisionId
from kodepoia.assets.serialization import canonical_json
from kodepoia.assets.store import VaultStore


class DuplicateKind(StrEnum):
    EXACT = "exact"
    NEAR = "near"


class DuplicateDecisionKind(StrEnum):
    KEEP_SEPARATE = "keep_separate"
    SUPERSEDE_LOGICAL = "supersede_logical"


@dataclass(frozen=True, slots=True)
class Fingerprint:
    algorithm: str
    version: int
    value: str


@dataclass(frozen=True, slots=True)
class DuplicateCandidate:
    left: AssetRevisionId
    right: AssetRevisionId
    kind: DuplicateKind
    score: float
    algorithm: str
    algorithm_version: int


class Fingerprinter(Protocol):
    algorithm: str
    version: int

    def supports(self, kind: AssetKind) -> bool: ...
    def fingerprint(self, path: Path) -> Fingerprint: ...
    def similarity(self, left: Fingerprint, right: Fingerprint) -> float: ...


class ImageDHashFingerprinter:
    algorithm = "image-dhash-64"
    version = 1

    def supports(self, kind: AssetKind) -> bool:
        return kind in {AssetKind.IMAGE, AssetKind.TEXTURE, AssetKind.UI}

    def fingerprint(self, path: Path) -> Fingerprint:
        with Image.open(path) as image:
            gray = image.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
            pixels = list(gray.getdata())
        bits = 0
        bit_index = 0
        for row in range(8):
            offset = row * 9
            for column in range(8):
                if pixels[offset + column] > pixels[offset + column + 1]:
                    bits |= 1 << bit_index
                bit_index += 1
        return Fingerprint(self.algorithm, self.version, f"{bits:016x}")

    def similarity(self, left: Fingerprint, right: Fingerprint) -> float:
        if (left.algorithm, left.version) != (right.algorithm, right.version):
            raise ValueError("Fingerprint algorithm/version mismatch")
        distance = (int(left.value, 16) ^ int(right.value, 16)).bit_count()
        return 1.0 - (distance / 64.0)


class TextByteShapeFingerprinter:
    algorithm = "text-shape-v1"
    version = 1
    _SPACE = re.compile(r"\s+")

    def supports(self, kind: AssetKind) -> bool:
        return kind is AssetKind.DOCUMENT

    def fingerprint(self, path: Path) -> Fingerprint:
        text = path.read_text(encoding="utf-8", errors="replace")
        normalized = self._SPACE.sub(" ", text.casefold()).strip()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return Fingerprint(self.algorithm, self.version, digest)

    def similarity(self, left: Fingerprint, right: Fingerprint) -> float:
        return 1.0 if left.value == right.value else 0.0


class DuplicateDetector:
    def __init__(self, store: VaultStore, fingerprint_backend: Fingerprinter | None = None) -> None:
        self.store = store
        self.backends: list[Fingerprinter] = []
        if fingerprint_backend is not None:
            self.backends.append(fingerprint_backend)
        self.backends.extend([ImageDHashFingerprinter(), TextByteShapeFingerprinter()])

    def exact_groups(self) -> list[tuple[AssetRevisionId, ...]]:
        rows = self.store.db.execute(
            "SELECT content_sha256, content_length FROM revisions GROUP BY content_sha256, content_length HAVING COUNT(*) > 1 ORDER BY content_sha256"
        ).fetchall()
        groups: list[tuple[AssetRevisionId, ...]] = []
        for row in rows:
            members = self.store.db.execute(
                "SELECT revision_id FROM revisions WHERE content_sha256 = ? AND content_length = ? ORDER BY revision_id",
                (str(row["content_sha256"]), int(row["content_length"])),
            ).fetchall()
            groups.append(tuple(AssetRevisionId(str(item["revision_id"])) for item in members))
        return groups

    def _backend_for(self, kind: AssetKind) -> Fingerprinter | None:
        for backend in self.backends:
            if backend.supports(kind):
                return backend
        return None

    def near_candidates(self, *, threshold: float = 0.90) -> list[DuplicateCandidate]:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        rows = self.store.db.execute(
            "SELECT revision_id, kind, content_sha256, content_length FROM revisions WHERE status = 'ready' ORDER BY revision_id"
        ).fetchall()
        prepared: list[tuple[AssetRevisionId, AssetKind, Fingerprinter, Fingerprint, str, int]] = []
        for row in rows:
            revision_id = AssetRevisionId(str(row["revision_id"]))
            kind = AssetKind(str(row["kind"]))
            backend = self._backend_for(kind)
            if backend is None:
                continue
            fingerprint = backend.fingerprint(self.store.object_path(revision_id))
            prepared.append((revision_id, kind, backend, fingerprint, str(row["content_sha256"]), int(row["content_length"])))

        candidates: list[DuplicateCandidate] = []
        for index, left in enumerate(prepared):
            for right in prepared[index + 1 :]:
                if left[1] != right[1]:
                    continue
                if (left[4], left[5]) == (right[4], right[5]):
                    continue
                if (left[2].algorithm, left[2].version) != (right[2].algorithm, right[2].version):
                    continue
                score = left[2].similarity(left[3], right[3])
                if score >= threshold:
                    candidates.append(
                        DuplicateCandidate(left[0], right[0], DuplicateKind.NEAR, score, left[2].algorithm, left[2].version)
                    )
        return sorted(candidates, key=lambda item: (-item.score, str(item.left), str(item.right)))

    def record_decision(
        self,
        left: AssetRevisionId,
        right: AssetRevisionId,
        decision: DuplicateDecisionKind,
        *,
        reason: str,
    ) -> Path:
        if left == right:
            raise ValueError("Duplicate decision requires two distinct revisions")
        if not reason.strip():
            raise ValueError("Duplicate decision reason must be non-empty")
        for revision_id in (left, right):
            self.store._load_revision_manifest(revision_id)
        ordered = sorted((str(left), str(right)))
        decision_id = hashlib.sha256(canonical_json({"revisions": ordered, "decision": decision.value, "reason": reason}).encode("utf-8")).hexdigest()
        document = {
            "schema_version": 1,
            "decision_id": decision_id,
            "revisions": ordered,
            "decision": decision.value,
            "reason": reason,
        }
        return self.store._atomic_json(f"manifests/duplicate-decisions/{decision_id}.json", document)
