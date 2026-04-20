import os
from typing import Dict, List, Optional

import httpx

NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"
PLACE_DETAILS_URL = "https://places.googleapis.com/v1/places"


async def search_nearby(lat: float, lng: float, radius: float, api_key: Optional[str] = None) -> List[dict]:
    """Search for nearby restaurants using Google Places API (New).

    Returns a list of restaurant dicts ready for caching, or empty list on failure.
    """
    key = api_key or os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not key:
        return []

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.priceLevel,"
            "places.currentOpeningHours,places.nationalPhoneNumber,"
            "places.photos,places.types"
        ),
    }

    body = {
        "includedTypes": ["restaurant", "cafe", "meal_delivery", "meal_takeaway"],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius,
            }
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(NEARBY_SEARCH_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, Exception) as e:
        print(f"[places.py] Nearby search failed: {e}")
        return []

    restaurants = []
    for place in data.get("places", []):
        price_map = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4,
        }

        # Extract cuisine tags from types
        cuisine_types = [t for t in place.get("types", []) if t not in (
            "restaurant", "cafe", "food", "point_of_interest", "establishment",
            "meal_delivery", "meal_takeaway", "store",
        )]

        photo_url = ""
        photos = place.get("photos", [])
        if photos:
            photo_name = photos[0].get("name", "")
            if photo_name:
                photo_url = (
                    f"https://places.googleapis.com/v1/{photo_name}/media"
                    f"?maxHeightPx=400&maxWidthPx=600&key={key}"
                )

        is_open = True
        opening_hours = place.get("currentOpeningHours", {})
        if "openNow" in opening_hours:
            is_open = opening_hours["openNow"]

        restaurants.append({
            "place_id": place.get("id", ""),
            "name": place.get("displayName", {}).get("text", "Unknown"),
            "address": place.get("formattedAddress", ""),
            "lat": place.get("location", {}).get("latitude", 0),
            "lng": place.get("location", {}).get("longitude", 0),
            "rating": place.get("rating", 0),
            "price_level": price_map.get(place.get("priceLevel", ""), 2),
            "cuisine_tags": ",".join(cuisine_types),
            "is_open": is_open,
            "phone": place.get("nationalPhoneNumber", ""),
            "photo_url": photo_url,
            "dishes": [],  # Google Places doesn't provide menu data
        })

    return restaurants


async def get_place_details(place_id: str, api_key: Optional[str] = None) -> Optional[dict]:
    """Get detailed info for a single place using Google Places API (New).

    Returns a restaurant dict or None on failure.
    """
    key = api_key or os.getenv("GOOGLE_PLACES_API_KEY", "")
    if not key:
        return None

    headers = {
        "X-Goog-Api-Key": key,
        "X-Goog-FieldMask": (
            "id,displayName,formattedAddress,location,rating,priceLevel,"
            "currentOpeningHours,nationalPhoneNumber,photos,types,"
            "editorialSummary,websiteUri"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{PLACE_DETAILS_URL}/{place_id}", headers=headers)
            resp.raise_for_status()
            place = resp.json()
    except (httpx.HTTPError, Exception) as e:
        print(f"[places.py] Place details failed for {place_id}: {e}")
        return None

    price_map = {
        "PRICE_LEVEL_FREE": 0,
        "PRICE_LEVEL_INEXPENSIVE": 1,
        "PRICE_LEVEL_MODERATE": 2,
        "PRICE_LEVEL_EXPENSIVE": 3,
        "PRICE_LEVEL_VERY_EXPENSIVE": 4,
    }

    cuisine_types = [t for t in place.get("types", []) if t not in (
        "restaurant", "cafe", "food", "point_of_interest", "establishment",
        "meal_delivery", "meal_takeaway", "store",
    )]

    photo_url = ""
    photos = place.get("photos", [])
    if photos:
        photo_name = photos[0].get("name", "")
        if photo_name:
            photo_url = (
                f"https://places.googleapis.com/v1/{photo_name}/media"
                f"?maxHeightPx=400&maxWidthPx=600&key={key}"
            )

    return {
        "place_id": place.get("id", place_id),
        "name": place.get("displayName", {}).get("text", "Unknown"),
        "address": place.get("formattedAddress", ""),
        "lat": place.get("location", {}).get("latitude", 0),
        "lng": place.get("location", {}).get("longitude", 0),
        "rating": place.get("rating", 0),
        "price_level": price_map.get(place.get("priceLevel", ""), 2),
        "cuisine_tags": ",".join(cuisine_types),
        "is_open": place.get("currentOpeningHours", {}).get("openNow", True),
        "phone": place.get("nationalPhoneNumber", ""),
        "photo_url": photo_url,
        "dishes": [],
    }
