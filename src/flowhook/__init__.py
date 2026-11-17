"""flowhook - a small webhook-driven automation engine."""
from .engine import Flow, FlowResult, run_flow
from .registry import FlowRegistry

__all__ = ["Flow", "FlowRegistry", "FlowResult", "run_flow"]
__version__ = "1.0.0"
