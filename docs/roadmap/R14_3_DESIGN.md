# R14.3 — Deterministic local backend scaffold/runtime design

## Scope

R14.3 provides only a reproducible **local/test** backend development surface. It does not implement authentication semantics, database persistence, authoritative gameplay/application logic, matchmaking, billing, public deployment, production TLS termination or managed hosting.

## Reused authorities

- `kodepoia.core.sandbox.ProcessSandbox` + `ManagedProcess` own the child process and register it with the existing KillSwitch.
- `kodepoia.core.secrets.KodeSecrets` / `SecretRef` remain the only secret boundary. Durable config contains references, never resolved values.
- R12 scaffold invariants are preserved: canonical bytes, SHA-256 lineage, sorted manifests, fail-closed path ownership and idempotent regeneration.
- R14.1 environment/service identities remain canonical; R14.2 `BackendRuntimeIntent` is the only bridge that can create a local backend config.

## Runtime architecture

`BackendLocalConfig` is strict and provider-neutral. It requires at least one R14.2 runtime intent, an explicit environment identity, IPv4 loopback bind, port `0` or an unprivileged fixed port, a typed log level and optional `SecretRef` values. Environment overlays may change environment/port/log level/secret references but cannot widen the bind address or mutate selected services.

`BackendScaffoldEngine` generates a canonical `.kodepoia/backend/runtime.json`, a deterministic workspace manifest and an explanatory README. Generation is idempotent; an already-owned file with divergent bytes is a hard conflict rather than an implicit overwrite.

`BackendLocalRuntime` starts the repository-owned module `kodepoia.backend.local_fixture_server` through `ProcessSandbox`, never through an arbitrary executable or shell command. The server binds loopback only, writes a bounded ready record, exposes `/healthz`, `/readyz` and `/livez`, and supports a loopback-only internal graceful shutdown request. Shutdown is attempted gracefully first and always falls back to the existing bounded ManagedProcess/KillSwitch cleanup.

Python 3.12 documents `ThreadingHTTPServer` as a basic threaded HTTP server and explicitly warns that `http.server` is not recommended for production. The same documentation shows explicit `--bind 127.0.0.1` usage. R14.3 therefore treats this server strictly as a deterministic local/test fixture, never as a production service.

Official reference: https://docs.python.org/3.12/library/http.server.html

## Secret boundary

No resolved secret is passed to the child process. Config and manifests retain `SecretRef(namespace,key)` only. Runtime logs contain service/config identity and secret-reference count, not values. `KodeSecrets.redact()` remains a defense-in-depth read boundary.

OWASP recommends centralized/controlled secret handling, notes that environment variables can leak through process/log/system surfaces, and states that secrets must never be logged. R14.3 therefore does not use environment variables as a secret transport.

Official reference: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

## Failure semantics

- non-loopback bind: rejected before launch;
- privileged fixed port: rejected before launch;
- occupied fixed port: child exits, parent fails closed and unregisters the process;
- `staging`/`production`: representable by typed config overlays but forbidden from starting this local fixture;
- divergent generated file: fail closed;
- readiness timeout or early exit: ManagedProcess cleanup is mandatory;
- KillSwitch activation: existing global/injected process governance remains authoritative.

## Acceptance evidence

Focused tests cover R14.2-to-R14.3 intent bridging, deterministic config/scaffold digests, strict schemas, environment overlays, secret-reference-only durability, byte-identical double generation, ownership conflicts, loopback policy, bounded start/health/stop, KillSwitch ownership, production refusal and fixed-port collision cleanup on supported CI hosts.
