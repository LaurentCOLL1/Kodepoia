from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from kodepoia.kodecode.workspace import WorkspaceViolation
from kodepoia.kodestudio.localization import KODESTUDIO_SOURCE_CATALOG, PSEUDO_LOCALE
from kodepoia.quality.localization import (
    KodeLocalization,
    LocaleCatalog,
    LocalizationReport,
    LocalizationStatus,
    LocalizationStore,
    LocalizedMessage,
    pseudo_catalog,
    pseudo_localize_text,
)
from kodepoia.quality.tests import TestCaseStatus


def _source() -> LocaleCatalog:
    return LocaleCatalog(
        locale="en",
        messages=(
            LocalizedMessage.text("hello", "Hello {name}"),
            LocalizedMessage("files", {"one": "{count} file", "other": "{count} files"}),
            LocalizedMessage.text("markup", "<b>Open</b> {path}"),
        ),
    )


def test_catalog_rejects_duplicate_ids_and_requires_other_form() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        LocaleCatalog(
            locale="en",
            messages=(LocalizedMessage.text("x", "A"), LocalizedMessage.text("x", "B")),
        )
    with pytest.raises(ValueError, match="other"):
        LocalizedMessage("files", {"one": "one"})


def test_valid_catalog_passes_with_explicit_fallback() -> None:
    source = _source()
    target = LocaleCatalog(
        locale="fr",
        fallback_locale="en",
        messages=(
            LocalizedMessage.text("hello", "Bonjour {name}"),
            LocalizedMessage("files", {"one": "{count} fichier", "other": "{count} fichiers"}),
            LocalizedMessage.text("markup", "<b>Ouvrir</b> {path}"),
        ),
    )
    report = KodeLocalization(source).validate_catalog(target)
    assert report.status is LocalizationStatus.PASS
    assert report.counts["failed"] == 0
    assert report.counts["blocking_failures"] == 0


def test_missing_key_and_placeholder_mismatch_are_blocking() -> None:
    source = _source()
    target = LocaleCatalog(
        locale="fr",
        fallback_locale="en",
        messages=(
            LocalizedMessage.text("hello", "Bonjour"),
            LocalizedMessage("files", {"one": "{count} fichier", "other": "{count} fichiers"}),
        ),
    )
    report = KodeLocalization(source).validate_catalog(target)
    assert report.status is LocalizationStatus.FAIL
    assert report.counts["blocking_failures"] == 2
    assert "catalog.placeholders.parity:hello" in report.blockers
    assert "catalog.key.present:markup" in report.blockers


def test_plural_form_mismatch_fails() -> None:
    source = _source()
    target = LocaleCatalog(
        locale="fr",
        fallback_locale="en",
        messages=(
            LocalizedMessage.text("hello", "Bonjour {name}"),
            LocalizedMessage.text("files", "{count} fichiers"),
            LocalizedMessage.text("markup", "<b>Ouvrir</b> {path}"),
        ),
    )
    report = KodeLocalization(source).validate_catalog(target)
    assert report.status is LocalizationStatus.FAIL
    assert "catalog.forms.parity:files" in report.blockers


def test_extra_key_warns_without_becoming_pass() -> None:
    source = _source()
    target = LocaleCatalog(
        locale="fr",
        fallback_locale="en",
        messages=source.messages + (LocalizedMessage.text("extra", "Supplément"),),
    )
    report = KodeLocalization(source).validate_catalog(target)
    assert report.status is LocalizationStatus.WARN
    assert report.counts["warnings"] == 1


def test_wrong_or_missing_fallback_is_explicit() -> None:
    source = _source()
    no_fallback = LocaleCatalog(locale="fr", messages=source.messages)
    warn = KodeLocalization(source).validate_catalog(no_fallback)
    assert warn.status is LocalizationStatus.WARN
    wrong = LocaleCatalog(locale="fr", fallback_locale="de", messages=source.messages)
    fail = KodeLocalization(source).validate_catalog(wrong)
    assert fail.status is LocalizationStatus.FAIL
    assert "catalog.fallback.explicit:fr" in fail.blockers


def test_pseudo_localization_preserves_placeholders_and_markup() -> None:
    text = "<b>Hello</b> {name} &amp; {count} files"
    pseudo = pseudo_localize_text(text)
    assert pseudo.startswith("⟦") and pseudo.endswith("⟧")
    assert "<b>" in pseudo and "</b>" in pseudo
    assert "{name}" in pseudo and "{count}" in pseudo
    assert "&amp;" in pseudo
    assert pseudo != text


def test_pseudo_catalog_validates_against_source() -> None:
    source = _source()
    pseudo = pseudo_catalog(source)
    assert pseudo.locale == "qps-ploc"
    assert pseudo.fallback_locale == "en"
    report = KodeLocalization(source).validate_catalog(pseudo)
    assert report.status is LocalizationStatus.PASS


def test_translate_uses_source_fallback_and_formats_values() -> None:
    source = _source()
    empty = LocaleCatalog(locale="fr", messages=(), fallback_locale="en")
    translated = KodeLocalization(source).translate(empty, "hello", values={"name": "Ada"})
    assert translated == "Hello Ada"
    with pytest.raises(KeyError):
        KodeLocalization(source).translate(empty, "missing")


def test_report_roundtrip_and_tamper_rejection() -> None:
    source = _source()
    report = KodeLocalization(source).validate_catalog(pseudo_catalog(source))
    restored = LocalizationReport.from_dict(report.to_dict())
    assert restored == report

    payload = report.to_dict()
    payload["counts"]["passed"] += 1
    with pytest.raises(ValueError, match="counts"):
        LocalizationReport.from_dict(payload)

    payload = report.to_dict()
    payload["evidence_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        LocalizationReport.from_dict(payload)


def test_r6_3_adapter_uses_stable_ids() -> None:
    source = _source()
    report = KodeLocalization(source).validate_catalog(pseudo_catalog(source))
    cases = KodeLocalization.to_test_cases(report)
    assert cases
    assert all(case.id.startswith("localization:") for case in cases)
    assert all(case.status is TestCaseStatus.PASS for case in cases)


def test_store_is_confined_and_roundtrips(tmp_path: Path) -> None:
    (tmp_path / ".kodepoia").mkdir()
    source = _source()
    report = KodeLocalization(source).validate_catalog(pseudo_catalog(source))
    store = LocalizationStore(tmp_path)
    latest, snapshot = store.save(report)
    assert latest.is_file() and snapshot.is_file()
    assert latest.parent == tmp_path / ".kodepoia" / "diagnostics" / "localization"
    assert store.load_latest("qps-ploc") == report


def test_store_rejects_symlink_escape(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("symlink creation may require elevated Windows policy")
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / ".kodepoia").mkdir()
    (tmp_path / ".kodepoia" / "diagnostics").symlink_to(outside, target_is_directory=True)
    with pytest.raises(WorkspaceViolation):
        LocalizationStore(tmp_path)


def test_kodestudio_pseudo_catalog_is_complete() -> None:
    pseudo = pseudo_catalog(KODESTUDIO_SOURCE_CATALOG, locale=PSEUDO_LOCALE)
    report = KodeLocalization(KODESTUDIO_SOURCE_CATALOG).validate_catalog(pseudo)
    assert report.status is LocalizationStatus.PASS
    assert len(pseudo.messages) == len(KODESTUDIO_SOURCE_CATALOG.messages)


def test_serialized_report_is_json_safe() -> None:
    report = KodeLocalization(_source()).validate_catalog(pseudo_catalog(_source()))
    encoded = json.dumps(report.to_dict(), ensure_ascii=False)
    assert "qps-ploc" in encoded
