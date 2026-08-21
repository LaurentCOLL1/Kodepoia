# R4.3 — LSP acceptance contract

R4.3 is accepted only when the exact PR head passes all repository workflows.

Required evidence:
- Repository Guard: SUCCESS;
- Python Core: SUCCESS on Ubuntu and Windows;
- KodeStudio UI Smoke: SUCCESS on Windows.

Functional acceptance:
- Content-Length framing round-trips UTF-8 JSON and rejects malformed/missing length;
- persistent stdio process launch stays within ProcessSandbox allowlist/root and remains kill-switch registered;
- scripted LSP lifecycle performs initialize/initialized, navigation requests, diagnostics capture, shutdown/exit;
- server->client JSON-RPC requests are answered rather than deadlocking;
- structured API exposes only registered server IDs, never arbitrary argv.

R4 remains IN PROGRESS after R4.3. R4.4 DAP is next.
