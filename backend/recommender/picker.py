"""
picker.py — Dish selection for each course type.

Three pickers, one per course. Each takes a restaurant, constraints, and a
mutable exclude_ids set (updated in-place so subsequent pickers never
re-pick the same dish).

Stage 1 — pick_mains (mandatory, called first)
  One main-course dish per person matched to their dietary preference.
  Dishes are chosen by highest price within ceiling (best value perception).
  Returns an empty list if any person cannot be served → disqualifies the restaurant.

Stage 2a — pick_starters (optional, called only if want_starters=True)
  Shared across the group: ceil(people / 2) dishes.
  Spend is capped at the starters budget slice (from budget.split_budget_for_extras).
  Soft failure: returns however many could be found; never disqualifies.

Stage 2b — pick_desserts (optional, called only if want_desserts=True)
  One dessert per person.
  Spend is capped at the desserts budget slice divided equally per person.
  Soft failure: returns however many could be found; never disqualifies.

All pickers annotate each returned dish dict with a "budget_label" from
budget.price_label so the frontend can render within-budget / slightly-over /
splurge badges consistently.
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING, Callable

from .filters import (
    matches_dietary,
    matches_meal_context,
    matches_category_filter,
    is_main_course,
    is_starter,
    is_dessert,
    MAIN_COURSE_CATEGORIES,
)
from .budget import BudgetPolicy, price_label

if TYPE_CHECKING:
    from models import Restaurant, Dish


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_candidates(
    restaurant: "Restaurant",
    predicate: Callable[["Dish"], bool],
    price_ceiling: float,
    meal_time: str,
    exclude_ids: set[int],
) -> list["Dish"]:
    """
    Return dishes from the restaurant that:
      - pass the caller's predicate (course type + dietary)
      - are within price_ceiling
      - are appropriate for the meal time
      - have not already been picked (not in exclude_ids)
    """
    return [
        d for d in restaurant.dishes
        if d.id not in exclude_ids
        and d.price <= price_ceiling
        and matches_meal_context(d, meal_time)
        and predicate(d)
    ]


def _dish_to_dict(
    dish: "Dish",
    course: str,
    budget_per_person: float,
    policy: BudgetPolicy,
    extra: dict | None = None,
) -> dict:
    """Serialise a Dish ORM object to a plain dict for the API response."""
    base = {
        "dish_id":       dish.id,
        "course":        course,
        "dish_name":     dish.name,
        "price":         round(dish.price, 2),
        "is_veg":        dish.is_veg,
        "is_vegan":      dish.is_vegan,
        "category":      dish.normalized_category,
        "raw_category":  dish.category,
        "budget_label":  price_label(dish.price, budget_per_person, policy),
    }
    if extra:
        base.update(extra)
    return base


# ---------------------------------------------------------------------------
# Stage 1: Mains
# ---------------------------------------------------------------------------

def pick_mains(
    restaurant: "Restaurant",
    person_diets: list[str],
    budget_per_person: float,
    policy: BudgetPolicy,
    meal_time: str,
    category_filters: list[str],
    exclude_ids: set[int],
) -> list[dict]:
    """
    Pick one main-course dish per person.

    Selection rule: highest price within the policy ceiling (best perceived value).
    If a category_filter is active, only dishes in those categories qualify.
    If any person cannot be served, returns [] to signal the restaurant is unfit.

    Mutates exclude_ids with the IDs of picked dishes so subsequent
    pickers (starters, desserts) never re-select the same item.
    """
    ceiling = policy.ceiling(budget_per_person)
    result: list[dict] = []

    for i, diet in enumerate(person_diets):
        def predicate(d: "Dish", _diet: str = diet) -> bool:
            return (
                is_main_course(d)
                and matches_dietary(d, _diet)
                and matches_category_filter(d, category_filters)
            )

        options = _get_candidates(restaurant, predicate, ceiling, meal_time, exclude_ids)
        if not options:
            return []  # cannot serve person i+1 → disqualify

        best = max(options, key=lambda d: d.price)
        exclude_ids.add(best.id)
        result.append(_dish_to_dict(
            best, "main", budget_per_person, policy,
            extra={"person": i + 1, "diet_label": diet},
        ))

    return result


# ---------------------------------------------------------------------------
# Stage 2a: Starters (shared)
# ---------------------------------------------------------------------------

def pick_starters(
    restaurant: "Restaurant",
    people: int,
    starters_budget: float,
    budget_per_person: float,
    policy: BudgetPolicy,
    meal_time: str,
    exclude_ids: set[int],
) -> list[dict]:
    """
    Pick shared starters: ceil(people / 2) dishes from the starters_budget pot.

    Starters are shared so the price ceiling per dish is the whole pot divided
    by the number of dishes we want — but we also cap at the policy ceiling so
    no single starter is unreasonably expensive per head.

    Soft failure: if the budget runs out or no starters are available, returns
    however many were found (could be zero). Never disqualifies the restaurant.

    Mutates exclude_ids with picked IDs.
    """
    target_count = math.ceil(people / 2)
    # Price ceiling per dish: lesser of policy ceiling and equal share of the pot
    per_dish_ceiling = min(
        policy.ceiling(budget_per_person),
        starters_budget / target_count if target_count else 0,
    )
    result: list[dict] = []
    budget_left = starters_budget

    for _ in range(target_count):
        options = _get_candidates(
            restaurant, is_starter, per_dish_ceiling, meal_time, exclude_ids
        )
        # Further restrict to what we can still afford right now
        options = [d for d in options if d.price <= budget_left]
        if not options:
            break

        best = max(options, key=lambda d: d.price)
        exclude_ids.add(best.id)
        budget_left -= best.price
        result.append(_dish_to_dict(
            best, "starter", budget_per_person, policy,
            extra={"shared": True},
        ))

    return result


# ---------------------------------------------------------------------------
# Stage 2b: Desserts (per person)
# ---------------------------------------------------------------------------

def pick_desserts(
    restaurant: "Restaurant",
    person_diets: list[str],
    desserts_budget: float,
    budget_per_person: float,
    policy: BudgetPolicy,
    meal_time: str,
    exclude_ids: set[int],
) -> list[dict]:
    """
    Pick one dessert per person from the desserts_budget pot.

    Budget per person for desserts = desserts_budget / people.
    Each person's dessert is matched to their dietary preference.
    Soft failure: if no dessert is found for a person they are skipped (logged
    in engine.py as extras_not_found). Never disqualifies the restaurant.

    Mutates exclude_ids with picked IDs.
    """
    people = len(person_diets)
    if people == 0 or desserts_budget <= 0:
        return []

    per_person_ceiling = min(
        policy.ceiling(budget_per_person),
        desserts_budget / people,
    )
    result: list[dict] = []

    for i, diet in enumerate(person_diets):
        def predicate(d: "Dish", _diet: str = diet) -> bool:
            return is_dessert(d) and matches_dietary(d, _diet)

        options = _get_candidates(
            restaurant, predicate, per_person_ceiling, meal_time, exclude_ids
        )
        if not options:
            continue  # soft skip — person gets no dessert

        best = max(options, key=lambda d: d.price)
        exclude_ids.add(best.id)
        result.append(_dish_to_dict(
            best, "dessert", budget_per_person, policy,
            extra={"person": i + 1, "diet_label": diet},
        ))

    return result
