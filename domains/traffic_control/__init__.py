"""Auto-registers TrafficControlDomain with DomainRegistry on import."""

from __future__ import annotations

try:
    from openenv_invotex.server.domain_registry import DomainRegistry
except ImportError:
    from server.domain_registry import DomainRegistry

from .domain import TrafficControlDomain

DomainRegistry.register("traffic_control", TrafficControlDomain)
