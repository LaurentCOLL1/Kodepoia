# R19.3 — Network UpdateTransport & Packaged Startup Wiring

R19.3 connects the production TUF trust bootstrap accepted in R19.2 to packaged KodeStudio without making network availability a startup dependency.

## Runtime transport

`NetworkUpdateTransport` is the single packaged network adapter for both trusted metadata discovery and verified target streaming.

- metadata is restricted to the four top-level TUF names (`root.json`, `targets.json`, `snapshot.json`, `timestamp.json`);
- metadata is fetched only from the canonical R19.2 HTTPS metadata base;
- canonical TUF target paths are converted to the matching GitHub Release `v<public_version>/<filename>` asset URL;
- connect and read timeouts are separate and bounded;
- metadata and installer responses have explicit byte ceilings;
- automatic redirects are disabled;
- metadata redirects cannot leave the configured metadata origin/path;
- release targets may redirect only between the declared GitHub release origin and explicit GitHub asset-delivery hosts;
- HTTPS downgrade, credential-bearing redirect URLs, path traversal and malformed target paths fail closed;
- connection/read outages map to `UpdateTransportOffline`; malformed, TLS, HTTP and confinement failures map to deterministic verification-safe errors.

GitHub Release assets are payload storage only. TUF metadata remains the authorization source for target path, length and SHA-256.

## Packaged startup

`build_packaged_update_services()` loads the exact R19.2 production Root pin locally, creates `UpdateDiscoveryService` and the network transport, and on Windows creates the verified delivery/install coordinator.

Service construction performs no HTTP request. Normal KodeStudio startup therefore remains independent of repository reachability. A local trust/bootstrap construction failure is converted to a non-destructive `verification-failed` discovery state rather than terminating the application.

The Windows install path keeps all R18.8 gates:

1. target must come from verified TUF metadata;
2. streamed length and SHA-256 must match the TUF authorization;
3. Authenticode must report `Valid` through fixed PowerShell code;
4. Windows ProductVersion must match the trusted public version;
5. explicit user confirmation is still required before launch;
6. staged bytes are hash/size rechecked immediately before installer handoff.

R19.3 does **not** authorize silent installation or the seamless replacement/restart behavior reserved for R19.4.

## Redirect contract

GitHub documents that release-asset downloads may be returned directly or by redirect. R19.3 therefore handles redirects explicitly instead of enabling generic redirect following. The accepted redirect host set is repository policy and cannot expand implicitly at runtime.

## Acceptance

The R19.3 acceptance workflow is exact-source and runs on Ubuntu and Windows. It covers compile/Ruff, focused network/startup tests, path and metadata allowlists, timeout/error mapping, byte ceilings, redirect confinement, production Root pinning, zero-network startup construction, Windows verified-install service construction, and preservation of explicit-consent semantics.

No private TUF key, Authenticode private key, token or password is required by R19.3.
