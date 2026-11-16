"""Tiny helpers for conditions and string templating over a context dict."""
from __future__ import annotations
import re
from typing import Any

_PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_.]+)\}")


def get_path(ctx: dict, path: str, default: Any = None) -> Any:
    cur: Any = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def render(template: str, ctx: dict) -> str:
    """Replace {a.b} with ctx values. Missing paths render as empty strings."""
    def sub(m: re.Match) -> str:
        val = get_path(ctx, m.group(1))
        return "" if val is None else str(val)
    return _PLACEHOLDER.sub(sub, template)


_OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: _num(a) > _num(b),
    "lt": lambda a, b: _num(a) < _num(b),
    "gte": lambda a, b: _num(a) >= _num(b),
    "lte": lambda a, b: _num(a) <= _num(b),
    "contains": lambda a, b: b in a if a is not None else False,
    "exists": lambda a, b: a is not None,
}


def _num(x: Any) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def evaluate(cond: dict, ctx: dict) -> bool:
    op = cond.get("op", "eq")
    if op not in _OPS:
        raise ValueError(f"unknown operator: {op}")
    left = get_path(ctx, cond["field"])
    return bool(_OPS[op](left, cond.get("value")))
