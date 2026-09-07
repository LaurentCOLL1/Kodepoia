from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = os.environ["KODEPOIA_RELEASE_SOURCE_SHA"]
INSTALLER_SHA256 = os.environ["KODEPOIA_INSTALLER_SHA256"]
INSTALLER_SIZE = os.environ["KODEPOIA_INSTALLER_SIZE"]
TAG = "v1.1.0-rc1"
RELEASE_URL = f"https://github.com/LaurentCOLL1/Kodepoia/releases/tag/{TAG}"


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one occurrence, found {count}: {old[:100]!r}")
    return text.replace(old, new, 1)

attrs_path = ROOT / ".gitattributes"
attrs = attrs_path.read_text(encoding="utf-8")
exe_attr = "*.exe filter=lfs diff=lfs merge=lfs -text"
if exe_attr not in attrs:
    attrs = attrs.rstrip() + "\n" + exe_attr + "\n"
attrs_path.write_text(attrs, encoding="utf-8")

r0_path = ROOT / "scripts/check_repo.py"
r0 = r0_path.read_text(encoding="utf-8")
r0 = replace_once(
    r0,
    '    "README.md", "CHANGELOG.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",\n',
    '    "README.md", "CHANGELOG.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",\n'
    '    "KodepoiaSetup.exe", "KodepoiaSetup.exe.sha256",\n',
)
r0 = replace_once(
    r0,
    'LFS_SUFFIXES = {".blend", ".fbx", ".glb", ".psd", ".kra", ".exr", ".hdr", ".tif", ".tiff", ".wav", ".flac", ".mp4", ".mov", ".mkv", ".zip", ".7z"}',
    'LFS_SUFFIXES = {".blend", ".fbx", ".glb", ".psd", ".kra", ".exr", ".hdr", ".tif", ".tiff", ".wav", ".flac", ".mp4", ".mov", ".mkv", ".zip", ".7z", ".exe"}',
)
r0_path.write_text(r0, encoding="utf-8")

readme_path = ROOT / "README.md"
readme = readme_path.read_text(encoding="utf-8")
start = readme.index("## Installer Kodepoia sur Windows — utilisateur final")
end = readme.index("### Désinstallation", start)
new_install = f'''## Installer Kodepoia sur Windows — utilisateur final

### Méthode principale — fichier à la racine

Le fichier d'installation principal est **`KodepoiaSetup.exe`**, placé directement à la **racine du dépôt**. Il s'agit du miroir Git LFS de l'installateur publié avec la GitHub Release `{TAG}`.

1. Dans la liste des fichiers à la racine du dépôt, ouvrir **`KodepoiaSetup.exe`** puis le télécharger.
2. Facultatif mais recommandé : comparer son SHA-256 avec **`KodepoiaSetup.exe.sha256`**.
3. Exécuter **`KodepoiaSetup.exe`**.
4. Suivre l'assistant d'installation en français ou en anglais.
5. Lancer **Kodepoia** depuis le menu Démarrer ou le raccourci Bureau.

SHA-256 du miroir actuellement accepté : `{INSTALLER_SHA256}`.

### GitHub Release

La même version est disponible dans **[Releases](https://github.com/LaurentCOLL1/Kodepoia/releases)** → **Kodepoia 1.1.0-rc1** → `KodepoiaSetup.exe`.

Cette version est une **prérelease / beta** et son manifeste indique toujours `production_signed=false`. Elle ne doit donc pas être présentée comme une release stable signée de production ; Windows/SmartScreen peut afficher un avertissement de réputation ou de signature.

`KodepoiaSetup.exe` installe KodeStudio dans le profil utilisateur, crée une entrée de désinstallation et les raccourcis. L'exécutable embarque le runtime nécessaire : Python et `pip` ne sont pas requis sur la machine cible.

'''
readme = readme[:start] + new_install + readme[end:]
readme_path.write_text(readme, encoding="utf-8")

record = f'''\n\n## Post-R18 public prerelease distribution record\n\n- Explicit user authorization on 2026-09-07 triggered the previously conditional GitHub publication effect for the Windows prerelease only.\n- Public GitHub prerelease `{TAG}` targets accepted exact source `{SOURCE_SHA}` and publishes `KodepoiaSetup.exe` plus `installer-manifest.json`.\n- The accepted Windows installer is {INSTALLER_SIZE} bytes with SHA-256 `{INSTALLER_SHA256}` and remains `production_signed=false`; this is a beta/RC publication, not a production-signed stable claim.\n- The identical installer payload is mirrored at repository root as Git LFS path `KodepoiaSetup.exe`, with root checksum file `KodepoiaSetup.exe.sha256`, so installation is discoverable without navigating CI artifact folders.\n- Public release URL: {RELEASE_URL}. Public WinGet submission, production Authenticode signing and production TUF key custody/rotation remain **NOT TRIGGERED**.\n- This is a post-completion distribution operation; it does not create R18.12, reopen R18, or constitute a second R18 phase normalization.\n'''

for rel in ("docs/roadmap/R18_PLAN.md", "docs/continuity/KODEPOIA_CONTINUITY.md"):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if "## Post-R18 public prerelease distribution record" not in text:
        text = text.rstrip() + record
    path.write_text(text, encoding="utf-8")
