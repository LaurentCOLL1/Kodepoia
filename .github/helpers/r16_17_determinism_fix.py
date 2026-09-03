from __future__ import annotations

import json
from pathlib import Path

DOWNLOAD_ACTION_SHA = "634f93cb2916e3fdff6788551b99b062d0335ce0"

policy_path = Path("configs/r16_supply_chain_policy.json")
policy = json.loads(policy_path.read_text(encoding="utf-8"))
pins = policy["external_action_pins"]
if "actions/download-artifact" in pins:
    raise SystemExit("download-artifact pin already exists unexpectedly")
pins["actions/download-artifact"] = {
    "source_ref": "v5",
    "commit_sha": DOWNLOAD_ACTION_SHA,
}
policy["pin_resolution_date"] = "2026-09-03"
policy_path.write_text(
    json.dumps(policy, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

test_path = Path("tests/test_supply_chain_r16_9.py")
test_text = test_path.read_text(encoding="utf-8")
old = '    assert len(policy.pins) == 7\n    assert len(policy.digest_sha256) == 64\n'
new = (
    '    assert len(policy.pins) == 8\n'
    '    assert policy.pins["actions/download-artifact"].commit_sha == (\n'
    f'        "{DOWNLOAD_ACTION_SHA}"\n'
    '    )\n'
    '    assert len(policy.digest_sha256) == 64\n'
)
if test_text.count(old) != 1:
    raise SystemExit("supply-chain pin-count test anchor drifted")
test_path.write_text(test_text.replace(old, new), encoding="utf-8")

workflow_path = Path(".github/workflows/r16-17-release-readiness-acceptance.yml")
workflow = workflow_path.read_text(encoding="utf-8")
checkout_anchor = "    steps:\n      - name: Checkout exact evidence source\n"
checkout_replacement = (
    "    steps:\n"
    "      - name: Canonicalize checkout line endings\n"
    "        shell: python\n"
    "        run: |\n"
    "          import subprocess\n"
    "          subprocess.run([\"git\", \"config\", \"--global\", \"core.autocrlf\", \"false\"], check=True)\n"
    "          subprocess.run([\"git\", \"config\", \"--global\", \"core.eol\", \"lf\"], check=True)\n"
    "\n"
    "      - name: Checkout exact evidence source\n"
)
if workflow.count(checkout_anchor) != 1:
    raise SystemExit("R16.17 checkout anchor drifted")
workflow = workflow.replace(checkout_anchor, checkout_replacement)

aggregate = f'''

  cross-platform-package-determinism:
    needs: release-readiness
    runs-on: ubuntu-latest
    env:
      EVIDENCE_SHA: ${{{{ github.event.pull_request.head.sha || github.sha }}}}
    steps:
      - name: Download exact-head RC evidence
        uses: actions/download-artifact@{DOWNLOAD_ACTION_SHA}
        with:
          pattern: r16-17-release-readiness-*-${{{{ env.EVIDENCE_SHA }}}}
          path: downloaded

      - name: Assert Linux and Windows package bytes are identical
        shell: python
        run: |
          import json
          from pathlib import Path

          manifests = sorted(Path("downloaded").glob("*/artifacts/r16_17_baseline_build.json"))
          if len(manifests) != 2:
              raise SystemExit(f"expected two cross-platform package manifests, got {{manifests}}")
          payloads = []
          platforms = set()
          for path in manifests:
              artifact_name = path.parents[1].name
              if "-Linux-" in artifact_name:
                  platforms.add("Linux")
              if "-Windows-" in artifact_name:
                  platforms.add("Windows")
              payload = json.loads(path.read_text(encoding="utf-8"))
              artifacts = payload.get("artifacts")
              if not isinstance(artifacts, dict) or len(artifacts) != 2:
                  raise SystemExit(f"invalid package hash manifest: {{path}}")
              payloads.append(dict(sorted(artifacts.items())))
          if platforms != {{"Linux", "Windows"}}:
              raise SystemExit(f"missing expected platform evidence: {{platforms}}")
          if payloads[0] != payloads[1]:
              raise SystemExit(
                  "cross-platform package bytes differ: "
                  + json.dumps(payloads, sort_keys=True)
              )
          print(json.dumps({{"cross_platform_identical": True, "artifacts": payloads[0]}}, sort_keys=True))
'''
if "cross-platform-package-determinism:" in workflow:
    raise SystemExit("aggregate determinism job already exists unexpectedly")
workflow_path.write_text(workflow.rstrip() + aggregate.rstrip() + "\n", encoding="utf-8")

expected = {
    ".github/workflows/r16-17-release-readiness-acceptance.yml",
    "configs/r16_supply_chain_policy.json",
    "tests/test_supply_chain_r16_9.py",
}
for path in expected:
    if not Path(path).exists():
        raise SystemExit(f"expected patched path missing: {path}")
