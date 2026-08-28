from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match in {path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


app = Path("src/kodepoia/kodestudio/app.py")
replace_once(
    app,
    "            from kodepoia.kodestudio.r13_project_wizard import create_project_dialog\n",
    "            from kodepoia.kodestudio.r14_project_wizard import create_project_dialog\n",
    "KodeStudio R14 wizard wiring",
)

for relative, online, multiplayer in (
    ("tests/fixtures/r14_2/offline_project.yaml", "no", "no"),
    ("tests/fixtures/r14_2/online_project.yaml", "yes", "yes"),
    ("tests/fixtures/r14_2/contradictory_billing.yaml", "no", "no"),
):
    path = Path(relative)
    replace_once(path, f"online: {online}\n", f'online: "{online}"\n', f"{relative} online")
    replace_once(
        path,
        f"multiplayer: {multiplayer}\n",
        f'multiplayer: "{multiplayer}"\n',
        f"{relative} multiplayer",
    )

print("R14.2 final wiring/fixture patch applied")
