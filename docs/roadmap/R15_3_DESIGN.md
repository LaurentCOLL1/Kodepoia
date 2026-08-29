# R15.3 — Sanitization, privacy, license/provenance governance and revocation

**Status:** TECHNICAL SOURCE ACCEPTED / EXACT END-HEAD RE-GATES PENDING
**Normalized base:** `ac1101d9e67f5e0b36d8daaca2287e625d88787b`
**Clean START:** `ba719dd9d556909b08606d6c7ebb4d4ef18dbd37`
**Immutable technical source:** `e049a8f5c8155accb1d64ca4028deec5f85c4aa8`
**Manual state:** NONE

## Design

R15.3 is a deterministic governance layer after R15.2 raw capture. It never treats successful redaction as authorization. Training authorization remains the conjunction of independent source-scope, consent, provenance, license and privacy decisions.

The sanitizer creates a distinct sanitized content reference, SHA-256 output identity and digest-bound `TransformationRef`. Reports expose only categories, counts, digests, policy decisions and blockers; detected values and governed storage paths are never copied into the report.

License handling supports SPDX-style compound expressions with `AND`, `OR`, `WITH`, parentheses and case-insensitive operators. Policy is fail-closed: missing licenses stay `UNKNOWN`; unsupported/custom/unknown expressions stay `REVIEW`; explicit deny rules produce `DENY`; only explicitly allowlisted identifiers/exceptions produce `ALLOW`.

Revocation is lineage-aware. A governed source revocation transitions training-eligible records to `REVOKED`, observed records to `QUARANTINED`, computes downstream invalidation through dependency identities and stores only a reason digest in the safe report.

## Security invariants

- no sanitizer result can promote `UNKNOWN`, `REVIEW` or `DENY` authorization axes;
- benchmark-protected content remains quarantined even when all other authorization axes allow;
- raw secrets/private paths do not appear in sanitization reports;
- policy and transformation digests make sanitizer decisions reproducible;
- revocation invalidates derived artifact identities without copying source payloads;
- no network, external dataset, legal-advice claim or manual intervention is required for R15.3 acceptance.
