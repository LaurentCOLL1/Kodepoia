from kodepoia.desktop.tauri2 import Tauri2Adapter


def test_tauri_rust_tool_version_parser_accepts_tool_prefix() -> None:
    assert Tauri2Adapter._version_tuple("rustc 1.97.1 (8bab26f4f 2026-07-14)") == (1, 97, 1)
    assert Tauri2Adapter._version_tuple("cargo 1.97.1 (c980f4866 2026-06-30)") == (1, 97, 1)
    assert Tauri2Adapter._version_tuple("not-a-version") == (0, 0, 0)
