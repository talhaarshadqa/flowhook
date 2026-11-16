"""The flow engine: run an ordered list of steps over an event payload."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

from .expr import evaluate, get_path, render

# A sender turns an http step into an outbound call. Injectable for tests.
Sender = Callable[[str, str, dict, Any], dict]


def _default_sender(method: str, url: str, headers: dict, body: Any) -> dict:  # pragma: no cover
    import json
    import urllib.request

    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return {"status": resp.status, "body": resp.read().decode(errors="replace")[:2000]}


@dataclass
class Flow:
    name: str
    steps: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Flow":
        if "name" not in data:
            raise ValueError("flow needs a name")
        return cls(name=data["name"], steps=list(data.get("steps", [])))


@dataclass
class FlowResult:
    status: str                 # "completed" | "filtered" | "error"
    context: dict
    actions: list[dict]
    error: str | None = None


def run_flow(flow: Flow, event: dict, *, sender: Sender | None = None) -> FlowResult:
    sender = sender or _default_sender
    ctx: dict[str, Any] = {"event": dict(event), **dict(event)}
    actions: list[dict] = []

    for i, step in enumerate(flow.steps):
        kind = step.get("type")
        try:
            if kind == "set":
                for k, v in step.get("fields", {}).items():
                    ctx[k] = render(v, ctx) if isinstance(v, str) else v
                actions.append({"step": i, "type": "set"})

            elif kind == "filter":
                if not evaluate(step["condition"], ctx):
                    actions.append({"step": i, "type": "filter", "passed": False})
                    return FlowResult("filtered", ctx, actions)
                actions.append({"step": i, "type": "filter", "passed": True})

            elif kind == "log":
                actions.append({"step": i, "type": "log", "message": render(step.get("message", ""), ctx)})

            elif kind == "http":
                body = step.get("body")
                if isinstance(body, dict):
                    body = {k: (render(v, ctx) if isinstance(v, str) else v) for k, v in body.items()}
                headers = {k: render(v, ctx) for k, v in step.get("headers", {}).items()}
                resp = sender(step.get("method", "POST"), render(step["url"], ctx), headers, body)
                if step.get("save_as"):
                    ctx[step["save_as"]] = resp
                actions.append({"step": i, "type": "http", "response": resp})

            else:
                raise ValueError(f"unknown step type: {kind!r}")
        except Exception as exc:  # noqa: BLE001 - surface step errors in the result
            return FlowResult("error", ctx, actions, error=f"step {i}: {exc}")

    return FlowResult("completed", ctx, actions)
