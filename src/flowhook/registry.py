"""In-memory registry of named flows (load from dicts, JSON or YAML)."""
from __future__ import annotations

import json
from pathlib import Path

from .engine import Flow


class FlowRegistry:
    def __init__(self) -> None:
        self._flows: dict[str, Flow] = {}

    def register(self, data: dict) -> Flow:
        flow = Flow.from_dict(data)
        self._flows[flow.name] = flow
        return flow

    def get(self, name: str) -> Flow | None:
        return self._flows.get(name)

    def delete(self, name: str) -> bool:
        return self._flows.pop(name, None) is not None

    def names(self) -> list[str]:
        return sorted(self._flows)

    def load_file(self, path: str | Path) -> Flow:
        text = Path(path).read_text()
        try:
            import yaml  # optional
            data = yaml.safe_load(text)
        except ModuleNotFoundError:
            data = json.loads(text)
        return self.register(data)

    def __len__(self) -> int:
        return len(self._flows)
