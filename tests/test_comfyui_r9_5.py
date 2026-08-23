from __future__ import annotations

import copy
import json
import socket
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import pytest
from jsonschema import Draft202012Validator

from kodepoia.comfyui import (
    ComfyCapabilitySnapshot,
    ComfyCapabilityState,
    ComfyExecutionBudget,
    ComfyExecutionService,
    ComfyGovernanceError,
    ComfyModelInventory,
    ComfyProtocolError,
    ComfyRunState,
    ComfyRunStore,
    ComfySubmissionAmbiguousError,
    ComfySubmissionOutcome,
    ComfyUIClient,
    GovernedModelResolver,
    ModelRequirement,
    WorkflowDefinition,
    WorkflowInputSlot,
    WorkflowOutputSlot,
    WorkflowParameterKind,
    WorkflowParameterSpec,
    WorkflowValidator,
    canonical_sha256,
    normalize_node_inventory,
    parse_event_frame,
)

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_FIXTURE = ROOT / "tests" / "fixtures" / "comfyui" / "r9_3_inventory.json"
WORKFLOW_FIXTURE = ROOT / "tests" / "fixtures" / "comfyui" / "r9_4_workflow_spec.json"
EXECUTION_FIXTURE = ROOT / "tests" / "fixtures" / "comfyui" / "r9_5_execution.json"
RUN_PAYLOAD_SCHEMA = ROOT / "schemas" / "comfy-run-manifest-payload-v1.schema.json"


class _Scenario:
    def __init__(self, fixture: dict[str, Any]) -> None:
        self.fixture = fixture
        self.post_count = 0
        self.posts: list[dict[str, Any]] = []
        self.pending: dict[str, dict[str, Any]] = {}
        self.histories: dict[str, dict[str, Any]] = {}
        self.lose_response = False
        self.accept_lost_post = True
        self.auto_complete_before_queue = False
        self.history_mode = "valid"

    def history_for(self, prompt_id: str, *, outputs: dict[str, Any] | None = None) -> dict[str, Any]:
        record = self.pending.get(prompt_id)
        if record is None:
            record = next((item for item in self.posts if item.get("prompt_id") == prompt_id), None)
        if record is None:
            raise AssertionError("unknown prompt fixture")
        prompt = copy.deepcopy(record["prompt"])
        extra_data = copy.deepcopy(record.get("extra_data", {}))
        extra_data["client_id"] = record["client_id"]
        if self.history_mode == "bad_prompt":
            prompt["2"]["inputs"]["steps"] = 99
        if self.history_mode == "bad_correlation":
            extra_data["kodepoia"]["run_id"] = "run_ffffffffffffffffffffffffffffffff"
        return {
            "prompt": [7.0, prompt_id, prompt, extra_data, ["2"]],
            "status": copy.deepcopy(self.fixture["status"]["success"]),
            "outputs": copy.deepcopy(outputs if outputs is not None else {"2": self.fixture["output"]}),
        }


class _Handler(BaseHTTPRequestHandler):
    scenario: _Scenario

    def log_message(self, format: str, *args: object) -> None:
        del format, args

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/prompt":
            self._send(404, b"missing")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        document = json.loads(raw.decode("utf-8"))
        self.scenario.post_count += 1
        self.scenario.posts.append(copy.deepcopy(document))
        prompt_id = document["prompt_id"]
        if not self.scenario.lose_response or self.scenario.accept_lost_post:
            self.scenario.pending[prompt_id] = copy.deepcopy(document)
        if self.scenario.lose_response:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.connection.close()
            self.close_connection = True
            return
        response = copy.deepcopy(self.scenario.fixture["submission_response"])
        response["prompt_id"] = prompt_id
        self._json(response)

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path == "/queue":
            if self.scenario.auto_complete_before_queue:
                for prompt_id in list(self.scenario.pending):
                    self.scenario.histories[prompt_id] = self.scenario.history_for(prompt_id)
                    self.scenario.pending.pop(prompt_id, None)
                self.scenario.auto_complete_before_queue = False
            pending = [
                [7.0 + index, prompt_id]
                for index, prompt_id in enumerate(sorted(self.scenario.pending))
            ]
            self._json({"queue_running": [], "queue_pending": pending})
            return
        if path == "/prompt":
            self._json({"exec_info": {"queue_remaining": len(self.scenario.pending)}})
            return
        if path.startswith("/history/"):
            prompt_id = unquote(path.removeprefix("/history/"))
            history = self.scenario.histories.get(prompt_id)
            self._json({prompt_id: history} if history is not None else {})
            return
        if path == "/history":
            self._json(copy.deepcopy(self.scenario.histories))
            return
        self._send(404, b"missing")

    def _json(self, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self._send(200, body, content_type="application/json")

    def _send(self, status: int, body: bytes, *, content_type: str = "text/plain") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


@contextmanager
def _server(scenario: _Scenario):
    handler_type = type("R95Handler", (_Handler,), {"scenario": scenario})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_type)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _snapshot(fixture: dict[str, Any], endpoint: str) -> ComfyCapabilitySnapshot:
    nodes = normalize_node_inventory(fixture["object_info"])
    models: list[ComfyModelInventory] = []
    for model_type in sorted(fixture["models"]["types"]):
        tokens = tuple(sorted(fixture["models"][model_type]))
        models.append(
            ComfyModelInventory(
                model_type=model_type,
                tokens=tokens,
                digest_sha256=canonical_sha256({"model_type": model_type, "tokens": list(tokens)}),
            )
        )
    system_digest = canonical_sha256(fixture["system_stats"])
    feature_digest = canonical_sha256(fixture["features"])
    system = fixture["system_stats"]["system"]
    identity_payload = {
        "endpoint": endpoint,
        "comfyui_version": system["comfyui_version"],
        "python_version": system["python_version"],
        "system_digest_sha256": system_digest,
        "feature_digest_sha256": feature_digest,
        "nodes": [item.canonical() for item in nodes],
        "models": [item.canonical() for item in models],
        "unavailable": [],
    }
    return ComfyCapabilitySnapshot(
        state=ComfyCapabilityState.CURRENT,
        endpoint=endpoint,
        captured_at="2026-08-23T08:00:00Z",
        comfyui_version=system["comfyui_version"],
        python_version=system["python_version"],
        system_digest_sha256=system_digest,
        feature_digest_sha256=feature_digest,
        nodes=nodes,
        models=tuple(models),
        unavailable=(),
        identity_sha256=canonical_sha256(identity_payload),
    )


def _definition(spec: dict[str, Any]) -> WorkflowDefinition:
    return WorkflowDefinition.create(
        name=spec["name"],
        revision=spec["revision"],
        graph=spec["graph"],
        parameters=tuple(
            WorkflowParameterSpec(
                name=item["name"],
                node_id=item["node_id"],
                input_name=item["input_name"],
                kind=WorkflowParameterKind(item["kind"]),
                minimum=item["minimum"],
                maximum=item["maximum"],
                choices=tuple(item["choices"]),
            )
            for item in spec["parameters"]
        ),
        input_slots=tuple(
            WorkflowInputSlot(item["name"], item["node_id"], item["input_name"], item["type_token"])
            for item in spec["input_slots"]
        ),
        output_slots=tuple(
            WorkflowOutputSlot(item["name"], item["node_id"], item["output_index"], item["type_token"])
            for item in spec["output_slots"]
        ),
        model_requirements=tuple(
            ModelRequirement(
                requirement_id=item["requirement_id"],
                model_type=item["model_type"],
                node_id=item["node_id"],
                input_name=item["input_name"],
                accepted_tokens=tuple(item["accepted_tokens"]),
            )
            for item in spec["model_requirements"]
        ),
        allowed_node_classes=tuple(spec["allowed_node_classes"]),
    )


def _execution_objects(endpoint: str) -> tuple[ComfyCapabilitySnapshot, WorkflowDefinition, Any, Any]:
    inventory = json.loads(INVENTORY_FIXTURE.read_text(encoding="utf-8"))
    spec = json.loads(WORKFLOW_FIXTURE.read_text(encoding="utf-8"))
    snapshot = _snapshot(inventory, endpoint)
    definition = _definition(spec)
    resolutions = GovernedModelResolver().resolve(definition, snapshot)
    instance = WorkflowValidator().instantiate(
        definition,
        snapshot,
        resolutions,
        parameters={"seed": 42, "steps": 20},
    )
    return snapshot, definition, resolutions, instance


def test_prepare_manifest_contains_explicit_audit_evidence_and_strict_schema(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        manifest = ComfyExecutionService(ComfyUIClient(endpoint), ComfyRunStore(tmp_path)).prepare(
            definition, snapshot, resolutions, instance
        )
    assert manifest.state is ComfyRunState.PREPARED
    assert manifest.submission_outcome is ComfySubmissionOutcome.NOT_ATTEMPTED
    assert dict(manifest.parameter_values) == {"seed": 42, "steps": 20}
    assert dict(manifest.seed_values) == {"seed": 42}
    assert manifest.capability_endpoint == snapshot.endpoint
    assert manifest.model_resolution_evidence()["resolutions"][0]["selected_token"] == "base/model-a.safetensors"
    schema = json.loads(RUN_PAYLOAD_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(manifest.payload())


def test_normal_submit_and_dropped_websocket_resolve_by_polling_only(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        store = ComfyRunStore(tmp_path)
        service = ComfyExecutionService(ComfyUIClient(endpoint), store)
        prepared = service.prepare(definition, snapshot, resolutions, instance)
        queued = service.submit(prepared.run_id, definition, snapshot, resolutions, instance)
        assert queued.state is ComfyRunState.QUEUED
        assert queued.submission_attempts == 1
        assert scenario.post_count == 1
        scenario.auto_complete_before_queue = True
        completed = service.wait(
            prepared.run_id,
            instance,
            budget=ComfyExecutionBudget(max_poll_attempts=4, poll_interval_seconds=0.0),
        )
    assert completed.state is ComfyRunState.SUCCEEDED
    assert completed.progress_fraction == 1.0
    assert {item.node_id for item in completed.output_references} == {"2"}
    assert scenario.post_count == 1


def test_lost_post_response_recovers_from_queue_without_second_submission(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    scenario.lose_response = True
    scenario.accept_lost_post = True
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        store = ComfyRunStore(tmp_path)
        service = ComfyExecutionService(ComfyUIClient(endpoint), store)
        prepared = service.prepare(definition, snapshot, resolutions, instance)
        recovered = service.submit(
            prepared.run_id,
            definition,
            snapshot,
            resolutions,
            instance,
            budget=ComfyExecutionBudget(ambiguous_reconcile_attempts=2, ambiguous_reconcile_interval_seconds=0.0),
        )
        assert recovered.state is ComfyRunState.QUEUED
        assert recovered.submission_outcome is ComfySubmissionOutcome.RECOVERED
        assert recovered.submission_attempts == 1
        assert scenario.post_count == 1
        again = service.submit(prepared.run_id, definition, snapshot, resolutions, instance)
        assert again.manifest_digest_sha256 == recovered.manifest_digest_sha256
        assert scenario.post_count == 1


def test_invisible_ambiguous_post_never_resubmits_even_on_second_submit_call(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    scenario.lose_response = True
    scenario.accept_lost_post = False
    budget = ComfyExecutionBudget(ambiguous_reconcile_attempts=2, ambiguous_reconcile_interval_seconds=0.0)
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        store = ComfyRunStore(tmp_path)
        service = ComfyExecutionService(ComfyUIClient(endpoint), store)
        prepared = service.prepare(definition, snapshot, resolutions, instance)
        with pytest.raises(ComfySubmissionAmbiguousError, match="resubmission is forbidden"):
            service.submit(prepared.run_id, definition, snapshot, resolutions, instance, budget=budget)
        after_first = store.load(prepared.run_id)
        assert after_first.submission_outcome is ComfySubmissionOutcome.AMBIGUOUS
        assert after_first.submission_attempts == 1
        assert scenario.post_count == 1
        with pytest.raises(ComfySubmissionAmbiguousError, match="resubmission is forbidden"):
            service.submit(prepared.run_id, definition, snapshot, resolutions, instance, budget=budget)
        assert scenario.post_count == 1


def test_websocket_progress_is_monotonic_but_success_event_is_not_terminal_authority(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        store = ComfyRunStore(tmp_path)
        service = ComfyExecutionService(ComfyUIClient(endpoint), store)
        prepared = service.prepare(definition, snapshot, resolutions, instance)
        queued = service.submit(prepared.run_id, definition, snapshot, resolutions, instance)
        high = parse_event_frame(
            json.dumps({"type": "progress", "data": {"prompt_id": queued.prompt_id, "node": "2", "value": 3, "max": 4}}),
            max_bytes=4096,
        )
        low = parse_event_frame(
            json.dumps({"type": "progress", "data": {"prompt_id": queued.prompt_id, "node": "2", "value": 2, "max": 4}}),
            max_bytes=4096,
        )
        success_hint = parse_event_frame(
            json.dumps({"type": "execution_success", "data": {"prompt_id": queued.prompt_id}}),
            max_bytes=4096,
        )
        current = service.observe_event(queued.run_id, high)
        current = service.observe_event(queued.run_id, low)
        current = service.observe_event(queued.run_id, success_hint)
    assert current.state is ComfyRunState.RUNNING
    assert current.progress_fraction == 0.75


@pytest.mark.parametrize("mode", ["bad_prompt", "bad_correlation"])
def test_mismatched_terminal_history_fails_closed(tmp_path: Path, mode: str) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    scenario.history_mode = mode
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        store = ComfyRunStore(tmp_path)
        service = ComfyExecutionService(ComfyUIClient(endpoint), store)
        prepared = service.prepare(definition, snapshot, resolutions, instance)
        queued = service.submit(prepared.run_id, definition, snapshot, resolutions, instance)
        scenario.histories[queued.prompt_id] = scenario.history_for(queued.prompt_id)
        scenario.pending.pop(queued.prompt_id, None)
        with pytest.raises(ComfyProtocolError, match="digest|correlation"):
            service.reconcile_once(queued.run_id, instance)


def test_success_without_required_output_reference_fails_closed(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        store = ComfyRunStore(tmp_path)
        service = ComfyExecutionService(ComfyUIClient(endpoint), store)
        prepared = service.prepare(definition, snapshot, resolutions, instance, required_output_node_ids=("2",))
        queued = service.submit(prepared.run_id, definition, snapshot, resolutions, instance)
        scenario.histories[queued.prompt_id] = scenario.history_for(queued.prompt_id, outputs={})
        scenario.pending.pop(queued.prompt_id, None)
        with pytest.raises(ComfyProtocolError, match="missing required output"):
            service.reconcile_once(queued.run_id, instance)


def test_append_only_revision_chain_and_current_pointer_recovery(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        store = ComfyRunStore(tmp_path)
        service = ComfyExecutionService(ComfyUIClient(endpoint), store)
        prepared = service.prepare(definition, snapshot, resolutions, instance)
        service.submit(prepared.run_id, definition, snapshot, resolutions, instance)
        revisions = store.revisions(prepared.run_id)
        assert revisions[0].revision == 0
        assert revisions[-1].revision >= 2
        for previous, current in zip(revisions, revisions[1:], strict=True):
            assert current.revision == previous.revision + 1
            assert current.previous_manifest_digest_sha256 == previous.manifest_digest_sha256
        latest = revisions[-1]
        current_path = tmp_path / f"{prepared.run_id}.json"
        current_path.write_text("{}", encoding="utf-8")
        with pytest.raises(ComfyProtocolError):
            store.load(prepared.run_id)
        recovered = store.recover(prepared.run_id)
        assert recovered.manifest_digest_sha256 == latest.manifest_digest_sha256
        assert store.load(prepared.run_id).manifest_digest_sha256 == latest.manifest_digest_sha256


def test_manifest_tamper_is_rejected_and_revision_history_remains_recoverable(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects(endpoint)
        store = ComfyRunStore(tmp_path)
        service = ComfyExecutionService(ComfyUIClient(endpoint), store)
        prepared = service.prepare(definition, snapshot, resolutions, instance)
        current_path = tmp_path / f"{prepared.run_id}.json"
        document = json.loads(current_path.read_text(encoding="utf-8"))
        document["payload"]["seed_values"]["seed"] = 43
        current_path.write_text(json.dumps(document), encoding="utf-8")
        with pytest.raises(ComfyProtocolError, match="digest"):
            store.load(prepared.run_id)
        recovered = store.recover(prepared.run_id)
        assert dict(recovered.seed_values) == {"seed": 42}


def test_execution_rejects_snapshot_for_different_comfyui_origin(tmp_path: Path) -> None:
    fixture = json.loads(EXECUTION_FIXTURE.read_text(encoding="utf-8"))
    scenario = _Scenario(fixture)
    with _server(scenario) as endpoint:
        snapshot, definition, resolutions, instance = _execution_objects("http://127.0.0.1:8188")
        service = ComfyExecutionService(ComfyUIClient(endpoint), ComfyRunStore(tmp_path))
        with pytest.raises(ComfyGovernanceError, match="endpoint|origin"):
            service.prepare(definition, snapshot, resolutions, instance)
