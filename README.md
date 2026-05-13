# WoW Profit Tracker — TBC Classic AH

Full-stack auction house profit tracker for WoW TBC Classic Anniversary realms.

**Features:** flip margin scanner, deal finder, crafting ROI table, recursive buy-vs-craft optimizer, price trend charts, and watchlist with price alerts.

---

## Quick Start

### 1. Configure your TSM API key

```bash
cp .env.example .env
# Edit .env and set TSM_API_KEY=<your key>
# Get your key at: https://id.tradeskillmaster.com/realms/app/account
```

### 2. Set your realm

In `.env`, set:
```
DEFAULT_REALM=faerlina   # or your realm
DEFAULT_FACTION=horde    # or alliance
```

### 3. Start everything

```bash
docker compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API docs:** http://localhost:8000/docs

---

## Local Dev (without Docker)

### Backend

```bash
cd backend
pip install uv
uv pip install -e .

# Start Postgres and Redis manually or via docker:
docker compose up postgres redis -d

export DATABASE_URL=postgresql+asyncpg://ahtracker:ahtracker@localhost:5432/ah_tracker
export REDIS_URL=redis://localhost:6379
# ... other env vars from .env

uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Architecture

```
frontend (React/Vite :5173)
    ↓ /api proxy
backend (FastAPI :8000)
    ├── TSMService      OAuth2 token refresh, bulk AH fetch (1 req/hr), cached in Redis
    ├── NexusHubService deals, crafting, history (no auth, 20 req/5s)
    ├── ItemDbService   static item metadata from data/items.json + WoWHead fallback
    └── Scheduler       hourly price snapshots written to PostgreSQL
```

## Seed Data

- `data/items.json` — item metadata (name, quality, vendor price). Add more items here.
- `data/recipes.json` — TBC crafting recipes used by the recursive optimizer. Seeded to DB on first startup.

To add more recipes, follow the format:
```json
{
  "outputItemId": 12345,
  "outputQty": 1,
  "profession": "Alchemy",
  "skillRequired": 300,
  "source": "trainer",
  "mats": [
    {"itemId": 22785, "qty": 3},
    {"itemId": 22337, "qty": 1}
  ]
}
```

## Notes

- **Blizzard Classic AH API is broken** — app uses TSM + NexusHub only.
- TSM bulk fetch runs once per hour. First load after startup may be slower.
- Price history accumulates over time via hourly snapshots. Trend charts will be sparse initially.
- NexusHub may not index newer Anniversary realms — deals/crafting will fall back gracefully.
- AH cut: 5% (factored into all flip profit calculations).
