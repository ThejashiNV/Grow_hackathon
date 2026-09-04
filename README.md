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

A background poller ingests market data, computes anomaly features and attention scores, and caches results in Redis. User requests read from cache/Mongo rather than recomputing on every hit.

## Project structure

```
backend/
  app/
    main.py            FastAPI app, CORS, lifespan wiring
    core/               config, mongo/redis/chroma connections
    api/routes/         REST endpoints
    services/           scoring, diff engine, market data, RAG, news, events
    repositories/       Mongo data access
    models/ schemas/    pydantic models
    workers/            background market poller
  requirements.txt
frontend/
  src/                  React 19 app (Vite)
docker-compose.yml       local MongoDB + Redis
.env.example
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
- **Redis exists to avoid recomputing scores on every request.** A background poller computes anomaly/attention scores once and caches them; user requests are cache reads, so the system doesn't degrade as watchlists grow.
- **Demo mode.** Live market conditions during a 24h window may be boring. A `DEMO_MODE` flag injects a small set of scripted, clearly-labeled scenarios (CEO resignation, sector-relative outperformance, muted earnings reaction, no-change) so the intelligence layer is always demonstrable.

## Status

Foundation (Phase 1) is being wired up: FastAPI + health check + Mongo/Redis/Chroma connections with graceful degradation, React 19 scaffold, docker-compose. Market data, scoring engine, diff engine, and RAG land next.
