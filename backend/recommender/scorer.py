"""
scorer.py — Restaurant qualification and priority scoring.

Qualification: a restaurant must have at least one main-course dish within
the budget ceiling for every dietary type present in the group. Starters and
desserts are never used for qualification — they are optional extras.

Scoring: assigns a scalar (higher = better) to each qualified restaurant
based on the user's chosen priority. Used only to sort; the absolute value
has no meaning outside of comparison.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from .filters import matches_dietary, matches_meal_context, MAIN_COURSE_CATEGORIES
from .budget import BudgetPolicy

if TYPE_CHECKING:
    from models import Restaurant


def restaurant_has_mains_coverage(
    restaurant: "Restaurant",
    unique_diets: set[str],
    budget_ceiling: float,
    meal_time: str,
) -> bool:
    """
    Qualification gate: True only if the restaurant has at least one
    affordable main-course dish for every dietary type in the group.

    Why mains only? Starters and desserts are optional; gating on them
    would unfairly exclude restaurants that are excellent for mains but
    happen not to have starters in stock.

    Args:
        unique_diets:   set of distinct dietary labels in the group
                        (e.g. {"veg", "non-veg"})
        budget_ceiling: policy-adjusted price ceiling (budget × multiplier)
        meal_time:      "lunch" | "dinner" | "anytime"
    """
    for diet in unique_diets:
        has_dish = any(
            d.price <= budget_ceiling
            and matches_dietary(d, diet)
            and matches_meal_context(d, meal_time)
            and d.normalized_category in MAIN_COURSE_CATEGORIES
            for d in restaurant.dishes
        )
        if not has_dish:
            return False
    return True


def score_restaurant(
    restaurant: "Restaurant",
    distance_km: float,
    priority: str,
    budget_ceiling: float,
    meal_time: str,
) -> float:
    """
    Scalar score for ranking qualified restaurants. Higher is better.

    priority options:
      "rating"   — restaurant's average star rating (from Swiggy)
      "distance" — negative distance so closer scores higher
      "variety"  — count of affordable main-course dishes (more choice = better)
      "value"    — negative average main-course price (cheaper = better)

    Only main-course dishes within the budget ceiling and meal context are
    considered for variety/value — we rank on what people will actually order.
    """
    affordable_mains = [
        d for d in restaurant.dishes
        if d.price <= budget_ceiling
        and d.normalized_category in MAIN_COURSE_CATEGORIES
        and matches_meal_context(d, meal_time)
    ]
    variety = len(affordable_mains)
    avg_price = (
        sum(d.price for d in affordable_mains) / variety
        if variety else budget_ceiling
    )

    if priority == "rating":   return restaurant.rating or 0.0
    if priority == "distance": return -distance_km
    if priority == "variety":  return float(variety)
    if priority == "value":    return -avg_price
    return restaurant.rating or 0.0  # default
