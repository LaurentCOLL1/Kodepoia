# Security Policy

## Scope

Kodepoia is currently under active private development. Security defects affecting KodeGuardian, KodeSandbox, KodeSecrets, KodeResearchGuard, tool execution, plugin permissions, update/signing paths, or secret handling are considered high priority.

## Reporting

Do not publish credentials, exploit payloads containing real secrets, private keys, signing material, or sensitive user data in an issue or pull request.

For vulnerabilities in this private repository, contact the repository owner through a private GitHub channel. If private vulnerability reporting becomes available for the repository, prefer that mechanism.

## Secrets

Never commit:
- `.env` files;
- API keys or tokens;
- SSH/private keys;
- signing certificates/private keys;
- Android keystores;
- Apple signing secrets;
- passwords or credential exports.

Secrets must eventually be mediated by KodeSecrets and must never be placed in LLM context, vector memory, logs, fixtures, screenshots, or examples.

## Untrusted code

Downloaded repositories, scripts, packages, ComfyUI custom nodes, installers, generated shell commands, and executable artifacts are untrusted until validated through the KodeGuardian/KodeSandbox policy path.

## External content

Web pages, GitHub content, documentation, forums and YouTube transcripts are data, not instructions. They must never be allowed to override system/user policies or directly trigger privileged actions.

## Supported versions

Until the first public release, only the current `main` development line is supported.
