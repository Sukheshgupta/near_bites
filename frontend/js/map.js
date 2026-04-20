// Leaflet.js map module — no API key required

let leafletLoaded = false;

async function loadLeaflet() {
    if (leafletLoaded) return;

    // Check if already injected
    if (document.querySelector('link[href*="leaflet"]')) {
        leafletLoaded = true;
        return;
    }

    // CSS
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    document.head.appendChild(css);

    // JS
    await new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });

    leafletLoaded = true;
}

export async function initializeMap(containerId, center = { lat: 13.0827, lng: 80.2707 }, zoom = 13) {
    await loadLeaflet();

    const container = document.getElementById(containerId);
    if (!container || typeof L === "undefined") {
        console.warn("[map.js] Cannot init map — container or Leaflet missing");
        return null;
    }

    // Prevent re-init on same container
    if (container._leaflet_id) {
        container._leafletMap.remove();
    }

    const map = L.map(containerId).setView([center.lat, center.lng], zoom);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
    }).addTo(map);

    // Store reference for re-init guard
    container._leafletMap = map;

    return map;
}

export function addMarkers(map, restaurants, budget = 2000) {
    if (!map || typeof L === "undefined") return [];

    const markers = [];

    // Custom orange marker icon
    const orangeIcon = L.divIcon({
        className: "custom-marker",
        html: `<div style="
            width:24px;height:24px;border-radius:50%;
            background:#FF5722;border:3px solid white;
            box-shadow:0 2px 6px rgba(0,0,0,0.3);
        "></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -14],
    });

    restaurants.forEach(r => {
        const tags = (r.cuisine_tags || [])
            .map(t => `<span style="background:#FFF3E0;color:#E65100;padding:2px 6px;border-radius:4px;font-size:0.7rem;margin-right:4px">${t}</span>`)
            .join("");

        const popupHtml = `
            <div style="min-width:200px;font-family:Inter,sans-serif">
                <h4 style="margin:0 0 4px;font-size:1rem">${r.name}</h4>
                <p style="margin:0 0 4px;font-size:0.8rem;color:#666">${r.address || ""}</p>
                <p style="margin:0 0 4px;font-size:0.85rem">
                    <span style="color:#FFC107">★</span> ${r.rating || "N/A"}
                    &nbsp;·&nbsp; ${r.distance_km || "?"} km
                </p>
                <div style="margin:4px 0">${tags}</div>
                ${r.dishes_under_budget != null ? `<p style="margin:4px 0 0;font-weight:600;color:#2E7D32;font-size:0.85rem">${r.dishes_under_budget} dishes under ₹${budget}</p>` : ""}
                <a href="restaurant.html?place_id=${encodeURIComponent(r.place_id)}&budget=${budget}"
                   style="display:inline-block;margin-top:8px;padding:6px 12px;background:#FF5722;color:white;border-radius:6px;text-decoration:none;font-size:0.8rem;font-weight:600">
                    View Menu
                </a>
            </div>
        `;

        const marker = L.marker([r.lat, r.lng], { icon: orangeIcon })
            .addTo(map)
            .bindPopup(popupHtml);

        markers.push(marker);
    });

    // Fit bounds if multiple markers
    if (markers.length > 1) {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }

    return markers;
}

export function showSingleMarker(map, lat, lng, name) {
    if (!map || typeof L === "undefined") return null;

    const orangeIcon = L.divIcon({
        className: "custom-marker",
        html: `<div style="
            width:28px;height:28px;border-radius:50%;
            background:#FF5722;border:3px solid white;
            box-shadow:0 2px 8px rgba(0,0,0,0.3);
        "></div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -16],
    });

    const marker = L.marker([lat, lng], { icon: orangeIcon })
        .addTo(map)
        .bindPopup(`<strong>${name}</strong>`)
        .openPopup();

    map.setView([lat, lng], 16);

    return marker;
}

export async function initAutocomplete(inputId) {
    // No autocomplete without Google Maps API — just return null
    // Location detection via browser geolocation still works
    return null;
}

export async function loadGoogleMaps() {
    // Compatibility stub — Leaflet replaces Google Maps
    return;
}
