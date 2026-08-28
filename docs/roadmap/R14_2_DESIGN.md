# R14.2 — Project DNA/KodeProduct backend service intent design

## Scope

R14.2 makes backend capability explicit, optional and product-driven. It records only provider-neutral service intent in Project DNA and derives conditional Wizard questions plus KodeProduct requirements. It does not provision, deploy, authenticate to, pay for or execute any backend provider.

## Compatibility contract

- Project DNA remains `schema_version: 1`.
- The top-level `backend` profile is optional.
- Legacy DNA with no `backend` key loads unchanged and serializes without manufacturing that key.
- `backend: {enabled: false, services: []}` is valid, but the canonical legacy/default representation remains absence of the optional block.
- An absent or disabled profile creates zero backend runtime intents and zero backend KodeProduct requirements/constraints.

## Project service vocabulary

R14.2 may express only product-facing service intents:

- `auth`
- `authoritative_server`
- `matchmaking`
- `cloud_save`
- `progression`
- `catalog`
- `entitlement`
- `billing`
- `remote_config`
- `content_delivery`
- `events`

`database` and `liveops` remain outside Project DNA service intent. They are implementation/operational concerns for later R14 subdivisions and cannot be selected by R14.2.

## Dependency graph

The profile validates fail-closed:

- `matchmaking` requires `authoritative_server`;
- `billing` requires both `catalog` and `entitlement`.

Service tuples are normalized to deterministic unique lexical order. Runtime intent identifiers are derived as `backend.<service>` and contain identities/dependencies only.

## Secret/provider exclusion

Project DNA, runtime-intent evidence and JSON schemas do not contain provider names, provider account IDs, credentials, tokens, raw URLs, raw commands or deployment targets. The backend profile parser rejects unknown fields rather than silently preserving them.

## Wizard behavior

Offline/local-only projects with no backend-relevant product signal do not receive hidden backend questions. A backend-relevant project first receives only `backend_enabled`. Once enabled, `backend_services` and service-specific questions are derived from the selected profile:

- auth → identity;
- authoritative server → authoritative state/session;
- matchmaking → matchmaking;
- cloud save → cloud saves;
- progression → progression;
- catalog/entitlement/billing → commerce;
- remote config → config/flags;
- content delivery → content;
- events → events.

KodeStudio layers a Backend tab over the accepted R13 Project Wizard. The UI declares intent only; it performs no network operation or provider provisioning.

## KodeProduct mapping

An enabled profile maps to a single reserved P0 requirement `BACKEND-SERVICE-INTENT` plus deterministic `backend.service=<kind>` constraints. Reapplying the same profile is idempotent. Replacing the profile replaces only R14.2-reserved constraints/requirement and preserves unrelated product content.

## Runtime-intent semantics

`BackendRuntimeIntent` is descriptive evidence, not transport. Creating it does not open sockets, provision resources or authorize execution. R14.1 governance/network boundaries remain authoritative for any future active operation.

## Acceptance focus

R14.2 tests must prove legacy/offline zero intent, deterministic profiles/digests, schema round-trip, conditional question snapshots, strict secret/provider rejection, contradictory dependency rejection, platform-independent profile semantics and idempotent KodeProduct derivation.

## Manual intervention

NONE. R14.2 requires no provider account, credential, paid quota, live endpoint or external deployment.
