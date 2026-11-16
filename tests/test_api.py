import pytest
pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from flowhook.api import create_app
from flowhook.registry import FlowRegistry


@pytest.fixture
def client():
    sent = []
    app = create_app(FlowRegistry(), sender=lambda m, u, h, b: (sent.append((m, u, b)) or {"status": 200}))
    c = TestClient(app)
    c.sent = sent
    return c


def test_register_and_trigger(client):
    spec = {"name": "signup", "steps": [
        {"type": "filter", "condition": {"field": "plan", "op": "eq", "value": "pro"}},
        {"type": "http", "method": "POST", "url": "https://hooks.test/x", "body": {"t": "{email}"}},
    ]}
    assert client.put("/flows", json=spec).json()["steps"] == 2
    assert client.get("/flows").json()["names"] == ["signup"]

    free = client.post("/hooks/signup", json={"plan": "free", "email": "a@b.com"}).json()
    assert free["status"] == "filtered" and not client.sent

    pro = client.post("/hooks/signup", json={"plan": "pro", "email": "a@b.com"}).json()
    assert pro["status"] == "completed"
    assert client.sent == [("POST", "https://hooks.test/x", {"t": "a@b.com"})]


def test_missing_flow(client):
    assert client.post("/hooks/none", json={}).status_code == 404
    assert client.delete("/flows/none").status_code == 404
