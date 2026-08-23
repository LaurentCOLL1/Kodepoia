# R10.1 — Acceptance record

Status: **PENDING EXACT-HEAD GATES**  
Manual intervention: **NONE**

## Frozen acceptance requirements

The implementation candidate must demonstrate all of the following on one exact head before merge:

- R0 Repository Guard SUCCESS;
- full Python Core SUCCESS on Ubuntu/Windows with prior R7/R8/R9 integrated acceptance still PASS;
- KodeStudio UI Smoke SUCCESS;
- `tests/test_blender_r10_1.py` passes;
- canonical recipe/runtime identities are deterministic;
- Blender 5.2.x policy accepts 5.2 and rejects adjacent 4.5/5.1/5.3 profiles;
- executable discovery/path escapes and environment injection fail closed;
- generated argv contains only the fixed R10.1 Blender process template;
- no Blender process, `bpy`, geometry mutation or export is executed by R10.1;
- all five R10 schema roots validate representative v1 documents.

The accepted head SHA and authoritative CI run IDs are appended only after the exact candidate has completed all gates. Missing evidence never becomes PASS.
