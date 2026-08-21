# R4.5 — Code intelligence graphs — Acceptance

R4.5 may be accepted only when all of the following are true on the exact PR head:

- symbol/call/dependency graphs are produced from Tree-sitter-parsed workspace files;
- stable IDs remain stable across body-only edits;
- source provenance is preserved;
- ambiguous call targets are not guessed;
- SHA-identical files are skipped during incremental refresh;
- structured graph tools are bounded and workspace-confined;
- tests cover Python symbols/calls/dependencies, stable IDs, ambiguity, bounds and path escape;
- R0 Repository Guard succeeds;
- Python Core succeeds on Ubuntu and Windows with the code extra;
- KodeStudio UI Smoke succeeds on Windows.

R4 remains IN PROGRESS after R4.5. R4.6 orchestration and final acceptance are still mandatory.
