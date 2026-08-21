# R4.3 — LSP design notes

Implementation basis: Language Server Protocol 3.18 and JSON-RPC 2.0 over `Content-Length` framed byte streams.

Security rules:
- language servers are registered by an explicit `LanguageServerSpec`; agents never provide arbitrary executable/argv;
- server processes launch through `ProcessSandbox.spawn_piped`, inheriting executable allowlisting, workspace cwd confinement and the global kill switch;
- no network transport is introduced in R4.3;
- file URIs are produced only from workspace-confined paths;
- protocol reads are timeout-bounded and message/header sizes are bounded.

Baseline lifecycle/features:
- `initialize` -> `initialized` -> requests -> `shutdown` -> `exit`;
- document symbols;
- definitions;
- references;
- `publishDiagnostics` capture;
- deterministic fake-server acceptance tests on Windows and Ubuntu.

R4 remains IN PROGRESS after R4.3; DAP, graphs and final orchestration/acceptance remain pending.
