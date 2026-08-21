# R4.6 — Governed orchestration — Final R4 acceptance

R4 may be marked COMPLETE only if all conditions below are true on the exact R4.6 PR head and after merge normalization.

## Functional acceptance

- base KodeCode and graph structured catalogs are both exposed through one governed executor;
- every exposed tool has an explicit policy classification;
- Guardian + PermissionSet authorize before invocation;
- missing FILE_WRITE denies patch before mutation;
- missing PROCESS_EXECUTE denies process-bearing tools before launch;
- protected file writes take a SafeChange snapshot before mutation;
- audit hash chain remains valid after denied and successful operations;
- Orchestrator supplies the tool catalog to a tool-capable Brain when configured;
- Ollama-style tool calls execute only through the governed executor;
- no hidden autonomous tool loop or arbitrary shell/filesystem tool is introduced.

## Repository-scale acceptance

A deterministic test workspace must create at least 30 source files and validate:

- file read;
- repository text search;
- Tree-sitter parse;
- graph refresh across all files;
- symbol, call and dependency queries;
- unchanged-file incremental skip;
- protected patch with snapshot;
- graph refresh of changed file;
- stable symbol ID across body-only edit;
- audit verification.

## CI acceptance

On the exact final R4.6 PR head:

- R0 Repository Guard — SUCCESS;
- Python Core — SUCCESS on Ubuntu and Windows;
- KodeStudio UI Smoke — SUCCESS on Windows.

After merge, roadmap/status and continuity must be normalized on `main`, record the final evidence and set `R4 = COMPLETE`. That post-merge normalization must itself pass required branch checks before merge. R5 is not authorized before this sequence is complete.
