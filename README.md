# Smart Market Watchlist

A market watchlist that isn't a price tracker — it's a diff engine with memory. It tells you what changed in your watchlist since you last checked, whether the change was unusual, why it might matter, and whether its own past signals held up.

Built for Groww CODE 2026.

## Core idea

```
Your watchlist -> your last-seen state -> what's changed? -> was it unusual? -> why? -> does it matter? -> remember it
```

Instead of a flat price table, the primary screen is a **triage inbox**: stocks ranked by an `attention_score` built from three separable concepts — **Surprise** (how unusual the move is, statistically), **Impact** (how important the underlying event is), and **Confidence** (how reliable the evidence is).

## Architecture

```
React 19 (Vite) --REST--> FastAPI --> MongoDB (user state, history)
                                   --> Redis (computed scores, cache)
                                   --> ChromaDB (headline embeddings, dedup, RAG)
                                   --> yfinance (market data, news)
                                   --> Gemini (grounded Ask-Why RAG, optional)
```

Each computed `ChangeBundle` (price/volume/sector anomaly + classified events + Surprise/Impact/Confidence/Attention scores) is cached in Redis for 90 seconds, keyed by symbol. A request within that window is a cache read, not a recompute — this also keeps the news-novelty/dedup step consistent: without it, viewing the same stock twice would make ChromaDB see the same headline twice and mark it "already seen" before the user had actually seen it once. (A dedicated background poller that refreshes the cache proactively rather than on first request is the natural next step for scaling past a handful of concurrent users — see Known limitations below.)

## Project structure

```
backend/
  app/
    main.py              FastAPI app, CORS, lifespan wiring
    core/                config, session (cookie auth), mongo/redis/chroma connections
    api/routes/          health, stocks, changes, attention, watchlist, state, ask
    services/            scoring, diff engine, market data, sector, event
                         classifier, novelty/dedup, RAG, change bundle orchestration
    repositories/        Mongo data access (watchlist, stock state)
    schemas/             pydantic models (market, events, scoring, attention, rag, ...)
    utils/               hardcoded sector map
  tests/                 unit tests (scoring, event classifier, diff engine)
  requirements.txt
frontend/
  src/
    pages/               AttentionPage, WatchlistPage
    components/          ChangeCard (the flagship card)
    services/ types/      API client, TS types mirroring backend schemas
docker-compose.yml       local MongoDB + Redis
.env.example
```

## API endpoints

```
GET    /api/health
GET    /api/stocks/{symbol}                 live quote
GET    /api/stocks/{symbol}/history
GET    /api/stocks/{symbol}/events           raw news
POST   /api/stocks/{symbol}/seen             mark as seen (server-side memory)
GET    /api/changes/{symbol}                 one ChangeBundle
GET    /api/changes                          ChangeBundles for the whole watchlist
GET    /api/attention                        the triage inbox (ranked, diffed, sector-wide flagged)
GET    /api/watchlist
POST   /api/watchlist/stocks
DELETE /api/watchlist/stocks/{symbol}
POST   /api/ask                              grounded Ask-Why RAG
```

## Local setup

### Prerequisites
- Python 3.11+
- Node 18+
- Docker Desktop (for local MongoDB/Redis) — optional if you point `.env` at MongoDB Atlas / a managed Redis instead

### 1. Environment
```bash
cp .env.example .env
```
Fill in `GEMINI_API_KEY` if you want live AI answers in Ask-Why (otherwise it runs in a grounded-fallback mode using only structured evidence, no LLM). Everything else works with the defaults.

### 2. Infrastructure
```bash
docker compose up -d
```
Starts MongoDB and Redis on their default ports. ChromaDB runs embedded (no container) and persists to `backend/chroma_data/`.

### 3. Backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Check `http://localhost:8000/api/health` — each service reports `ok`, `unavailable`, or `not_configured`. The app runs even if Mongo/Redis/Chroma/LLM are down; features that need them degrade instead of crashing.

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs at `http://localhost:5173`.

## Design decisions (for judges)

- **No fixed % threshold.** A move is scored by how many standard deviations it is from *that stock's own* historical daily volatility (z-score), not a global cutoff — 2% is huge for a stable bank stock and noise for a volatile small-cap.
- **Surprise / Impact / Confidence are separate scores.** A stock can move a lot for no real reason (high surprise, low impact) or move very little despite major news (low surprise, high impact — the "silence signal"). Collapsing these into one number loses that distinction.
- **Server-side memory is the source of truth.** `last_seen_price/volume/score` live in MongoDB per user per symbol, not localStorage, so watchlists and "what changed since you checked" work identically across devices.
- **News dedup via embeddings.** Ten articles about the same CEO resignation should be one event, not ten alerts — headlines are embedded (`all-MiniLM-L6-v2`) and clustered by cosine similarity in ChromaDB before they reach the scoring layer.
- **RAG is grounded, not free-floating.** The Ask-Why LLM prompt is only ever given structured evidence (current/previous state, score components, headlines, sector move, data freshness) and is instructed to say when evidence is insufficient rather than invent a causal story.
- **Redis exists to avoid recomputing scores on every request**, and to keep one computed bundle authoritative for a window of time so different endpoints (`/attention`, `/changes/{symbol}`, `/seen`) agree on what the user actually saw, instead of each independently recomputing (and each recompute silently mutating ChromaDB's dedup state).
- **The core product works with no AI configured.** `GEMINI_API_KEY` unset -> Ask-Why falls back to a deterministic, evidence-only summary instead of failing. yfinance/Mongo/Redis/Chroma down -> each degrades independently (`/api/health` reports per-service status) rather than taking the whole app down.
- **Sector-wide vs company-specific.** If >=2 watchlist stocks share a sector, both moved *with* the sector (low sector-relative-divergence score) rather than against it, and the sector itself moved meaningfully, they're flagged `sector_wide` — so five correlated stocks don't generate five independent-looking alerts.

## Judge questions

**What makes this different from a normal watchlist?** It doesn't show current state — it diffs current state against *this user's* last-seen state (server-side, MongoDB) and ranks by how unusual + important + reliable the change is, not just whether price moved.

**Why no fixed 2%/5% threshold?** `price_anomaly` is a z-score against that stock's own trailing 30-day daily-return volatility (`app/services/scoring.py`). The same 2% move scores very differently for a stable bank stock vs a volatile small-cap, because the denominator is stock-specific.

**How do you know a movement is unusual?** Three independent signals feed `Surprise`: price z-score, log-normalized volume ratio vs 20-day average, and divergence from the stock's sector move — combined, not any single one.

**How do you avoid duplicate news alerts?** Headlines are embedded (`all-MiniLM-L6-v2`) and compared against previously-stored embeddings for that symbol in ChromaDB (`novelty_service.py`). A near-duplicate (distance below threshold) is marked as the same event, not a new signal.

**How does the system know what the user already saw?** `StockState` in MongoDB, keyed by `(user_id, symbol)` — never localStorage. The same watchlist and diff state show up from any device with the session cookie.

**What happens when data is delayed or a source fails?** Every `ChangeBundle` carries `is_delayed`/`data_ok`/`confidence_factors`; a failed yfinance call returns a bundle with `data_ok:false` and a clear reason rather than fabricated numbers. `/api/health` exposes per-service status (`ok`/`unavailable`/`not_configured`) so failures are visible, not silent.

**Why is a muted reaction meaningful?** A high-impact event (e.g. earnings) with an unusually small price_anomaly score gets a "Silence signal" explain chip — big news, no reaction, is itself informative and is exactly the kind of thing a flat price-mover list would miss.

**How do you stop the LLM from hallucinating?** The RAG prompt (`rag_service.py`) is built entirely from structured evidence already computed deterministically (score components, headlines, sector move, confidence factors) and is explicitly instructed not to invent facts, to separate observation from interpretation, and to say when evidence is insufficient. The LLM is never asked to produce a price, a fact, or an event — only to narrate evidence it's handed.

**Why Redis, why ChromaDB?** Redis: avoid recomputing the whole scoring pipeline (market fetch + news fetch + embeddings + classification) on every request, and keep one bundle's numbers consistent across a user session. ChromaDB: semantic similarity is the only reliable way to tell "this headline is the same underlying event as one we already showed" from "this is genuinely new" — string matching doesn't work for that.

**How does this scale to more users/larger watchlists?** The scoring pipeline is already decoupled from the request path via the Redis cache; the natural next step (not yet built) is a background poller that refreshes bundles proactively for a fixed universe of symbols instead of computing lazily on first request per user — see below.

## Known limitations / not yet built

- **No dedicated background poller.** Bundles are computed on first request and cached for 90s, not proactively refreshed on a schedule (Part 22/30's ideal). Fine for a hackathon demo; the fix under load is a `workers/market_poller.py` that walks the union of all watchlisted symbols on an interval.
- **No demo-mode scripted scenarios yet.** If live market conditions are quiet during judging, the triage inbox may legitimately show "nothing meaningful changed" for the whole watchlist — which is the intended behavior, but less visually dramatic for a 2-minute demo. `DEMO_MODE` is stubbed in `.env.example` but unimplemented.
- **No history/timeline view.** Only the current triage inbox and watchlist screens exist; a per-stock timeline of past changes (Part 29) would need change bundles persisted to MongoDB over time (currently only cached in Redis, not archived).
- **yfinance news for NSE tickers is often generic/syndicated** rather than company-specific (confirmed while testing) — the event classifier and confidence scoring are built assuming this, but a dedicated news API would improve headline relevance if one becomes available.

## Status

Phases 1-6 are complete and verified live: foundation, yfinance market data layer, the Surprise/Impact/Confidence scoring engine, server-side memory + diff engine, the triage inbox UI, and grounded Ask-Why RAG (LLM-backed when `GEMINI_API_KEY` is set, deterministic fallback otherwise). 17 backend unit tests passing.
