# R12.8 — Qt 6 / CMake desktop adapter

## Scope

R12.8 adds the frozen-roadmap Qt 6 adapter without creating a second project wizard, shell surface or package manager. It maps the R12.4 framework-neutral desktop model to a repository-owned Qt/CMake fixture, discovers an already provisioned Qt/CMake toolchain, records compiler/kit identity, builds through fixed argv under `ProcessSandbox`/KillSwitch, executes a bounded runtime probe and emits deterministic resource/project and artifact evidence.

Manual intervention is **CONDITIONAL / NOT TRIGGERED**. The authoritative Qt/compiler build/runtime seam required by acceptance was demonstrated by accepted hosted macOS CI. Failed CI bootstrap approaches were corrected without requesting user credentials or local execution.

## External compatibility baseline

R12.8 capability-probes supported Qt 6 rather than hard-coding one mutable version into architecture. The accepted implementation evidence used Qt **6.11.1** on hosted macOS ARM64 from Homebrew `qtbase`; exact discovered toolchain identity is recorded in acceptance evidence.

Upstream constraints used by the design:

- Qt 6 projects require C++17 or newer.
- the supported CMake floor is 3.22 on most current target platforms; Kodepoia freezes 3.22 for the fixture;
- Qt supports macOS 13+ including macOS 26 on x86_64 and arm64 with Xcode 15 or newer;
- Qt documents package managers on macOS/Linux as an account-free automation path for recent Qt versions;
- Homebrew `qtbase` currently provides Qt 6.11.1 bottles on Apple Silicon and contains the Core/Widgets scope used by this fixture;
- CMake may be pointed to an already installed Qt prefix; Kodepoia derives `Qt6_ROOT` only from validated `qtpaths`, never project/model raw flags.

CI provisioning is infrastructure outside Kodepoia runtime. Kodepoia itself does not install Qt, CMake, compilers, package managers or licenses.

## Contracts

### `QtProjectManifest`

Binds the shared logical-model SHA-256 to CMake minimum `3.22`, C++17, frozen components `Core` + `Widgets`, and sorted generated files with SHA-256 digests. The repository-owned fixture embeds the logical-model digest through Qt resources and validates it at runtime.

### `QtKitIdentity`

Durable toolchain evidence records actual Qt version, OS/architecture, allowlisted generator (`Visual Studio 17 2022` or `Ninja`), CMake version/hash, `qtpaths` hash, CMake-selected compiler name/ID/version/hash, exact components and explicit license state `REVIEW_REQUIRED`. Absolute runner paths are not durable identity.

### License / BOM semantics

`QtDependencyDeclaration` records `Qt6::Core` and `Qt6::Widgets` with the discovered exact version. `redistribution_rights_inferred` is permanently false. Presence of Qt never establishes redistribution rights; R6 License/BOM review remains authoritative.

## Secure execution boundaries

- `cmake`, `qtpaths` and the built repository-owned fixture are launched only via `ProcessSandbox` and KillSwitch.
- No shell command string is accepted by Kodepoia.
- `Qt6_ROOT` is derived only from `qtpaths --query QT_INSTALL_PREFIX` and validated against the discovered installation.
- generator/architecture are fixed by adapter policy; project/model text cannot provide `-G`, `-A`, `CMAKE_TOOLCHAIN_FILE`, compiler paths or arbitrary CMake cache arguments.
- `CMAKE_PREFIX_PATH`, `QTDIR`, `QT_PLUGIN_PATH`, `CC` and `CXX` remain rejected project/user environment overrides.
- source remains below repository root and build outputs below staging.
- CMake configure emits compiler metadata from repository-owned CMake logic; missing/tampered metadata fails closed.
- no `FetchContent`, Qt installer invocation or implicit dependency download exists in generated project logic.

## Canonical fixture and accepted CI route

The fixture uses Qt Core + Widgets, one C++17 executable and a `model.txt` resource. Runtime uses `QCoreApplication`, validates the public `QWidget` meta-object identity, reads the embedded model digest and emits a source-bound sentinel. It deliberately makes no interactive-window/rendering claim.

The accepted CI route is `macos-latest` (macOS 26 ARM64 at acceptance time). CI installs `qtbase`, CMake and Ninja through Homebrew, adds the discovered `qtbase/bin` to PATH, verifies a Qt 6 `qtpaths` executable, and then invokes Kodepoia. The accepted evidence reports Qt 6.11.1, CMake 4.4.0, Ninja and AppleClang 21 with executable SHA-256 identity.

Earlier Windows bootstrap experiments are explicitly non-authoritative: aqt mirror metadata failed before Kodepoia execution, while the official Qt Online Installer required Qt Account/license credentials. Since Qt's documented account-free package-manager route on a supported hosted platform passed the same build/runtime semantic, the R12.8 CONDITIONAL did not trigger.

## Rollback / failure states

Missing CMake or `qtpaths` => `UNAVAILABLE`. Too-old/incompatible Qt/CMake => `UNSUPPORTED`. Configure, kit identity, build or runtime failure => `FAILED`. No state is converted to PASS by unit tests. Failed work remains in staging and no generated project is promoted.
