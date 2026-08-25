# R13.3 acceptance — Android deterministic native scaffold

**Subdivision:** R13.3  
**Manual:** NONE  
**External runtime:** not required in this subdivision

## Accepted claim

R13.3 may be marked complete only when Kodepoia deterministically renders a repository-owned native Android/Kotlin/Compose source workspace from accepted mobile Project DNA, product lineage and the accepted logical app model, without invoking an Android build toolchain.

R13.3 does not claim compilation, APK/AAB production, device execution, signing or store readiness. Those claims start in later R13 subdivisions.

## Required files

- `src/kodepoia/mobile/android_scaffold.py`
- `schemas/r13/android-scaffold-definition.schema.json`
- `schemas/r13/android-workspace-manifest.schema.json`
- `tests/test_r13_3_android_scaffold.py`
- `docs/roadmap/R13_3_DESIGN.md`
- `docs/roadmap/R13_3_ACCEPTANCE.md`

## Determinism

Focused tests must show that identical accepted inputs produce identical rendered file tuples, identical canonical workspace-manifest bytes and the same semantic digest. Paths must be sorted, newlines normalized and each recorded SHA-256 must match the UTF-8 bytes of its rendered file.

Both durable payloads must validate with their JSON Schema Draft 2020-12 schemas.

## Android workspace structure

The canonical fixture must include Kotlin DSL settings/build files, `gradle/libs.versions.toml`, an Android application module, manifest, package-derived Kotlin sources, Compose UI, the shared logical-model projection, localized strings and theme resources.

Dependency declarations must be explicit. Dynamic or unbounded version labels are not valid dependency evidence.

## Shared logical model

The generated app-model source must carry the accepted logical-model SHA-256 and deterministically project accepted state, route and command identities. R13.3 reuses the accepted logical contract and does not introduce a competing global app architecture.

## Dependency evidence

The dependency evidence model must require explicit Android Gradle Plugin and Compose BOM versions, a bounded compile SDK, an observation date and official Android documentation provenance. A compile SDK below the Project DNA target SDK must fail validation. Mutable Android ecosystem values remain evidence rather than permanent architecture constants.

## Target partition

Native Android scaffold derivation must reject non-mobile-app DNA, missing Android target intent and Godot-export source intent. The native renderer must not silently reinterpret a game export profile.

## Context safety

Project text is data. Kotlin strings and Android XML strings must be escaped for their destination. Resource names and generated paths use bounded grammars. The renderer exposes no raw Gradle task, plugin, repository, command or executable parameter.

## No tool execution

Rendering and preview are pure source-generation operations. Focused tests must succeed without an Android SDK and must not invoke a process-launch API. This absence of execution is part of R13.3's boundary and is not build evidence for R13.4.

## Ownership and regeneration

The tests must prove that user-owned files are preserved, modified generated files become conflicts, replacement requires accepted SafeChange and backup controls, audit evidence remains valid, and path/symlink escape fails closed where the platform supports creating the test symlink.

## Lineage

The workspace manifest must bind the scaffold-definition digest, dependency-evidence digest, logical-app-model digest, Project DNA digest, KodeProduct digest and each generated file digest/ownership state.

## Exact-head CI

Freeze one implementation candidate and require on that exact SHA:

- R0 Repository Guard SUCCESS;
- full Python Core SUCCESS;
- KodeStudio UI Smoke SUCCESS.

A failed candidate is rejected. Any byte change after an accepted candidate requires new exact-head gates.

After implementation acceptance, synchronize plan and continuity so R13.3 is COMPLETE and R13.4 remains PLANNED, re-run the three gates, merge with `expected_head_sha`, perform exactly one continuity-only post-merge normalization, re-gate it and merge it before R13.4 starts.

## Manual state

**NONE.** No Android SDK, device, signing credential or store account is required to establish the frozen R13.3 claim.
