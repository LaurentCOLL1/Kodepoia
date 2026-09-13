# Updater Authenticode policy

Windows updater Authenticode acceptance is a property of the exact target authorized by verified TUF Targets metadata.

The only recognized custom key is `authenticode_policy`.

- If the key is absent, the effective policy is `require-valid`.
- `authenticode_policy: "require-valid"` accepts only PowerShell Authenticode status `Valid`.
- `authenticode_policy: "allow-unsigned"` additionally accepts status `NotSigned` for that exact TUF-authorized target.
- Any other value, type, spelling, alias, or malformed declaration fails closed.
- `signing_status` is informational only and never grants permission to accept an unsigned installer.
- A broken or untrusted signature status is never accepted by `allow-unsigned`.

This policy does not replace TUF authorization. Exact target length and SHA-256, withdrawal state, and installer identity/version verification remain mandatory. The policy is evaluated only after the downloaded bytes satisfy the TUF-authorized length and SHA-256 checks.

Both packaged PowerShell verifier paths use fixed PowerShell code and `-LiteralPath`. The staged installer path is supplied only as process data through `KODEPOIA_UPDATER_LITERAL_PATH`; it is never concatenated into `-Command` text. This includes the staging form `.KodepoiaSetup.exe.partial` and ordinary Windows parent directories containing spaces.

The already-published rc6 metadata has no `authenticode_policy` key and therefore remains `require-valid`. It must not be reinterpreted from its historical `signing_status` text or mutated in place. A future target that intentionally authorizes an unsigned installer must explicitly carry `authenticode_policy: "allow-unsigned"` in its signed TUF target metadata.
