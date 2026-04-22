"""
engine.py — Recommendation orchestration.

Accepts a validated RecommendRequest and a list of nearby restaurants,
returns a structured response dict ready to be serialised by FastAPI.

Two modes:

  same_restaurant
    Finds restaurants that can serve the full group for mains. Then, only
    if the user opted in and there is leftover budget, adds starters and/or
    desserts from the same restaurant. Returns the top 5.

  best_per_person
    For each person independently finds their best main-course dish across
    all nearby restaurants (possibly different restaurants per person).
    Starters and desserts are not picked — cross-restaurant course mixing
    is impractical for a real order.

Order of operations (same_restaurant):
  1. Filter by cuisine preference
  2. Qualify: restaurant must cover all dietary types in mains
  3. Score and rank by user's priority
  4. For each of top-5: pick mains → calculate remaining budget → pick extras
  5. Annotate over-budget items and missing extras

All haversine distance calculations are delegated to the caller via the
distance_fn argument so the engine stays free of coordinate math.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .budget import BudgetPolicy, split_budget_for_extras
from .scorer import restaurant_has_mains_coverage, score_restaurant
from .picker import pick_mains, pick_starters, pick_desserts

if TYPE_CHECKING:
    from models import Restaurant


# ---------------------------------------------------------------------------
# Request dataclass — validated by FastAPI before reaching the engine
# ---------------------------------------------------------------------------

@dataclass
class RecommendRequest:
    """
    All inputs the engine needs. Constructed once per API call in main.py
    after FastAPI validates the query parameters.

    Keeping this as a plain dataclass (not a Pydantic model) separates
    the HTTP layer from the business logic layer.
    """
    # Group composition
    people: int
    person_diets: list[str]       # one per person, e.g. ["veg", "non-veg", "veg"]

    # Location
    lat: float
    lng: float
    radius_m: float

    # Budget
    budget_per_person: float
    budget_policy: BudgetPolicy   # strict | flexible | generous

    # Meal context
    meal_time: str                # "lunch" | "dinner" | "anytime"

    # Optional courses (only requested if user opted in)
    want_starters: bool = False
    want_desserts: bool = False

    # Dish-type and cuisine filters (empty = no filter)
    cuisine_filters: list[str] = field(default_factory=list)
    category_filters: list[str] = field(default_factory=list)

    # Ranking priority
    priority: str = "rating"      # "rating" | "distance" | "variety" | "value"

    # Mode
    mode: str = "same_restaurant" # "same_restaurant" | "best_per_person"

    # ------------------------------------------------------------------
    # Derived properties (computed, never stored)
    # ------------------------------------------------------------------

    @property
    def unique_diets(self) -> set[str]:
        """Distinct dietary labels in the group (used for qualification)."""
        return set(self.person_diets)

    @property
    def total_budget(self) -> float:
        return self.budget_per_person * self.people

    @property
    def budget_ceiling(self) -> float:
        """Per-dish price ceiling after applying the budget policy multiplier."""
        return self.budget_policy.ceiling(self.budget_per_person)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cuisine_matches(restaurant: "Restaurant", cuisine_filters: list[str]) -> bool:
    """True if no cuisine filter is active, or the restaurant serves one of them."""
    if not cuisine_filters:
        return True
    r_cuisines = [t.strip().lower() for t in restaurant.cuisine_tags.split(",")]
    return any(cf in " ".join(r_cuisines) for cf in cuisine_filters)


def _build_same_restaurant_card(
    restaurant: "Restaurant",
    distance_km: float,
    rank: int,
    req: RecommendRequest,
) -> dict | None:
    """
    Build one recommendation card for same_restaurant mode.

    Returns None if mains picking fails (should not happen after qualification,
    but handled defensively in case the DB changed mid-request).

    exclude_ids is a mutable set passed through all pickers so no dish
    is ever selected twice within the same order.
    """
    exclude_ids: set[int] = set()

    # ── Stage 1: mains (mandatory) ────────────────────────────────────────────
    mains = pick_mains(
        restaurant=restaurant,
        person_diets=req.person_diets,
        budget_per_person=req.budget_per_person,
        policy=req.budget_policy,
        meal_time=req.meal_time,
        category_filters=req.category_filters,
        exclude_ids=exclude_ids,
    )
    if not mains:
        return None

    mains_cost = sum(d["price"] for d in mains)
    remaining = req.total_budget - mains_cost

    # ── Stage 2: extras (optional, only if budget allows) ────────────────────
    starters: list[dict] = []
    desserts: list[dict] = []
    extras_not_found: list[str] = []

    if remaining > 0 and (req.want_starters or req.want_desserts):
        budget_split = split_budget_for_extras(
            remaining=remaining,
            want_starters=req.want_starters,
            want_desserts=req.want_desserts,
            people=req.people,
        )

        if req.want_starters and budget_split["starters"] > 0:
            starters = pick_starters(
                restaurant=restaurant,
                people=req.people,
                starters_budget=budget_split["starters"],
                budget_per_person=req.budget_per_person,
                policy=req.budget_policy,
                meal_time=req.meal_time,
                exclude_ids=exclude_ids,
            )
            if not starters:
                extras_not_found.append("starters")

        if req.want_desserts and budget_split["desserts"] > 0:
            desserts = pick_desserts(
                restaurant=restaurant,
                person_diets=req.person_diets,
                desserts_budget=budget_split["desserts"],
                budget_per_person=req.budget_per_person,
                policy=req.budget_policy,
                meal_time=req.meal_time,
                exclude_ids=exclude_ids,
            )
            served_count = len(desserts)
            if served_count < req.people:
                missing = req.people - served_count
                extras_not_found.append(
                    f"desserts for {missing} of {req.people} people"
                )
    elif remaining <= 0 and (req.want_starters or req.want_desserts):
        # Budget fully consumed by mains — let the frontend know
        if req.want_starters:
            extras_not_found.append("starters (no budget left after mains)")
        if req.want_desserts:
            extras_not_found.append("desserts (no budget left after mains)")

    # ── Cost summary ──────────────────────────────────────────────────────────
    starters_cost = sum(d["price"] for d in starters)
    desserts_cost = sum(d["price"] for d in desserts)
    estimated_total = mains_cost + starters_cost + desserts_cost

    # Count affordable mains for the variety indicator
    from .filters import MAIN_COURSE_CATEGORIES, matches_meal_context
    affordable_mains_count = sum(
        1 for d in restaurant.dishes
        if d.price <= req.budget_ceiling
        and d.normalized_category in MAIN_COURSE_CATEGORIES
        and matches_meal_context(d, req.meal_time)
    )

    return {
        "rank": rank,
        "restaurant": {**restaurant.to_dict(), "distance_km": distance_km},
        "order": {
            "starters": starters,   # shared dishes
            "mains": mains,         # one per person
            "desserts": desserts,   # one per person
        },
        "costs": {
            "starters_total":  round(starters_cost, 2),
            "mains_total":     round(mains_cost, 2),
            "desserts_total":  round(desserts_cost, 2),
            "estimated_total": round(estimated_total, 2),
            "remaining":       round(req.total_budget - estimated_total, 2),
        },
        "affordable_mains_count": affordable_mains_count,
        "extras_not_found": extras_not_found,
    }


# ---------------------------------------------------------------------------
# Public: same_restaurant mode
# ---------------------------------------------------------------------------

def recommend_same_restaurant(
    req: RecommendRequest,
    nearby: list["Restaurant"],
    distance_fn: Callable[["Restaurant"], float],
) -> dict:
    """
    Find up to 5 restaurants that can serve the full group for mains,
    ranked by the user's priority. Extras are added if opted in and budget allows.

    Args:
        req:         validated request
        nearby:      restaurants within the search radius (pre-filtered)
        distance_fn: callable(restaurant) -> float km — avoids importing math here
    """
    qualified: list[tuple] = []  # (restaurant, distance_km, score)

    for r in nearby:
        if not _cuisine_matches(r, req.cuisine_filters):
            continue
        if not restaurant_has_mains_coverage(
            r, req.unique_diets, req.budget_ceiling, req.meal_time
        ):
            continue
        dist = distance_fn(r)
        sc = score_restaurant(r, dist, req.priority, req.budget_ceiling, req.meal_time)
        qualified.append((r, dist, sc))

    qualified.sort(key=lambda x: -x[2])

    recommendations = []
    for rank, (r, dist, _) in enumerate(qualified[:5], start=1):
        card = _build_same_restaurant_card(r, round(dist, 1), rank, req)
        if card:
            recommendations.append(card)

    return {
        "mode": "same_restaurant",
        "people": req.people,
        "budget_per_person": req.budget_per_person,
        "total_budget": round(req.total_budget, 2),
        "meal_time": req.meal_time,
        "budget_policy": req.budget_policy.name,
        "want_starters": req.want_starters,
        "want_desserts": req.want_desserts,
        "recommendations": recommendations,
        "count": len(recommendations),
    }


# ---------------------------------------------------------------------------
# Public: best_per_person mode
# ---------------------------------------------------------------------------

def recommend_best_per_person(
    req: RecommendRequest,
    nearby: list["Restaurant"],
    distance_fn: Callable[["Restaurant"], float],
) -> dict:
    """
    For each person, find their best main-course dish independently,
    potentially from different restaurants.

    Starters and desserts are NOT picked here — it is impractical to suggest
    cross-restaurant shared starters. The UI should note this limitation and
    offer to switch to same_restaurant mode if extras are wanted.
    """
    from .filters import is_main_course, matches_meal_context, matches_dietary
    from .budget import price_label

    per_person: list[dict] = []

    for i, diet in enumerate(req.person_diets):
        best_dish = None
        best_restaurant = None
        best_score = float("-inf")

        for r in nearby:
            if not _cuisine_matches(r, req.cuisine_filters):
                continue

            dist = distance_fn(r)
            candidates = [
                d for d in r.dishes
                if d.price <= req.budget_ceiling
                and is_main_course(d)
                and matches_meal_context(d, req.meal_time)
                and matches_dietary(d, diet)
                and (not req.category_filters or d.normalized_category in req.category_filters)
            ]
            if not candidates:
                continue

            dish = max(candidates, key=lambda d: d.price)

            if req.priority == "rating":    sc = r.rating or 0.0
            elif req.priority == "distance": sc = -dist
            elif req.priority == "variety":  sc = float(len(candidates))
            elif req.priority == "value":    sc = -dish.price
            else:                            sc = r.rating or 0.0

            if sc > best_score:
                best_score = sc
                best_dish = dish
                best_restaurant = r

        if best_dish and best_restaurant:
            dist = distance_fn(best_restaurant)
            per_person.append({
                "person":               i + 1,
                "diet_label":           diet,
                "dish_name":            best_dish.name,
                "price":                round(best_dish.price, 2),
                "is_veg":               best_dish.is_veg,
                "is_vegan":             best_dish.is_vegan,
                "category":             best_dish.normalized_category,
                "budget_label":         price_label(best_dish.price, req.budget_per_person, req.budget_policy),
                "restaurant_name":      best_restaurant.name,
                "restaurant_place_id":  best_restaurant.place_id,
                "restaurant_rating":    best_restaurant.rating,
                "distance_km":          round(dist, 1),
            })

    unique_restaurants = len(set(p["restaurant_place_id"] for p in per_person))
    estimated_total = round(sum(p["price"] for p in per_person), 2)

    return {
        "mode":                 "best_per_person",
        "people":               req.people,
        "budget_per_person":    req.budget_per_person,
        "total_budget":         round(req.total_budget, 2),
        "meal_time":            req.meal_time,
        "budget_policy":        req.budget_policy.name,
        "per_person":           per_person,
        "estimated_total":      estimated_total,
        "unique_restaurants":   unique_restaurants,
        "multiple_deliveries":  unique_restaurants > 1,
        "note":                 "Starters and desserts are not suggested in this mode. Switch to same-restaurant mode to add extras." if (req.want_starters or req.want_desserts) else None,
    }
