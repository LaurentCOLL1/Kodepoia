# R16.4 — Secrets, privacy and exfiltration hardening

## Security contract

R16.4 keeps raw secrets out of durable AI context, evidence, reports and artifacts. `SecretRef` remains the durable identity; raw material is resolved only at the narrow execution boundary that needs it.

`SecretTaintGuard` treats registered secret values and common reversible encodings (Base64, URL-safe Base64, double Base64 and hex) as tainted. It also treats common secret-bearing field names and well-known token signatures as sensitive. Redaction produces metadata and placeholders only; no raw value or transformed secret is returned by durable reporting APIs.

## Boundary rules

1. Secret values are never required in roadmap/continuity, acceptance JSON, log/report evidence or repository fixtures.
2. Raw secret material is denied in command-line arguments and ordinary environment maps.
3. `EphemeralSecretResolver` resolves `SecretRef` objects only at the immediate use boundary and does not durably cache values. A later resolution therefore observes backend rotation/revocation state.
4. `SecretAwareProcessSandbox` adds secret environment values only immediately before process launch and redacts captured stdout/stderr before returning them.
5. Secret-tainted network/tool payloads require both an explicitly approved destination host and an explicit `allow_secret_payload` decision. Secret material in destination URLs is always denied.
6. Failure diagnostics keep exception type/context while redacting secret material.
7. `ArtifactLeakScanner` scans bounded local evidence/artifact trees for registered raw or encoded secret canaries, reports locations only, and fails closed when scan bounds are exceeded.
8. Synthetic secret canaries are the only secret material used by R16.4 acceptance. No live credential, external upload or destructive action is authorized.

## Evidence model

The acceptance report binds the exact Git SHA and exposes only case IDs, PASS/FAIL observations, security-claim state and a semantic digest. The runner self-checks that neither the synthetic canary nor its rotated value appears in the serialized report.

## Acceptance coverage

Cross-platform Ubuntu/Windows acceptance verifies:

- raw, Base64 and double-Base64 redaction;
- durable `SecretRef` serialization without materialization;
- denial of raw secrets in argv and ordinary environment maps;
- explicit destination authorization for secret-tainted egress without performing network calls;
- rotation-aware re-resolution and redaction of both old and new values;
- narrow subprocess environment resolution with captured stdout/stderr redaction;
- artifact leak detection with location-only evidence;
- useful redacted failure diagnostics.

The implementation follows the same principles documented by OWASP for secret lifecycle, logging exclusion, rotation/revocation and artifact hygiene, and by Python for explicit subprocess environment construction. GitHub-specific masking remains defense in depth rather than the primary R16.4 boundary.
