from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from .contracts import ExperienceRecord, ExperienceState, SanitizationStatus
from .dedup import ContaminationReport, DedupResult, DuplicateCluster

DATASET_SCHEMA = "kodepoia.experience.dataset-manifest"
DATASET_SCHEMA_VERSION = 1
DATASET_CARD_SCHEMA = "kodepoia.experience.dataset-card"
DATASET_CARD_SCHEMA_VERSION = 1
DATASET_POLICY_VERSION = "r15.5-dataset-v1"
REPRESENTATION_VERSION = "r15.5-representation-v1"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_LANGUAGE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$|^und$")


class DatasetError(ValueError):
    """Base error for immutable dataset construction."""


class DatasetPolicyError(DatasetError):
    """Raised for an invalid or incompatible dataset policy."""


class DatasetSourceError(DatasetError):
    """Raised when a source record/payload cannot be reconciled safely."""


class DatasetSplit(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class DatasetFormat(StrEnum):
    TEXT = "text"
    PROMPT_COMPLETION = "prompt_completion"
    CONVERSATIONAL = "conversational"


class DuplicateHandling(StrEnum):
    REPRESENTATIVE_ONLY = "representative_only"
    KEEP_GROUP = "keep_group"


@dataclass(frozen=True, slots=True)
class DatasetPolicy:
    seed: int
    sanitizer_digest: str
    governance_policy_digest: str
    dedup_policy_digest: str
    train_weight: int = 80
    validation_weight: int = 20
    test_weight: int = 0
    allowed_domains: tuple[str, ...] = ()
    allowed_tasks: tuple[str, ...] = ()
    duplicate_handling: DuplicateHandling = DuplicateHandling.REPRESENTATIVE_ONLY
    max_groups_per_domain: int | None = None
    version: str = DATASET_POLICY_VERSION

    def __post_init__(self) -> None:
        if self.seed < 0:
            raise DatasetPolicyError("seed must be >= 0")
        for name in (
            "sanitizer_digest",
            "governance_policy_digest",
            "dedup_policy_digest",
        ):
            _require_digest(name, getattr(self, name))
        weights = (self.train_weight, self.validation_weight, self.test_weight)
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in weights
        ):
            raise DatasetPolicyError("split weights must be non-negative integers")
        if self.train_weight <= 0 or self.validation_weight <= 0:
            raise DatasetPolicyError("train and validation weights must both be > 0")
        if self.max_groups_per_domain is not None and self.max_groups_per_domain <= 0:
            raise DatasetPolicyError("max_groups_per_domain must be > 0")
        _require_safe_id("version", self.version)
        for name, values in (
            ("allowed_domains", self.allowed_domains),
            ("allowed_tasks", self.allowed_tasks),
        ):
            if tuple(sorted(set(values))) != values:
                raise DatasetPolicyError(f"{name} must be unique and sorted")
            for value in values:
                _require_safe_id(name, value)

    def descriptor(self) -> dict[str, object]:
        return {
            "allowed_domains": list(self.allowed_domains),
            "allowed_tasks": list(self.allowed_tasks),
            "dedup_policy_digest": self.dedup_policy_digest,
            "duplicate_handling": self.duplicate_handling.value,
            "governance_policy_digest": self.governance_policy_digest,
            "max_groups_per_domain": self.max_groups_per_domain,
            "sanitizer_digest": self.sanitizer_digest,
            "seed": self.seed,
            "split_weights": {
                "test": self.test_weight,
                "train": self.train_weight,
                "validation": self.validation_weight,
            },
            "version": self.version,
        }

    @property
    def digest(self) -> str:
        return _digest_json(self.descriptor())


@dataclass(frozen=True, slots=True)
class DatasetSource:
    record: ExperienceRecord
    text: str
    format: DatasetFormat = DatasetFormat.TEXT
    language: str = "und"

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise DatasetSourceError("dataset source text must be str")
        if not _LANGUAGE.fullmatch(self.language):
            raise DatasetSourceError("language must be a BCP-47-like tag or 'und'")
        encoded = self.text.encode("utf-8")
        if hashlib.sha256(encoded).hexdigest() != self.record.content.sha256:
            raise DatasetSourceError(
                "source text digest does not match governed content digest"
            )
        if len(encoded) != self.record.content.byte_length:
            raise DatasetSourceError(
                "source byte length does not match governed content reference"
            )

    @property
    def item_id(self) -> str:
        return self.record.experience_id.value

    def canonical_payload(self) -> dict[str, object]:
        if self.format is DatasetFormat.TEXT:
            return {"text": self.text}
        try:
            decoded = json.loads(self.text)
        except json.JSONDecodeError as exc:
            raise DatasetSourceError(
                f"{self.format.value} source must be valid JSON text"
            ) from exc
        if self.format is DatasetFormat.PROMPT_COMPLETION:
            if not isinstance(decoded, dict) or set(decoded) != {
                "prompt",
                "completion",
            }:
                raise DatasetSourceError(
                    "prompt_completion source must contain only prompt and completion"
                )
            prompt = decoded.get("prompt")
            completion = decoded.get("completion")
            if not isinstance(prompt, str) or not isinstance(completion, str):
                raise DatasetSourceError("prompt and completion must be strings")
            return {"completion": completion, "prompt": prompt}
        if not isinstance(decoded, dict) or set(decoded) != {"messages"}:
            raise DatasetSourceError(
                "conversational source must contain only messages"
            )
        messages = decoded.get("messages")
        if not isinstance(messages, list) or not messages:
            raise DatasetSourceError("messages must be a non-empty list")
        canonical_messages: list[dict[str, str]] = []
        for message in messages:
            if not isinstance(message, dict) or set(message) != {"role", "content"}:
                raise DatasetSourceError(
                    "each message must contain only role and content"
                )
            role = message.get("role")
            content = message.get("content")
            if role not in {"system", "user", "assistant", "tool"}:
                raise DatasetSourceError("message role is invalid")
            if not isinstance(content, str):
                raise DatasetSourceError("message content must be a string")
            canonical_messages.append({"content": content, "role": role})
        return {"messages": canonical_messages}


@dataclass(frozen=True, slots=True)
class DatasetEntry:
    example_id: str
    experience_id: str
    source_digest: str
    source_contract_digest: str
    group_id: str
    split: DatasetSplit
    task: str
    domain: str
    language: str
    license_expression: str
    format: DatasetFormat
    representation_digest: str
    row_digest: str
    transformations: tuple[Mapping[str, str], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "domain": self.domain,
            "example_id": self.example_id,
            "experience_id": self.experience_id,
            "format": self.format.value,
            "group_id": self.group_id,
            "language": self.language,
            "license_expression": self.license_expression,
            "representation_digest": self.representation_digest,
            "row_digest": self.row_digest,
            "source_contract_digest": self.source_contract_digest,
            "source_digest": self.source_digest,
            "split": self.split.value,
            "task": self.task,
            "transformations": [dict(item) for item in self.transformations],
        }


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    dataset_id: str
    dataset_digest: str
    policy_digest: str
    policy: Mapping[str, object]
    dedup_policy_digest: str
    representation_version: str
    entries: tuple[DatasetEntry, ...]
    split_stats: Mapping[str, Mapping[str, object]]
    selection_summary: Mapping[str, object]
    export_digests: Mapping[str, str]
    schema: str = DATASET_SCHEMA
    schema_version: int = DATASET_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_digest": self.dataset_digest,
            "dataset_id": self.dataset_id,
            "dedup_policy_digest": self.dedup_policy_digest,
            "entries": [entry.to_dict() for entry in self.entries],
            "export_digests": dict(sorted(self.export_digests.items())),
            "policy": _json_safe_mapping(self.policy),
            "policy_digest": self.policy_digest,
            "representation_version": self.representation_version,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "selection_summary": _json_safe_mapping(self.selection_summary),
            "split_stats": {
                key: _json_safe_mapping(value)
                for key, value in sorted(self.split_stats.items())
            },
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @property
    def file_digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DatasetCard:
    dataset_id: str
    dataset_digest: str
    policy_digest: str
    intended_use: str
    limitations: tuple[str, ...]
    licenses: tuple[str, ...]
    languages: tuple[str, ...]
    domains: tuple[str, ...]
    tasks: tuple[str, ...]
    split_stats: Mapping[str, Mapping[str, object]]
    schema: str = DATASET_CARD_SCHEMA
    schema_version: int = DATASET_CARD_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_digest": self.dataset_digest,
            "dataset_id": self.dataset_id,
            "domains": list(self.domains),
            "intended_use": self.intended_use,
            "languages": list(self.languages),
            "licenses": list(self.licenses),
            "limitations": list(self.limitations),
            "policy_digest": self.policy_digest,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "split_stats": {
                key: _json_safe_mapping(value)
                for key, value in sorted(self.split_stats.items())
            },
            "tasks": list(self.tasks),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def markdown(self) -> str:
        lines = [
            "---",
            f'pretty_name: {json.dumps("Kodepoia " + self.dataset_id)}',
            "language:",
            *[f"  - {json.dumps(language)}" for language in self.languages],
            "tags:",
            '  - "kodepoia"',
            '  - "local-first"',
            "---",
            "",
            f"# Kodepoia dataset {self.dataset_id}",
            "",
            "## Identity",
            "",
            f"- Dataset digest: `{self.dataset_digest}`",
            f"- Policy digest: `{self.policy_digest}`",
            "",
            "## Intended use",
            "",
            self.intended_use,
            "",
            "## Licenses",
            "",
            *[
                f"- `{license_expression}`"
                for license_expression in self.licenses
            ],
            "",
            "## Domains and tasks",
            "",
            f"- Domains: {', '.join(self.domains)}",
            f"- Tasks: {', '.join(self.tasks)}",
            "",
            "## Splits",
            "",
        ]
        for split, stats in sorted(self.split_stats.items()):
            lines.append(
                f"- `{split}`: {stats.get('rows', 0)} rows / "
                f"{stats.get('groups', 0)} groups"
            )
        lines.extend(["", "## Limitations", ""])
        lines.extend(f"- {item}" for item in self.limitations)
        lines.append("")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class DatasetBuild:
    manifest: DatasetManifest
    card: DatasetCard
    exports: Mapping[DatasetSplit, bytes] = field(repr=False)

    def export_bytes(self, split: DatasetSplit) -> bytes:
        return self.exports.get(split, b"")

    @property
    def card_markdown(self) -> str:
        return self.card.markdown()


class DatasetBuilder:
    def __init__(self, policy: DatasetPolicy) -> None:
        self.policy = policy

    def build(
        self,
        sources: Iterable[DatasetSource],
        *,
        dedup: DedupResult,
        contamination: ContaminationReport,
        intended_use: str = (
            "Local supervised fine-tuning and validation inside Kodepoia."
        ),
        limitations: tuple[str, ...] = (
            "Derived from explicitly curated and governed local experiences only.",
            "Not a benchmark holdout and not authorized for public upload by this build.",
            "Tokenizer and chat-template formatting are deferred to training time.",
        ),
    ) -> DatasetBuild:
        intended_use = intended_use.strip()
        if not intended_use:
            raise DatasetPolicyError("intended_use must be non-empty")
        if not limitations or any(not item.strip() for item in limitations):
            raise DatasetPolicyError("limitations must contain non-empty entries")
        if dedup.policy_digest != self.policy.dedup_policy_digest:
            raise DatasetPolicyError(
                "dedup result does not match required dedup policy"
            )
        if contamination.policy_digest != self.policy.dedup_policy_digest:
            raise DatasetPolicyError(
                "contamination report does not match required dedup policy"
            )

        ordered = tuple(sorted(sources, key=lambda source: source.item_id))
        ids = [source.item_id for source in ordered]
        if len(ids) != len(set(ids)):
            raise DatasetSourceError("experience IDs must be unique within a build")

        by_id = {source.item_id: source for source in ordered}
        excluded = Counter[str]()
        eligible_by_group: dict[str, list[DatasetSource]] = defaultdict(list)
        contaminated_groups = set(contamination.contaminated_group_ids)
        quarantined_ids = set(contamination.quarantined_item_ids)

        for source in ordered:
            record = source.record
            try:
                group_id = dedup.group_for(source.item_id)
            except Exception as exc:
                raise DatasetSourceError(
                    f"source {source.item_id} is missing from the dedup result"
                ) from exc
            if record.state is not ExperienceState.CURATED:
                excluded[f"state:{record.state.value}"] += 1
                continue
            if record.benchmark_protected:
                excluded["benchmark_protected"] += 1
                continue
            if source.item_id in quarantined_ids or group_id in contaminated_groups:
                excluded["benchmark_contamination"] += 1
                continue
            if record.sanitization.status is not SanitizationStatus.PASSED:
                excluded["sanitization_not_passed"] += 1
                continue
            if record.sanitization.sanitizer_digest != self.policy.sanitizer_digest:
                raise DatasetPolicyError(
                    "source sanitizer digest does not match dataset policy"
                )
            if not record.authorization.is_allowed():
                excluded["training_authorization"] += 1
                continue
            if record.provenance.license_expression is None:
                excluded["license_missing"] += 1
                continue
            if (
                self.policy.allowed_domains
                and record.domain_label not in self.policy.allowed_domains
            ):
                excluded["domain_filter"] += 1
                continue
            if (
                self.policy.allowed_tasks
                and record.task_label not in self.policy.allowed_tasks
            ):
                excluded["task_filter"] += 1
                continue
            governance_digests = {
                item.policy_digest
                for item in record.transformations
                if item.transformation_id == "r15.3-sanitize-v1"
            }
            if governance_digests != {self.policy.governance_policy_digest}:
                raise DatasetPolicyError(
                    "source governance lineage does not match dataset policy"
                )
            source.canonical_payload()
            eligible_by_group[group_id].append(source)

        selected_groups = self._select_groups(eligible_by_group, dedup, by_id)
        selected: list[tuple[DatasetSource, str]] = []
        for group_id in selected_groups:
            members = sorted(
                eligible_by_group[group_id], key=lambda source: source.item_id
            )
            if self.policy.duplicate_handling is DuplicateHandling.REPRESENTATIVE_ONLY:
                representative_id = _cluster_for_group(
                    dedup, group_id
                ).representative_id
                representative = next(
                    (
                        source
                        for source in members
                        if source.item_id == representative_id
                    ),
                    None,
                )
                if representative is None:
                    excluded["representative_unavailable"] += len(members)
                    continue
                selected.append((representative, group_id))
                excluded["duplicate_member"] += max(0, len(members) - 1)
            else:
                selected.extend((source, group_id) for source in members)

        if not selected:
            raise DatasetSourceError("dataset build has no eligible selected records")

        rows_by_split: dict[DatasetSplit, list[dict[str, object]]] = {
            split: [] for split in DatasetSplit
        }
        entries: list[DatasetEntry] = []
        group_split: dict[str, DatasetSplit] = {}
        for source, group_id in selected:
            split = group_split.setdefault(group_id, self.assign_split(group_id))
            payload = source.canonical_payload()
            representation_digest = _digest_json(
                {
                    "format": source.format.value,
                    "payload": payload,
                    "version": REPRESENTATION_VERSION,
                }
            )
            example_id = "ex_" + hashlib.sha256(
                f"{source.item_id}\0{group_id}\0{representation_digest}".encode()
            ).hexdigest()
            row: dict[str, object] = {
                "domain": source.record.domain_label,
                "example_id": example_id,
                "experience_id": source.item_id,
                "format": source.format.value,
                "group_id": group_id,
                "language": source.language,
                "source_digest": source.record.content.sha256,
                "task": source.record.task_label,
                **payload,
            }
            row_digest = _digest_json(row)
            transformations = tuple(
                {
                    "input_digest": item.input_digest,
                    "output_digest": item.output_digest,
                    "policy_digest": item.policy_digest,
                    "transformation_id": item.transformation_id,
                }
                for item in source.record.transformations
            )
            entries.append(
                DatasetEntry(
                    example_id=example_id,
                    experience_id=source.item_id,
                    source_digest=source.record.content.sha256,
                    source_contract_digest=source.record.contract_digest(),
                    group_id=group_id,
                    split=split,
                    task=source.record.task_label,
                    domain=source.record.domain_label,
                    language=source.language,
                    license_expression=source.record.provenance.license_expression,
                    format=source.format,
                    representation_digest=representation_digest,
                    row_digest=row_digest,
                    transformations=transformations,
                )
            )
            rows_by_split[split].append(row)

        entries.sort(key=lambda item: item.example_id)
        export_bytes: dict[DatasetSplit, bytes] = {}
        export_digests: dict[str, str] = {}
        for split in DatasetSplit:
            rows = sorted(
                rows_by_split[split], key=lambda row: str(row["example_id"])
            )
            encoded = "".join(
                _canonical_json(row) + "\n" for row in rows
            ).encode("utf-8")
            export_bytes[split] = encoded
            export_digests[split.value] = hashlib.sha256(encoded).hexdigest()

        split_stats = self._split_stats(entries)
        selection_summary: dict[str, object] = {
            "excluded_by_reason": dict(sorted(excluded.items())),
            "input_records": len(ordered),
            "selected_groups": len({entry.group_id for entry in entries}),
            "selected_records": len(entries),
        }
        core = {
            "dedup_policy_digest": self.policy.dedup_policy_digest,
            "entries": [entry.to_dict() for entry in entries],
            "export_digests": dict(sorted(export_digests.items())),
            "policy": self.policy.descriptor(),
            "policy_digest": self.policy.digest,
            "representation_version": REPRESENTATION_VERSION,
            "selection_summary": selection_summary,
            "split_stats": split_stats,
        }
        dataset_digest = _digest_json(core)
        dataset_id = "ds_" + dataset_digest
        manifest = DatasetManifest(
            dataset_id=dataset_id,
            dataset_digest=dataset_digest,
            policy_digest=self.policy.digest,
            policy=self.policy.descriptor(),
            dedup_policy_digest=self.policy.dedup_policy_digest,
            representation_version=REPRESENTATION_VERSION,
            entries=tuple(entries),
            split_stats=split_stats,
            selection_summary=selection_summary,
            export_digests=export_digests,
        )
        card = DatasetCard(
            dataset_id=dataset_id,
            dataset_digest=dataset_digest,
            policy_digest=self.policy.digest,
            intended_use=intended_use,
            limitations=tuple(item.strip() for item in limitations),
            licenses=tuple(
                sorted({entry.license_expression for entry in entries})
            ),
            languages=tuple(sorted({entry.language for entry in entries})),
            domains=tuple(sorted({entry.domain for entry in entries})),
            tasks=tuple(sorted({entry.task for entry in entries})),
            split_stats=split_stats,
        )
        return DatasetBuild(manifest=manifest, card=card, exports=export_bytes)

    def assign_split(self, group_id: str) -> DatasetSplit:
        if not re.fullmatch(r"grp_[0-9a-f]{64}", group_id):
            raise DatasetSourceError(
                "group_id must be an authoritative R15.4 group identifier"
            )
        total = (
            self.policy.train_weight
            + self.policy.validation_weight
            + self.policy.test_weight
        )
        digest = hashlib.sha256(
            f"{self.policy.seed}\0{self.policy.digest}\0{group_id}".encode()
        ).digest()
        bucket = int.from_bytes(digest[:8], "big") % total
        if bucket < self.policy.train_weight:
            return DatasetSplit.TRAIN
        if bucket < self.policy.train_weight + self.policy.validation_weight:
            return DatasetSplit.VALIDATION
        return DatasetSplit.TEST

    def _select_groups(
        self,
        eligible_by_group: Mapping[str, list[DatasetSource]],
        dedup: DedupResult,
        by_id: Mapping[str, DatasetSource],
    ) -> tuple[str, ...]:
        candidates: list[tuple[str, str]] = []
        for group_id in sorted(eligible_by_group):
            cluster = _cluster_for_group(dedup, group_id)
            representative = by_id.get(cluster.representative_id)
            if representative is None:
                domain = min(
                    source.record.domain_label
                    for source in eligible_by_group[group_id]
                )
            else:
                domain = representative.record.domain_label
            candidates.append((group_id, domain))

        if self.policy.max_groups_per_domain is None:
            return tuple(group_id for group_id, _ in candidates)

        grouped: dict[str, list[str]] = defaultdict(list)
        for group_id, domain in candidates:
            grouped[domain].append(group_id)
        selected: list[str] = []
        for domain in sorted(grouped):
            ranked = sorted(
                grouped[domain],
                key=lambda group_id: hashlib.sha256(
                    (
                        f"{self.policy.digest}\0balance\0"
                        f"{domain}\0{group_id}"
                    ).encode()
                ).hexdigest(),
            )
            selected.extend(ranked[: self.policy.max_groups_per_domain])
        return tuple(sorted(selected))

    @staticmethod
    def _split_stats(
        entries: Iterable[DatasetEntry],
    ) -> dict[str, dict[str, object]]:
        result: dict[str, dict[str, object]] = {}
        all_entries = tuple(entries)
        for split in DatasetSplit:
            subset = tuple(
                entry for entry in all_entries if entry.split is split
            )
            result[split.value] = {
                "domain_counts": dict(
                    sorted(Counter(entry.domain for entry in subset).items())
                ),
                "groups": len({entry.group_id for entry in subset}),
                "language_counts": dict(
                    sorted(Counter(entry.language for entry in subset).items())
                ),
                "rows": len(subset),
                "task_counts": dict(
                    sorted(Counter(entry.task for entry in subset).items())
                ),
            }
        return result


def _cluster_for_group(dedup: DedupResult, group_id: str) -> DuplicateCluster:
    for cluster in dedup.clusters:
        if cluster.group_id == group_id:
            return cluster
    raise DatasetSourceError(f"unknown dedup group: {group_id}")


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _digest_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _json_safe_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return json.loads(_canonical_json(dict(value)))


def _require_digest(name: str, value: str) -> None:
    if not _HEX64.fullmatch(value):
        raise DatasetPolicyError(f"{name} must be 64 lowercase hex chars")


def _require_safe_id(name: str, value: str) -> None:
    if not _SAFE_ID.fullmatch(value):
        raise DatasetPolicyError(f"{name} must be a stable safe identifier")
