"""
Addon Plugin System — PigOS extensibility core.

How it works:
1. Each Addon is a Python package under app/addons/<name>/
2. It calls AddonRegistry.register(addon_module) at import time
3. main.py imports all addon packages → routers mount automatically
4. require_addon("ADDON_FCR") dependency blocks access if not subscribed

Adding a new Addon:
  1. Create app/addons/fcr/__init__.py
  2. Define router = APIRouter(...)
  3. Register: AddonRegistry.register(AddonModule(code="ADDON_FCR", ...))
  4. main.py: from app.addons import fcr  (one line)
  Nothing else changes in the base code.
"""
from dataclasses import dataclass, field
from fastapi import APIRouter


@dataclass
class AddonModule:
    code: str                  # e.g. "ADDON_FCR"
    name: str                  # e.g. "FCR Optimizer AI"
    router: APIRouter
    url_prefix: str            # e.g. "fcr"  → mounts at /addons/fcr
    tags: list[str] = field(default_factory=list)
    description: str = ""


class _AddonRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, AddonModule] = {}

    def register(self, addon: AddonModule) -> None:
        if addon.code in self._registry:
            raise ValueError(f"Addon '{addon.code}' is already registered")
        self._registry[addon.code] = addon

    def get(self, code: str) -> AddonModule | None:
        return self._registry.get(code)

    def all(self) -> list[AddonModule]:
        return list(self._registry.values())

    def codes(self) -> list[str]:
        return list(self._registry.keys())


AddonRegistry = _AddonRegistry()
