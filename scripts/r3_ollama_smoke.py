from __future__ import annotations

import argparse
import json

from kodepoia.brain.base import BrainMessage
from kodepoia.brain.ollama import OllamaClient


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--url", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    client = OllamaClient(args.url)
    response = client.chat(args.model, [BrainMessage("user", "Reply with exactly: KODEPOIA_OK")])
    print(json.dumps({"version": client.version(), "model": response.model, "content": response.content, "metrics": response.metrics}, indent=2))
    return 0 if "KODEPOIA_OK" in response.content else 1


if __name__ == "__main__":
    raise SystemExit(main())
