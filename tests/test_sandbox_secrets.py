import sys
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend


def test_process_sandbox_executes_allowlisted_python(tmp_path: Path) -> None:
    sandbox = ProcessSandbox(tmp_path, {Path(sys.executable).name})
    result = sandbox.run([sys.executable, "-c", "print('OK')"])
    assert result.returncode == 0
    assert result.stdout.strip() == "OK"


def test_secrets_are_redacted() -> None:
    secrets = KodeSecrets(MemorySecretBackend())
    secrets.store("test", "token", "super-secret-token")
    assert secrets.redact("value=super-secret-token") == "value=***REDACTED***"
