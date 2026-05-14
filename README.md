# WoW Profit Tracker — TBC Classic AH

Full-stack auction house profit tracker for WoW TBC Classic (including Anniversary realms).  
Data comes entirely from your own Auctionator scans — no third-party API keys required.

**Features:** flip opportunity scanner, deal finder, crafting ROI table, recursive buy-vs-craft optimizer, price trend charts, watchlist with price alerts.

---

## Quick Start

```bash
docker compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000/docs

That's it. No API keys, no configuration required.

---

## How to get data

1. Install the **Auctionator** addon in WoW (Classic/TBC).
2. Open the Auction House in-game and click **Full Scan** (or type `/atr scan`).
3. Wait ~30 seconds for the scan to complete.
4. Type `/reload` or log out to flush data to disk.
5. Find your file:
   - **Mac:** `~/Library/Application Support/World of Warcraft/_classic_/WTF/Account/<ACCOUNT>/SavedVariables/Auctionator.lua`
   - **Windows:** `C:\Program Files (x86)\World of Warcraft\_classic_\WTF\Account\<ACCOUNT>\SavedVariables\Auctionator.lua`
6. Go to **Upload Scan** in the app and drop the file.

After upload, item names and icons are automatically fetched from Wowhead in the background (~1-2 minutes for a full scan). Flip opportunities build up after multiple scans over time.

---

## Architecture

```
frontend (React/Vite :5173)
    ↓ /api proxy
backend (FastAPI :8000)
    ├── LuaParserService   Auctionator.lua parser — supports v2 (Lua tables) and
    │                      v8 (LibCBOR binary blobs). Extracts item_id → price maps.
    ├── IngestService      Writes price snapshots to PostgreSQL on each upload
    ├── SeedingService     Background Wowhead fetcher — fills items table with
    │                      names, icons, quality after each upload
    ├── PricingService     14-day rolling market value via SQL CTEs
    ├── ItemDbService      In-memory item cache loaded from items table on startup,
    │                      with per-item Wowhead fallback for detail views
    └── PostgreSQL         price_snapshots, items, recipes, upload_logs, watchlist
```

### Price data flow

```
Auctionator.lua upload
    → parse binary CBOR blob (v8) or Lua table (v2)
    → extract {realm: {faction: {item_id: min_buyout_copper}}}
    → bulk insert into price_snapshots
    → trigger background seeding (Wowhead → items table)
    → market_value = 14-day rolling avg of daily MIN(min_buyout)
```

---

## Local Dev (without Docker)

### Backend

```bash
cd backend
pip install uv
uv pip install -e .

# Start Postgres and Redis via docker
docker compose up postgres redis -d

export DATABASE_URL=postgresql+asyncpg://ahtracker:ahtracker@localhost:5432/ah_tracker
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Seed Data

- `data/recipes.json` — TBC crafting recipes used by the recursive buy-vs-craft optimizer. Seeded to the DB on first startup.
- `data/items.json` — small bootstrap item list (loaded on first startup before Wowhead seeding completes). The `items` database table is the live source after first upload.

### Adding recipes

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

---

## Notes

- **Flip opportunities** require multiple scans over different days to build price history. A single scan shows market_value = min_buyout (no historical comparison yet).
- **AH cut:** 5% is factored into all flip profit and ROI calculations.
- **Item names** are seeded automatically after each upload via `nether.wowhead.com`. The first upload seeds ~8,000+ items in about 2 minutes.
- **Multiple scans:** each upload adds a new snapshot. The 14-day rolling average improves as history accumulates. Re-uploading the same scan is safe (adds another snapshot at the current timestamp).
- Supports both **Auctionator v2** (older format, item names as keys) and **v8** (current format, LibCBOR binary blobs with item IDs).
