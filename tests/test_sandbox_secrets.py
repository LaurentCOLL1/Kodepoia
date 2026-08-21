import json
import sys
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox
from kodepoia.core.secrets import KodeSecrets, MemorySecretBackend


def test_process_sandbox_executes_allowlisted_python(tmp_path: Path) -> None:
    sandbox = ProcessSandbox(tmp_path, {Path(sys.executable).name})
    result = sandbox.run([sys.executable, "-c", "print('OK')"])
    assert result.returncode == 0
    assert result.stdout.strip() == "OK"


def test_process_sandbox_inherits_only_bounded_desktop_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("APPDATA", "C:/Users/Test/AppData/Roaming")
    monkeypatch.setenv("LOCALAPPDATA", "C:/Users/Test/AppData/Local")
    monkeypatch.setenv("USERPROFILE", "C:/Users/Test")
    monkeypatch.setenv("KODEPOIA_TEST_SECRET", "must-not-leak")
    sandbox = ProcessSandbox(tmp_path, {Path(sys.executable).name})
    code = (
        "import json, os; "
        "print(json.dumps({"
        "'APPDATA': os.environ.get('APPDATA'), "
        "'LOCALAPPDATA': os.environ.get('LOCALAPPDATA'), "
        "'USERPROFILE': os.environ.get('USERPROFILE'), "
        "'secret': os.environ.get('KODEPOIA_TEST_SECRET')}))"
    )
    result = sandbox.run([sys.executable, "-c", code])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["APPDATA"] == "C:/Users/Test/AppData/Roaming"
    assert payload["LOCALAPPDATA"] == "C:/Users/Test/AppData/Local"
    assert payload["USERPROFILE"] == "C:/Users/Test"
    assert payload["secret"] is None


def test_secrets_are_redacted() -> None:
    secrets = KodeSecrets(MemorySecretBackend())
    secrets.store("test", "token", "super-secret-token")
    assert secrets.redact("value=super-secret-token") == "value=***REDACTED***"
