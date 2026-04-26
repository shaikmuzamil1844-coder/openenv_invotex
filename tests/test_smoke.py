from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def _import_domains() -> None:
    try:
        importlib.import_module("openenv_invotex.domains")
    except ImportError:
        importlib.import_module("domains")


def _import_domain_registry():
    try:
        module = importlib.import_module("openenv_invotex.server.domain_registry")
    except ImportError:
        module = importlib.import_module("server.domain_registry")
    return module.DomainRegistry


def _import_app():
    try:
        module = importlib.import_module("openenv_invotex.server.app")
    except ImportError:
        module = importlib.import_module("server.app")
    return module.app


def test_domains_are_registered() -> None:
    _import_domains()
    domain_registry = _import_domain_registry()
    domains = set(domain_registry.list_domains())
    assert {"email_triage", "traffic_control", "customer_support"}.issubset(domains)


def test_health_endpoint_returns_ok() -> None:
    app = _import_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") in {"ok", "healthy"}
    if "registered_domains" in payload:
        assert isinstance(payload.get("registered_domains"), list)
