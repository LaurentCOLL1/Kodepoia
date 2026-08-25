# R13.3 — Android deterministic native scaffold + Kotlin/Compose shared app model

**Status:** IN_PROGRESS  
**Manual state:** NONE  
**Authorized base:** normalized `main` `4a4985b58f449fb1bc1b2a455a41255d40fccfac`  
**Branch:** `r13/03-android-scaffold`

## Objective

R13.3 turns the accepted R13.2 **mobile intent** into a deterministic, repository-owned Android source workspace. It does not build that workspace. Gradle/JDK/Android SDK execution, APK/AAB validation, signing, devices and store operations remain R13.4+.

The implementation extends accepted architecture rather than introducing an Android-only global state model:

- Project identity and Android min/target API come from accepted `ProjectDNA.mobile`.
- Logical state/routes/commands reuse the accepted R12 app-model contract as a read-only logical projection.
- R8/R12 ownership semantics are preserved: Kodepoia-generated files can be regenerated only when their prior digest proves they were not edited; user-owned files are preserved.
- SafeChange + Backup + Audit are required for destructive regeneration.
- The renderer is pure Python text generation. It has no Gradle, JDK, SDK, shell, device or network execution seam.

## Current Android evidence boundary

Mutable Android ecosystem versions are **evidence**, not architecture constants. `AndroidDependencyEvidence` requires explicit bounded versions, an observation date and official `https://developer.android.com/...` provenance. Values such as `latest`, dynamic `+` versions and unofficial evidence sources are rejected.

The canonical R13.3 tests use:

- Android Gradle Plugin `9.1.2` as the phase baseline already recorded by R13 planning;
- Compose BOM `2026.08.00`;
- `compileSdk=37`, while project `targetSdk` remains DNA intent (`36` in the canonical fixture).

Android's current documentation recommends Kotlin DSL for Gradle build configuration and the standard `gradle/libs.versions.toml` version-catalog location. The Compose setup documentation identifies BOM `2026.08.00` and requires `buildFeatures.compose=true`. These mutable values must be re-evaluated by later capability/build evidence rather than silently upgraded by the renderer.

Official references used for the scaffold shape:

- https://developer.android.com/build/migrate-to-kotlin-dsl
- https://developer.android.com/build/migrate-to-catalogs
- https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler

## Domain model

### `AndroidDependencyEvidence`

Durably identifies the dependency/tooling inputs represented by generated Gradle files:

- stable evidence id;
- explicit Android Gradle Plugin version;
- explicit Compose BOM version;
- compile SDK integer;
- ISO observation date;
- bounded official Android documentation URLs.

Its canonical JSON has a SHA-256 digest which is bound into the workspace manifest.

### `AndroidScaffoldDefinition`

A typed immutable definition derived from accepted Project DNA plus the accepted logical app model:

- `source_kind=native` only;
- Android application id / namespace;
- app display name;
- min/target SDK;
- dependency evidence;
- app-model semantic digest;
- deterministic localized string catalogs.

`from_project()` rejects non-`mobile_app`, non-Android and Godot-export profiles. Godot Android export remains a bridge definition for later work and is not silently translated to this native scaffold.

### `AndroidWorkspaceManifest`

The semantic manifest binds:

- scaffold definition digest;
- dependency-evidence digest;
- app-model digest;
- Project DNA digest supplied by lineage;
- KodeProduct digest supplied by lineage;
- sorted generated-file path, digest and ownership tuples.

The manifest is canonical JSON. Identical accepted inputs therefore produce identical manifest bytes and digest.

## Fixed generated workspace

The renderer owns the project shape; project/model text cannot inject additional Gradle scripts, repositories, plugins, tasks or commands.

Generated Kodepoia-owned files include:

- `settings.gradle.kts`;
- root `build.gradle.kts`;
- `gradle/libs.versions.toml`;
- `gradle.properties`;
- `app/build.gradle.kts`;
- `app/src/main/AndroidManifest.xml`;
- package-derived `MainActivity.kt`;
- package-derived `KodepoiaAppModel.kt`;
- `res/values*/strings.xml`;
- `res/values/themes.xml`.

`README.md` is explicitly user-owned and is preserved on regeneration.

No Gradle wrapper binary/JAR is synthesized in R13.3. Toolchain/bootstrap/build authority belongs to R13.4, where real tool identity and execution can be validated rather than fabricated.

## Compose/shared-model projection

`MainActivity.kt` uses a minimal Compose root with:

- Material theme;
- `Scaffold`;
- `BoxWithConstraints` adaptive padding baseline;
- explicit semantic content description baseline;
- no hidden network or service execution.

`KodepoiaAppModel.kt` deterministically projects the accepted logical model:

- typed state defaults;
- route ids/paths;
- command ids/operations;
- original logical-model SHA-256.

Logical ids are mapped to bounded Kotlin symbols with a short SHA-derived suffix, preventing collisions caused by punctuation normalization.

## Localization/resource safety

Android resource names are validated against a narrow lowercase identifier grammar. Text is bounded, control characters are rejected, XML values are escaped and Kotlin strings are escaped for their target context. The renderer does not interpret text as templates or Gradle code.

## Ownership and regeneration

Preview classifies each desired file as `CREATE`, `UNCHANGED`, `PRESERVE`, `REPLACE` or `CONFLICT`.

A Kodepoia-owned file may be `REPLACE` only when its current bytes still match the SHA recorded by the previous workspace manifest. Editing a generated file therefore removes automatic replacement authority and creates `CONFLICT`.

Any real replacement requires both `SafeChangeManager` and `BackupManager`; audit evidence records manifest/definition/dependency digests and actions. Existing symlink ancestors are resolved and any path escaping the project root fails closed.

## Security boundary

R13.3 deliberately has no API for:

- executable paths;
- raw Gradle arguments/properties/tasks;
- arbitrary Maven repositories;
- arbitrary plugin coordinates;
- shell commands;
- environment variables;
- SDK installation;
- signing material;
- device ids;
- network endpoints;
- Play tracks/tokens.

These omissions are architectural controls, not missing convenience features.

## Durable schemas

- `schemas/r13/android-scaffold-definition.schema.json`
- `schemas/r13/android-workspace-manifest.schema.json`

Both use JSON Schema Draft 2020-12. Cross-field semantic conditions (for example namespace matching the accepted application id) remain domain validation and are not implemented with non-standard JSON Schema extensions.

## R13.4 handoff

R13.4 may consume an accepted R13.3 workspace manifest and dependency evidence to perform bounded toolchain discovery/build/export. It must not reinterpret arbitrary project text as executable Gradle configuration, and any mutable version/tool capability must be independently probed there.
