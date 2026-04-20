import { getPreferences } from './preferences.js';

export function getUrlParams() {
    return Object.fromEntries(new URLSearchParams(window.location.search));
}

export function updateUrlParams(params) {
    const url = new URL(window.location);
    for (const [key, value] of Object.entries(params)) {
        if (value === "" || value === null || value === undefined || value === false) {
            url.searchParams.delete(key);
        } else {
            url.searchParams.set(key, value);
        }
    }
    history.replaceState(null, "", url.toString());
}

export function getActiveFilters() {
    const params = getUrlParams();
    return {
        lat: parseFloat(params.lat) || null,
        lng: parseFloat(params.lng) || null,
        radius: parseInt(params.radius) || 15000,
        budget: parseInt(params.budget) || 500,
        cuisine: params.cuisine || "",
        dietary: params.dietary || "",
        open_now: params.open_now === "true",
        location_name: params.location_name || "",
    };
}

export function applyFiltersFromPreferences() {
    const prefs = getPreferences();
    const params = getUrlParams();

    // Only apply defaults if no URL params exist
    if (!params.budget) {
        updateUrlParams({ budget: prefs.defaultBudget });
    }
    if (!params.radius) {
        updateUrlParams({ radius: prefs.defaultRadius });
    }
    if (!params.cuisine && prefs.defaultCuisines.length > 0) {
        updateUrlParams({ cuisine: prefs.defaultCuisines.join(",") });
    }
    if (!params.dietary && prefs.defaultDietary) {
        updateUrlParams({ dietary: prefs.defaultDietary });
    }
}

export function buildSearchUrl(params) {
    const url = new URL("results.html", window.location.href);
    for (const [key, value] of Object.entries(params)) {
        if (value !== "" && value !== null && value !== undefined && value !== false) {
            url.searchParams.set(key, value);
        }
    }
    return url.toString();
}

export function initFilterUI(containerId, onChange) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const filters = getActiveFilters();

    // Budget slider
    const budgetSlider = container.querySelector("#filter-budget");
    const budgetValue = container.querySelector("#filter-budget-value");
    if (budgetSlider) {
        budgetSlider.value = filters.budget;
        if (budgetValue) budgetValue.textContent = `₹${filters.budget}`;
        budgetSlider.addEventListener("input", () => {
            if (budgetValue) budgetValue.textContent = `₹${budgetSlider.value}`;
            updateUrlParams({ budget: budgetSlider.value });
            onChange();
        });
    }

    // Radius slider
    const radiusSlider = container.querySelector("#filter-radius");
    const radiusValue = container.querySelector("#filter-radius-value");
    if (radiusSlider) {
        radiusSlider.value = filters.radius;
        if (radiusValue) radiusValue.textContent = `${(filters.radius / 1000).toFixed(1)} km`;
        radiusSlider.addEventListener("input", () => {
            if (radiusValue) radiusValue.textContent = `${(radiusSlider.value / 1000).toFixed(1)} km`;
            updateUrlParams({ radius: radiusSlider.value });
            onChange();
        });
    }

    // Dietary chips
    container.querySelectorAll("[data-dietary]").forEach(chip => {
        if (chip.dataset.dietary === filters.dietary) {
            chip.classList.add("active");
        }
        chip.addEventListener("click", () => {
            container.querySelectorAll("[data-dietary]").forEach(c => c.classList.remove("active"));
            if (chip.dataset.dietary === filters.dietary) {
                updateUrlParams({ dietary: "" });
            } else {
                chip.classList.add("active");
                updateUrlParams({ dietary: chip.dataset.dietary });
            }
            onChange();
        });
    });

    // Cuisine chips
    const activeCuisines = filters.cuisine ? filters.cuisine.split(",") : [];
    container.querySelectorAll("[data-cuisine]").forEach(chip => {
        if (activeCuisines.includes(chip.dataset.cuisine)) {
            chip.classList.add("active");
        }
        chip.addEventListener("click", () => {
            chip.classList.toggle("active");
            const selected = Array.from(container.querySelectorAll("[data-cuisine].active"))
                .map(c => c.dataset.cuisine);
            updateUrlParams({ cuisine: selected.join(",") });
            onChange();
        });
    });

    // Open now toggle
    const openNowToggle = container.querySelector("#filter-open-now");
    if (openNowToggle) {
        openNowToggle.checked = filters.open_now;
        openNowToggle.addEventListener("change", () => {
            updateUrlParams({ open_now: openNowToggle.checked ? "true" : "" });
            onChange();
        });
    }
}
