# NearBites — Find Food Near You, Within Your Budget

A responsive restaurant finder web app that helps you discover nearby restaurants and dishes within your budget. Built with vanilla HTML/CSS/JS frontend and Python FastAPI backend.

## Features

- **Location-based search** — Detect your location or search manually
- **Budget filtering** — Set your per-dish budget (₹50–₹2000)
- **3 result views** — List, Map, and Dish views
- **Dietary filters** — Veg, Non-Veg, Vegan
- **Cuisine filters** — South Indian, North Indian, Chinese, Biryani, and more
- **Restaurant detail pages** — Full menu with budget highlighting
- **User preferences** — Saved to localStorage, auto-applied on searches
- **Responsive** — Mobile, tablet, and desktop layouts
- **10 seeded Chennai restaurants** — Works in demo mode without API keys

## Tech Stack

- **Frontend:** HTML + CSS + Vanilla JavaScript (ES modules)
- **Backend:** Python + FastAPI
- **Database:** SQLite via SQLAlchemy (caching layer)
- **Maps:** Google Maps JavaScript API + Places API (New)

## Project Structure

```
nearBites/
├── backend/
│   ├── main.py           # FastAPI app (3 API endpoints + config)
│   ├── models.py         # SQLAlchemy models (Restaurant, Dish)
│   ├── places.py         # Google Places API (New) wrapper
│   ├── cache.py          # 24-hour cache logic
│   ├── seed_data.py      # 10 Chennai restaurants with menus
│   └── requirements.txt
├── frontend/
│   ├── index.html        # Landing/search page
│   ├── results.html      # Results (List/Map/Dish views)
│   ├── restaurant.html   # Restaurant detail + menu
│   ├── preferences.html  # User preferences
│   ├── css/
│   │   ├── style.css     # Main styles
│   │   └── responsive.css
│   └── js/
│       ├── api.js        # Backend API client
│       ├── map.js        # Google Maps logic
│       ├── filters.js    # Filter state management
│       └── preferences.js # localStorage preferences
├── .env.example
└── README.md
```

## Setup

### 1. Clone and install backend dependencies

```bash
cd nearBites/backend
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp ../.env.example .env
```

Edit `.env` and add your Google API keys (optional — the app works with seed data without them):

```
GOOGLE_PLACES_API_KEY=your_server_side_key_here
GOOGLE_MAPS_JS_API_KEY=your_client_side_key_here
```

### 3. Start the backend server

```bash
cd nearBites/backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. On first run, the database is automatically created and seeded with 10 Chennai restaurants.

### 4. Open the frontend

Open `frontend/index.html` in your browser. You can use any of these methods:

- **VS Code Live Server** — Right-click `index.html` → "Open with Live Server"
- **Python HTTP server** — `cd nearBites/frontend && python -m http.server 5500`
- **Direct file** — Open the file directly in your browser

### 5. Try it out

1. Click "Find Food" on the landing page (defaults to Chennai center)
2. Browse restaurants in List, Map, or Dish view
3. Click a restaurant to see its full menu
4. Set your preferences on the Preferences page

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/config` | GET | Returns client-side Maps API key |
| `/api/restaurants` | GET | Search nearby restaurants (params: lat, lng, radius, budget, cuisine, dietary, open_now) |
| `/api/restaurants/{place_id}` | GET | Restaurant detail with menu (params: budget) |
| `/api/dishes` | GET | All dishes from nearby restaurants under budget |

## Demo Mode

The app ships with 10 seeded Chennai restaurants and 96 dishes across multiple cuisines. No API keys are needed for demo mode — the app automatically falls back to seed data when Google API keys are not configured.
