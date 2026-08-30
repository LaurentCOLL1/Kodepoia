# R15.8 acceptance contract

R15.8 is accepted only on an exact source head after all of the following pass on Ubuntu and Windows where applicable:

- core installation/tests with no tuning ML extras installed;
- import of `kodepoia.tuning` without loading torch/transformers/bitsandbytes/PEFT/TRL;
- synthetic CPU `SUPPORTED` capability;
- synthetic accelerator `SUPPORTED`, `UNSUPPORTED` and unknown/failure paths;
- actual-operation semantics for requested dtype and bitsandbytes NF4 capability;
- disk/RAM preflight prevents any subprocess when already over budget;
- VRAM preflight prevents model load when free/total evidence is insufficient or unavailable;
- model/tokenizer dry-run is a distinct second local-only phase after admission;
- model/tokenizer/config values never enter subprocess argv;
- timeout and KillSwitch cancellation produce terminal non-success states;
- stdout/stderr failures are bounded/redacted and secrets/private user paths are absent from reports;
- capability request/report digests are deterministic;
- JSON schema validates;
- R15.8 workflow, R0 Repository Guard, full Python Core and KodeStudio UI Smoke all succeed on the exact final head.

A real GPU result is optional for this subdivision unless a specific backend is explicitly being qualified. Hardware-specific authoritative qualification remains conditional and cannot be inferred from a device name.
