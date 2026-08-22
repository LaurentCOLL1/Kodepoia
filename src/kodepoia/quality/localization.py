from __future__ import annotations

import hashlib
import json
import re
import string
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.tests import TestCaseResult, TestCaseStatus


_SCHEMA_VERSION = 1
_PLACEHOLDER_FORMATTER = string.Formatter()
_PROTECTED_TOKEN_RE = re.compile(r"(\{[^{}]+\}|<[^>]+>|&[A-Za-z0-9#]+;)")


class LocalizationStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    UNKNOWN = "unknown"


class LocalizationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class LocalizedMessage:
    id: str
    forms: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("message id must be non-empty")
        normalized = {str(key).strip(): str(value) for key, value in self.forms.items()}
        if not normalized or any(not key for key in normalized):
            raise ValueError("message forms must contain non-empty form ids")
        if "other" not in normalized:
            raise ValueError("message forms must include 'other'")
        object.__setattr__(self, "forms", normalized)

    @classmethod
    def text(cls, message_id: str, value: str) -> "LocalizedMessage":
        return cls(message_id, {"other": value})

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "forms": dict(sorted(self.forms.items()))}


@dataclass(frozen=True, slots=True)
class LocaleCatalog:
    locale: str
    messages: tuple[LocalizedMessage, ...]
    fallback_locale: str | None = None

    def __post_init__(self) -> None:
        locale = self.locale.strip()
        if not locale:
            raise ValueError("locale must be non-empty")
        ids = [message.id for message in self.messages]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate message ids are not allowed")
        fallback = self.fallback_locale.strip() if self.fallback_locale else None
        if fallback == locale:
            raise ValueError("fallback locale must differ from locale")
        object.__setattr__(self, "locale", locale)
        object.__setattr__(self, "fallback_locale", fallback)

    @property
    def by_id(self) -> dict[str, LocalizedMessage]:
        return {message.id: message for message in self.messages}

    def to_dict(self) -> dict[str, Any]:
        return {
            "locale": self.locale,
            "fallback_locale": self.fallback_locale,
            "messages": [message.to_dict() for message in sorted(self.messages, key=lambda item: item.id)],
        }


@dataclass(frozen=True, slots=True)
class LocalizationResult:
    rule_id: str
    target_id: str
    status: LocalizationStatus
    severity: LocalizationSeverity
    message: str
    blocking: bool = False
    details: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.rule_id.strip() or not self.target_id.strip():
            raise ValueError("rule_id and target_id must be non-empty")
        if self.blocking and self.status is not LocalizationStatus.FAIL:
            raise ValueError("only FAIL localization results can be blocking")

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "target_id": self.target_id,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "blocking": self.blocking,
            "details": dict(self.details or {}),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LocalizationResult":
        return cls(
            rule_id=str(payload["rule_id"]),
            target_id=str(payload["target_id"]),
            status=LocalizationStatus(str(payload["status"])),
            severity=LocalizationSeverity(str(payload["severity"])),
            message=str(payload["message"]),
            blocking=bool(payload.get("blocking", False)),
            details=dict(payload.get("details") or {}),
        )


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _evidence_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _aggregate_status(results: Iterable[LocalizationResult]) -> LocalizationStatus:
    values = tuple(results)
    if not values:
        return LocalizationStatus.UNKNOWN
    if any(result.status is LocalizationStatus.FAIL for result in values):
        return LocalizationStatus.FAIL
    if any(result.status in {LocalizationStatus.WARN, LocalizationStatus.UNKNOWN} for result in values):
        return LocalizationStatus.WARN
    return LocalizationStatus.PASS


@dataclass(frozen=True, slots=True)
class LocalizationReport:
    generated_at: str
    source_locale: str
    locale: str
    fallback_locale: str | None
    results: tuple[LocalizationResult, ...]
    status: LocalizationStatus
    evidence_sha256: str
    schema_version: int = _SCHEMA_VERSION

    @property
    def counts(self) -> dict[str, int]:
        return {
            "total": len(self.results),
            "passed": sum(item.status is LocalizationStatus.PASS for item in self.results),
            "warnings": sum(item.status is LocalizationStatus.WARN for item in self.results),
            "failed": sum(item.status is LocalizationStatus.FAIL for item in self.results),
            "unknown": sum(item.status is LocalizationStatus.UNKNOWN for item in self.results),
            "blocking_failures": sum(item.blocking for item in self.results),
        }

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(
            f"{item.rule_id}:{item.target_id}"
            for item in self.results
            if item.blocking
        )

    def _evidence_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "source_locale": self.source_locale,
            "locale": self.locale,
            "fallback_locale": self.fallback_locale,
            "status": self.status.value,
            "results": [item.to_dict() for item in self.results],
            "counts": self.counts,
            "blockers": list(self.blockers),
        }

    def validate(self) -> None:
        datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        keys = [(item.rule_id, item.target_id) for item in self.results]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate localization rule/target pairs")
        expected_status = _aggregate_status(self.results)
        if self.status is not expected_status:
            raise ValueError("localization report status does not match results")
        expected_hash = _evidence_hash(self._evidence_payload())
        if self.evidence_sha256 != expected_hash:
            raise ValueError("localization report evidence hash mismatch")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = self._evidence_payload()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def build(
        cls,
        *,
        source_locale: str,
        locale: str,
        fallback_locale: str | None,
        results: Iterable[LocalizationResult],
        generated_at: str | None = None,
    ) -> "LocalizationReport":
        timestamp = generated_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_tuple = tuple(results)
        status = _aggregate_status(result_tuple)
        provisional = cls(timestamp, source_locale, locale, fallback_locale, result_tuple, status, "")
        digest = _evidence_hash(provisional._evidence_payload())
        report = cls(timestamp, source_locale, locale, fallback_locale, result_tuple, status, digest)
        report.validate()
        return report

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LocalizationReport":
        report = cls(
            generated_at=str(payload["generated_at"]),
            source_locale=str(payload["source_locale"]),
            locale=str(payload["locale"]),
            fallback_locale=(str(payload["fallback_locale"]) if payload.get("fallback_locale") else None),
            results=tuple(LocalizationResult.from_dict(item) for item in payload["results"]),
            status=LocalizationStatus(str(payload["status"])),
            evidence_sha256=str(payload["evidence_sha256"]),
            schema_version=int(payload.get("schema_version", _SCHEMA_VERSION)),
        )
        if int(payload.get("schema_version", 0)) != _SCHEMA_VERSION:
            raise ValueError("unsupported localization report schema version")
        if dict(payload.get("counts") or {}) != report.counts:
            raise ValueError("serialized localization counts do not match results")
        if tuple(payload.get("blockers") or ()) != report.blockers:
            raise ValueError("serialized localization blockers do not match results")
        report.validate()
        return report


def _placeholders(text: str) -> tuple[str, ...]:
    values: list[str] = []
    try:
        for _, field_name, _, _ in _PLACEHOLDER_FORMATTER.parse(text):
            if field_name is not None:
                root = field_name.split(".", 1)[0].split("[", 1)[0]
                values.append(root)
    except ValueError as exc:
        raise ValueError(f"invalid format string: {text!r}") from exc
    return tuple(sorted(values))


def _pseudo_segment(segment: str) -> str:
    table = str.maketrans(
        {
            "a": "à", "A": "À", "e": "ë", "E": "Ë", "i": "ï", "I": "Ï",
            "o": "ô", "O": "Ô", "u": "ü", "U": "Ü", "y": "ÿ", "Y": "Ÿ",
        }
    )
    converted = segment.translate(table)
    letters = sum(character.isalpha() for character in converted)
    padding = "~" * max(1, letters // 3) if letters else ""
    return converted + padding


def pseudo_localize_text(text: str) -> str:
    parts = _PROTECTED_TOKEN_RE.split(text)
    transformed = [part if _PROTECTED_TOKEN_RE.fullmatch(part or "") else _pseudo_segment(part) for part in parts]
    return "⟦" + "".join(transformed) + "⟧"


def pseudo_catalog(source: LocaleCatalog, *, locale: str = "qps-ploc") -> LocaleCatalog:
    messages = tuple(
        LocalizedMessage(
            message.id,
            {form: pseudo_localize_text(text) for form, text in message.forms.items()},
        )
        for message in source.messages
    )
    return LocaleCatalog(locale=locale, messages=messages, fallback_locale=source.locale)


class KodeLocalization:
    def __init__(self, source: LocaleCatalog) -> None:
        self.source = source

    def validate_catalog(self, catalog: LocaleCatalog) -> LocalizationReport:
        source_map = self.source.by_id
        target_map = catalog.by_id
        results: list[LocalizationResult] = []

        for message_id in sorted(source_map):
            source_message = source_map[message_id]
            target_message = target_map.get(message_id)
            if target_message is None:
                results.append(LocalizationResult(
                    "catalog.key.present", message_id, LocalizationStatus.FAIL,
                    LocalizationSeverity.ERROR, "required source message is missing", True,
                ))
                continue
            results.append(LocalizationResult(
                "catalog.key.present", message_id, LocalizationStatus.PASS,
                LocalizationSeverity.INFO, "message id is present",
            ))
            source_forms = set(source_message.forms)
            target_forms = set(target_message.forms)
            if source_forms != target_forms:
                results.append(LocalizationResult(
                    "catalog.forms.parity", message_id, LocalizationStatus.FAIL,
                    LocalizationSeverity.ERROR, "message forms differ from source", True,
                    {"source_forms": sorted(source_forms), "target_forms": sorted(target_forms)},
                ))
                continue
            results.append(LocalizationResult(
                "catalog.forms.parity", message_id, LocalizationStatus.PASS,
                LocalizationSeverity.INFO, "message forms match source",
            ))
            source_placeholders = {
                form: _placeholders(text) for form, text in source_message.forms.items()
            }
            target_placeholders = {
                form: _placeholders(text) for form, text in target_message.forms.items()
            }
            if source_placeholders != target_placeholders:
                results.append(LocalizationResult(
                    "catalog.placeholders.parity", message_id, LocalizationStatus.FAIL,
                    LocalizationSeverity.ERROR, "placeholder set differs from source", True,
                    {"source": source_placeholders, "target": target_placeholders},
                ))
            else:
                results.append(LocalizationResult(
                    "catalog.placeholders.parity", message_id, LocalizationStatus.PASS,
                    LocalizationSeverity.INFO, "placeholder sets match source",
                ))

        for message_id in sorted(set(target_map) - set(source_map)):
            results.append(LocalizationResult(
                "catalog.key.extra", message_id, LocalizationStatus.WARN,
                LocalizationSeverity.WARNING, "target contains a message id absent from source",
            ))

        fallback = catalog.fallback_locale
        if fallback is None:
            results.append(LocalizationResult(
                "catalog.fallback.explicit", catalog.locale, LocalizationStatus.WARN,
                LocalizationSeverity.WARNING, "catalog has no explicit fallback locale",
            ))
        elif fallback != self.source.locale:
            results.append(LocalizationResult(
                "catalog.fallback.explicit", catalog.locale, LocalizationStatus.FAIL,
                LocalizationSeverity.ERROR, "catalog fallback does not resolve to source locale", True,
                {"expected": self.source.locale, "actual": fallback},
            ))
        else:
            results.append(LocalizationResult(
                "catalog.fallback.explicit", catalog.locale, LocalizationStatus.PASS,
                LocalizationSeverity.INFO, "catalog explicitly falls back to source locale",
            ))

        return LocalizationReport.build(
            source_locale=self.source.locale,
            locale=catalog.locale,
            fallback_locale=catalog.fallback_locale,
            results=results,
        )

    def translate(
        self,
        catalog: LocaleCatalog,
        message_id: str,
        *,
        form: str = "other",
        values: Mapping[str, Any] | None = None,
    ) -> str:
        message = catalog.by_id.get(message_id) or self.source.by_id.get(message_id)
        if message is None:
            raise KeyError(message_id)
        text = message.forms.get(form) or message.forms["other"]
        return text.format(**dict(values or {}))

    @staticmethod
    def to_test_cases(report: LocalizationReport) -> tuple[TestCaseResult, ...]:
        mapping = {
            LocalizationStatus.PASS: TestCaseStatus.PASS,
            LocalizationStatus.WARN: TestCaseStatus.SKIP,
            LocalizationStatus.FAIL: TestCaseStatus.FAIL,
            LocalizationStatus.UNKNOWN: TestCaseStatus.ERROR,
        }
        return tuple(
            TestCaseResult(
                id=f"localization:{item.rule_id}:{item.target_id}",
                status=mapping[item.status],
                duration_s=0.0,
                message=item.message,
                source="KodeLocalization",
                details={"severity": item.severity.value, "blocking": item.blocking},
            )
            for item in report.results
        )


class LocalizationStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve(strict=False)
        self.boundary = WorkspaceBoundary(self.project_root)
        self.metadata_root = self.boundary.resolve(".kodepoia", must_exist=False)
        self.localization_root = self.boundary.resolve(".kodepoia/diagnostics/localization", must_exist=False)

    @staticmethod
    def _safe_locale(locale: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", locale).strip(".-")
        if not safe:
            raise ValueError("locale does not produce a safe file name")
        return safe

    def save(self, report: LocalizationReport) -> tuple[Path, Path]:
        report.validate()
        if not self.metadata_root.is_dir():
            raise FileNotFoundError("project .kodepoia metadata directory is not initialized")
        self.localization_root.mkdir(parents=True, exist_ok=True)
        safe_locale = self._safe_locale(report.locale)
        latest = self.boundary.resolve(f".kodepoia/diagnostics/localization/{safe_locale}-latest.json")
        stamp = report.generated_at.replace(":", "").replace("-", "").replace(".", "")
        snapshot = self.boundary.resolve(
            f".kodepoia/diagnostics/localization/localization-{safe_locale}-{stamp}.json"
        )
        payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        for destination in (latest, snapshot):
            temporary = destination.with_name(f".{destination.name}.tmp")
            temporary.write_text(payload, encoding="utf-8")
            temporary.replace(destination)
        return latest, snapshot

    def load_latest(self, locale: str) -> LocalizationReport:
        path = self.boundary.resolve(
            f".kodepoia/diagnostics/localization/{self._safe_locale(locale)}-latest.json",
            must_exist=True,
        )
        return LocalizationReport.from_dict(json.loads(path.read_text(encoding="utf-8")))
