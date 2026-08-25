# R12.9 — Tauri v2 / Rust / WebView2 desktop adapter

## Scope

R12.9 adds the frozen-roadmap Tauri v2 adapter without introducing a JavaScript package manager, server-rendered frontend, installer policy or second desktop project model. It maps the shared R12.4 logical model to a repository-owned static Tauri fixture, discovers an already provisioned Rust MSVC toolchain, consumes a CI-preloaded Cargo lock/cache, builds through fixed `cargo --locked --offline` argv under `ProcessSandbox`/KillSwitch, initializes a real Windows Tauri WebView and records the installed WebView2 version.

Manual intervention is **CONDITIONAL**. It is triggered only if accepted hosted Windows CI cannot demonstrate the required Rust/MSVC/Tauri/WebView2 build/runtime seam. Source, fixture, dependency-lock or adapter failures are corrected in-branch and are not manual triggers.

## External compatibility baseline

The R12.9 acceptance fixture pins Tauri crate **2.11.5** and `tauri-build` **2.6.3**. Tauri's Windows prerequisites require Microsoft C++ Build Tools, Microsoft Edge WebView2 and a Rust MSVC toolchain. The accepted workflow uses a hosted Windows 2022 runner and explicitly selects `stable-msvc`.

The fixture uses a plain static frontend; Node, npm, pnpm, yarn and a development server are intentionally absent. Tauri's documented static-host model accepts an embedded `frontendDist` directory.

MSI packaging is out of R12.9 scope. Therefore the Windows VBSCRIPT optional feature is not a prerequisite here; installer/signing behavior belongs to R12.14.

## Security model

Tauri v2 capabilities are treated as an explicit trust boundary. The canonical fixture declares an empty capability set, disables `withGlobalTauri`, loads no plugins and exposes no custom Tauri commands. A frontend without a matching capability has no IPC access to native commands. The application uses a restrictive CSP with no network connection target.

No remote URL, `devUrl`, `beforeBuildCommand`, shell plugin, filesystem plugin, opener plugin or arbitrary external binary is generated.

## Dependency / network boundary

The workflow may prepare Cargo registry/cache state as CI infrastructure **before** governed acceptance:

1. Kodepoia renders deterministic source/config files.
2. CI generates `Cargo.lock` and fetches its exact dependency graph.
3. Kodepoia validates the lock contains exact `tauri 2.11.5` and `tauri-build 2.6.3` entries.
4. The authoritative build executes only `cargo build --locked --offline` through the R12 desktop boundary.

Kodepoia runtime itself does not run `cargo install`, `cargo update`, `rustup`, package-manager commands or network dependency resolution.

## Contracts

### `TauriProjectManifest`

Binds the common logical-model SHA-256 to:

- exact Tauri and tauri-build versions;
- empty frontend IPC permissions;
- no bundle/installer target;
- sorted generated source/config/static files and SHA-256 digests.

### `TauriKitIdentity`

Durable evidence records:

- Windows x64 platform;
- Cargo and rustc versions plus executable SHA-256;
- exact Rust host triple, which must end in `pc-windows-msvc`;
- Tauri runtime version;
- real WebView2 runtime version returned by `tauri::webview_version()`;
- Cargo.lock SHA-256;
- capability/CSP/bundle policy SHA-256.

### License / BOM semantics

`TauriDependencyDeclaration` records `tauri` and `tauri-build` with exact versions and explicit `REVIEW_REQUIRED` state. Local availability or successful compilation never infers redistribution rights; R6 license/BOM policy remains authoritative.

## Canonical runtime fixture

The fixture creates one invisible `main` WebView window backed by embedded static HTML. During Tauri setup it verifies that the configured `main` WebView exists, obtains the system WebView version using Tauri's public `webview_version()` API, emits a source-bound sentinel containing logical-model SHA + Tauri version + WebView version, and requests a bounded clean exit.

The proof is runtime initialization, not a claim of interactive UI correctness. Accessibility/localization/DPI behavior remains R12.13 and packaging/signing remains R12.14.

## Failure states

Missing Cargo/rustc => `UNAVAILABLE`. Non-Windows/non-x64/non-MSVC host or too-old Rust => `UNSUPPORTED`. Missing/tampered lock, offline build failure, missing executable, missing main WebView, missing WebView2 version or runtime failure => `FAILED`. Unit tests never manufacture an adapter PASS.
