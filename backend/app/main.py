from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from typing import Any, Optional
from .models import IngestResponse, AskRequest, AskResponse, MetricsResponse, Citation, Chunk
from .settings import settings
from .ingest import load_documents
from .rag import RAGEngine, build_chunks_from_docs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Policy & Product Helper")

# SECURITY: Use environment-specific CORS configuration
if settings.environment == "production":
    allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(',') if origin.strip()]
    logger.info(f"Production CORS: {allowed_origins}")
else:
    # Development: localhost variations
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    logger.info("Development CORS: localhost only")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

engine = RAGEngine()

# Security setup for protected endpoints
security = HTTPBearer(auto_error=False)

async def verify_monitoring_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """Verify monitoring API key for access to protected endpoints."""
    if settings.monitoring_api_key is None:
        # If no monitoring key is configured, allow access in development only
        if settings.environment == "development":
            return None
        raise HTTPException(status_code=500, detail="Monitoring key not configured")

    # If monitoring key is configured, require valid authentication
    if credentials is None or credentials.credentials != settings.monitoring_api_key:
        logger.warning("Unauthorized access attempt to protected endpoint")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing monitoring API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return None

@app.get("/api/health")
def health() -> dict[str, Any]:
    """Basic health check for load balancers."""
    return engine.get_public_service_status()

@app.get("/api/service-status")
def service_status(auth: Optional[str] = Depends(verify_monitoring_key)) -> dict[str, Any]:
    """Get detailed service status for monitoring (authentication required)."""
    try:
        return engine.get_service_status()
    except ConnectionError as e:
        logger.error(f"Connection error retrieving service status: {e}")
        return {
            "services": {
                "vector_store": {"healthy": False, "type": "unknown", "degraded": True, "error": "connection_error"},
                "llm": {"healthy": False, "type": "unknown", "degraded": True, "error": "connection_error"}
            },
            "any_degraded": True,
            "all_healthy": False,
            "status_message": "Service status unavailable due to connection errors",
            "error_type": "connection_error"
        }
    except TimeoutError as e:
        logger.error(f"Timeout error retrieving service status: {e}")
        return {
            "services": {
                "vector_store": {"healthy": False, "type": "unknown", "degraded": True, "error": "timeout"},
                "llm": {"healthy": False, "type": "unknown", "degraded": True, "error": "timeout"}
            },
            "any_degraded": True,
            "all_healthy": False,
            "status_message": "Service status unavailable due to timeout",
            "error_type": "timeout"
        }
    except Exception as e:
        logger.error(f"Unexpected error retrieving service status: {e}", exc_info=True)
        return {
            "services": {
                "vector_store": {"healthy": False, "type": "unknown", "degraded": True, "error": "unexpected_error"},
                "llm": {"healthy": False, "type": "unknown", "degraded": True, "error": "unexpected_error"}
            },
            "any_degraded": True,
            "all_healthy": False,
            "status_message": "Service status unavailable due to unexpected error",
            "error_type": "unexpected_error"
        }

@app.get("/api/metrics", response_model=MetricsResponse)
def metrics(auth: Optional[str] = Depends(verify_monitoring_key)) -> MetricsResponse:
    """Get system metrics including document counts and latencies (authentication required)."""
    try:
        s = engine.stats()
        return MetricsResponse(
            total_docs=s["total_docs"],
            total_chunks=s["total_chunks"],
            avg_retrieval_latency_ms=s["avg_retrieval_latency_ms"],
            avg_generation_latency_ms=s["avg_generation_latency_ms"],
            p95_retrieval_latency_ms=s["p95_retrieval_latency_ms"],
            p95_generation_latency_ms=s["p95_generation_latency_ms"],
            total_asks=s["total_asks"],
            total_ingests=s["total_ingests"],
            embedding_model=s["embedding_model"],
            llm_model=s["llm_model"],
            vector_store=s.get("vector_store"),
            collection_name=s.get("collection_name"),
            service_health=s.get("service_health")
        )
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@app.post("/api/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    """Ingest documents from the data directory into the vector store."""
    try:
        logger.info(f"Starting ingestion from {settings.data_dir}")
        docs = load_documents(settings.data_dir)

        if not docs:
            raise HTTPException(status_code=400, detail="No documents found in data directory")

        chunks = build_chunks_from_docs(docs, settings.chunk_size, settings.chunk_overlap)
        new_docs, new_chunks = engine.ingest_chunks(chunks)

        logger.info(f"Ingestion complete: {new_docs} docs, {new_chunks} chunks")
        return IngestResponse(indexed_docs=new_docs, indexed_chunks=new_chunks)

    except FileNotFoundError as e:
        logger.error(f"Data directory not found: {e}")
        raise HTTPException(status_code=500, detail="Data directory not configured correctly")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """Answer a question using RAG with document citations."""
    try:
        logger.info(f"Processing query: {req.query[:50]}...")

        ctx = engine.retrieve(req.query, k=req.k or 8)

        if not ctx:
            logger.warning("No relevant context found for query")
            return AskResponse(
                query=req.query,
                answer="I couldn't find relevant information to answer your question. Please try rephrasing or ask about our policies.",
                citations=[],
                chunks=[],
                metrics={"retrieval_ms": 0, "generation_ms": 0}
            )

        answer = engine.generate(req.query, ctx)
        citations = [Citation(title=c.get("title", "Unknown"), section=c.get("section")) for c in ctx]
        chunks = [Chunk(title=c.get("title", "Unknown"), section=c.get("section"), text=c.get("text", "")) for c in ctx]
        stats = engine.stats()

        logger.info(f"Query processed successfully with {len(citations)} citations")

        # Include service health information if services are degraded
        service_health = None
        if stats.get("service_health", {}).get("any_degraded", False):
            service_health = stats["service_health"]
            logger.warning(f"Returning response with degraded services: {service_health.get('status_message')}")

        return AskResponse(
            query=req.query,
            answer=answer,
            citations=citations,
            chunks=chunks,
            metrics={
                "retrieval_ms": stats["avg_retrieval_latency_ms"],
                "generation_ms": stats["avg_generation_latency_ms"],
            },
            service_health=service_health
        )
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process your question. Please try again.")


