# R15.8 acceptance contract

R15.8 is accepted only on an exact source head after all of the following pass on Ubuntu and Windows where applicable:

- core installation/tests with no tuning ML extras installed;
- import of `kodepoia.tuning` without loading torch/transformers/bitsandbytes/PEFT/TRL;
- synthetic CPU `SUPPORTED` capability;
- synthetic accelerator `SUPPORTED`, `UNSUPPORTED` and unknown/failure paths;
- actual-operation semantics for requested dtype and bitsandbytes NF4 capability;
- disk/RAM preflight prevents any subprocess when already over budget, and a configured nonzero requirement with unavailable host measurement fails closed before subprocess launch;
- VRAM preflight prevents model load when free/total evidence is insufficient or unavailable;
- model/tokenizer dry-run is a distinct second local-only phase after admission;
- model/tokenizer/config values never enter subprocess argv;
- timeout and KillSwitch cancellation produce terminal non-success states;
- stdout/stderr failures are bounded/redacted and secrets/private user paths are absent from reports;
- capability request/report digests are deterministic;
- JSON schema validates;
- R15.8 workflow, R0 Repository Guard, full Python Core and KodeStudio UI Smoke all succeed on the exact final head.

A real GPU result is optional for this subdivision unless a specific backend is explicitly being qualified. Hardware-specific authoritative qualification remains conditional and cannot be inferred from a device name.

## Technical acceptance evidence

- Immutable technical source: `fa932e4a436004045074f417005b2edc038cfc87`.
- R15.8 #5 / 33306096508: SUCCESS on Ubuntu + Windows.
- Focused suite: 13/13 tests per OS, followed by Ruff, compileall, `python -m kodepoia.tuning --help` and JSON-schema validation.
- Workflow installs only core + `dev`, proving core acceptance without tuning ML extras.
- Compatibility hardening from current upstream documentation is included: NF4 is operation-probed without a hard-coded CPU rejection, and unknown configured host budgets fail closed.
- Manual local GPU/backend qualification: **CONDITIONAL / NOT TRIGGERED** for core R15.8.
- These are immutable technical-source proofs only. Fresh R15.8, R0 Repository Guard, full Python Core and KodeStudio UI Smoke must all succeed on the exact final documentation END-head before merge.
