# R12.3 — Deterministic desktop scaffold/template/workspace manifest engine

## Status

Implementation candidate. Manual intervention: **NONE**.

## Frozen scope

R12.3 introduces a framework-neutral, Kodepoia-owned scaffold engine. It does **not** build, restore, install SDKs, launch framework tools, or implement WPF/WinUI/Avalonia/Qt/Tauri adapters. Those remain R12.5–R12.9.

## Durable contracts

- `DesktopTemplateManifest` schema v1 describes only repository-owned static template files, version, paths, content and ownership.
- `WorkspaceManifest` schema v1 records template identity/digest, Project DNA digest, KodeProduct digest and every generated file SHA-256/ownership.
- Canonical JSON is UTF-8, sorted-key, compact and newline-independent; generated text is normalized to LF.
- Repository fixture: `templates/r12/desktop/canonical/template.json`.

## Template language

The engine is intentionally not a general template interpreter. The only recognized tokens are:

- `{{identifier:name}}`
- `{{namespace:name}}`
- `{{text:name}}`
- `{{bool:name}}`

Values are typed and validated before substitution. Unknown/malformed `{{...}}` directives fail. No expressions, includes, loops, functions, shell commands, Python, JavaScript or executable callbacks exist. Other text is emitted literally.

## Path and collision boundary

- POSIX-relative template paths only; backslashes, absolute paths, `..`, NUL, Windows reserved device names and Windows-forbidden filename characters fail closed.
- Rendered paths are revalidated after substitution.
- Duplicate rendered paths and collision with the workspace-manifest path fail.
- Resolved output paths must remain under the project root, including symlink resolution.

## Ownership and regeneration

Ownership is whole-file and explicit:

- `kodepoia`: generated file may be replaced only when a prior workspace manifest records it as Kodepoia-owned **and** the current bytes still match that prior SHA-256.
- `user`: existing file is always preserved during regeneration.
- Unowned, modified generated, directory/file collision or otherwise ambiguous targets are `CONFLICT` and block apply.

R12.3 deliberately does not invent editable generated regions. User customization belongs in user-owned files or later adapter extension points.

## Preview / apply

`preview()` is read-only and returns CREATE / REPLACE / UNCHANGED / PRESERVE / CONFLICT actions. `apply()` refuses conflicts. Any REPLACE requires both existing `SafeChangeManager` snapshotting and `BackupManager` verified archive creation before bytes change. `AuditLog`, when supplied, records the workspace/template digests, safety artifacts and per-path actions.

## Lineage

The workspace manifest binds every listed file digest to the same Project DNA SHA-256, KodeProduct SHA-256 and versioned template SHA-256. The manifest digest therefore forms the deterministic R8-compatible lineage root for the generated workspace.

## Security properties

- no process launch;
- no network;
- no shell/raw argv surface;
- no executable template language;
- traversal/symlink/reserved-name rejection;
- typed substitution and unresolved-directive rejection;
- user-owned/unverified existing content never overwritten;
- destructive regeneration cannot proceed without SafeChange + Backup.

## Rollback

Before any accepted replacement, SafeChange creates a path snapshot and BackupManager creates/verifies a project archive. If apply is not reached, preview is side-effect free. R12.3 itself does not auto-restore; existing Backup/Recovery authority remains responsible for recovery workflows.
