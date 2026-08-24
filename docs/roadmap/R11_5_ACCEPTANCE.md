# R11.5 — Acceptance

Status: **REVISED HOSTED ACCEPTED — MANUAL REQUIRED / NOT MERGEABLE YET**

Manual intervention: **REQUIRED**.

## Candidate history

### Candidate 1 — hosted accepted, local rejected

- Exact implementation SHA: `441ea87436c6851cd106654454f955a91460f7af`.
- R0 Repository Guard #1359 / run `32734530111`: **SUCCESS**.
- Python Core #1333 / run `32734530102`: **SUCCESS**.
  - Ubuntu Python: **961 passed / 8 skipped / 46 warnings**.
  - Ubuntu integrated R7/R8/R9: **PASS**.
  - Windows Python, Ubuntu/Windows package builds and internal KodeStudio smoke: **SUCCESS**.
- KodeStudio UI Smoke #1300 / run `32734530119`: **SUCCESS**.

Real local evidence on candidate 1 returned **FAIL** and remains immutable rejected evidence:

- Piper capability probe: PASS;
- synthesis process: return code 0, no timeout/cancel, no stdout/stderr payload;
- privacy: no private recording, no voice clone, no collector download, no retained audio;
- WAV: mono PCM, 22,050 Hz, 4.829750566893424 s, 106,496 frames;
- QA: BLOCKED only because `clipped_samples = 1` while the original generic R11.2 profile required zero.

This result is **not** retrospectively reclassified as PASS. Candidate 1 is superseded by candidate 2 below.

### Candidate 2 — current frozen implementation candidate

- Base normalized `main`: `354a0ec2f6889561afcee3b1f547e0b77ca3804b`.
- Branch: `r11/5-local-tts-adapters`.
- PR: #165.
- Exact implementation candidate SHA: `a9862b3bf475b259fe154d1e2486116ad04602f3`.

Hosted exact-head evidence on candidate 2:

- R0 Repository Guard #1394 / run `32740559995`: **SUCCESS**.
- Python Core #1368 / run `32740559969`: **SUCCESS**.
  - Ubuntu Python: **970 passed / 8 skipped / 46 warnings**.
  - Ubuntu integrated R7/R8/R9: **PASS**.
  - Windows Python: **SUCCESS**.
  - Ubuntu + Windows package builds: **SUCCESS**.
  - internal KodeStudio UI smoke: **SUCCESS**.
- KodeStudio UI Smoke #1335 / run `32740559942`: **SUCCESS**.

The hosted gate is therefore satisfied for exact candidate `a9862b3bf475b259fe154d1e2486116ad04602f3`.

## Revision introduced after candidate 1

Candidate 2 keeps all original R11.5 boundaries and additionally:

- establishes `<repo>/models/` as Kodepoia's canonical physical local model catalog;
- keeps large model payloads local/ignored by Git while tracking manifests, SHA-256 identities, license/provenance and category documentation;
- adds `KodeModelRegistry` beside the existing logical `ModelRegistry` router rather than replacing it;
- resolves the acceptance voice by stable model id `tts.piper.fr-FR.siwis-medium`;
- binds evidence to the tracked model manifest digest as well as model/config SHA-256;
- leaves the generic R11.2 `max_clipped_samples=0` policy unchanged;
- uses a dedicated `tts.local.v2` QA profile allowing only an isolated full-scale endpoint rate of at most 10 ppm, with an absolute cap of 16 samples; counts above the bound remain BLOCKED.

## Hosted acceptance requirements — satisfied for candidate 2

- focused R11.5 TTS/backend/cache tests PASS;
- repository-local model catalog/path/SHA/schema tests PASS;
- isolated TTS endpoint tolerance and repeated-clipping rejection tests PASS;
- backend registry returns `UNAVAILABLE` for absent adapters rather than failing the phase;
- Godot/system TTS remains accessibility/runtime-only and non-canonical for production assets;
- Piper capability probe is bounded and requires fixed CLI markers;
- synthesis text is supplied only via an ephemeral staging `--input-file`, never directly in argv;
- exact `<model>.onnx.json` sibling/config identity is SHA-bound to the tracked model manifest and R11.4 binding;
- no network/model download/cloud/voice-cloning/training/arbitrary-engine-flag surface exists in the collector;
- timeout/cancel/non-zero/stale-output/malformed-WAV cases fail closed;
- output passes the dedicated bounded TTS QA profile before accepted manifest status;
- cache records resolve only for exact request/runtime/model/config identities and reference R8 revision identity rather than owning physical bytes;
- synthesis manifest/cache/model-catalog/local-evidence JSON schemas validate;
- full Python Core PASS Ubuntu/Windows;
- R0 Repository Guard PASS;
- KodeStudio UI Smoke PASS.

## Required real local acceptance — candidate 2

The required real-runtime evidence MUST bind to:

`a9862b3bf475b259fe154d1e2486116ad04602f3`

The accepted catalog voice is:

- model id: `tts.piper.fr-FR.siwis-medium`;
- repository-local payload directory: `models/tts/piper/fr-FR/siwis-medium/`;
- locale: `fr-FR`;
- single speaker;
- sample rate: 22,050 Hz;
- license id recorded in tracked manifest: `cc-by-4.0`;
- provenance id: `piper.fr-fr.siwis.medium`;
- expected model SHA-256: `641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99`;
- expected config SHA-256: `39479916c2db192b5ac9764daddd0c744d83e023ad890c6976c0633ae4df8959`.

The operator must still personally review the selected voice/model card/license and only use the approval string if accepted.

### Phase A — preserve the rejected candidate-1 evidence and switch to candidate 2

Run from the Kodepoia repository root:

```powershell
$ErrorActionPreference = "Stop"
$Candidate = "a9862b3bf475b259fe154d1e2486116ad04602f3"
$RejectedEvidence = ".\R11_5_LOCAL_ACCEPTANCE.local.json"

if (Test-Path -LiteralPath $RejectedEvidence -PathType Leaf) {
    $RejectedArchive = Join-Path $env:TEMP "R11_5_LOCAL_ACCEPTANCE.rejected-441ea874.json"
    Move-Item -LiteralPath $RejectedEvidence -Destination $RejectedArchive -Force
    Write-Host "Archived rejected candidate-1 evidence: $RejectedArchive"
}

if (git status --porcelain) {
    throw "Kodepoia working tree is not clean. STOP and report git status --short."
}

git fetch origin r11/5-local-tts-adapters
if ((git cat-file -t $Candidate).Trim() -ne "commit") {
    throw "Frozen R11.5 candidate 2 is unavailable locally. STOP."
}
git switch --detach $Candidate
if ((git rev-parse HEAD).Trim() -ne $Candidate) {
    throw "HEAD does not equal frozen R11.5 candidate 2. STOP."
}
```

### Phase B — copy the already-downloaded voice into Kodepoia/models

Piper may remain in its dedicated `%LOCALAPPDATA%` runtime venv. Only the model payload moves into Kodepoia's local model catalog.

```powershell
$PiperRoot = Join-Path $env:LOCALAPPDATA "Kodepoia\Piper\runtime-1.6.0"
$Piper = Join-Path $PiperRoot ".venv\Scripts\piper.exe"
$OldVoiceDir = Join-Path $env:LOCALAPPDATA "Kodepoia\Piper\voices"
$OldModel = Join-Path $OldVoiceDir "fr_FR-siwis-medium.onnx"
$OldConfig = "$OldModel.json"

$CatalogVoiceDir = Join-Path (Get-Location) "models\tts\piper\fr-FR\siwis-medium"
$Model = Join-Path $CatalogVoiceDir "fr_FR-siwis-medium.onnx"
$Config = "$Model.json"

if (-not (Test-Path -LiteralPath $Piper -PathType Leaf)) { throw "Dedicated piper.exe is missing. STOP." }
if (-not (Test-Path -LiteralPath $OldModel -PathType Leaf)) { throw "Previously downloaded ONNX model is missing. STOP." }
if (-not (Test-Path -LiteralPath $OldConfig -PathType Leaf)) { throw "Previously downloaded ONNX config is missing. STOP." }

New-Item -ItemType Directory -Force -Path $CatalogVoiceDir | Out-Null
Copy-Item -LiteralPath $OldModel -Destination $Model -Force
Copy-Item -LiteralPath $OldConfig -Destination $Config -Force

$ModelHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Model).Hash.ToLowerInvariant()
$ConfigHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Config).Hash.ToLowerInvariant()

if ($ModelHash -ne "641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99") {
    throw "Repository-local model SHA-256 mismatch. STOP."
}
if ($ConfigHash -ne "39479916c2db192b5ac9764daddd0c744d83e023ad890c6976c0633ae4df8959") {
    throw "Repository-local config SHA-256 mismatch. STOP."
}

Get-Item -LiteralPath $Piper, $Model, $Config | Select-Object FullName, Length
if (git status --porcelain) {
    throw "Model payloads unexpectedly changed the Git working tree. STOP and report git status --short."
}
```

The `.onnx` and `.onnx.json` payloads are intentionally ignored by Git under `models/`; the tracked `manifest.json` remains the authority for their hashes/license/provenance.

### Phase C — execute the offline collector on exact candidate 2

Do not run this block until you have personally reviewed the selected voice/model card/license and agree with the approval statement.

```powershell
$Evidence = Join-Path $env:TEMP "R11_5_LOCAL_ACCEPTANCE.a9862b3.json"

python .\scripts\r11_5_accept_local.py `
  --source-sha $Candidate `
  --piper $Piper `
  --model-id tts.piper.fr-FR.siwis-medium `
  --repo-root . `
  --approval I_REVIEWED_AND_APPROVE_THIS_VOICE_LICENSE `
  --output $Evidence

if ($LASTEXITCODE -ne 0) {
    Write-Host "Collector evidence path: $Evidence"
    throw "R11.5 candidate-2 collector failed. STOP and return the console error plus JSON if created."
}

Get-Content -LiteralPath $Evidence -Raw
```

The collector performs no download. It synthesizes only neutral repository-owned acceptance text, uses temporary staging, removes temporary text/WAV and emits privacy-minimized JSON evidence outside the Git worktree.

## Expected PASS evidence

Return the generated candidate-2 JSON (or its full JSON text), not the voice model, WAV, private paths or unrelated logs.

Expected values:

- `schema = kodepoia.r11_5_local_acceptance`;
- `source_sha = a9862b3bf475b259fe154d1e2486116ad04602f3`;
- `status = pass` and `blockers = []`;
- `voice_identity.model_id = tts.piper.fr-FR.siwis-medium`;
- `voice_identity.model_sha256 = 641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99`;
- `voice_identity.config_sha256 = 39479916c2db192b5ac9764daddd0c744d83e023ad890c6976c0633ae4df8959`;
- `voice_identity.manifest_digest` is present and SHA-256 shaped;
- capability status PASS;
- synthesis status PASS;
- `synthesis.qa.profile_id = tts.local.v2`;
- `synthesis.qa.state = PASS`;
- duration greater than 0.05 seconds;
- runtime/model/config/input/output identities are SHA-bound;
- `synthesis.process.text_passed_via_argv = false`;
- `synthesis.process.ephemeral_input_deleted = true`;
- `private_recording_used = false`;
- `voice_clone_used = false`;
- `network_download_performed_by_collector = false`;
- `audio_retained = false`.

If Piper/model/config is missing, the tracked model manifest/hash is inconsistent, the voice license is unclear, a network request is made by the TTS runtime/collector, synthesis fails, or evidence has blockers, **STOP** and return the error/evidence instead of improvising.

## Completion rule

R11.5 cannot merge from hosted CI alone. After the required candidate-2 local JSON is returned and validated against the frozen candidate, acceptance documentation/evidence will be finalized. That final documentation head must be re-gated with R0 + full Python Core + UI Smoke, and only then may the exact accepted PR head merge. A continuity-only normalization must then pass and merge before R11.6 is authorized.
