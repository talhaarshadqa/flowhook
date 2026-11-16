import pytest
from flowhook.engine import Flow, run_flow
from flowhook.expr import render, evaluate, get_path
from flowhook.registry import FlowRegistry


def test_render_and_paths():
    ctx = {"user": {"name": "Sam"}, "amount": 42}
    assert render("Hi {user.name}, total {amount}", ctx) == "Hi Sam, total 42"
    assert render("{missing}", ctx) == ""
    assert get_path(ctx, "user.name") == "Sam"


@pytest.mark.parametrize("op,val,field,expected", [
    ("eq", "paid", "status", True),
    ("ne", "paid", "status", False),
    ("gt", 10, "amount", True),
    ("lt", 10, "amount", False),
    ("contains", "oo", "note", True),
    ("exists", None, "status", True),
    ("exists", None, "nope", False),
])
def test_evaluate(op, val, field, expected):
    ctx = {"status": "paid", "amount": 42, "note": "food"}
    assert evaluate({"field": field, "op": op, "value": val}, ctx) is expected


def test_set_and_log():
    flow = Flow("f", [
        {"type": "set", "fields": {"greeting": "Hello {name}"}},
        {"type": "log", "message": "sent: {greeting}"},
    ])
    r = run_flow(flow, {"name": "Ada"})
    assert r.status == "completed"
    assert r.context["greeting"] == "Hello Ada"
    assert r.actions[-1]["message"] == "sent: Hello Ada"


def test_filter_stops_flow():
    flow = Flow("f", [
        {"type": "filter", "condition": {"field": "amount", "op": "gt", "value": 100}},
        {"type": "log", "message": "big order"},
    ])
    assert run_flow(flow, {"amount": 50}).status == "filtered"
    done = run_flow(flow, {"amount": 150})
    assert done.status == "completed" and len(done.actions) == 2


def test_http_step_uses_sender():
    calls = []
    def fake(method, url, headers, body):
        calls.append((method, url, body))
        return {"status": 200, "body": "ok"}
    flow = Flow("notify", [
        {"type": "http", "method": "POST", "url": "https://hooks.test/{channel}",
         "body": {"text": "New signup: {email}"}, "save_as": "resp"},
    ])
    r = run_flow(flow, {"channel": "alerts", "email": "a@b.com"}, sender=fake)
    assert r.status == "completed"
    assert calls == [("POST", "https://hooks.test/alerts", {"text": "New signup: a@b.com"})]
    assert r.context["resp"]["status"] == 200


def test_unknown_step_is_error():
    r = run_flow(Flow("f", [{"type": "bogus"}]), {})
    assert r.status == "error" and "unknown step" in r.error


def test_registry():
    reg = FlowRegistry()
    reg.register({"name": "a", "steps": []})
    reg.register({"name": "b", "steps": [{"type": "log", "message": "x"}]})
    assert reg.names() == ["a", "b"]
    assert reg.get("b").steps
    assert reg.delete("a") is True
    assert reg.delete("a") is False
    with pytest.raises(ValueError):
        reg.register({"steps": []})
