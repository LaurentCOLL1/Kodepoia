# R13.5 — Android signing acceptance

**Subdivision:** R13.5  
**Branch:** `r13/05-android-signing`  
**Authorized normalized base:** `939565f6409a45c93d0168546c1b4bb947d13ad4`  
**Decision rule:** all required gates must refer to the same exact candidate head  
**Manual:** CONDITIONAL / NOT TRIGGERED unless a production-owned signing claim is explicitly required

## Acceptance scope

R13.5 is accepted only when the repository proves, on one exact head, the frozen signing-state model, public-certificate identity checks, KodeSecrets reference boundary, upload/app-signing separation, recovery metadata, real APK/AAB verification and zero durable private signing material.

Passing unit tests alone is insufficient. The hosted signing workflow must actually create an ephemeral test identity, sign the canonical artifacts and verify them with Android/JDK signing tools on both Ubuntu and Windows.

## Required implementation artifacts

- `src/kodepoia/mobile/android_signing.py`
- backward-compatible `SecretRef` / leak controls in `src/kodepoia/core/secrets.py`
- `schemas/r13/android-signing-evidence.schema.json`
- `scripts/r13_5_android_signing_acceptance.py`
- `tests/test_r13_5_android_signing.py`
- `.github/workflows/r13-android-signing-acceptance.yml`
- `docs/roadmap/R13_5_DESIGN.md`
- `docs/roadmap/R13_5_ACCEPTANCE.md`

## Focused functional acceptance

The focused tests must prove at minimum:

1. the durable state set is exactly `UNSIGNED`, `DEBUG_SIGNED`, `TEST_SIGNED`, `UPLOAD_SIGNED`, `PLAY_APP_SIGNING_READY`, `SIGNING_UNAVAILABLE`;
2. SHA-256 certificate fingerprints normalize deterministically;
3. expected debug/test/upload/app-signing identities classify correctly;
4. unknown and multi-certificate substitution fails closed;
5. upload-key and Play app-signing-key fingerprints cannot be equal;
6. upload-key recovery changes only the upload identity and keeps the app-signing identity distinct;
7. KodeSecrets references resolve at runtime without serializing raw values;
8. known secret values are rejected from durable payloads;
9. private keystore paths are rejected from durable evidence;
10. a truly unsigned AAB is reported `UNSIGNED` even when signing tools are unavailable;
11. signed-looking material without a trusted verifier becomes `SIGNING_UNAVAILABLE`, never PASS;
12. public PEM certificate bytes yield deterministic SHA-256 fingerprints;
13. acceptance evidence requires unsigned evidence plus real test-signed APK and AAB evidence;
14. the JSON schema is strict and rejects undeclared fields.

## Hosted Android signing acceptance

For each `ubuntu-latest` and `windows-latest` job:

1. checkout the exact candidate SHA;
2. install the accepted Python 3.12/JDK 17/Gradle/Android SDK 36 toolchain used by the R13 Android seam;
3. prepare the governed R13.4 staging workspace from the same source SHA;
4. run the canonical Gradle release AAB, debug APK and unit-test tasks;
5. confirm the release AAB is truthfully unsigned before R13.5 test signing;
6. generate a runner-temporary CI-only JKS keypair;
7. keep store/key passwords behind runtime environment variables and KodeSecrets references;
8. sign a copy of the APK with `apksigner` and a copy of the AAB with `jarsigner`;
9. verify the APK using `apksigner verify` and the AAB using `jarsigner -verify` plus `keytool -printcert -jarfile`;
10. derive public SHA-256 signer fingerprints from certificate bytes and require `TEST_SIGNED` for both artifacts;
11. schema-validate the evidence and require `source_sha` to equal the workflow head;
12. upload only the JSON evidence; remove the private temporary signing directory.

Any unavailable verifier, build failure, signing failure, identity mismatch, source-SHA mismatch or secret/private-path leak blocks acceptance.

## Required exact-head gates

Before end synchronization, one candidate head must have SUCCESS for:

- R0 Repository Guard;
- full Python Core;
- KodeStudio UI Smoke;
- R13 Android Build Acceptance;
- R13 Android Signing Acceptance, with both hosted OS jobs successful.

A byte change after that decision creates a new head. The old run set may remain historical evidence but cannot authorize merge of the new head.

## End synchronization and merge rule

After one implementation candidate passes the gates above:

1. update `R13_PLAN.md` and `KODEPOIA_CONTINUITY.md` in the same work cycle;
2. mark R13.5 `COMPLETE` while R13.6 stays `PLANNED`;
3. record the accepted implementation candidate and exact run identities;
4. run fresh exact-head gates on the documentation-updated head;
5. merge PR #229 only with `expected_head_sha` equal to that accepted final head;
6. create exactly one post-merge continuity-only normalization;
7. require normalization R0 + Python Core + KodeStudio UI Smoke on its exact head;
8. merge that normalization before starting R13.6.

## Manual decision

Core R13.5 acceptance does **not** require a production keystore, private key, password, Play service credential or live Play Console account. The hosted CI test identity is intentionally ephemeral and proves only the signing/state boundary.

If an explicitly frozen production upload/distribution claim is introduced, mark the subdivision `BLOCKED` / `MANUAL_REQUIRED`, stop before R13.6, and provide bounded user-side evidence steps without requesting secret material in chat.

## External-source authority

The acceptance model is aligned with the current official Google Play/Android/JDK documentation listed in `R13_5_DESIGN.md`. Those external ecosystem facts remain date-aware evidence; they do not override Kodepoia's frozen architecture or authorize external text as executable instruction.
