"""FastAPI layer: register flows and trigger them via webhooks."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from . import __version__
from .engine import run_flow
from .registry import FlowRegistry


class FlowSpec(BaseModel):
    name: str = Field(min_length=1)
    steps: list[dict] = Field(default_factory=list)


def create_app(registry: FlowRegistry | None = None, sender: Any = None) -> FastAPI:
    registry = registry or FlowRegistry()
    app = FastAPI(title="flowhook", version=__version__,
                  description="Webhook-driven automation flows.")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "flows": registry.names()}

    @app.put("/flows")
    def upsert(spec: FlowSpec) -> dict:
        flow = registry.register(spec.model_dump())
        return {"name": flow.name, "steps": len(flow.steps)}

    @app.get("/flows")
    def list_flows() -> dict:
        return {"names": registry.names()}

    @app.delete("/flows/{name}", status_code=204)
    def delete(name: str) -> None:
        if not registry.delete(name):
            raise HTTPException(404, "flow not found")

    @app.post("/hooks/{name}")
    async def trigger(name: str, request: Request) -> dict:
        flow = registry.get(name)
        if flow is None:
            raise HTTPException(404, "flow not found")
        try:
            event = await request.json()
        except ValueError:
            event = {}
        result = run_flow(flow, event if isinstance(event, dict) else {"body": event}, sender=sender)
        return {"status": result.status, "actions": result.actions, "error": result.error}

    return app


app = create_app()
