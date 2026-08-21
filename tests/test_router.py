from kodepoia.models.router import KodeModelRouter, ModelRegistry, ModelRole, ModelSpec, TaskProfile


def registry() -> ModelRegistry:
    return ModelRegistry([ModelSpec("fast", ModelRole.FAST, 3000), ModelSpec("core", ModelRole.CORE, 7000, supports_vision=True, supports_tools=True), ModelSpec("coder", ModelRole.CODER, 10000, supports_tools=True), ModelSpec("embed", ModelRole.EMBED, 1000)])


def test_router_selects_coder_for_complex_task() -> None:
    assert KodeModelRouter(registry()).route(TaskProfile(code_complexity=0.9)).name == "coder"


def test_router_selects_embed() -> None:
    assert KodeModelRouter(registry()).route(TaskProfile(needs_embeddings=True)).name == "embed"


def test_router_uses_vision_capable_model() -> None:
    assert KodeModelRouter(registry()).route(TaskProfile(visual_requirement=0.8)).name == "core"
