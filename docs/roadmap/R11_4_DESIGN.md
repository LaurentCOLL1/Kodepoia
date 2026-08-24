# R11.4 — Voice Profiles, pronunciation/prosody and rights governance

## Scope

R11.4 introduces engine-neutral character/role voice intent before any real TTS synthesis exists.

Delivered contracts:
- `VoiceProfile`: stable profile/scope IDs, primary locale, ordered fallbacks and bounded prosody intent;
- `PronunciationLexicon`: locale-aware grapheme → pronunciation entries with deterministic identity;
- `VoiceModelBinding`: backend/model/config identity kept separate from character voice intent;
- `RightsDeclaration`: provenance, license, explicit allowed-use set, optional authorization reference and `RIGHTS_BLOCKED` fail-closed state;
- `SpeechSegment`: typed `text` / `pause` / `emphasis` markup only; raw XML/SSML-like payloads are rejected.

## Locale and Unicode policy

Locale identifiers use a bounded BCP-47-shaped structural form. Kodepoia canonical storage uses hyphen separators with language lower-case, script title-case, region upper-case and other accepted subtags lower-case. This v1 policy deliberately does not perform network/IANA-registry lookups or silently rewrite deprecated subtags.

User-facing voice text is normalized to Unicode NFC so canonically equivalent text receives the same stored representation. C0/C1 controls and bidi formatting/override/isolate controls are rejected from voice text used by the voice pipeline. Pronunciation lookup uses NFC plus Unicode case-folding while retaining the original normalized display grapheme.

## Governance boundaries

- A `VoiceProfile` does not contain a filesystem path, biometric speaker identity or model bytes.
- A model binding requires model/config SHA-256 plus explicit provenance and license IDs.
- A use is authorized only when the rights state is `AVAILABLE` and that use is explicitly allowlisted.
- `requires_authorization=true` fails closed without an `authorization_ref`.
- Unknown/restricted rights can be represented as `RIGHTS_BLOCKED` and cannot be promoted for synthesis.
- No voice cloning, training, biometric verification, age/gender inference or reference-recording ingestion surface is added.
- Reference/media bytes remain governed by R8; future external execution remains governed by R11.1 `ProcessSandbox` boundaries.

## Security properties

Arbitrary SSML/XML is not passed through. The future R11.5 adapter must compile typed segments and bounded prosody into a backend-specific request; model-provided raw engine flags remain forbidden. Bidi controls and non-finite prosody values fail closed. Canonical digests use the R11 canonical JSON serializer.

## External baseline note

Piper-compatible bindings are only identifiers at R11.4. No Piper runtime or model is downloaded or executed. Per-voice/model licensing remains authoritative and must be recorded in `RightsDeclaration`; repository-level licensing must never be assumed to grant identical rights for each voice model/dataset.
