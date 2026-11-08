"""
Rule Registry - the single place that assembles the knowledge base.

The inference engine imports ``ALL_RULES`` from here instead of importing each
module directly. When a module gains rules, nothing else needs to change.
"""

from __future__ import annotations

from typing import Iterable

from .authentication import AUTH_RULES
from .data_security import DATA_RULES
from .malware import MALWARE_RULES
from .network import NETWORK_RULES
from .security_policy import POLICY_RULES

# Ordered on purpose: the UI and the rule catalogue follow this order.
RULES_BY_MODULE: dict[str, tuple] = {
    "Authentication & Account Security": AUTH_RULES,
    "Malware & Process Security": MALWARE_RULES,
    "Network Security": NETWORK_RULES,
    "Data Security & Protection": DATA_RULES,
    "Privilege & Security Policy": POLICY_RULES,
}

MODULES: tuple[str, ...] = tuple(RULES_BY_MODULE)

ALL_RULES: tuple = tuple(rule for module_rules in RULES_BY_MODULE.values() for rule in module_rules)


def get_rule(rule_id: str):
    """Look up a rule by id; raises a clear error for unknown ids."""
    for rule in ALL_RULES:
        if rule.id == rule_id:
            return rule
    raise KeyError(f"No rule registered with id {rule_id!r}")


def rules_for_module(module: str) -> tuple:
    return RULES_BY_MODULE.get(module, ())


def module_summary() -> list[dict[str, object]]:
    return [
        {
            "module": module,
            "rules": len(rules),
            "conditions": sum(len(rule.conditions) for rule in rules),
        }
        for module, rules in RULES_BY_MODULE.items()
    ]


def iter_conclusions(rules: Iterable = ALL_RULES) -> set[str]:
    return {rule.conclusion_key for rule in rules}
