# 🪝 flowhook

[![CI](https://github.com/talhaarshadqa/flowhook/actions/workflows/ci.yml/badge.svg)](https://github.com/talhaarshadqa/flowhook/actions)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

**A tiny webhook-driven automation engine.** Define a *flow* as a list of steps —
filter events, build messages, call other APIs — then trigger it with an incoming webhook.
Think "a self-hosted Zapier/Make step runner," in a few hundred lines of Python.

## ✨ Features

- **Flows as data**: JSON (or YAML) — `trigger → filter → set → http → log`
- **Conditions**: `eq`, `ne`, `gt`, `lt`, `gte`, `lte`, `contains`, `exists`
- **Templating**: `{user.name}`, `{email}` pulled from the event payload
- **Outbound actions** with a pluggable sender (easy to test, easy to swap)
- **Safe execution**: a failing step returns an error result instead of crashing the server
- REST API to register flows and fire them via `POST /hooks/{name}`
- Pure-Python core engine — fully unit-tested, no external services needed to run the tests

## 🚀 Quick start

```bash
git clone https://github.com/talhaarshadqa/flowhook.git
cd flowhook
pip install -e .
uvicorn flowhook.api:app --reload
```

Register a flow that notifies Slack only for Pro signups:

```bash
curl -X PUT localhost:8000/flows -H "Content-Type: application/json" -d '{
  "name": "new-signup",
  "steps": [
    {"type": "filter", "condition": {"field": "plan", "op": "eq", "value": "pro"}},
    {"type": "set", "fields": {"message": "New Pro signup: {email}"}},
    {"type": "http", "method": "POST", "url": "https://hooks.slack.com/services/XXX",
     "body": {"text": "{message}"}}
  ]
}'
```

Fire it from your app's webhook:

```bash
curl -X POST localhost:8000/hooks/new-signup \
  -H "Content-Type: application/json" \
  -d '{"plan": "pro", "email": "sam@acme.com"}'
```

## 🧩 Step types

| Type | What it does |
|---|---|
| `filter` | Stop the flow unless a condition is true |
| `set` | Add or template new fields into the context |
| `http` | Call an external URL (with templated body/headers), optionally save the response |
| `log` | Record a templated message in the run trace |

## 📡 API

| Method | Endpoint | Description |
|---|---|---|
| `PUT` | `/flows` | Register or replace a flow |
| `GET` | `/flows` | List flow names |
| `DELETE` | `/flows/{name}` | Remove a flow |
| `POST` | `/hooks/{name}` | Trigger a flow with an event payload |
| `GET` | `/health` | Health + registered flows |

## 🧪 Development

```bash
pip install -e ".[dev]"
pytest --cov=flowhook
```

## 📄 License

MIT
