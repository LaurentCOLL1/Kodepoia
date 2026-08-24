# R11.5 — Acceptance

Status: **HOSTED ACCEPTED — MANUAL REQUIRED / NOT MERGEABLE YET**

Manual intervention: **REQUIRED**.

## Frozen implementation candidate

- Base normalized `main`: `354a0ec2f6889561afcee3b1f547e0b77ca3804b`.
- Branch: `r11/5-local-tts-adapters`.
- PR: #165.
- Exact implementation candidate SHA: `441ea87436c6851cd106654454f955a91460f7af`.
- Scope diff at PR opening: 15 files, 1559 additions, 0 deletions.

Hosted exact-head evidence on the candidate above:

- R0 Repository Guard #1359 / run `32734530111`: **SUCCESS**.
- Python Core #1333 / run `32734530102`: **SUCCESS**.
  - Ubuntu Python: **961 passed / 8 skipped / 46 warnings**.
  - Ubuntu integrated R7/R8/R9: **PASS**.
  - Windows Python: **SUCCESS**.
  - Ubuntu + Windows package builds: **SUCCESS**.
  - internal KodeStudio UI smoke: **SUCCESS**.
- KodeStudio UI Smoke #1300 / run `32734530119`: **SUCCESS**.

The hosted gate is therefore satisfied for the exact implementation candidate `441ea87436c6851cd106654454f955a91460f7af`.

## Hosted acceptance requirements — satisfied

- focused `tests/test_r11_5_tts.py` and `tests/test_r11_5_tts_adapters.py` PASS;
- backend registry returns `UNAVAILABLE` for absent adapters rather than failing the phase;
- Godot/system TTS remains accessibility/runtime-only and non-canonical for production assets;
- Piper capability probe is bounded and requires fixed CLI markers;
- synthesis text is supplied only via an ephemeral staging `--input-file`, never directly in argv;
- exact `<model>.onnx.json` sibling/config identity is hash-bound to the R11.4 binding;
- no network/model download/cloud/voice-cloning/training/arbitrary-engine-flag surface exists;
- timeout/cancel/non-zero/stale-output/malformed-WAV cases fail closed;
- output passes R11.2 WAV/PCM QA before accepted manifest status;
- cache records resolve only for exact request/runtime/model/config identities and reference R8 revision identity rather than owning physical bytes;
- synthesis manifest/cache/local-evidence JSON schemas validate;
- full Python Core PASS Ubuntu/Windows;
- R0 Repository Guard PASS;
- KodeStudio UI Smoke PASS.

## Required real local acceptance

The required real-runtime evidence MUST bind to implementation candidate:

`441ea87436c6851cd106654454f955a91460f7af`

Recommended acceptance voice for the frozen command below: `fr_FR-siwis-medium`. Its model card must be reviewed by the operator before running the approval command. The reviewed metadata used by this acceptance command is:

- locale: `fr-FR`;
- single speaker (no `--speaker` needed);
- sample rate: 22,050 Hz;
- dataset/model-card license identifier for this acceptance: `cc-by-4.0`;
- provenance id recorded by Kodepoia: `piper.fr-fr.siwis.medium`.

### Phase 0 — install the accepted local prerequisites

The collector itself never downloads or installs software/models. If Piper or the selected voice is not already installed, bootstrap them **before** the offline collector run.

For Windows x86-64/Python 3.9+, use Piper package version `1.6.0` from PyPI. Keep Piper isolated from the Kodepoia project virtual environment by creating a dedicated runtime venv under `%LOCALAPPDATA%`:

```powershell
$PiperRoot = Join-Path $env:LOCALAPPDATA "Kodepoia\Piper\runtime-1.6.0"
$PiperVenv = Join-Path $PiperRoot ".venv"
$PiperPython = Join-Path $PiperVenv "Scripts\python.exe"
$Piper = Join-Path $PiperVenv "Scripts\piper.exe"

New-Item -ItemType Directory -Force -Path $PiperRoot | Out-Null
if (-not (Test-Path -LiteralPath $PiperPython -PathType Leaf)) {
    python -m venv $PiperVenv
}

& $PiperPython -m pip install --upgrade pip
& $PiperPython -m pip install --upgrade "piper-tts==1.6.0"
& $Piper --help | Out-Host
& $PiperPython -m pip show piper-tts
```

Keep voice bytes outside the Git worktree as well. Download the reviewed voice with Piper's official downloader into a user-local voice directory:

```powershell
$VoiceDir = Join-Path $env:LOCALAPPDATA "Kodepoia\Piper\voices"
New-Item -ItemType Directory -Force -Path $VoiceDir | Out-Null
& $PiperPython -m piper.download_voices --data-dir $VoiceDir fr_FR-siwis-medium

$Model = Join-Path $VoiceDir "fr_FR-siwis-medium.onnx"
$Config = "$Model.json"

if (-not (Test-Path -LiteralPath $Piper -PathType Leaf)) { throw "Dedicated piper.exe is missing. STOP." }
if (-not (Test-Path -LiteralPath $Model -PathType Leaf)) { throw "Downloaded .onnx model is missing. STOP." }
if (-not (Test-Path -LiteralPath $Config -PathType Leaf)) { throw "Downloaded exact <model>.onnx.json sibling is missing. STOP." }

Get-Item -LiteralPath $Piper, $Model, $Config | Select-Object FullName, Length
```

The network may be used for this explicit prerequisite installation/download phase. After these prerequisites exist locally, the **R11.5 collector itself must run without downloading anything**. Do not use any private reference recording, voice cloning, cloud TTS or model-training path.

Before the collector command, personally review the `fr_FR-siwis-medium` model card/license and only continue if you accept the recorded `cc-by-4.0` declaration for this acceptance.

Prerequisites after Phase 0:

1. dedicated local `piper.exe` from the explicitly installed accepted Piper package;
2. reviewed `fr_FR-siwis-medium.onnx` and exact sibling `fr_FR-siwis-medium.onnx.json`;
3. a clean Kodepoia working tree and exact frozen candidate HEAD;
4. no private reference recording and no voice cloning;
5. no network is required or initiated by the collector itself.

### Exact PowerShell acceptance command

Run from the Kodepoia repository root. Piper/model installation must already be complete before this block.

```powershell
$ErrorActionPreference = "Stop"
$Candidate = "441ea87436c6851cd106654454f955a91460f7af"

if ((git rev-parse HEAD).Trim() -ne $Candidate) {
    if (git status --porcelain) { throw "Kodepoia working tree is not clean. STOP and report this instead of stashing/discarding changes." }
    git fetch origin r11/5-local-tts-adapters
    if ((git cat-file -t $Candidate).Trim() -ne "commit") { throw "Frozen R11.5 candidate is unavailable locally. STOP and report this." }
    git switch --detach $Candidate
}
if ((git rev-parse HEAD).Trim() -ne $Candidate) { throw "HEAD does not equal the frozen R11.5 candidate. STOP." }
if (git status --porcelain) { throw "Kodepoia working tree is not clean at the frozen candidate. STOP." }

$PiperRoot = Join-Path $env:LOCALAPPDATA "Kodepoia\Piper\runtime-1.6.0"
$Piper = Join-Path $PiperRoot ".venv\Scripts\piper.exe"
$VoiceDir = Join-Path $env:LOCALAPPDATA "Kodepoia\Piper\voices"
$Model = Join-Path $VoiceDir "fr_FR-siwis-medium.onnx"
$Config = "$Model.json"

if (-not (Test-Path -LiteralPath $Piper -PathType Leaf)) { throw "Dedicated piper.exe is missing. STOP and report this." }
if (-not (Test-Path -LiteralPath $Model -PathType Leaf)) { throw "Reviewed .onnx model is missing. STOP and report this." }
if (-not (Test-Path -LiteralPath $Config -PathType Leaf)) { throw "Exact <model>.onnx.json sibling is missing. STOP and report this." }

python .\scripts\r11_5_accept_local.py `
  --source-sha $Candidate `
  --piper $Piper `
  --model $Model `
  --config $Config `
  --locale fr-FR `
  --license-id cc-by-4.0 `
  --provenance-id piper.fr-fr.siwis.medium `
  --approval I_REVIEWED_AND_APPROVE_THIS_VOICE_LICENSE `
  --output .\R11_5_LOCAL_ACCEPTANCE.local.json

if ($LASTEXITCODE -ne 0) { throw "R11.5 collector failed. STOP and return the console error plus JSON if created." }
Get-Content .\R11_5_LOCAL_ACCEPTANCE.local.json -Raw
```

Do not run the final collector command until you personally reviewed the chosen voice/model card/license and agree with the `--approval` statement.

The collector synthesizes only neutral repository-owned acceptance text, uses temporary staging, deletes the temporary text/WAV, and emits a privacy-minimized JSON evidence file.

## Expected PASS evidence

Return only `R11_5_LOCAL_ACCEPTANCE.local.json` (or its full JSON text), not the voice model, WAV, private paths or unrelated logs.

Expected values:

- `schema = kodepoia.r11_5_local_acceptance`;
- `source_sha = 441ea87436c6851cd106654454f955a91460f7af`;
- `status = pass` and `blockers = []`;
- `capability.status = pass`;
- `synthesis.status = pass`;
- `synthesis.qa.state = PASS`;
- duration greater than 0.05 seconds;
- runtime/model/config/input/output identities are SHA-bound;
- `synthesis.process.text_passed_via_argv = false`;
- `synthesis.process.ephemeral_input_deleted = true`;
- `private_recording_used = false`;
- `voice_clone_used = false`;
- `network_download_performed_by_collector = false`;
- `audio_retained = false`.

If Piper/model/config is missing, the voice license is unclear, a network request is made by the TTS runtime/collector, the config is not the exact sibling, synthesis fails, or evidence has blockers, **STOP** and return the error/evidence instead of improvising.

## Completion rule

R11.5 cannot merge from hosted CI alone. After the required local JSON is returned and validated against the frozen implementation candidate, acceptance documentation/evidence will be finalized. That final documentation head must be re-gated with R0 + full Python Core + UI Smoke, and only then may the exact accepted PR head merge. A continuity-only normalization must then pass and merge before R11.6 is authorized.
