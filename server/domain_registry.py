"""Minimal registry for registering and discovering domain plugins."""

from __future__ import annotations

from typing import Type


class DomainRegistry:
    """Singleton registry that maps domain names to domain classes."""

    _registry: dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, domain_cls: Type) -> None:
        """Register a domain under the provided name.

        Raises ValueError if the name is already registered to prevent
        duplicate domain imports.
        """
        if name in cls._registry:
            return  # idempotent — safe for re-imports
        cls._registry[name] = domain_cls

    @classmethod
    def get(cls, name: str) -> Type | None:
        """Return the domain class registered under `name`, or None if missing."""
        return cls._registry.get(name)

    @classmethod
    def list_domains(cls) -> list[str]:
        """Return a sorted list of registered domain names."""
        return sorted(cls._registry.keys())

    @classmethod
    def require(cls, name: str) -> Type:
        """Return the domain class or raise with guidance for missing registrations."""
        domain_cls = cls.get(name)
        if domain_cls is not None:
            return domain_cls
        available = cls.list_domains()
        raise RuntimeError(
            f"Domain '{name}' is not registered. Available domains: {available}. "
            "Make sure domains/__init__.py is imported before the server starts."
        )
