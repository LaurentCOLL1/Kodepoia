# R9.5 — Execution engine, queue/progress/reconciliation + run manifests

## Scope

R9.5 executes only a `WorkflowInstance` already accepted by R9.4 against the exact R9.3 capability/model evidence used to instantiate it. It adds prompt submission, queue/progress/history reconciliation and durable run evidence. It does **not** promote outputs to the R8 Vault, delete queue entries, interrupt running work, release memory, schedule VRAM, install nodes/models, or expose a generic HTTP surface.

## Submission identity and duplicate protection

Each prepared run receives independent Kodepoia-owned `run_id`, `prompt_id` and `client_id` values before any network side effect. The `PREPARED` manifest is persisted first. Immediately before `POST /prompt`, R9.5 appends an `ATTEMPTING` manifest revision with `submission_attempts=1`.

A logical run permits exactly one POST attempt. `ComfySubmissionOutcome` distinguishes `NOT_ATTEMPTED`, `ATTEMPTING`, `ACCEPTED`, `AMBIGUOUS` and `RECOVERED`.

If a connection is lost while the POST may have reached ComfyUI, the manifest becomes `AMBIGUOUS`. Only fixed idempotent queue/history reads are then allowed. Presence of the exact prompt ID recovers the run; absence after the bounded reconciliation budget remains an explicit ambiguity and raises `ComfySubmissionAmbiguousError`. R9.5 never sends a second POST for that logical run, including after process restart or a repeated `submit()` call.

This policy relies on current ComfyUI accepting a caller-supplied `prompt_id` and retaining that ID in queue/history. The upstream behavior is compatibility evidence, not a relaxation of Kodepoia's trust boundary.

## Terminal authority

WebSocket events are live telemetry only. Active prompt events may advance the local observation from `PREPARED`/`QUEUED` toward `RUNNING` and progress fractions are monotonically accumulated with `max(previous, current)`. `execution_success`, `execution_error` and interruption WebSocket messages never by themselves create a terminal run manifest.

Each polling reconciliation reads queue plus the prompt-specific history. Contradictory evidence (simultaneously running and pending, or terminal history while still active in queue) fails closed. History is accepted only when:

- its prompt ID equals the persisted prompt ID;
- the exact stored prompt digest equals the prepared workflow-instance prompt digest;
- Kodepoia correlation metadata contains the persisted run ID, workflow definition ID and instance digest;
- a successful terminal history contains every explicitly required output node reference.

Only then may the run become `SUCCEEDED`. Failed/cancelled history remains explicit terminal evidence and cannot be rewritten as success.

## Durable run evidence

`ComfyRunManifest` contains explicit audit evidence rather than only opaque references:

- workflow definition ID/digest;
- capability snapshot identity, endpoint, ComfyUI version and Python version;
- canonical model-resolution evidence plus digest;
- workflow-instance and concrete prompt digests;
- typed parameter/input values and explicit seed values;
- submission outcome/attempt evidence and response digest when available;
- queue/history evidence digests;
- monotonic progress;
- required-output IDs and reconciled output references.

The frozen R9.1 root `comfy-run-manifest-v1` envelope is unchanged. R9.5 adds `schemas/comfy-run-manifest-payload-v1.schema.json` for the strict payload contract.

## Append-only recovery

`ComfyRunStore` keeps a mutable atomic current pointer for fast reads plus immutable revisions under `.revisions/<run_id>/`. Every mutation increments `revision` and binds `previous_manifest_digest_sha256`; revision files are create-once and digest-named. The full chain can be revalidated and can rebuild a missing/corrupt current pointer without erasing prior evidence.

Symlink escapes, revision gaps, wrong previous digests, conflicting immutable revision bytes, noncanonical model evidence and manifest-digest tampering fail closed.

## Operation budgets and cancellation

Polling and ambiguous-reconciliation loops have explicit attempt/time/interval budgets. A cancellation token before submission can cancel the local prepared run without a network side effect. Once submitted, R9.5 cancellation stops local waiting only; remote queue deletion/interruption is intentionally deferred to R9.7.

## Security/governance invariants

- No arbitrary URL/path/method surface is exported.
- POST redirects are rejected rather than followed.
- Raw model-generated graphs remain forbidden; only R9.4 instances are accepted.
- Capability/model/instance evidence is recomputed before submission.
- No output bytes are promoted and no external files are scanned in R9.5.
- No model/custom-node download or process control is introduced.

## Conditional manual gate

The R9 plan marks R9.5 `CONDITIONAL`. It is triggered only if an execution/recovery behavior required above cannot be established from deterministic loopback fixtures plus the current upstream ComfyUI contract. The candidate test suite explicitly exercises lost-response acceptance, invisible ambiguous submission, queue/history recovery, dropped WebSocket polling, prompt/correlation tampering, missing required output references, manifest recovery and duplicate prevention.
