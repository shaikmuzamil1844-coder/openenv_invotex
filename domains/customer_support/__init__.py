"""Auto-registers CustomerSupportDomain with DomainRegistry on import."""

from __future__ import annotations

try:
    from server.domain_registry import DomainRegistry
except ImportError:
    try:
        from openenv_invotex.server.domain_registry import DomainRegistry
    except ImportError:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from server.domain_registry import DomainRegistry

from .domain import CustomerSupportDomain

DomainRegistry.register("customer_support", CustomerSupportDomain)
