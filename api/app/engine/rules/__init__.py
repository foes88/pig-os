# Import rules to trigger self-registration into RuleRegistry.
# Addon rules are imported in their respective addon packages.
from app.engine.rules import (  # noqa: F401
    base,
    disease,
    grow_finish,
    litter,
    reproduction,
    sow_herd,
)
