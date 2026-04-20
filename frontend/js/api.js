const API_BASE = "http://localhost:8000";

export async function fetchConfig() {
    try {
        const resp = await fetch(`${API_BASE}/api/config`);
        if (!resp.ok) throw new Error(`Config fetch failed: ${resp.status}`);
        return await resp.json();
    } catch (err) {
        console.error("[api.js] fetchConfig error:", err);
        return { maps_api_key: "" };
    }
}

export async function fetchRestaurants(params = {}) {
    try {
        const query = new URLSearchParams();
        if (params.lat != null) query.set("lat", params.lat);
        if (params.lng != null) query.set("lng", params.lng);
        if (params.radius) query.set("radius", params.radius);
        if (params.budget) query.set("budget", params.budget);
        if (params.cuisine) query.set("cuisine", params.cuisine);
        if (params.dietary) query.set("dietary", params.dietary);
        if (params.open_now) query.set("open_now", "true");

        const resp = await fetch(`${API_BASE}/api/restaurants?${query.toString()}`);
        if (!resp.ok) throw new Error(`Restaurants fetch failed: ${resp.status}`);
        return await resp.json();
    } catch (err) {
        console.error("[api.js] fetchRestaurants error:", err);
        return { restaurants: [], count: 0, source: "error" };
    }
}

export async function fetchRestaurantDetail(placeId, budget = 2000) {
    try {
        const query = new URLSearchParams({ budget: budget.toString() });
        const resp = await fetch(`${API_BASE}/api/restaurants/${encodeURIComponent(placeId)}?${query.toString()}`);
        if (!resp.ok) throw new Error(`Restaurant detail fetch failed: ${resp.status}`);
        return await resp.json();
    } catch (err) {
        console.error("[api.js] fetchRestaurantDetail error:", err);
        return null;
    }
}

export async function fetchDishes(params = {}) {
    try {
        const query = new URLSearchParams();
        if (params.lat != null) query.set("lat", params.lat);
        if (params.lng != null) query.set("lng", params.lng);
        if (params.radius) query.set("radius", params.radius);
        if (params.budget) query.set("budget", params.budget);
        if (params.cuisine) query.set("cuisine", params.cuisine);
        if (params.dietary) query.set("dietary", params.dietary);

        const resp = await fetch(`${API_BASE}/api/dishes?${query.toString()}`);
        if (!resp.ok) throw new Error(`Dishes fetch failed: ${resp.status}`);
        return await resp.json();
    } catch (err) {
        console.error("[api.js] fetchDishes error:", err);
        return { dishes: [], count: 0 };
    }
}

export async function fetchReviews(placeId) {
    try {
        const resp = await fetch(`${API_BASE}/api/restaurants/${encodeURIComponent(placeId)}/reviews`);
        if (!resp.ok) throw new Error(`Reviews fetch failed: ${resp.status}`);
        return await resp.json();
    } catch (err) {
        console.error("[api.js] fetchReviews error:", err);
        return { reviews: [], count: 0, average_rating: 0 };
    }
}

export async function submitReview(placeId, reviewData) {
    try {
        const resp = await fetch(`${API_BASE}/api/restaurants/${encodeURIComponent(placeId)}/reviews`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(reviewData),
        });
        if (!resp.ok) throw new Error(`Review submit failed: ${resp.status}`);
        return await resp.json();
    } catch (err) {
        console.error("[api.js] submitReview error:", err);
        return null;
    }
}
