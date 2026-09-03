# Kodepoia v1.0.0rc1 — Release Candidate Notes

## Release status

`1.0.0rc1` is the first v1.0 release-candidate identity for the repository-owned Python package and R16 release-readiness evidence. It is an **unsigned core RC**, not a public production release. The R16.17 workflow builds wheel and source-distribution artifacts from one exact Git SHA, records SHA-256 evidence, verifies a same-source rebuild, and consumes the wheel through an offline `pip --no-index --no-deps` installation probe.

No store submission, public package-registry publication, production signing, production credential use, provider cutover, or domain cutover is performed automatically. Those actions remain conditional and require separate explicit authorization and evidence.

## Supported RC evidence

The core RC evidence covers the repository Python wheel and sdist, exact-source `BuildManifest`, R16.9 supply-chain binding, deterministic dependency/BOM inventory, license-review evidence, the declared `0.1.0a4` prior-state migration fixture, verified pre-migration backup, successful upgrade to `1.0.0rc1`, and exact rollback after an injected migration failure. Existing representative Windows desktop, Godot, ComfyUI, media, durability, resource and adversarial evidence remains governed by its own R16 authorities and is not silently converted into new live-capability claims here.

## Known limitations and truthful unknowns

Dependency declarations in `pyproject.toml` are version ranges, not a fully resolved lockfile. R16.17 therefore records those dependency components as unresolved with unknown integrity and `NOASSERTION` license evidence rather than claiming exact third-party package hashes or licenses. The SPDX output is a compatibility view and explicitly **not** an SPDX conformance claim.

GitHub artifact attestations can provide additional cryptographically signed provenance for public-repository artifacts, but the frozen R16.9 policy does not require external attestation for core promotion and treats it as provenance-only, not a security verdict. R16.17 therefore records external attestation as `NOT_EXERCISED` unless separately added under an authorized policy change.

## Promotion boundary

`1.0.0rc1` is only a candidate. R16.18 must still re-run the final integrated adversarial and representative-project RC authority on one exact source. A green R16.17 result does not by itself declare R16 or Kodepoia v1.0 complete, signed, published, production-ready, or generally available.
