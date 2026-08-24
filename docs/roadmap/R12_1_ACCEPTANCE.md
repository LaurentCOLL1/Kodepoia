# Kodepoia — R12.1 Acceptance

**Subdivision:** R12.1 — Desktop contracts, identities, capability model + secure toolchain boundaries  
**Manual intervention:** NONE  
**Acceptance state:** PENDING EXACT-HEAD GATES

## Acceptance criteria

R12.1 is accepted only when one immutable implementation/documentation head satisfies all criteria below.

### Contract correctness

- all five frozen R12 framework families are represented without concrete adapter implementation;
- target/profile validation rejects impossible WPF/WinUI non-Windows targets and invalid MSI/MSIX target combinations;
- toolchain identities include exact executable SHA-256, version, OS, architecture and normalized capabilities;
- `AVAILABLE` cannot be manufactured without an exact toolchain identity;
- negative capability states cannot omit blockers;
- canonical serialization is deterministic and rejects NaN/non-serializable payloads.

### Secure toolchain boundary

- executable candidate must resolve to a real regular file under a configured runtime root and use the expected basename;
- project inputs cannot escape the project root and must have an allowlisted suffix;
- staging outputs cannot escape the staging root;
- only the bounded R12.1 environment override allowlist is accepted;
- dotnet/CMake/Cargo operations are selected from Kodepoia-owned fixed templates;
- no raw shell command, raw argv, arbitrary property/flag or unrestricted environment surface is introduced;
- Cargo build/test/check templates are locked and offline by default;
- R1 `ProcessSandbox` + KillSwitch remains the only execution authority.

### Schemas and adversarial tests

- target-profile and capability-report JSON schemas are Draft 2020-12 and reject unknown properties;
- traversal, executable substitution, environment injection, operation/config injection and forged capability states fail closed;
- deterministic digest behavior is tested.

## Automated evidence

Focused coverage is implemented in `tests/test_r12_1_desktop_contracts.py` and is part of the full Python Core `pytest` run.

Required exact-head gates:

1. R0 Repository Guard — SUCCESS;
2. full Python Core — SUCCESS on Ubuntu and Windows, including package builds and the internal KodeStudio smoke;
3. KodeStudio UI Smoke — SUCCESS.

The accepted head SHA and run IDs are recorded in continuity only after the first triplet succeeds. If that documentation update changes bytes, the resulting final documentation head is re-gated before merge.

## Manual gate

`NONE`. R12.1 makes no claim that dotnet/MSBuild/CMake/Qt/Rust toolchains are installed or that any generated desktop program executes. Therefore no local runtime evidence is required in this subdivision.

## Merge and normalization rule

After the exact final head passes all required gates, merge the R12.1 PR with `expected_head_sha`. Then create exactly one continuity-only post-merge normalization branch from that merge, gate the normalization head with the same triplet, merge it with `expected_head_sha`, and only then authorize R12.2.
