# R13.5 — Android signing states, keystore boundary + Play App Signing model

**Phase:** R13.5  
**Status:** IMPLEMENTED — acceptance is exact-head gated  
**Authorized base:** normalized R13.4 `main` `939565f6409a45c93d0168546c1b4bb947d13ad4`  
**Dedicated branch:** `r13/05-android-signing`  
**Manual:** CONDITIONAL / NOT TRIGGERED for core acceptance

## Objective

R13.5 adds a truthful Android signing model without turning signing credentials into durable project data. The implementation distinguishes unsigned, development/test, upload-key and Play App Signing readiness states; validates the public certificate identity actually attached to APK/AAB artifacts; and keeps keystore/private-key/password material behind `KodeSecrets` references resolved only at execution time.

R13.5 extends the accepted R13.4 Android build/export boundary. It does not create a second Android build pipeline, auto-publish to Google Play, create unattended production keys, or require a live Play account for core acceptance.

## External baseline — checked 2026-08-25

The design follows current official Android/Google Play semantics:

- Play App Signing separates the developer-held **upload key** from the **app signing key** used by Google Play to sign APKs delivered to users.
- A lost or compromised upload key can be replaced through the Play Console flow when Play App Signing is used; this does not mean that the app-signing private key is exposed to Kodepoia.
- Android `apksigner` supports verification of APK signatures and public signer-certificate output.
- JDK `jarsigner` verifies JAR-format signatures used by Android App Bundles; `keytool -printcert -jarfile` can expose the public signer certificate.
- Password-bearing signing tools support environment-backed password input; R13.5 therefore does not place literal secret values in model-visible or persisted argv.

Official references:

- https://support.google.com/googleplay/android-developer/answer/9842756
- https://developer.android.com/studio/publish/app-signing
- https://developer.android.com/tools/apksigner
- https://docs.oracle.com/en/java/javase/17/docs/specs/man/jarsigner.html
- https://docs.oracle.com/en/java/javase/17/docs/specs/man/keytool.html

These ecosystem facts are date-aware evidence, not frozen architecture constants.

## Frozen signing states

R13.5 exposes exactly these durable states:

| State | Meaning |
| --- | --- |
| `UNSIGNED` | No recognized signing material is present. |
| `DEBUG_SIGNED` | Verified certificate matches the configured public debug identity. |
| `TEST_SIGNED` | Verified certificate matches the configured public CI/test identity. |
| `UPLOAD_SIGNED` | Verified certificate matches the configured upload-key identity, without a complete Play App Signing identity pair. |
| `PLAY_APP_SIGNING_READY` | Verified certificate belongs to the accepted upload/app-signing identity model and the upload/app identities remain distinct. |
| `SIGNING_UNAVAILABLE` | Signing material appears present but the required trusted verifier/tool capability is unavailable, so no signed claim is manufactured. |

Certificate display names, aliases, filenames and labels are never sufficient to claim one of the signed states. Classification is bound to normalized public SHA-256 certificate fingerprints.

## Public identity model

`AndroidSigningIdentity` carries only optional public SHA-256 certificate fingerprints for debug, test, upload and app-signing identities. Fingerprints are normalized to lowercase 64-hex form.

Fail-closed rules:

- an unexpected certificate is rejected;
- multiple observed signer certificates are outside the R13.5 single-signer contract and are rejected;
- configured upload and app-signing fingerprints must be distinct;
- `PLAY_APP_SIGNING_READY` cannot be fabricated from a certificate name or alias;
- app-signing evidence without a distinct upload-key identity is rejected.

## KodeSecrets boundary

`src/kodepoia/core/secrets.py` adds the backward-compatible `SecretRef(namespace, key)` durable reference type and runtime-only resolution through `KodeSecrets`.

`AndroidSigningSecretRefs` contains references for:

- keystore location;
- store password;
- key alias;
- key password.

Durable evidence serializes only each reference's `namespace` and `key`. Raw resolved values are forbidden from source-controlled evidence. R13.5 adds reusable secret-leak checks that reject known secret values in JSON payloads.

The CI test keystore is intentionally ephemeral. Its private path, passwords and private-key material are created under a runner temporary directory, held only for execution, and removed in `finally` cleanup. Production credentials are never generated or requested by core acceptance.

## Process and environment boundary

Signing/verification uses fixed repository-owned argument construction. R13.5 does not accept arbitrary shell command strings.

A bounded environment is passed to signing tools. Only the platform/toolchain variables required for execution are inherited, plus explicitly generated temporary password variables. Literal password values are not persisted in evidence and are not inserted directly into signing argv.

## Artifact verification

### APK

1. Detect absence of JAR/APK-signing material truthfully.
2. For signed material, invoke trusted `apksigner verify --print-certs-pem`.
3. Reject a non-zero verifier result.
4. Parse returned PEM certificate bytes and compute SHA-256 over DER.
5. Classify only against the expected public identity.

### AAB

1. Detect JAR signature metadata under `META-INF`.
2. If absent, report `UNSIGNED` without requiring a signing tool.
3. For signed material, invoke `jarsigner -verify`.
4. Extract the public signer certificate with `keytool -printcert -rfc -jarfile`.
5. Compute SHA-256 over DER and classify only against the expected public identity.

If signature material exists but a required verifier is unavailable, the result is `SIGNING_UNAVAILABLE`, not a synthetic signed PASS.

## Durable signing evidence

`AndroidSigningInspection` records only:

- artifact kind (`apk` or `aab`);
- artifact SHA-256 digest;
- signing state and role;
- public certificate SHA-256 fingerprint(s);
- verifier identity;
- bounded blockers.

It deliberately does not contain artifact filesystem paths, keystore paths, passwords, private keys or raw process output.

`AndroidSigningAcceptanceEvidence` is schema version 1 and is bound to one exact lowercase 40-hex Git source SHA plus runner OS. A PASS requires truthful unsigned evidence and real `TEST_SIGNED` evidence for both APK and AAB.

## Upload-key rotation / recovery model

`AndroidUploadKeyRotation` records public identity transition metadata only:

- previous upload certificate SHA-256;
- replacement upload certificate SHA-256;
- unchanged/distinct app-signing certificate SHA-256;
- reason;
- positive recovery sequence.

The replacement upload certificate must differ from the previous upload certificate, and neither upload certificate may equal the app-signing certificate. No private key material is represented.

## Hosted acceptance design

`.github/workflows/r13-android-signing-acceptance.yml` runs on hosted Ubuntu and Windows and:

1. checks out the exact decision SHA;
2. provisions the accepted Python/JDK/Gradle/Android SDK toolchain;
3. reuses the R13.4 deterministic staging preparation;
4. builds the canonical debug APK and unsigned release AAB;
5. generates one ephemeral CI-only JKS identity;
6. signs copies of APK and AAB using environment-backed passwords;
7. verifies both signed artifacts with platform tools;
8. records only public/digest/reference evidence;
9. schema-validates and exact-head checks the JSON;
10. uploads only the redacted acceptance JSON.

The test keystore itself is never uploaded.

## Threat model and negative acceptance

R13.5 explicitly defends against:

- raw password/private-path leakage into durable evidence;
- certificate-name or alias spoofing;
- unexpected certificate substitution;
- conflating upload and app-signing keys;
- reporting signed state when trusted verification is unavailable;
- evidence replay against another source SHA;
- retaining CI private signing material after the collector exits.

## Manual gate

Manual intervention remains **CONDITIONAL / NOT TRIGGERED** for core R13.5 acceptance because hosted CI can prove the frozen state-model and test-signing semantics with an ephemeral identity.

Manual becomes required only if a later explicitly frozen claim needs a user/account-owned production upload/distribution signing operation. If that happens, execution must stop before the next subdivision and request only bounded user-controlled evidence; passwords, private keys and tokens must never be pasted into chat or committed to the repository.
