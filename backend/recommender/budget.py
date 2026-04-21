"""
budget.py — Budget policy definitions and price ceiling calculations.

Three named policies let the user express how strictly they want to
stick to their per-person budget:

  strict   (1.0×) — only dishes at or below budget_per_person
  flexible (1.2×) — up to 20 % over budget; dish flagged "slightly over"
  generous (1.5×) — up to 50 % over budget; dish flagged "splurge"

A dish between the strict ceiling and the policy ceiling is still shown
but labelled so the UI can add a visual warning. This prevents good
options from vanishing just because one dish costs ₹10 more than expected.
"""

from __future__ import annotations
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Policy registry
# ---------------------------------------------------------------------------

POLICY_MULTIPLIERS: dict[str, float] = {
    "strict":   1.0,
    "flexible": 1.2,
    "generous": 1.5,
}


@dataclass(frozen=True)
class BudgetPolicy:
    name: str           # "strict" | "flexible" | "generous"
    multiplier: float   # effective ceiling = budget_per_person * multiplier

    @classmethod
    def from_name(cls, name: str) -> "BudgetPolicy":
        """
        Factory from a string name. Falls back to strict if name is unknown.
        Call this at the API boundary so the rest of the engine always works
        with a validated BudgetPolicy object.
        """
        mult = POLICY_MULTIPLIERS.get(name, POLICY_MULTIPLIERS["strict"])
        return cls(name=name, multiplier=mult)

    def ceiling(self, budget_per_person: float) -> float:
        """Maximum price allowed for a single dish under this policy."""
        return budget_per_person * self.multiplier


# ---------------------------------------------------------------------------
# Labelling
# ---------------------------------------------------------------------------

def price_label(price: float, budget_per_person: float, policy: BudgetPolicy) -> str:
    """
    Human-readable label for how a dish price relates to the per-person budget.

    "within budget" — at or below strict budget (always shown)
    "slightly over"  — between strict ceiling and 1.2× (flexible zone)
    "splurge"        — above 1.2× (only reachable under generous policy)
    """
    if price <= budget_per_person:
        return "within budget"
    if price <= budget_per_person * 1.2:
        return "slightly over"
    return "splurge"


def split_budget_for_extras(
    remaining: float,
    want_starters: bool,
    want_desserts: bool,
    people: int,
) -> dict[str, float]:
    """
    Divide leftover budget across optional courses.

    If both starters and desserts are wanted, split evenly.
    Starters are shared so their total allocation is not multiplied by people.
    Desserts are per-person so the allocation is the total pot for all of them.

    Returns a dict with keys "starters" and "desserts" (in INR total).
    """
    if not want_starters and not want_desserts:
        return {"starters": 0.0, "desserts": 0.0}

    active = sum([want_starters, want_desserts])
    per_slot = remaining / active if active else 0.0

    return {
        "starters": per_slot if want_starters else 0.0,
        "desserts": per_slot if want_desserts else 0.0,
    }
