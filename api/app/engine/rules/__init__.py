# Import rules to trigger self-registration into RuleRegistry.
# Addon rules are imported in their respective addon packages.
from app.engine.rules import base, disease, reproduction  # noqa: F401
