# ADR-0001 — Python 3.12 Protected Core and optional PySide6 KodeStudio

- Status: Accepted
- Date: 2026-08-21
- Scope: implementation choice; no change to frozen Architecture v1.0

## Context

R1 must deliver the Protected Core before the AI model and before tool integrations. The implementation must run locally on Windows, be easy to test headlessly, integrate naturally with future AI/automation tooling, and keep the desktop shell replaceable.

## Decision

- Implement the R1 Protected Core in Python >= 3.12.
- Prefer the Python standard library in the security boundary.
- Package runtime code under `src/kodepoia`.
- Implement KodeStudio with PySide6/Qt as an **optional** dependency.
- Pin the R1 UI dependency to PySide6 6.11.1.
- Keep imports of Qt out of the core so Kodepoia's security tests run without any GUI dependency.

## Consequences

- Fast iteration and excellent compatibility with future local-AI tooling.
- Protected Core remains testable on Windows and Linux without a desktop session.
- Qt licensing/provenance must be tracked by KodeLicense before distribution.
- KodeStudio can later evolve or be replaced without changing the Protected Core APIs.

## Rollback

The core contracts are Python interfaces/dataclasses and can be wrapped by another host language later. The UI is optional and can be replaced independently.
