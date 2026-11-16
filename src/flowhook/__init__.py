"""flowhook - a small webhook-driven automation engine."""
from .engine import Flow, run_flow, FlowResult
from .registry import FlowRegistry

__all__ = ["Flow", "run_flow", "FlowResult", "FlowRegistry"]
__version__ = "1.0.0"
