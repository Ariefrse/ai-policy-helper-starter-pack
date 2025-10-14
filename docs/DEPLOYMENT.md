# Production Deployment Guide

This guide covers environment configuration, CORS, model providers, scaling, metrics/monitoring, and troubleshooting for deploying the AI Policy & Product Helper.

## Prerequisites
- Docker + Docker Compose
- Optional: OpenAI API key for real LLMs

## Environment Variables
Set these in `.env` (see `.env.example`):
- `EMBEDDING_MODEL` — embedding identifier (default: `local-384`)
- `LLM_PROVIDER` — `stub` | `openai` (default: `stub`)
- `OPENAI_API_KEY` — required when `LLM_PROVIDER=openai`
- `OLLAMA_HOST` — URL to Ollama if you extend provider (default: `http://ollama:11434`)
- `VECTOR_STORE` — `qdrant` | `memory` (default: `qdrant`)
- `COLLECTION_NAME` — Qdrant collection (default: `policy_helper`)
- `CHUNK_SIZE` / `CHUNK_OVERLAP` — ingestion chunking (defaults: `700` / `80`)
- `ALLOWED_ORIGINS` — comma-separated allowed origins (prod only)
- `ENVIRONMENT` — `development` | `production` (default: `development`)
- Frontend: `FRONTEND_PORT` (default: `3000`)

 

## CORS
- Development: localhost origins are allowed automatically.
- Production: set `ENVIRONMENT=production` and define `ALLOWED_ORIGINS` (comma-separated full URLs).

## Model Providers
- Stub (default): fully offline deterministic responses for dev.
- OpenAI: set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.
- Ollama: keep `LLM_PROVIDER=stub` and extend `rag.py` with an `OllamaLLM` if desired.

## Run (Docker Compose)
```bash
cp .env.example .env
docker compose up --build
```
- Frontend: `http://localhost:${FRONTEND_PORT:-3000}`
- Backend Swagger: `http://localhost:8000/docs`
- Qdrant UI: `http://localhost:6333`
 

## Metrics & Monitoring
- Backend exposes JSON metrics at `GET /api/metrics` (avg/p95 latencies, totals, model identifiers).
- Logs are structured (JSON-like) for basic observability.

## Scaling
- Backend: scale with multiple `uvicorn` workers behind a reverse proxy (e.g., Nginx). Example: `uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000`.
- Qdrant: allocate persistent storage, consider clustering/replication for HA in production.
- Frontend: deploy static Next.js output with a CDN or run SSR with autoscaling as needed.

## Troubleshooting
- Qdrant down: check container logs and port `6333` availability.
- CORS: In production set `ENVIRONMENT=production` and define `ALLOWED_ORIGINS`.
- Metrics: use `/api/metrics`; generate traffic (ingest/ask) before checking.
- OpenAI errors: verify `OPENAI_API_KEY` and outbound network egress policy.

## Security Notes
- Keep `.env` out of version control.
- Limit allowed origins; avoid wildcard `*` in production.
- Consider adding auth + rate limiting before internet exposure.
