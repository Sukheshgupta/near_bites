"""
recommender/ — Group meal recommendation engine.

Package layout:
  filters.py  — dish-level predicates (dietary, meal context, course type)
  budget.py   — BudgetPolicy dataclass, price ceilings, budget splitting
  scorer.py   — restaurant qualification and priority scoring
  picker.py   — dish selection per course (mains, starters, desserts)
  engine.py   — orchestration; RecommendRequest dataclass; two mode functions

Public API (import from here, not from sub-modules):
  RecommendRequest  — input dataclass; construct in main.py, pass to recommend()
  recommend()       — entry point; dispatches to same_restaurant or best_per_person
"""

from .engine import RecommendRequest, recommend_same_restaurant, recommend_best_per_person
from .budget import BudgetPolicy


def recommend(
    request: RecommendRequest,
    nearby: list,
    distance_fn,
) -> dict:
    """
    Main entry point for the recommendation engine.

    Args:
        request:     validated RecommendRequest from main.py
        nearby:      list of Restaurant ORM objects within the search radius
        distance_fn: callable(Restaurant) -> float km

    Returns:
        dict ready to be returned as a FastAPI JSON response
    """
    if request.mode == "same_restaurant":
        return recommend_same_restaurant(request, nearby, distance_fn)
    return recommend_best_per_person(request, nearby, distance_fn)


__all__ = ["RecommendRequest", "BudgetPolicy", "recommend"]
