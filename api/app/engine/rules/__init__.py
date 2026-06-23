# Import rules to trigger self-registration into RuleRegistry.
# Addon rules are imported in their respective addon packages.
from app.engine.rules import (  # noqa: F401
    base,
    boar,
    composite,
    disease,
    grow_finish,
    litter,
    loss,
    reproduction,
    sow_herd,
)
