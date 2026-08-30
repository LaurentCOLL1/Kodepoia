from __future__ import annotations

import importlib.metadata
import json
import platform
import random
import sys
from pathlib import Path
from typing import Any

_PACKAGE_NAMES = ("accelerate", "bitsandbytes", "peft", "safetensors", "torch", "transformers", "trl")


def _version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _read_payload(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("worker config must be an object")
    allowed = {
        "action",
        "backend",
        "dtype",
        "model_ref",
        "model_revision",
        "quantization",
        "seeds",
        "tokenizer_ref",
    }
    if set(data) - allowed:
        raise ValueError("worker config has unsupported fields")
    return data


def _base_result() -> dict[str, object]:
    return {
        "backend": "unknown",
        "backend_capability": "unknown",
        "device": None,
        "dtype_supported": None,
        "four_bit_supported": None,
        "model_load": None,
        "packages": {name: _version(name) for name in _PACKAGE_NAMES},
        "python_version": platform.python_version(),
        "seed_applied": False,
        "torch_backend_version": None,
        "vram_free_bytes": None,
        "vram_total_bytes": None,
    }


def _torch_probe(data: dict[str, Any], result: dict[str, object]) -> tuple[Any, Any] | None:
    try:
        import torch
    except Exception:
        result["backend_capability"] = "unsupported"
        return None

    seed = int(dict(data.get("seeds") or {}).get("seed", 3407))
    random.seed(seed)
    torch.manual_seed(seed)
    requested = str(data.get("backend", "cpu"))
    hip = getattr(torch.version, "hip", None)
    cuda = getattr(torch.version, "cuda", None)
    result["torch_backend_version"] = str(hip or cuda or "cpu")

    if requested == "cpu":
        device = torch.device("cpu")
        backend_type = "cpu"
        name = platform.machine() or "cpu"
    elif requested in {"cuda", "rocm"}:
        if not torch.cuda.is_available():
            result["backend"] = requested
            result["backend_capability"] = "unsupported"
            return None
        if requested == "rocm" and not hip:
            result["backend"] = requested
            result["backend_capability"] = "unsupported"
            return None
        if requested == "cuda" and hip:
            result["backend"] = requested
            result["backend_capability"] = "unsupported"
            return None
        device = torch.device("cuda:0")
        backend_type = "rocm" if hip else "cuda"
        if backend_type != requested:
            result["backend"] = backend_type
            result["backend_capability"] = "unsupported"
            return None
        props = torch.cuda.get_device_properties(0)
        name = str(getattr(props, "name", backend_type))[:256]
        try:
            free_bytes, total_bytes = torch.cuda.mem_get_info(0)
            result["vram_free_bytes"] = int(free_bytes)
            result["vram_total_bytes"] = int(total_bytes)
        except Exception:
            result["vram_free_bytes"] = None
            result["vram_total_bytes"] = None
        torch.cuda.manual_seed_all(seed)
    else:
        result["backend_capability"] = "unsupported"
        return None

    result["backend"] = backend_type
    result["device"] = {"backend_type": backend_type, "index": 0, "name": name}
    result["seed_applied"] = True
    try:
        probe = torch.ones((2, 2), dtype=torch.float32, device=device)
        _ = (probe @ probe).sum().item()
    except Exception:
        result["backend_capability"] = "unsupported"
        return None
    result["backend_capability"] = "supported"

    dtype_name = str(data.get("dtype", "float32"))
    dtype = {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
    }.get(dtype_name)
    if dtype is None:
        result["dtype_supported"] = False
    else:
        try:
            typed = torch.ones((2, 2), dtype=dtype, device=device)
            _ = (typed @ typed).sum().item()
            result["dtype_supported"] = True
        except Exception:
            result["dtype_supported"] = False

    quantization = str(data.get("quantization", "none"))
    if quantization == "none":
        result["four_bit_supported"] = None
    elif quantization == "bnb_nf4":
        try:
            import bitsandbytes as bnb

            layer = bnb.nn.Linear4bit(
                4,
                4,
                bias=False,
                compute_dtype=dtype or torch.float32,
                compress_statistics=True,
                quant_type="nf4",
            ).to(device)
            sample = torch.ones((1, 4), dtype=dtype or torch.float32, device=device)
            _ = layer(sample)
            result["four_bit_supported"] = True
        except Exception:
            result["four_bit_supported"] = False
    else:
        result["four_bit_supported"] = False
    return torch, device


def _model_load(
    data: dict[str, Any],
    result: dict[str, object],
    torch_device: tuple[Any, Any] | None,
) -> None:
    if torch_device is None:
        result["model_load"] = "unsupported"
        return
    model_ref = data.get("model_ref")
    if not isinstance(model_ref, str) or not model_ref:
        result["model_load"] = "unsupported"
        return
    tokenizer_ref = data.get("tokenizer_ref") or model_ref
    revision = data.get("model_revision")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_ref,
            revision=revision,
            local_files_only=True,
            trust_remote_code=False,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_ref,
            revision=revision,
            local_files_only=True,
            trust_remote_code=False,
            low_cpu_mem_usage=True,
        )
        _ = tokenizer.eos_token_id
        _ = int(model.num_parameters())
        del model
        del tokenizer
        result["model_load"] = "supported"
    except Exception:
        result["model_load"] = "unsupported"


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    try:
        data = _read_payload(Path(sys.argv[1]))
        result = _base_result()
        torch_device = _torch_probe(data, result)
        if data.get("action") == "model_load":
            _model_load(data, result, torch_device)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
