# Kodepoia — R7.4 acceptance

**Subdivision:** R7.4 — GitHub research adapter  
**Status:** COMPLETE  
**Accepted implementation head:** `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be`  
**Implementation PR:** #66  
**Implementation merge:** `d17746b03fe4a8db47ec2c55ef11715fdd820f73`  
**Manual:** CONDITIONAL — NOT TRIGGERED

## Exact-head CI evidence

All required gates ran against exact implementation head `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be`:

- R0 Repository Guard #972 / run `32589899654`: **SUCCESS**;
- Python Core #946 / run `32589899648`: **SUCCESS**, 5/5 jobs;
- Python authoritative Ubuntu suite: **388 passed / 3 skipped / 46 warnings**;
- Python Core Windows test job: **SUCCESS**;
- package-build Ubuntu: **SUCCESS**;
- package-build Windows: **SUCCESS**;
- embedded KodeStudio UI job in Python Core: **SUCCESS**;
- KodeStudio UI Smoke #913 / run `32589899651`: **SUCCESS**.

No failed, cancelled, missing or fabricated required gate is accepted as PASS.

## Accepted capability

R7.4 provides a read-only typed GitHub research adapter with:

- structured owner/repository/resource selectors;
- repository metadata, commits, exact blobs, repository files, releases/tags, issues/PRs and comments;
- mutable ref -> exact commit SHA resolution before file evidence;
- exact-SHA human-facing file locators;
- fixed `https://api.github.com:443` production origin;
- R7.3 DNS/public-target protections and existing Guardian `NETWORK` authorization;
- bounded pagination and explicit truncation;
- GitHub rate-limit response evidence and explicit `UNAVAILABLE/rate_limited` state;
- optional secret-reference authentication via `KodeSecrets`, resolved only inside the transport;
- deterministic fixture transport for CI;
- ResearchGuard wrapping for every GitHub content artifact;
- versioned `github-research-evidence-v1` schema.

## Security invariants accepted

1. No GitHub write endpoint is exposed by the adapter.
2. No model-supplied arbitrary HTTP method, body, header, GraphQL document, proxy, host or cookie surface is introduced.
3. `Link` pagination URLs are not executed directly; only the existence of `rel=next` is used and the next bounded page is reconstructed on the fixed API origin.
4. File research does not cite mutable branch content as immutable: the ref is resolved first and the exact returned SHA is used for the content request and locator.
5. Exact blob research requires a validated object SHA.
6. Provider JSON/file/comment content remains external untrusted data and cannot become agent instruction.
7. Optional tokens never enter request-domain objects, artifacts, metadata or acceptance evidence.
8. A 403 with exhausted primary limit or a 429 is explicit unavailable evidence; the adapter does not hide retries or sleeps.
9. No remote state is mutated by acceptance or by the adapter design.

## External reference context

Implementation was cross-checked against GitHub's current REST documentation for pagination, rate-limit headers and REST best practices. These references are implementation context only; Kodepoia makes no certification/compliance claim.

## Manual gate

R7.4 manual status is **CONDITIONAL NOT TRIGGERED**. Hosted acceptance exercised public unauthenticated behavior and deterministic optional-secret injection without requiring a private repository or real credential. If a future acceptance explicitly requires private/authenticated proof, use a least-privilege read-only credential stored through KodeSecrets and persist only redacted capability/result evidence.

## Rollback

Rollback is repository-local: remove/disable the R7.4 adapter, exports, schema and tests, remove any configured optional secret reference, and purge cached GitHub research artifacts if desired. No GitHub remote mutation needs reversal.
