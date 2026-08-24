# R11.8 — Cinematic shots, sequences + deterministic timeline model

## Scope

R11.8 creates a portable, deterministic cinematic representation before any Godot movie capture. It owns shot/sequence structure, rational frame time, allowlisted track/event semantics, deterministic branch conditions, reference validation, budgets and canonical identities.

It does **not** execute Godot, generate arbitrary scripts, replace an NLE or mutate R8 assets.

## Time model

Canonical timing is integer frame count plus rational FPS numerator/denominator. Seconds are derived with exact `Fraction` arithmetic and are never the durable timing identity. This avoids cumulative float drift and supports integer rates plus rates such as 24000/1001.

## Shot model

A `ShotDefinition` contains:

- stable shot id;
- one bounded `Timebase`;
- duration in frames;
- digest-bound `CinematicRef` identities;
- globally monotonic `TimelineEvent` records.

Track kinds are allowlisted: camera, body, facial, dialogue, music, SFX, Foley, subtitle and declarative event. Payload keys are allowlisted per track and payload values are bounded primitives only. Raw code/script/command/path surfaces are not accepted.

## Sequence model

A `SequenceTimeline` references immutable shot identities/digests through `SequenceEntry`. Validation reports missing refs, digest/timebase/duration mismatch, gaps, overlaps, nested-sequence cycles and frame/count budget violations.

## Branches

`BranchCondition` evaluates one explicit context key using an allowlisted scalar comparison operator. Callers must provide only the requested context key. No expression language, Python, GDScript or arbitrary predicate callback exists.

## Identity and schemas

Shot, sequence and validation reports use canonical JSON/SHA-256 identity under R11 serialization rules. Versioned schemas live under `schemas/r11/`.

## Manual checkpoint

R11.8 manual intervention is **NONE**. Every accepted semantic is reproducible in hosted CI with synthetic identities and deterministic inputs.
