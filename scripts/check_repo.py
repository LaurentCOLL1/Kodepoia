#!/usr/bin/env python3
"""Kodepoia R0 repository bootstrap validator."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    print("PyYAML is required for the R0 repository check.", file=sys.stderr)
    print("Install with: python -m pip install -r scripts/requirements-r0.txt", file=sys.stderr)
    raise SystemExit(2) from exc

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md", "CHANGELOG.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
    ".gitignore", ".gitattributes", ".github/workflows/r0-bootstrap.yml", ".github/CODEOWNERS",
    "docs/architecture/KODEPOIA_ARCHITECTURE_V1_0.md",
    "docs/architecture/KODEPOIA_ARCHITECTURE_DECISIONS.md",
    "docs/architecture/KODEPOIA_FREEZE_MANIFEST.json",
    "docs/architecture/adr/0000-template.md",
    "docs/continuity/KODEPOIA_CONTINUITY.md",
    "docs/roadmap/KODEPOIA_ROADMAP_V1_0.md",
    "docs/governance/BRANCHING_POLICY.md",
    "schemas/architecture-freeze.schema.json",
    "src/kodestudio/.gitkeep", "src/orchestrator/.gitkeep", "src/brain/.gitkeep",
    "src/core/guardian/.gitkeep", "src/core/sandbox/.gitkeep", "src/core/secrets/.gitkeep",
    "src/quality/health/.gitkeep", "src/quality/budget/.gitkeep", "src/models/router/.gitkeep",
    "tests/.gitkeep",
]

FORBIDDEN_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keystore", ".gguf", ".safetensors", ".ckpt", ".pth", ".onnx"}
LFS_SUFFIXES = {".blend", ".fbx", ".glb", ".psd", ".kra", ".exr", ".hdr", ".tif", ".tiff", ".wav", ".flac", ".mp4", ".mov", ".mkv", ".zip", ".7z"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".ps1", ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".gd", ".cs", ".cpp", ".h", ".hpp", ".ts", ".tsx", ".js"}
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,255}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
MAX_NON_LFS_BYTES = 10 * 1024 * 1024
SKIP_SCAN = {"scripts/check_repo.py"}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> int:
    errors: list[str] = []

    for item in REQUIRED:
        if not (ROOT / item).exists():
            fail(errors, f"missing required path: {item}")

    for path in ROOT.rglob("*.json"):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(errors, f"invalid JSON {relative(path)}: {exc}")

    for pattern in ("*.yml", "*.yaml"):
        for path in ROOT.rglob(pattern):
            if ".git" in path.parts:
                continue
            try:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception as exc:
                fail(errors, f"invalid YAML {relative(path)}: {exc}")

    manifest_path = ROOT / "docs/architecture/KODEPOIA_FREEZE_MANIFEST.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("project") != "Kodepoia":
                fail(errors, "freeze manifest project must be Kodepoia")
            if manifest.get("status") != "FROZEN":
                fail(errors, "freeze manifest status must be FROZEN")
            priorities = set(manifest.get("foundation_priorities", []))
            expected = {"KodeGuardian", "KodeSandbox", "KodeSecrets", "KodeHealth", "KodeBudget"}
            if missing := expected - priorities:
                fail(errors, f"freeze manifest missing foundation priorities: {sorted(missing)}")
        except Exception as exc:
            fail(errors, f"cannot validate freeze manifest: {exc}")

    attrs_path = ROOT / ".gitattributes"
    attributes = attrs_path.read_text(encoding="utf-8") if attrs_path.exists() else ""

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = relative(path)
        lower_name = path.name.lower()
        suffix = path.suffix.lower()

        if lower_name in FORBIDDEN_NAMES or suffix in FORBIDDEN_SUFFIXES:
            fail(errors, f"forbidden secret/model file in repository: {rel}")

        size = path.stat().st_size
        if size > MAX_NON_LFS_BYTES:
            if suffix not in LFS_SUFFIXES:
                fail(errors, f"large file is not covered by R0 LFS policy: {rel} ({size} bytes)")
            elif f"*{suffix} filter=lfs" not in attributes:
                fail(errors, f"LFS extension not declared in .gitattributes: {suffix}")

        if rel in SKIP_SCAN:
            continue
        if suffix in TEXT_SUFFIXES or path.name in {"README", "LICENSE"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    fail(errors, f"possible hard-coded secret in {rel} matching {pattern.pattern!r}")

    if errors:
        print("Kodepoia R0 repository check: FAIL", file=sys.stderr)
        for item in errors:
            print(f" - {item}", file=sys.stderr)
        return 1

    print("Kodepoia R0 repository check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
