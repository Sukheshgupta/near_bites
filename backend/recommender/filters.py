"""
filters.py — Dish-level filtering predicates.

Every function takes a Dish ORM object and returns a bool.
These are the single source of truth for what counts as a starter,
main, dessert, or breakfast item. Compose them freely in picker.py
and engine.py — never duplicate the logic elsewhere.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import Dish

# ---------------------------------------------------------------------------
# Category sets — which normalized_category values belong to each course
# ---------------------------------------------------------------------------

MAIN_COURSE_CATEGORIES: frozenset[str] = frozenset([
    "Main Course",
    "Biryani & Rice",
    "Rice & Noodles",
    "Fast Food",
    "Combos & Meals",
])

STARTER_CATEGORIES: frozenset[str] = frozenset([
    "Starters",
])

DESSERT_CATEGORIES: frozenset[str] = frozenset([
    "Desserts",
    "Ice Cream & Shakes",
])

# ---------------------------------------------------------------------------
# Meal-context filtering — breakfast exclusion
#
# South Indian tiffin items (dosa, idli) are valid all-day, so we do NOT
# exclude the Breads & Tiffin category wholesale. Instead we exclude only
# dishes whose raw Swiggy section name contains explicitly breakfast-only
# keywords. This is intentionally conservative.
# ---------------------------------------------------------------------------

BREAKFAST_ONLY_KEYWORDS: tuple[str, ...] = (
    "breakfast special",
    "morning special",
    "all day breakfast",
    "early morning",
    "breakfast only",
)


def is_breakfast_item(dish: "Dish") -> bool:
    """True if the dish's raw Swiggy category label marks it breakfast-only."""
    raw = (dish.category or "").lower()
    return any(kw in raw for kw in BREAKFAST_ONLY_KEYWORDS)


def matches_meal_context(dish: "Dish", meal_time: str) -> bool:
    """
    True if the dish is appropriate for the given meal time.

    meal_time values:
      "lunch"   — exclude breakfast-only items
      "dinner"  — exclude breakfast-only items
      "anytime" — no exclusions
    """
    if meal_time == "anytime":
        return True
    return not is_breakfast_item(dish)


# ---------------------------------------------------------------------------
# Dietary filtering
# ---------------------------------------------------------------------------

def matches_dietary(dish: "Dish", diet: str) -> bool:
    """
    True if the dish satisfies the given dietary preference.

    diet values:
      "veg"     — must be vegetarian
      "vegan"   — must be vegan
      "non-veg" — any dish accepted
      "any"     — any dish accepted
    """
    if diet == "veg":
        return dish.is_veg
    if diet == "vegan":
        return dish.is_vegan
    return True  # non-veg and any accept everything


# ---------------------------------------------------------------------------
# Category filtering (user-selected dish-type chips)
# ---------------------------------------------------------------------------

def matches_category_filter(dish: "Dish", category_filters: list[str]) -> bool:
    """
    True if no category filter is active, or the dish's normalized_category
    is in the active filter list.
    """
    if not category_filters:
        return True
    return dish.normalized_category in category_filters


# ---------------------------------------------------------------------------
# Course-type helpers
# ---------------------------------------------------------------------------

def is_main_course(dish: "Dish") -> bool:
    return dish.normalized_category in MAIN_COURSE_CATEGORIES


def is_starter(dish: "Dish") -> bool:
    return dish.normalized_category in STARTER_CATEGORIES


def is_dessert(dish: "Dish") -> bool:
    return dish.normalized_category in DESSERT_CATEGORIES
