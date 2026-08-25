# R12.12 — Acceptance

## Scope

Versioned, bounded, authenticated local IPC contracts with deterministic framing, replay protection, authorization, explicit OS-local transports and lifecycle cleanup. No TCP/network listener fallback is introduced.

Manual intervention: **CONDITIONAL / NOT TRIGGERED**.

Hosted exact-head Python Core proved both required OS transport seams: real Windows `AF_PIPE` and Linux `AF_UNIX` request/response roundtrips passed on the accepted candidate. No bounded manual evidence is required.

## Required acceptance

- protocol version, frame limits, replay window and endpoint identity are explicit and digest-stable;
- endpoint scope is structurally `local_only=true`; no `AF_INET`/TCP fallback exists;
- Windows uses an `AF_PIPE` address rooted at `\\.\pipe\`; hosted Linux uses `AF_UNIX` in a private runtime directory;
- application envelopes use deterministic canonical JSON plus SHA-256 HMAC authentication; runtime authentication keys are never serialized into envelopes/evidence;
- the transport's `multiprocessing.connection` authentication challenge also uses the runtime auth key;
- message length is explicitly framed and bounded before parsing; truncated, overlong, malformed and oversized messages fail closed;
- stale protocol versions fail closed;
- peer session, role and method are authorized against a bounded allowlist;
- replayed message IDs fail closed through a bounded replay window;
- transport receive uses bytes APIs only; untrusted pickle/object deserialization is not an IPC execution surface;
- listener/client resources are explicitly closed; Unix runtime socket directories are removed after owned endpoint closure;
- server acceptance threads are owned non-daemon threads and cannot silently outlive the acceptance run;
- focused R12.12 tests perform a real request/response roundtrip on hosted Windows `AF_PIPE` and hosted Linux `AF_UNIX` through Python Core;
- exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke succeed; desktop adapter workflows remain regression evidence.

## Web-researched implementation basis

- Microsoft documents that named-pipe access is controlled by security descriptors/DACLs and that default descriptors can grant broader read access than Kodepoia should assume; R12.12 therefore does **not** manufacture a claim that a custom Windows DACL is installed by Python's high-level transport wrapper;
- Microsoft documents that named pipes may be reachable remotely when the server service is available; Kodepoia allocates only local-machine `\\.\pipe\...` addresses, never accepts a remote machine address, requires authenticated application envelopes, and exposes no network-listener fallback;
- Python documents `multiprocessing.connection.Listener`/`Client` support for Windows `AF_PIPE` and Unix `AF_UNIX`, HMAC-based connection authentication, `send_bytes`/`recv_bytes`, and explicit listener closure.

Official references:

- https://learn.microsoft.com/windows/win32/ipc/named-pipe-security-and-access-rights
- https://learn.microsoft.com/windows/win32/ipc/named-pipes
- https://docs.python.org/3/library/multiprocessing.html#listeners-and-clients

## Evidence state

Base normalized `main`: `1f2d18b01e79845473fefbda98f722485310d92a`.
Branch: `r12/12-local-ipc`.
Accepted implementation candidate: `2ba561745f59b2701e5578df0915e58dab2345e0`.
Manual state: **CONDITIONAL / NOT TRIGGERED**.

Exact-head candidate gates:

- R0 Repository Guard #1556 / run `32825111226` — SUCCESS;
- Python Core #1530 / run `32825111135` — SUCCESS; hosted `python-core-windows-latest` and `python-core-ubuntu-latest` both completed `Test` successfully, proving the required real `AF_PIPE` and `AF_UNIX` seams;
- KodeStudio UI Smoke #1497 / run `32825111255` — SUCCESS;
- R12 WPF Acceptance #53 / run `32825111230` — SUCCESS;
- R12 WinUI3 Acceptance #43 / run `32825111274` — SUCCESS;
- R12 Avalonia Acceptance #39 / run `32825111277` — SUCCESS;
- R12 Qt6 Acceptance #34 / run `32825111137` — SUCCESS;
- R12 Tauri2 Acceptance #25 / run `32825111146` — SUCCESS.

The focused suite `tests/test_desktop_r12_12.py` is exercised by Python Core. Because both required hosted OS transport seams passed, the conditional manual gate is **NOT TRIGGERED**.

Evidence-recording documentation bytes changed after the accepted candidate. The resulting final documentation HEAD must therefore pass a fresh exact-head standard gate set plus desktop adapter regressions before merge.

## Merge / normalization rule

Freeze the resulting final documentation head and require exact-head gates. Merge PR #209 with `expected_head_sha`, perform exactly one continuity-only post-merge normalization, gate that exact head and merge it. R12.13 remains forbidden until R12.12 normalization merges.
