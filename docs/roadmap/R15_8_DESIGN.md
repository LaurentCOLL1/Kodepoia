# R15.8 — Optional training runtime and capability probes

## Scope

R15.8 creates a bounded optional training-runtime boundary. It does **not** train adapters, install drivers, download models, mutate GPU drivers, or make PyTorch/Transformers/bitsandbytes dependencies of the Kodepoia core install. Actual QLoRA/SFT execution remains R15.9.

## Dependency isolation

`kodepoia.tuning` is core-importable with no ML extra installed. Heavy packages are imported only by `kodepoia.tuning.probe_worker`, which is launched through the accepted R1 `ProcessSandbox` and `KillSwitch` boundary. The optional dependency profiles are declared in `pyproject.toml`:

- `tuning`: PyTorch, Transformers, Accelerate, PEFT, TRL and safetensors;
- `tuning-bnb`: bitsandbytes, separately optional because 4-bit backend support must be proven by operation rather than assumed.

No training dependency is imported by the top-level Kodepoia CLI merely to expose R15.8.

## Structured launch boundary

The public API accepts `RuntimeRequest`, not arbitrary commands, argv, cwd, URLs or environments. The subprocess argv is repository-owned and fixed to Python + `-m kodepoia.tuning.probe_worker` + one generated configuration filename. Model/tokenizer identifiers are written only into the private ephemeral configuration file inside the sandbox root; they never appear in argv or the capability report.

The child environment is the already accepted reduced `ProcessSandbox` environment. R15.8 adds no arbitrary environment passthrough. Timeouts and global cancellation use the existing KillSwitch registration semantics.

## Capability semantics

A package import is not proof of a usable backend. The worker performs the smallest actual operations required by the requested path:

1. import and version evidence for PyTorch;
2. a real tensor/matrix operation on the requested CPU/CUDA/ROCm device;
3. the requested dtype operation;
4. for `bnb_nf4`, construction and execution of a tiny bitsandbytes `Linear4bit` NF4 operation;
5. optional local-only tokenizer/model load with `trust_remote_code=False` after resource admission.

ROCm is identified from the PyTorch runtime (`torch.version.hip`) plus an actual accelerator operation. CUDA and ROCm are never inferred from the GPU marketing/device name.

## Resource preflight

Disk and RAM are measured before any ML worker launch. Accelerator free/total VRAM is measured by the successful PyTorch device probe. The model-load dry-run is a second process and cannot start until all configured disk/RAM/VRAM requirements pass.

Resource evidence uses the accepted R6 metric vocabulary (`storage_mb`, `ram_mb`, `vram_mb`). VRAM policy uses the same fail-closed semantics established by R9: insufficient current free VRAM blocks work, an impossible total requirement blocks work, and missing accelerator telemetry is `UNKNOWN`/blocked rather than guessed. R15.8 does not introduce a second GPU scheduler or unload unrelated workloads.

## Reproducibility and privacy

The request records deterministic model/data seeds and has a canonical SHA-256 identity. Capability reports have a canonical digest. Reports contain only bounded package versions, Python/backend versions, minimal device descriptors, resource evidence and state. They do not serialize process argv, unrelated environment variables, usernames or arbitrary machine paths.

Worker stderr/stdout failure evidence is bounded and redacted for credential assignments, private keys, email addresses and user-home paths before it can enter a report.

## External compatibility note

Official Hugging Face bitsandbytes documentation checked during R15.8 implementation documents NF4 as the recommended 4-bit type for QLoRA and documents backend-specific installation/support requirements. These references guide probe construction only; Kodepoia treats the actual bounded operation probe on the accepted runtime as authority.

## Manual intervention

None for core R15.8 acceptance. A real local GPU/backend probe is conditional evidence only and must not be substituted for the deterministic CI/fake acceptance suite. No driver installation or system mutation is requested by R15.8.
