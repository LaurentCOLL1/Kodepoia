from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.audit import AuditLog
from kodepoia.core.backup import BackupManager
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.desktop.scaffold import (
    DesktopScaffoldEngine,
    DesktopTemplateManifest,
    FileOwnership,
    PreviewAction,
    ScaffoldLineage,
    TemplateFile,
    TemplateValue,
    TemplateValueKind,
)

ROOT = Path(__file__).resolve().parents[1]


def _digest(ch: str) -> str:
    return ch * 64


def _template(content: str = "namespace {{namespace:namespace}};\nclass {{identifier:name}} {}\n") -> DesktopTemplateManifest:
    return DesktopTemplateManifest(
        schema_version=1,
        template_id="canonical_desktop",
        template_version="1.0.0",
        files=(
            TemplateFile(
                "src/{{identifier:name}}.cs",
                content,
                FileOwnership.KODEPOIA,
            ),
            TemplateFile(
                "README.md",
                "{{text:description}}\n",
                FileOwnership.USER,
            ),
        ),
    )


def _values(name: str = "SampleApp") -> dict[str, TemplateValue]:
    return {
        "name": TemplateValue(TemplateValueKind.IDENTIFIER, name),
        "namespace": TemplateValue(TemplateValueKind.NAMESPACE, f"Kodepoia.{name}"),
        "description": TemplateValue(TemplateValueKind.TEXT, "Generated desktop fixture"),
    }


def _lineage() -> ScaffoldLineage:
    return ScaffoldLineage(_digest("a"), _digest("b"))


def test_r12_3_same_definition_is_byte_deterministic() -> None:
    engine = DesktopScaffoldEngine()
    files_a, manifest_a = engine.render(_template(), _values(), _lineage())
    files_b, manifest_b = engine.render(_template(), _values(), _lineage())

    assert files_a == files_b
    assert manifest_a.canonical_bytes() == manifest_b.canonical_bytes()
    assert manifest_a.digest() == manifest_b.digest()
    assert [item.path for item in files_a] == sorted(item.path for item in files_a)
    assert all("\r" not in item.content for item in files_a)


def test_r12_3_workspace_manifest_matches_strict_schema() -> None:
    _, manifest = DesktopScaffoldEngine().render(_template(), _values(), _lineage())
    schema = json.loads(
        (ROOT / "schemas" / "r12" / "desktop-workspace-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(manifest.to_dict())


def test_r12_3_repository_template_manifest_is_strict_and_loadable() -> None:
    path = ROOT / "templates" / "r12" / "desktop" / "canonical" / "template.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "schemas" / "r12" / "desktop-template-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(raw)
    loaded = DesktopTemplateManifest.load(path)
    assert loaded.template_id == "canonical_desktop"
    assert loaded.template_version == "1.0.0"
    assert loaded.digest() == DesktopTemplateManifest.from_dict(raw).digest()


def test_r12_3_rejects_path_traversal_reserved_names_and_directives() -> None:
    engine = DesktopScaffoldEngine()
    malicious = DesktopTemplateManifest(
        1,
        "bad",
        "1.0",
        (TemplateFile("../owned.txt", "x"),),
    )
    with pytest.raises(ValueError, match="unsafe scaffold path"):
        engine.render(malicious, {}, _lineage())

    reserved = DesktopTemplateManifest(1, "bad", "1.0", (TemplateFile("CON.txt", "x"),))
    with pytest.raises(ValueError, match="reserved"):
        engine.render(reserved, {}, _lineage())

    directive = DesktopTemplateManifest(
        1,
        "bad",
        "1.0",
        (TemplateFile("safe.txt", "{% execute shell %}"),),
    )
    # Non-token text remains inert; executable template languages are never interpreted.
    files, _ = engine.render(directive, {}, _lineage())
    assert files[0].content == "{% execute shell %}"

    malformed = DesktopTemplateManifest(
        1,
        "bad",
        "1.0",
        (TemplateFile("safe.txt", "{{shell:boom}}"),),
    )
    with pytest.raises(ValueError, match="unsupported or malformed"):
        engine.render(malformed, {}, _lineage())


def test_r12_3_typed_substitution_blocks_identifier_and_directive_injection() -> None:
    engine = DesktopScaffoldEngine()
    values = _values("SampleApp")
    values["name"] = TemplateValue(TemplateValueKind.IDENTIFIER, "../Owned")
    with pytest.raises(ValueError, match="unsafe identifier"):
        engine.render(_template(), values, _lineage())

    values = _values("SampleApp")
    values["description"] = TemplateValue(
        TemplateValueKind.TEXT,
        "hello {{identifier:Injected}}",
    )
    with pytest.raises(ValueError, match="forbidden control/directive"):
        engine.render(_template(), values, _lineage())

    values = _values("SampleApp")
    values["namespace"] = TemplateValue(TemplateValueKind.TEXT, "Kodepoia.SampleApp")
    with pytest.raises(ValueError, match="requires namespace"):
        engine.render(_template(), values, _lineage())


def test_r12_3_preview_before_apply_and_user_owned_file_is_preserved(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "README.md").write_text("user notes\n", encoding="utf-8")

    engine = DesktopScaffoldEngine()
    preview = engine.preview(root, _template(), _values(), _lineage())
    actions = {item.path: item.action for item in preview.items}
    assert actions["README.md"] is PreviewAction.PRESERVE
    assert actions["src/SampleApp.cs"] is PreviewAction.CREATE
    assert not (root / "src" / "SampleApp.cs").exists()

    engine.apply(root, preview)
    assert (root / "README.md").read_text(encoding="utf-8") == "user notes\n"
    assert (root / "src" / "SampleApp.cs").is_file()


def test_r12_3_unowned_existing_file_conflicts_and_is_not_overwritten(tmp_path: Path) -> None:
    root = tmp_path / "project"
    target = root / "src" / "SampleApp.cs"
    target.parent.mkdir(parents=True)
    target.write_text("hand written\n", encoding="utf-8")

    engine = DesktopScaffoldEngine()
    preview = engine.preview(root, _template(), _values(), _lineage())
    action = next(item.action for item in preview.items if item.path == "src/SampleApp.cs")
    assert action is PreviewAction.CONFLICT
    with pytest.raises(FileExistsError, match="conflicts"):
        engine.apply(root, preview)
    assert target.read_text(encoding="utf-8") == "hand written\n"


def test_r12_3_regeneration_requires_safechange_backup_and_audit(tmp_path: Path) -> None:
    root = tmp_path / "project"
    backups = BackupManager(tmp_path / "backups")
    audit = AuditLog(tmp_path / "audit.jsonl")
    engine = DesktopScaffoldEngine()

    initial = engine.preview(root, _template("class {{identifier:name}} {}\n"), _values(), _lineage())
    engine.apply(root, initial, audit_log=audit)
    target = root / "src" / "SampleApp.cs"
    old = target.read_bytes()

    changed = engine.preview(
        root,
        _template("class {{identifier:name}} { public bool Ready => true; }\n"),
        _values(),
        _lineage(),
    )
    action = next(item.action for item in changed.items if item.path == "src/SampleApp.cs")
    assert action is PreviewAction.REPLACE
    with pytest.raises(ValueError, match="SafeChangeManager and BackupManager"):
        engine.apply(root, changed, audit_log=audit)

    safe_change = SafeChangeManager(root, root / ".kodepoia" / "snapshots")
    engine.apply(
        root,
        changed,
        safe_change=safe_change,
        backup_manager=backups,
        audit_log=audit,
    )
    assert target.read_bytes() != old
    assert any((root / ".kodepoia" / "snapshots").iterdir())
    archives = list((tmp_path / "backups").glob("*.zip"))
    assert len(archives) == 1
    assert backups.verify(archives[0])
    assert audit.verify()


def test_r12_3_tampered_generated_file_cannot_authorize_replace(tmp_path: Path) -> None:
    root = tmp_path / "project"
    engine = DesktopScaffoldEngine()
    first = engine.preview(root, _template("v1 {{identifier:name}}\n"), _values(), _lineage())
    engine.apply(root, first)

    target = root / "src" / "SampleApp.cs"
    target.write_text("user changed generated file\n", encoding="utf-8")
    changed = engine.preview(root, _template("v2 {{identifier:name}}\n"), _values(), _lineage())
    assert next(item.action for item in changed.items if item.path == "src/SampleApp.cs") is PreviewAction.CONFLICT

    # Forging only ownership cannot grant replacement: current bytes must still match
    # the SHA recorded by the previous Kodepoia manifest.
    manifest_path = root / DesktopScaffoldEngine.MANIFEST_PATH
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in raw["files"]:
        if item["path"] == "src/SampleApp.cs":
            item["ownership"] = "kodepoia"
    manifest_path.write_text(json.dumps(raw), encoding="utf-8")
    changed_again = engine.preview(root, _template("v3 {{identifier:name}}\n"), _values(), _lineage())
    assert next(item.action for item in changed_again.items if item.path == "src/SampleApp.cs") is PreviewAction.CONFLICT


def test_r12_3_symlink_escape_fails_closed_when_supported(tmp_path: Path) -> None:
    root = tmp_path / "project"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "src"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this runner")

    engine = DesktopScaffoldEngine()
    with pytest.raises(ValueError, match="escapes project root"):
        engine.preview(root, _template(), _values(), _lineage())
    assert not (outside / "SampleApp.cs").exists()


def test_r12_3_manifest_lineage_binds_dna_product_template_and_files() -> None:
    files, manifest = DesktopScaffoldEngine().render(_template(), _values(), _lineage())
    assert manifest.dna_sha256 == _digest("a")
    assert manifest.product_sha256 == _digest("b")
    assert manifest.template_sha256 == _template().digest()
    for item in files:
        assert item.sha256 == hashlib.sha256(item.content.encode("utf-8")).hexdigest()
