"""
Rule Engine — core intelligence layer.

Flow:
  RuleContext (KPI snapshot + farm metadata)
      → RuleRegistry.for_intent() → Rule[]
      → each Rule.fn(ctx) → Finding[]
      → StructuredResult

Tier filtering:
  "base"  rules → always active
  addon code rules → active only when farm has that subscription

Renderer consumes StructuredResult:
  Base tier  → template text
  Addon tier → LLM natural language (Renderer swapped, Rule Engine unchanged)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Callable, Coroutine
from uuid import UUID


class Severity(str, Enum):
    OK = "OK"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


_SEVERITY_RANK = {Severity.OK: 0, Severity.INFO: 1, Severity.WARNING: 2, Severity.CRITICAL: 3}


@dataclass
class RuleContext:
    """Immutable snapshot fed into every rule function."""
    farm_id: UUID
    country: str                           # ISO-3166-1 alpha-2: "KR", "US", "BR" …
    kpi: dict[str, float | None]           # "PSY" → 22.4, "NPD" → 42.0, …
    benchmarks: dict[str, dict]            # "PSY" → {"avg": 21.9, "top25": 32.5, "target": 24.0}
    sow_counts: dict[str, int]             # "OPEN" → 120, "PREGNANT" → 850, …
    as_of: date = field(default_factory=date.today)
    extra: dict[str, Any] = field(default_factory=dict)  # domain-specific pass-through


@dataclass
class Finding:
    """One rule violation or insight. Multiple findings compose a StructuredResult."""
    rule_id: str
    kpi: str
    severity: Severity
    current_value: float | None
    target_value: float | None
    causes: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class StructuredResult:
    """
    Rule Engine output consumed by Renderer.

    Base tier: renderer.render_text(result, locale)
    Addon LLM: llm_renderer.render(result, locale)
    LLM sees only this struct — never raw DB data.
    """
    farm_id: UUID
    intent: str
    severity: Severity
    findings: list[Finding]
    as_of: date


# Rule function type: async to allow DB lookups inside rules if needed
RuleFn = Callable[[RuleContext], Coroutine[Any, Any, list[Finding]]]


@dataclass
class Rule:
    rule_id: str
    domain: str    # intent category: "npd", "psy", "farrowing", "fcr", …
    description: str
    fn: RuleFn
    tier: str = "base"  # "base" | addon code e.g. "fcr", "health"


class RuleRegistry:
    """
    Module-level singleton. Rules self-register at import time via register().
    Addon rules register in their own package and stay idle until that addon
    is mounted (same lazy-import pattern as AddonRegistry).
    """
    _rules: list[Rule] = []

    @classmethod
    def register(cls, rule: Rule) -> None:
        cls._rules.append(rule)

    @classmethod
    def all(cls) -> list[Rule]:
        return list(cls._rules)

    @classmethod
    def for_intent(cls, intent: str, tiers: list[str] | None = None) -> list[Rule]:
        """
        "dashboard" intent → all rules (filtered by tier).
        Any other intent   → rules whose domain matches exactly.
        """
        if intent == "dashboard":
            rules = list(cls._rules)
        else:
            rules = [r for r in cls._rules if r.domain == intent]
        if tiers is not None:
            rules = [r for r in rules if r.tier in tiers]
        return rules


class RuleEngine:
    @staticmethod
    async def evaluate(
        ctx: RuleContext,
        intent: str = "dashboard",
        tiers: list[str] | None = None,
    ) -> StructuredResult:
        """
        Run all applicable rules and aggregate findings.

        tiers defaults to ["base"]. Pass farm's active addon codes to unlock
        higher-tier rules:
          tiers = ["base"] + [sub.addon_code for sub in farm.active_subscriptions]
        """
        if tiers is None:
            tiers = ["base"]

        rules = RuleRegistry.for_intent(intent, tiers)
        all_findings: list[Finding] = []
        for rule in rules:
            findings = await rule.fn(ctx)
            all_findings.extend(findings)

        severity = max(
            (f.severity for f in all_findings),
            key=lambda s: _SEVERITY_RANK[s],
            default=Severity.OK,
        )
        return StructuredResult(
            farm_id=ctx.farm_id,
            intent=intent,
            severity=severity,
            findings=all_findings,
            as_of=ctx.as_of,
        )
