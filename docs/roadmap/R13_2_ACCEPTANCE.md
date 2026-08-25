# R13.2 — Acceptance

**Subdivision:** R13.2 — Project DNA/KodeProduct mobile profiles + Project Wizard target selection  
**Manual intervention:** NONE  
**Candidate status:** PENDING exact-head acceptance

## Required scope evidence

The frozen R13.2 candidate must prove all of the following without invoking an external mobile toolchain:

1. Pre-R13 Project DNA schema-v1 data loads and serializes without a `mobile` key or semantic drift.
2. Native `mobile_app` intent is limited to Android/iOS, has explicit bounded platform identity/version/package/release/signing/network/budget state, and carries no secret/tool argv fields.
3. Godot mobile game intent uses `godot_export`; native mobile apps use `native`; impossible project/source/platform combinations fail closed.
4. Android application ID and Apple bundle ID are validated as durable platform identities through the R13.1 contracts.
5. Platform-specific hidden fields and package-kind substitution are rejected.
6. KodeProduct receives deterministic `mobile.*` constraints plus one reserved P0 `MOBILE-TARGET` requirement; conflicting replacement is rejected.
7. `schemas/project-dna-v1.schema.json` remains backward compatible and the dedicated `schemas/r13/mobile-project-profile.schema.json` rejects unknown/raw build fields.
8. The existing KodeStudio Projects flow opens the R13-enhanced Project Wizard rather than a parallel mobile wizard.
9. Mobile Wizard controls are adaptive, accessible and pseudo-localizable, and project creation writes DNA/Product only — no APK/AAB/Xcode/signing/device/store side effect.

## Focused automated tests

`tests/test_r13_2_mobile_profiles.py` covers:

- legacy round-trip;
- Android and Android+iOS native profiles;
- Godot-export game profile;
- impossible source/platform/engine combinations;
- identifier/version/package/name injection failures;
- cross-platform hidden-field rejection;
- deterministic/idempotent Product mapping and reserved requirement protection;
- Draft 2020-12 schemas and unknown raw Gradle/Xcode fields;
- source/pseudo localization registration;
- offscreen PySide6 real Wizard creation for native mobile and mobile game paths.

## Standard exact-head gates

For one frozen candidate SHA, require all of:

- **R0 Repository Guard** — SUCCESS;
- **Python Core** — SUCCESS, including Ubuntu and Windows test jobs plus package builds;
- **KodeStudio UI Smoke** — SUCCESS.

No result from an earlier/rejected SHA may be reused. Any byte change after candidate acceptance creates a new head and requires fresh gates.

## End-of-subdivision governance

Only after the implementation candidate passes:

1. update `R13_PLAN.md` and continuity in the same work cycle so R13.2 becomes `COMPLETE` and R13.3 remains `PLANNED`;
2. re-run R0/full Python/UI on that exact final documentation head;
3. merge the implementation PR with `expected_head_sha`;
4. create exactly one post-merge normalization changing only `docs/continuity/KODEPOIA_CONTINUITY.md`;
5. prove its diff is continuity-only, run fresh exact-head R0/full Python/UI, and merge with the expected SHA;
6. only then declare R13.2 `COMPLETE + NORMALIZED` and authorize R13.3.

## Conditional/manual decision

No real SDK, toolchain, device, signing credential or store account is necessary for the R13.2 claim. Therefore its manual state is **NONE**. If an implementation accidentally introduces such a prerequisite, that is a scope defect to remove rather than a reason to manufacture PASS.
