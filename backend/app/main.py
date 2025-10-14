from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import logging
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

@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    """Get system metrics including document counts and latencies."""
    try:
        s = engine.stats()
        return MetricsResponse(**s)
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

        return AskResponse(
            query=req.query,
            answer=answer,
            citations=citations,
            chunks=chunks,
            metrics={
                "retrieval_ms": stats["avg_retrieval_latency_ms"],
                "generation_ms": stats["avg_generation_latency_ms"],
            }
        )
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process your question. Please try again.")
