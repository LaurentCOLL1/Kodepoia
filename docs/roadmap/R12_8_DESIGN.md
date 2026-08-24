# R12.8 — Qt 6 / CMake desktop adapter

## Scope

R12.8 adds the frozen-roadmap Qt 6 adapter without creating a second project wizard, shell surface or package manager. It maps the R12.4 framework-neutral desktop model to a repository-owned Qt/CMake fixture, discovers an already provisioned Qt/CMake toolchain, records compiler/kit identity, builds through fixed argv under `ProcessSandbox`/KillSwitch, executes a bounded runtime probe and emits deterministic resource/project and artifact evidence.

Manual intervention is **CONDITIONAL**. It is triggered only if the authoritative Qt/compiler build/runtime seam required by this acceptance cannot be demonstrated by the accepted hosted CI environment. Missing or broken Kodepoia fixture logic is corrected in-branch and is not a manual trigger.

## External compatibility baseline

The R12.8 acceptance fixture is pinned to Qt **6.11.2** on hosted Windows with the Qt MSVC 2022 x64 kit. This pin is acceptance evidence, not permanent architecture. The adapter accepts supported Qt 6 toolchains at or above the frozen fixture minimum of Qt 6.5 and capability-probes the actual discovered version.

Upstream constraints used by the design:

- Qt 6 projects require C++17 or newer.
- Qt's current CMake guidance requires projects to declare at least CMake 3.16, while the actual supported CMake version is 3.22 on most target platforms; Kodepoia therefore freezes 3.22 for this acceptance fixture.
- Qt is made available to user projects through a preinstalled/equivalent prepared Qt installation discoverable by CMake; Qt `FetchContent` is not a supported Qt delivery mechanism.
- The Qt 6.11 Windows support line includes Windows x86_64 with MSVC 2022.
- CMake command-line builds may use explicit `CMAKE_PREFIX_PATH`/`Qt6_ROOT`; Kodepoia uses only the internally discovered `QT_INSTALL_PREFIX`, never project/model raw flags.

CI may provision the exact Qt SDK as infrastructure before Kodepoia runs. Kodepoia runtime itself does not install Qt, CMake, Visual Studio workloads, compiler kits or licenses.

## Contracts

### `QtProjectManifest`

Binds the shared logical-model SHA-256 to:

- CMake minimum `3.22`;
- C++ standard `17`;
- frozen components `Core` + `Widgets`;
- sorted generated files and SHA-256 digests.

The repository-owned fixture embeds the logical-model digest through Qt's resource system and validates it at runtime.

### `QtKitIdentity`

Durable toolchain evidence records:

- actual Qt version;
- OS/architecture;
- allowlisted generator (`Visual Studio 17 2022` or `Ninja`);
- CMake version and executable digest;
- `qtpaths` executable digest;
- CMake-selected compiler name, compiler ID/version and executable digest;
- exact Qt components;
- explicit license state `REVIEW_REQUIRED`.

Absolute runner paths are not durable identity. Compiler identity is captured only after fixed CMake configure because CMake is authoritative for the selected compiler.

### License / BOM semantics

`QtDependencyDeclaration` records `Qt6::Core` and `Qt6::Widgets` with the discovered exact version. `redistribution_rights_inferred` is permanently false and any attempt to set it true fails closed. Presence of a local Qt installation does not establish redistribution rights; R6 License/BOM review remains authoritative.

## Secure execution boundaries

- `cmake`, `qtpaths` and the built repository-owned fixture are launched only via `ProcessSandbox` and the global KillSwitch.
- No shell command string is accepted or executed.
- `Qt6_ROOT` is derived only from `qtpaths --query QT_INSTALL_PREFIX` and validated against the discovered `qtpaths` location.
- The generator and architecture are fixed by adapter policy; project/model text cannot provide `-G`, `-A`, `CMAKE_TOOLCHAIN_FILE`, compiler paths or other CMake cache arguments.
- `CMAKE_PREFIX_PATH`, `QTDIR`, `QT_PLUGIN_PATH`, `CC` and `CXX` remain rejected user/project environment overrides.
- Source paths remain under the repository root; build outputs remain under staging.
- CMake configure emits compiler metadata from Kodepoia-owned CMake logic; missing/tampered metadata fails closed.
- No `FetchContent`, package-manager invocation or implicit network restore is present in the generated project.

## Canonical fixture

The fixture uses `Qt6::Core` and `Qt6::Widgets`, compiles one C++17 executable and embeds `model.txt` with `qt_add_resources`. The runtime probe uses `QCoreApplication`, links the Widgets module, verifies the public `QWidget` meta-object identity, reads the embedded model digest and emits a source-bound sentinel with the runtime Qt version. It deliberately makes no interactive-window/rendering claim.

Hosted Windows CI provisions Qt 6.11.2 MSVC 2022 x64 as **CI infrastructure** using pinned `aqtinstall==3.3.0`, then Kodepoia independently discovers and validates the toolchain. The real build uses the Visual Studio 17 2022 CMake generator and the CMake-selected compiler identity is hashed into evidence.

## Rollback / failure states

Missing CMake or `qtpaths` => `UNAVAILABLE`. Too-old/incompatible Qt/CMake => `UNSUPPORTED`. Configure, kit identity, build or runtime failure => `FAILED`. No state is converted to PASS by unit tests. Failed work remains in staging and no generated project is promoted.
