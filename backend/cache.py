import math
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from models import Dish, Restaurant

CACHE_DURATION_HOURS = 24


def _grid_key(lat, lng):
    """Round lat/lng to 3 decimal places (~110m precision) for cache grouping."""
    return round(lat, 3), round(lng, 3)


def _is_fresh(cached_at: datetime) -> bool:
    """Check if a cached record is less than 24 hours old."""
    if cached_at is None:
        return False
    return datetime.utcnow() - cached_at < timedelta(hours=CACHE_DURATION_HOURS)


def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters between two lat/lng points."""
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_cached_restaurants(db: Session, lat: float, lng: float, radius: float) -> Optional[List[Restaurant]]:
    """Return cached restaurants within radius if cache is fresh. Returns None on cache miss."""
    restaurants = db.query(Restaurant).all()
    if not restaurants:
        return None

    nearby = []
    for r in restaurants:
        dist = _haversine_distance(lat, lng, r.lat, r.lng)
        if dist <= radius and _is_fresh(r.cached_at):
            nearby.append(r)

    return nearby if nearby else None


def get_cached_restaurant_detail(db: Session, place_id: str) -> Optional[Restaurant]:
    """Return a single cached restaurant with dishes if cache is fresh."""
    restaurant = db.query(Restaurant).filter(Restaurant.place_id == place_id).first()
    if restaurant and _is_fresh(restaurant.cached_at):
        return restaurant
    return None


def cache_restaurants(db: Session, restaurants_data: List[dict]) -> List[Restaurant]:
    """Upsert restaurants and their dishes into the cache."""
    cached = []
    for data in restaurants_data:
        dishes_data = data.pop("dishes", [])

        existing = db.query(Restaurant).filter(Restaurant.place_id == data["place_id"]).first()
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            existing.cached_at = datetime.utcnow()
            # Replace dishes
            db.query(Dish).filter(Dish.restaurant_place_id == existing.place_id).delete()
            restaurant = existing
        else:
            restaurant = Restaurant(**data, cached_at=datetime.utcnow())
            db.add(restaurant)

        for dish_data in dishes_data:
            dish = Dish(restaurant_place_id=restaurant.place_id, **dish_data)
            db.add(dish)

        cached.append(restaurant)

    db.commit()
    return cached


def invalidate_stale_cache(db: Session) -> int:
    """Delete restaurants (and cascade dishes) older than 24 hours. Returns count deleted."""
    cutoff = datetime.utcnow() - timedelta(hours=CACHE_DURATION_HOURS)
    stale = db.query(Restaurant).filter(
        Restaurant.cached_at < cutoff,
        ~Restaurant.place_id.startswith("seed_"),  # Never delete seed data
    ).all()
    count = len(stale)
    for r in stale:
        db.delete(r)
    if count:
        db.commit()
    return count
