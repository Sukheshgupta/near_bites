import math
import os
from contextlib import asynccontextmanager

from datetime import datetime

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import event
from sqlalchemy.orm import Session

from cache import (
    cache_restaurants,
    get_cached_restaurant_detail,
    get_cached_restaurants,
    invalidate_stale_cache,
)
from models import Base, Dish, Restaurant, Review, get_engine, get_session_factory
from places import get_place_details, search_nearby

load_dotenv()

engine = get_engine()
SessionFactory = get_session_factory(engine)


# Enable WAL mode for better concurrent reads
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="NearBites API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()


def _haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@app.get("/api/config")
async def get_config():
    return {
        "maps_api_key": os.getenv("GOOGLE_MAPS_JS_API_KEY", ""),
    }


@app.get("/api/restaurants")
async def list_restaurants(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(15000, description="Search radius in meters"),
    budget: float = Query(2000, description="Max budget in INR"),
    cuisine: str = Query("", description="Comma-separated cuisine filters"),
    dietary: str = Query("", description="veg, non-veg, or vegan"),
    open_now: bool = Query(False, description="Only show open restaurants"),
    db: Session = Depends(get_db),
):
    # Clean up stale cache
    invalidate_stale_cache(db)

    # Try cache first (non-seed data)
    restaurants = get_cached_restaurants(db, lat, lng, radius)
    source = "cache"

    if restaurants is None:
        # Cache miss — try Google Places API
        api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
        if api_key:
            api_results = await search_nearby(lat, lng, radius, api_key)
            if api_results:
                restaurants = cache_restaurants(db, api_results)
                source = "api"

    if restaurants is None:
        # No cache and no API key — fall back to all restaurants in DB within range
        all_restaurants = db.query(Restaurant).all()
        restaurants = [
            r for r in all_restaurants
            if _haversine_km(lat, lng, r.lat, r.lng) * 1000 <= radius
        ]
        source = "db"

    # Apply filters
    results = []
    cuisine_filters = [c.strip().lower() for c in cuisine.split(",") if c.strip()]
    dietary_lower = dietary.strip().lower()

    for r in restaurants:
        # Open now filter
        if open_now and not r.is_open:
            continue

        # Cuisine filter
        if cuisine_filters:
            r_cuisines = [t.strip().lower() for t in r.cuisine_tags.split(",") if t.strip()]
            if not any(c in r_cuisines for c in cuisine_filters):
                continue

        # Dietary filter
        if dietary_lower:
            r_cuisines = [t.strip().lower() for t in r.cuisine_tags.split(",") if t.strip()]
            if dietary_lower == "veg" and "vegetarian" not in r_cuisines and "vegan" not in r_cuisines:
                # Check if restaurant has veg dishes
                veg_dishes = [d for d in r.dishes if d.is_veg]
                if not veg_dishes:
                    continue
            elif dietary_lower == "vegan":
                vegan_dishes = [d for d in r.dishes if d.is_vegan]
                if not vegan_dishes:
                    continue

        # Count dishes under budget
        dishes_under_budget = [d for d in r.dishes if d.price <= budget]
        dish_count = len(dishes_under_budget)
        min_price = min((d.price for d in r.dishes), default=0)
        max_price = max((d.price for d in r.dishes), default=0)

        distance_km = round(_haversine_km(lat, lng, r.lat, r.lng), 1)

        result = r.to_dict()
        result["dishes_under_budget"] = dish_count
        result["min_dish_price"] = min_price
        result["max_dish_price"] = max_price
        result["distance_km"] = distance_km
        results.append(result)

    # Sort by distance
    results.sort(key=lambda x: x["distance_km"])

    return {
        "restaurants": results,
        "count": len(results),
        "source": source,
    }


@app.get("/api/restaurants/{place_id}")
async def get_restaurant(
    place_id: str,
    budget: float = Query(2000, description="Budget for highlighting dishes"),
    db: Session = Depends(get_db),
):
    # Try cache
    restaurant = get_cached_restaurant_detail(db, place_id)

    if restaurant is None:
        # Try fetching from Google
        api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
        if api_key:
            details = await get_place_details(place_id, api_key)
            if details:
                cached = cache_restaurants(db, [details])
                restaurant = cached[0] if cached else None

    if restaurant is None:
        # Fall back to DB lookup (covers swiggy_ records not in cache)
        restaurant = db.query(Restaurant).filter(Restaurant.place_id == place_id).first()

    if restaurant is None:
        return {"error": "Restaurant not found"}, 404

    # Group dishes by category
    menu = {}
    dishes_within_budget = 0
    for dish in restaurant.dishes:
        cat = dish.category or "Other"
        if cat not in menu:
            menu[cat] = []
        dish_dict = dish.to_dict()
        dish_dict["within_budget"] = dish.price <= budget
        if dish.price <= budget:
            dishes_within_budget += 1
        menu[cat].append(dish_dict)

    return {
        "restaurant": restaurant.to_dict(),
        "menu": menu,
        "dishes_within_budget": dishes_within_budget,
        "total_dishes": len(restaurant.dishes),
    }


@app.get("/api/dishes")
async def list_dishes(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(15000, description="Search radius in meters"),
    budget: float = Query(2000, description="Max price per dish"),
    cuisine: str = Query("", description="Comma-separated cuisine filters"),
    dietary: str = Query("", description="veg, non-veg, or vegan"),
    db: Session = Depends(get_db),
):
    # Get all restaurants in range
    all_restaurants = db.query(Restaurant).all()
    nearby = [
        r for r in all_restaurants
        if _haversine_km(lat, lng, r.lat, r.lng) * 1000 <= radius
    ]

    cuisine_filters = [c.strip().lower() for c in cuisine.split(",") if c.strip()]
    dietary_lower = dietary.strip().lower()

    dishes = []
    for r in nearby:
        # Cuisine filter
        if cuisine_filters:
            r_cuisines = [t.strip().lower() for t in r.cuisine_tags.split(",") if t.strip()]
            if not any(c in r_cuisines for c in cuisine_filters):
                continue

        distance_km = round(_haversine_km(lat, lng, r.lat, r.lng), 1)

        for d in r.dishes:
            if d.price > budget:
                continue

            # Dietary filter
            if dietary_lower == "veg" and not d.is_veg:
                continue
            if dietary_lower == "vegan" and not d.is_vegan:
                continue

            dishes.append({
                "name": d.name,
                "description": d.description,
                "price": d.price,
                "category": d.category,
                "is_veg": d.is_veg,
                "is_vegan": d.is_vegan,
                "restaurant_name": r.name,
                "restaurant_place_id": r.place_id,
                "distance_km": distance_km,
            })

    # Sort by price ascending
    dishes.sort(key=lambda x: x["price"])

    return {
        "dishes": dishes,
        "count": len(dishes),
    }


# --- Group Recommender ---
# Thin route: validates params, builds RecommendRequest, delegates to recommender/

from recommender import recommend as _recommend_engine, RecommendRequest, BudgetPolicy

@app.get("/api/recommend")
async def recommend(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(15000),
    budget_per_person: float = Query(..., description="Per-person budget in INR"),
    people: int = Query(..., ge=1, le=20),
    group_dietary: str = Query("", description="Comma-separated dietary per person, e.g. veg,non-veg,veg"),
    cuisine: str = Query("", description="Comma-separated cuisine preferences"),
    dish_category: str = Query("", description="Comma-separated normalized_category filters"),
    meal_time: str = Query("lunch", description="lunch | dinner | anytime"),
    want_starters: bool = Query(False, description="Include shared starters if budget allows"),
    want_desserts: bool = Query(False, description="Include per-person desserts if budget allows"),
    budget_policy: str = Query("strict", description="strict | flexible | generous"),
    priority: str = Query("rating", description="rating | distance | variety | value"),
    mode: str = Query("same_restaurant", description="same_restaurant | best_per_person"),
    db: Session = Depends(get_db),
):
    # Parse per-person dietary list; pad/truncate to `people` length
    raw_diets = [d.strip().lower() for d in group_dietary.split(",") if d.strip()]
    person_diets = (raw_diets + ["any"] * people)[:people]

    req = RecommendRequest(
        people=people,
        person_diets=person_diets,
        lat=lat,
        lng=lng,
        radius_m=radius,
        budget_per_person=budget_per_person,
        budget_policy=BudgetPolicy.from_name(budget_policy),
        meal_time=meal_time,
        want_starters=want_starters,
        want_desserts=want_desserts,
        cuisine_filters=[c.strip().lower() for c in cuisine.split(",") if c.strip()],
        category_filters=[c.strip() for c in dish_category.split(",") if c.strip()],
        priority=priority,
        mode=mode,
    )

    all_restaurants = db.query(Restaurant).all()
    nearby = [
        r for r in all_restaurants
        if _haversine_km(lat, lng, r.lat, r.lng) * 1000 <= radius
    ]

    def distance_fn(r):
        return _haversine_km(lat, lng, r.lat, r.lng)

    return _recommend_engine(req, nearby, distance_fn)


# --- Reviews ---

class ReviewCreate(BaseModel):
    reviewer_name: str = Field(..., min_length=1, max_length=100)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=1000)


@app.get("/api/restaurants/{place_id}/reviews")
async def get_reviews(
    place_id: str,
    db: Session = Depends(get_db),
):
    reviews = (
        db.query(Review)
        .filter(Review.restaurant_place_id == place_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    avg_rating = 0.0
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)

    return {
        "reviews": [r.to_dict() for r in reviews],
        "count": len(reviews),
        "average_rating": avg_rating,
    }


@app.post("/api/restaurants/{place_id}/reviews")
async def create_review(
    place_id: str,
    review: ReviewCreate,
    db: Session = Depends(get_db),
):
    # Verify restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.place_id == place_id).first()
    if not restaurant:
        return {"error": "Restaurant not found"}

    new_review = Review(
        restaurant_place_id=place_id,
        reviewer_name=review.reviewer_name,
        rating=review.rating,
        comment=review.comment,
        created_at=datetime.utcnow(),
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return {"review": new_review.to_dict(), "message": "Review submitted!"}
