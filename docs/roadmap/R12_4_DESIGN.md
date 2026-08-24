# R12.4 — Framework-neutral MVVM/state/navigation/command/service contracts

## Status

Implementation candidate. Manual intervention: **NONE**.

## Frozen scope

R12.4 defines the logical application model shared by every later desktop adapter. It does not emit WPF XAML, WinUI XAML, Avalonia AXAML, Qt UI/C++, Tauri frontend/Rust, or invoke any framework toolchain.

## Contract model

`DesktopAppModel` schema v1 contains only durable logical primitives:

- typed observable state fields;
- typed validation rules;
- services with explicit lifetime, dependencies and disposal ownership;
- commands with bounded operation identifiers, optional service target and boolean can-execute state;
- view-model references to state/commands/services;
- view-to-view-model binding intent;
- navigation routes with parent relationships;
- typed dialogs.

No concrete framework object, class name, runtime handle, executable path or generated source is serialized.

## Determinism

Canonical JSON sorts every logical collection by stable ID and sorts reference lists. Semantically identical models therefore have identical canonical bytes and SHA-256 even when construction order differs.

`canonical_sample_app()` is the one deterministic logical fixture consumed by R12.5–R12.9.

## Validation / fail-closed rules

- all logical identifiers and command operations use bounded grammars;
- IDs and route paths are unique;
- all state/service/command/view-model/view/route/dialog references must resolve;
- command can-execute state must be boolean;
- route path must be local logical navigation only and route-parent cycles are rejected;
- service dependency cycles are rejected;
- longer-lived services may not capture shorter-lived dependencies;
- validation-rule arguments must match their state type.

## Lifecycle/disposal

The service graph produces deterministic dependent-before-dependency disposal ordering for services marked disposable. This is a logical lifecycle contract only; concrete async/thread/IPC/database disposal is mapped later by R12.10–R12.12 and framework adapters.

## Adapter conformance

`AdapterConformanceProjection` binds a concrete `DesktopFramework` to the same logical model digest and stable state/command/route/service signature. Tests require all five frozen R12 adapters to receive an equivalent logical signature. Concrete adapters may add framework-specific build metadata later but cannot silently mutate logical app behavior.

## Security boundary

- no raw script or arbitrary command string;
- no executable/template/process/network surface;
- no framework object serialization;
- graph cycles and dangling references fail before adapter generation;
- deterministic sample fixture prevents adapter-specific acceptance drift.

## Rollback

R12.4 is additive contract code/schema/tests only. No project files are generated or mutated by this subdivision, so repository rollback is the normal Git revert/branch abandonment path.
