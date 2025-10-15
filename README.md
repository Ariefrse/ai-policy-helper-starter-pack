<video src="ai-policy-helper-demo-title.mp4" controls width="600">
  
</video>

# AI Policy & Product Helper

A local-first RAG starter with **FastAPI** (backend), **Next.js** (frontend), and **Qdrant** (vector DB). Runs with one command using Docker Compose.


## Quick start

1) **Copy `.env.example` → `.env`** and edit as needed.

2) **Run everything**:
```bash
docker compose up --build
```
- Frontend: http://localhost:3000  
- If port 3000 is busy, set `FRONTEND_PORT` in `.env` (e.g., `FRONTEND_PORT=3001`) and access `http://localhost:3001`.
- Backend:  http://localhost:8000/docs  
- Qdrant:   http://localhost:6333 (UI)
 

3) **Ingest sample docs** (from the UI Admin tab) or:
```bash
curl -X POST http://localhost:8000/api/ingest
```

4) **Ask a question**:
```bash
curl -X POST http://localhost:8000/api/ask -H 'Content-Type: application/json' \
  -d '{"query":"What’s the shipping SLA to East Malaysia for bulky items?"}'
```

## Offline-friendly
- If you **don’t** set an API key, the backend uses a **deterministic stub LLM** and a **built-in embedding** to keep everything fully local.
- If you set `OPENAI_API_KEY` (or configure Ollama), the backend will use real models automatically.

## Project layout
```
ai-policy-helper/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # FastAPI app + endpoints (with deduplication & categorization)
│  │  ├─ settings.py             # config/env
│  │  ├─ orchestrator.py         # RAG engine orchestrator with metrics & service health
│  │  ├─ embeddings.py           # Local embedding implementation (deterministic hashing)
│  │  ├─ vector_store.py         # Qdrant + InMemory store with fallback
│  │  ├─ llm_providers.py        # OpenAI + Stub LLM with deduplication logic
│  │  ├─ ingest.py               # doc loader & chunker
│  │  ├─ utils.py                # Utility functions (retry logic, etc.)
│  │  ├─ rag.py                  # Backward compatibility wrapper
│  │  ├─ models.py               # pydantic models
│  │  ├─ __init__.py
│  │  └─ tests/
│  │     ├─ conftest.py
│  │     ├─ test_api.py           # API endpoint tests
│  │     ├─ test_acceptance.py    # Acceptance criteria tests
│  │     └─ test_end_to_end.py   # End-to-end integration tests
│  ├─ requirements.txt
│  └─ Dockerfile
├─ frontend/
│  ├─ app/
│  │  ├─ page.tsx                # chat UI
│  │  ├─ layout.tsx
│  │  └─ globals.css
│  ├─ components/
│  │  ├─ Chat.tsx                # Enhanced chat with deduplication & categorization display
│  │  └─ AdminPanel.tsx          # Admin panel for ingestion & metrics
│  ├─ lib/api.ts                 # API client
│  ├─ package.json
│  ├─ tsconfig.json
│  ├─ next.config.js
│  ├─ next-env.d.ts              # Next.js type definitions
│  └─ Dockerfile
├─ data/                         # sample policy docs
│  ├─ Compliance_Notes.md
│  ├─ Delivery_and_Shipping.md
│  ├─ Internal_SOP_Agent_Guide.md
│  ├─ Product_Catalog.md
│  ├─ Returns_and_Refunds.md
│  └─ Warranty_Policy.md
├─ docs/                         # Additional documentation
│  ├─ DEVELOPER_GUIDE.md         # Developer setup guide
│  ├─ DEPLOYMENT.md              # Production deployment guide
│  └─ API_PLAYGROUND.md          # Interactive API testing
├─ docker-compose.yml            # Removed obsolete version attribute
├─ Makefile
├─ .env.example
└── .gitignore                    # Proper gitignore for security
```

## Tests
Run all tests inside the backend container:
```bash
docker compose run --rm -v ./data:/app/data:ro backend pytest -q
```

**Test Coverage:**
- **Unit tests**: API endpoints, models validation (3 tests)
- **Integration tests**: End-to-end RAG pipeline, citation accuracy, performance benchmarks (4 tests)
- **Acceptance tests**: Acceptance criteria validation (2 tests)
- **Total**: 9 tests covering functionality, performance, and error handling

Run specific test suites:
```bash
# API and unit tests only
docker compose run --rm -v ./data:/app/data:ro backend pytest app/tests/test_api.py -v

# End-to-end integration tests
docker compose run --rm -v ./data:/app/data:ro backend pytest app/tests/test_end_to_end.py -v

# Acceptance criteria tests
docker compose run --rm -v ./data:/app/data:ro backend pytest app/tests/test_acceptance.py -v
```

## Performance Benchmarks

**System Performance (measured on local development):**
- **Retrieval Latency**: ~12ms average (local embeddings)
- **Generation Latency**: ~2.7s average (OpenAI gpt-4o-mini API)  
- **Memory Usage**: Bounded at 1000 retrieval + 500 generation cache entries
- **Throughput**: Handles concurrent requests with thread-safe operations
- **Cache Hit Rates**: Improves performance for repeated queries

**Production Considerations Implemented:**
- 🔒 **Security**: Input validation (1-1000 chars), API key protection, environment-specific CORS
- 🚀 **Performance**: LRU caching with bounded memory, deterministic local embeddings
- 🔍 **Observability**: Structured logging, comprehensive metrics collection, health endpoints
- 🛡️ **Reliability**: Error handling with LLM fallbacks, thread-safe vector operations, graceful degradation

## Notes
- Keep it simple. For take-home, focus on correctness, citations, and clean code.

## Architecture (ASCII)

```
┌─────────────────┐    HTTP/3001    ┌──────────────────────┐
│   User Browser  │ ──────────────> │    Next.js Frontend  │
└─────────────────┘                 │  ┌─ Chat Component    │
                                    │  └─ Admin Panel      │
                                    └──────────┬───────────┘
                                               │ fetch /api/*
                                               ▼ HTTP/8000
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                              │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│  │  Input Validation│   │  Error Handling │   │  CORS Config  │  │
│  │  ├─ Pydantic     │   │  ├─ Structured  │   │  ├─ Dev: local │  │
│  │  ├─ XSS Filter   │   │  │   Logging    │   │  └─ Prod: env │  │
│  │  └─ Length Limit │   │  └─ Fallbacks   │   └───────────────┘  │
│  └─────────────────┘   └─────────────────┘                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    RAG Engine                               │ │
│  │  ┌──────────────┐ ┌─────────────┐ ┌──────────────────────┐  │ │
│  │  │   Ingest     │ │  Retrieve   │ │      Generate        │  │ │
│  │  │ ├─ Load /data │ │ ├─ Embed Q  │ │ ├─ OpenAI/Stub LLM  │  │ │
│  │  │ ├─ Chunk docs │ │ ├─ Search   │ │ ├─ Context prompt   │  │ │
│  │  │ └─ Thread-safe│ │ ├─ MMR rank │ │ ├─ PII masking     │  │ │
│  │  └──────────────┘ │ └─ LRU cache │ │ └─ LRU cache       │  │ │
│  │                   └─────────────┘ └──────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼ upsert/search
┌─────────────────────────────────────────┐
│            Qdrant Vector DB             │
│  ┌─────────────────┐ ┌─────────────────┐ │
│  │   Collections   │ │    Persistence  │ │
│  │ ├─ policy_helper│ │ ├─ Docker Vol   │ │
│  │ └─ 384-dim vecs │ │ └─ Health check │ │
│  └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────┘
        ▲ fallback to in-memory if unavailable
```

---

## Candidate Instructions (Read Me First)

### Goal
Build a local-first **Policy & Product Helper** using RAG that:
- Ingests the sample docs under `/data`
- Answers questions with **citations** (title + section)
- Exposes metrics and health endpoints
- Provides a minimal **chat UI** and **admin panel**

You have **48 hours** once you start. AI coding tools are allowed.

### Deliverables
1. **GitHub repo link** with your changes.
2. **README** describing setup, architecture, trade-offs, and what you’d ship next.
3. **2–5 minute screen capture** demonstrating ingestion + Q&A + citations.
4. **Tests**: show how to run them and their results (e.g., `pytest -q`).

### Acceptance Checks (we will run)
1. `docker compose up --build` boots **Qdrant + backend + frontend**.
2. Use Admin tab to **ingest** docs without errors.
3. Ask: *“Can a customer return a damaged blender after 20 days?”* → cites **Returns_and_Refunds.md** and **Warranty_Policy.md**.
4. Ask: *“What’s the shipping SLA to East Malaysia for bulky items?”* → cites **Delivery_and_Shipping.md** (mentions bulky item surcharge).
5. Expand a citation chip and see the underlying chunk text.

### Rubric (100 pts)
- **Functionality & correctness (35)** — ingestion, RAG with citations, metrics, health.
- **Code quality & structure (20)** — small functions, separation of concerns, typing, linting.
- **Reproducibility & docs (15)** — clear README, env.example, diagrams.
- **UX & DX polish (10)** — responsive, accessible, solid loading/errors.
- **Testing (10)** — meaningful unit/integration tests that run locally.
- **Performance & observability (10)** — reasonable latency, useful metrics/logs.

### How to Run (Docker)
```bash
# copy env
cp .env.example .env

# run all services
docker compose up --build

# endpoints
# frontend: http://localhost:3000
# backend swagger: http://localhost:8000/docs
# qdrant ui: http://localhost:6333
 
```

### How to Run (No Docker, optional)
Backend:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
```
Frontend:
```bash
cd frontend
npm install
npm run dev
# open http://localhost:3000
```

### Switching LLMs
- Default is **stub** (deterministic, offline).
- To use OpenAI: set `LLM_PROVIDER=openai` and `OPENAI_API_KEY` in `.env`. (You are required to demo with OpenAI, API key is provided)
- To use Ollama: set `LLM_PROVIDER=stub` (keep stub) or extend `rag.py` to add an `OllamaLLM` class.
- Please document any changes you make.

### Vector Store
- Default is **Qdrant** via Docker. Fallback is in-memory if Qdrant isn’t available.
- To switch to in-memory explicitly: `VECTOR_STORE=memory` in `.env`.

### API Reference
- `POST /api/ingest` → `{ indexed_docs, indexed_chunks }`
- `POST /api/ask` body:
  ```json
  { "query": "What's the refund window for Category A?", "k": 4 }
  ```
  Response includes `answer`, `citations[]`, `chunks[]`, `metrics`.
- `GET /api/metrics` → counters + avg latencies
- `GET /api/health` → `{ "status": "ok" }`

### UI Walkthrough
1. Open **http://localhost:3000**.
2. In **Admin** card, click **Ingest sample docs** and then **Refresh metrics**.
3. In **Chat**, ask questions. Click the **source badges** to expand supporting chunks.

### What You Can Modify
- Anything. Improve chunking, reranking (MMR), prompt, UI polish, streaming, caching, guardrails (PDPA masking), feedback logging, small eval script, etc.
- Keep the one-command run and README accurate.

### Constraints & Notes
- Keep keys out of the frontend.
- Validate file types if you extend ingestion to uploads.
- Provide small architecture diagram if you can (ASCII is fine).

### Troubleshooting
- **Qdrant healthcheck failing**: ensure port `6333` is free; re-run compose.
 
- **CORS errors**: 
  - Development: allows localhost:3000, localhost:3001, 127.0.0.1:3000, 127.0.0.1:3001
  - Production: set `ALLOWED_ORIGINS` env var (comma-separated URLs)
  - Environment detection: set `ENVIRONMENT=production` for prod CORS rules
- **Frontend port conflicts**: set `FRONTEND_PORT` in `.env` if 3000 is busy
- **Embeddings/LLM**: With no keys, stub models run by default so the app always works.
- **Input validation errors**: queries are limited to 1000 chars, XSS patterns blocked
- **Memory issues**: caches are bounded (1000 retrieval, 500 generation entries)

---

## Implementation Notes

### Security & Quality Improvements Made

**Critical Security Fixes:**
- ✅ **Removed API key exposure** - `.env` file removed from git, proper `.gitignore` added
- ✅ **Input validation** - Pydantic validators with length limits (1-1000 chars), XSS pattern detection
- ✅ **CORS security** - Environment-specific origins instead of wildcard `*`

**Code Quality Enhancements:**
- ✅ **Error handling** - Structured logging with fallback mechanisms for LLM failures
- ✅ **Thread safety** - Locks for concurrent ingestion operations to prevent race conditions
- ✅ **Memory management** - LRU caches (1000 retrieval, 500 generation) to prevent unbounded growth
- ✅ **Observability** - Detailed logging for debugging and monitoring

### Trade-offs & Design Decisions

**Performance vs Security:**
- Input validation adds ~1-2ms latency but prevents injection attacks
- Thread locks reduce concurrency but ensure data consistency
- Cache size limits prevent memory leaks but may increase miss rates

**Complexity vs Maintainability:**
- Added structured logging increases code size but improves debugging
- LRU cache implementation adds complexity but essential for production
- Environment-based CORS adds configuration but improves security

**Development vs Production:**
- Stub LLM fallback ensures offline development works
- Different CORS policies for dev vs prod environments
- Deterministic embeddings for reproducible testing

### Next Steps for Production

**Short-term (next sprint):**
1. **Authentication & authorization** - Add user sessions and API keys
2. **Rate limiting** - Prevent abuse with request throttling  
3. **Monitoring** - Add Prometheus metrics and health checks
4. **Error recovery** - Implement circuit breakers for external APIs

**Medium-term (next quarter):**
1. **Streaming responses** - Real-time answer generation for better UX
2. **Advanced retrieval** - Hybrid search (semantic + keyword)
3. **Document versioning** - Track changes to policy documents
4. **A/B testing** - Experiment with different prompt strategies

**Long-term (roadmap):**
1. **Multi-tenant support** - Separate document collections per organization
2. **Advanced analytics** - Usage patterns and query analysis
3. **AI-powered summaries** - Automatic policy change summaries
4. **Integration APIs** - Connect with external systems (Slack, Teams)

### Submission
- Share GitHub repo link + your short demo video.
- Include any notes on trade-offs and next steps.

## Deployment Guide
See `docs/DEPLOYMENT.md` for production setup: env vars, CORS, OpenAI/Ollama, scaling, monitoring, and troubleshooting.
