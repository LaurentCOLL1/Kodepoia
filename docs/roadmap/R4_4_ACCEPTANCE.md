# R4.4 — DAP acceptance contract

Protocol basis: Debug Adapter Protocol 1.71.x over the shared Content-Length framed JSON transport introduced in R4.3.

Security requirements:
- debug adapters are explicitly pre-registered;
- launch/attach configurations are pre-registered by `config_id`; model tool calls cannot submit arbitrary adapter argv or launch arguments;
- adapters launch only through `ProcessSandbox.spawn_piped()` and remain bound to the global kill switch;
- adapter->client execution requests such as `runInTerminal` are rejected in the R4.4 baseline;
- breakpoint source paths are workspace-confined.

Functional acceptance:
- initialize capability negotiation;
- launch or attach from a pre-registered configuration;
- setBreakpoints and configurationDone;
- threads -> stackTrace -> scopes -> variables waterfall;
- event capture and disconnect;
- structured Tool API hides argv/config arguments.

R4.4 is accepted only when Repository Guard, Python Core Ubuntu+Windows, and KodeStudio UI Smoke all succeed on the exact final PR head.
