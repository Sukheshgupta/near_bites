const STORAGE_KEY = "nearbites_preferences";

const DEFAULTS = {
    defaultBudget: 500,
    defaultRadius: 15000,
    defaultCuisines: [],
    defaultDietary: "",
    allergens: [],
    spiceLevel: 3,
};

export function getPreferences() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return { ...DEFAULTS };
        return { ...DEFAULTS, ...JSON.parse(stored) };
    } catch {
        return { ...DEFAULTS };
    }
}

export function savePreferences(prefs) {
    const merged = { ...DEFAULTS, ...prefs };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
    return merged;
}

export function resetPreferences() {
    localStorage.removeItem(STORAGE_KEY);
    return { ...DEFAULTS };
}

export function showToast(message, duration = 2500) {
    let toast = document.getElementById("toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "toast";
        toast.className = "toast";
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), duration);
}
