# R4.5 — Code intelligence graphs — Implementation summary

Implemented on `agent/r4-5-code-graphs`:

- Tree-sitter-backed multi-file `CodeGraphIndex`;
- symbols with stable IDs and source provenance;
- call edges with conservative target resolution;
- dependency/import edges;
- SHA-256 incremental file refresh with skip of unchanged files;
- stable symbol identity across body-only edits;
- bounded workspace-confined `GraphToolAPI`;
- tests for stability, provenance, ambiguity, dependencies, bounds and path escape.

Acceptance requires the exact PR head to pass Repository Guard, Python Core on Ubuntu+Windows and KodeStudio UI Smoke.
