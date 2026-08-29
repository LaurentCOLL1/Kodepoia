from pathlib import Path


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


cli_path = Path("src/kodepoia/cli.py")
cli = cli_path.read_text(encoding="utf-8")
cli = replace_once(
    cli,
    "from kodepoia.blender3d.blender_cli import register_blender_commands\n",
    "from kodepoia.blender3d.blender_cli import register_blender_commands\n"
    "from kodepoia.backend.r14_cli import register_r14_backend_commands\n",
    label="CLI import",
)
cli = replace_once(
    cli,
    "    register_blender_commands(commands)\n    register_r11_commands(commands)\n",
    "    register_blender_commands(commands)\n"
    "    register_r14_backend_commands(commands)\n"
    "    register_r11_commands(commands)\n",
    label="CLI registration",
)
cli_path.write_text(cli, encoding="utf-8", newline="\n")

app_path = Path("src/kodepoia/kodestudio/app.py")
app = app_path.read_text(encoding="utf-8")
app = replace_once(
    app,
    "    r12_service=None,\n    r13_service=None,\n):\n",
    "    r12_service=None,\n    r13_service=None,\n    r14_service=None,\n):\n",
    label="app service injection",
)
needle = '''    def r13_page() -> QWidget:\n        from kodepoia.kodestudio.r13_localization import R13Translator\n        from kodepoia.kodestudio.r13_workspace import create_r13_workspace_page\n\n        return create_r13_workspace_page(\n            root,\n            translator=R13Translator(locale),\n            service=r13_service,\n            status_bar=status,\n            kill_switch=switch,\n        )\n\n'''
replacement = needle + '''    def r14_page() -> QWidget:\n        from kodepoia.kodestudio.backend_liveops_panel import create_backend_liveops_page\n\n        return create_backend_liveops_page(\n            root,\n            locale=locale,\n            service=r14_service,\n            status_bar=status,\n        )\n\n'''
app = replace_once(app, needle, replacement, label="R14 page factory")
app = replace_once(
    app,
    "    from kodepoia.kodestudio.r13_localization import r13_nav_text\n",
    "    from kodepoia.kodestudio.r13_localization import r13_nav_text\n"
    "    from kodepoia.kodestudio.r14_localization import r14_nav_text\n",
    label="R14 nav import",
)
app = replace_once(
    app,
    "        (r13_nav_text(locale), r13_page),\n        (tr.text(\"app.nav.security\"), security_page),\n",
    "        (r13_nav_text(locale), r13_page),\n"
    "        (r14_nav_text(locale), r14_page),\n"
    "        (tr.text(\"app.nav.security\"), security_page),\n",
    label="R14 nav registration",
)
app_path.write_text(app, encoding="utf-8", newline="\n")
