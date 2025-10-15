import time
import logging
from collections import deque
from typing import List, Dict, Tuple
import numpy as np

from .embeddings import LocalEmbedder
from .vector_store import create_vector_store
from .llm_providers import create_llm_provider
from .ingest import doc_hash
from .settings import settings

# Configure structured logging
logger = logging.getLogger(__name__)

class Metrics:
    """
    Performance metrics collector for RAG operations.

    Tracks retrieval and generation latencies, operation counts,
    and provides statistical summaries.
    """

    def __init__(self, buffer_size: int = 1000):
        """
        Initialize metrics collector.

        Args:
            buffer_size: Maximum number of latency measurements to store
        """
        self.buffer_size = buffer_size
        # Use deque with maxlen for circular buffer - prevents unbounded memory growth
        self.t_retrieval = deque(maxlen=buffer_size)
        self.t_generation = deque(maxlen=buffer_size)
        self.total_asks = 0
        self.total_ingests = 0
        logger.debug(f"Initialized Metrics with buffer size {buffer_size}")

    def add_retrieval(self, ms: float):
        """
        Add a retrieval latency measurement.

        Args:
            ms: Latency in milliseconds
        """
        self.t_retrieval.append(ms)

    def add_generation(self, ms: float):
        """
        Add a generation latency measurement.

        Args:
            ms: Latency in milliseconds
        """
        self.t_generation.append(ms)

    def summary(self) -> Dict:
        """
        Generate a summary of collected metrics.

        Returns:
            Dictionary containing metric statistics
        """
        # Convert deque to numpy array for calculations
        arr_r = np.array(self.t_retrieval, dtype=float) if self.t_retrieval else np.array([])
        arr_g = np.array(self.t_generation, dtype=float) if self.t_generation else np.array([])

        avg_r = float(arr_r.mean()) if arr_r.size else 0.0
        avg_g = float(arr_g.mean()) if arr_g.size else 0.0
        p95_r = float(np.percentile(arr_r, 95)) if arr_r.size else 0.0
        p95_g = float(np.percentile(arr_g, 95)) if arr_g.size else 0.0

        return {
            "avg_retrieval_latency_ms": round(avg_r, 2),
            "avg_generation_latency_ms": round(avg_g, 2),
            "p95_retrieval_latency_ms": round(p95_r, 2),
            "p95_generation_latency_ms": round(p95_g, 2),
            "total_asks": int(self.total_asks),
            "total_ingests": int(self.total_ingests),
            "buffer_size": self.buffer_size,
            "current_buffer_entries": len(self.t_retrieval) + len(self.t_generation),
        }

class RAGEngine:
    """
    Main RAG (Retrieval-Augmented Generation) engine orchestrator.

    Coordinates embedding generation, vector storage, retrieval, and
    language model generation to provide question-answering capabilities.
    """

    def __init__(self, embedder=None, vector_store=None, llm_provider=None):
        """
        Initialize the RAG engine with configurable components.

        Args:
            embedder: Embedding function (defaults to LocalEmbedder)
            vector_store: Vector store instance (defaults based on settings)
            llm_provider: LLM provider instance (defaults based on settings)
        """
        # Initialize service status tracking
        self.service_status = {
            "vector_store": {"healthy": False, "type": None, "degraded": False},
            "llm": {"healthy": False, "type": None, "degraded": False}
        }

        # Initialize embedder with dependency injection
        self.embedder = embedder or LocalEmbedder(dim=384)

        # Initialize vector store with dependency injection and error handling
        self._initialize_vector_store(vector_store)

        # Initialize LLM provider with dependency injection and error handling
        self._initialize_llm_provider(llm_provider)

        # Initialize metrics and tracking
        self.metrics = Metrics()
        self._doc_titles = set()
        self._chunk_count = 0

        # Log initialization summary
        self._log_initialization_status()

    def _initialize_vector_store(self, vector_store=None):
        """Initialize vector store with comprehensive error handling."""
        if vector_store:
            self.store = vector_store
            store_type = type(vector_store).__name__
        else:
            store_type = settings.vector_store
            try:
                self.store = create_vector_store(
                    store_type=settings.vector_store,
                    collection_name=settings.collection_name,
                    dim=384
                )
            except Exception as e:
                logger.error(f"Critical error initializing vector store: {str(e)} - falling back to in-memory store")
                from .vector_store import InMemoryStore
                self.store = InMemoryStore(dim=384)
                store_type = "memory"

        # Determine service health and type
        store_class_name = type(self.store).__name__
        if store_class_name == "QdrantStore":
            self.service_status["vector_store"] = {
                "healthy": getattr(self.store, 'service_healthy', False),
                "type": "qdrant",
                "degraded": not getattr(self.store, 'service_healthy', False)
            }
        else:
            # InMemoryStore is always healthy, but degraded if not the requested type
            self.service_status["vector_store"] = {
                "healthy": True,
                "type": "memory",
                "degraded": store_type != "memory"
            }

    def _initialize_llm_provider(self, llm_provider=None):
        """Initialize LLM provider with comprehensive error handling."""
        if llm_provider:
            self.llm = llm_provider
        else:
            try:
                self.llm = create_llm_provider(
                    provider_type=settings.llm_provider,
                    api_key=settings.openai_api_key
                )
            except Exception as e:
                logger.error(f"Critical error initializing LLM provider: {str(e)} - falling back to stub LLM")
                from .llm_providers import StubLLM
                self.llm = StubLLM()

        # Determine LLM service health and type
        llm_class_name = type(self.llm).__name__
        if llm_class_name == "OpenAILLM":
            self.service_status["llm"] = {
                "healthy": getattr(self.llm, 'service_healthy', False),
                "type": "openai:gpt-4o-mini",
                "degraded": not getattr(self.llm, 'service_healthy', False)
            }
            self.llm_name = "openai:gpt-4o-mini"
        else:
            # StubLLM is always healthy, but degraded if not the requested type
            is_degraded = settings.llm_provider != "stub"
            self.service_status["llm"] = {
                "healthy": True,
                "type": "stub",
                "degraded": is_degraded
            }
            self.llm_name = "stub"

    def _log_initialization_status(self):
        """Log the initialization status for monitoring."""
        logger.info("=" * 60)
        logger.info("RAG ENGINE INITIALIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Vector Store: {self.service_status['vector_store']['type']} "
                   f"(Healthy: {self.service_status['vector_store']['healthy']}, "
                   f"Degraded: {self.service_status['vector_store']['degraded']})")
        logger.info(f"LLM Provider: {self.service_status['llm']['type']} "
                   f"(Healthy: {self.service_status['llm']['healthy']}, "
                   f"Degraded: {self.service_status['llm']['degraded']})")

        if any(service['degraded'] for service in self.service_status.values()):
            logger.warning("⚠️  One or more services are running in degraded mode")
        else:
            logger.info("✅ All services running normally")
        logger.info("=" * 60)

    def get_service_status(self) -> Dict:
        """Get current service status for user notification."""
        return {
            "services": self.service_status,
            "any_degraded": any(service['degraded'] for service in self.service_status.values()),
            "all_healthy": all(service['healthy'] for service in self.service_status.values()),
            "status_message": self._build_status_message()
        }

    def _build_status_message(self) -> str:
        """Build a user-friendly status message."""
        degraded_services = []

        if self.service_status["vector_store"]["degraded"]:
            if self.service_status["vector_store"]["type"] == "memory":
                degraded_services.append("Vector search is using local storage (slower performance)")
            else:
                degraded_services.append("Vector search service experiencing issues")

        if self.service_status["llm"]["degraded"]:
            if self.service_status["llm"]["type"] == "stub":
                degraded_services.append("AI responses are using basic mode (reduced quality)")
            else:
                degraded_services.append("AI generation service experiencing issues")

        if degraded_services:
            return "⚠️ System running in degraded mode: " + "; ".join(degraded_services)
        else:
            return "All systems operational"

    def ingest_chunks(self, chunks: List[Dict]) -> Tuple[int, int]:
        """
        Ingest document chunks into the vector store.

        Args:
            chunks: List of document chunks with metadata

        Returns:
            Tuple of (new_documents, new_chunks) processed
        """
        vectors = []
        metas = []
        doc_titles_before = set(self._doc_titles)

        for ch in chunks:
            text = ch["text"]
            h = doc_hash(text)
            meta = {
                "id": h,
                "hash": h,
                "title": ch["title"],
                "section": ch.get("section"),
                "text": text,
            }
            v = self.embedder.embed(text)
            vectors.append(v)
            metas.append(meta)
            self._doc_titles.add(ch["title"])
            self._chunk_count += 1

        self.store.upsert(vectors, metas)
        self.metrics.total_ingests += 1

        new_docs = len(self._doc_titles) - len(doc_titles_before)
        new_chunks = len(metas)

        logger.info(f"Ingested {new_chunks} chunks from {new_docs} new documents")
        return (new_docs, new_chunks)

    def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        """
        Retrieve relevant document chunks for a query.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of retrieved document metadata
        """
        t0 = time.time()
        qv = self.embedder.embed(query)
        results = self.store.search(qv, k=k)
        self.metrics.add_retrieval((time.time() - t0) * 1000.0)

        # Extract metadata from results
        contexts = [meta for score, meta in results]
        logger.debug(f"Retrieved {len(contexts)} contexts for query: {query[:50]}...")
        return contexts

    def generate(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate a response based on query and retrieved contexts.

        Args:
            query: User's query
            contexts: Retrieved document contexts

        Returns:
            Generated response text
        """
        t0 = time.time()
        answer = self.llm.generate(query, contexts)
        self.metrics.add_generation((time.time() - t0) * 1000.0)
        self.metrics.total_asks += 1
        logger.debug(f"Generated response in {(time.time() - t0) * 1000.0:.2f}ms")
        return answer

    def ask(self, query: str, k: int = 4) -> str:
        """
        Complete RAG pipeline: retrieve and generate response.

        Args:
            query: User's query
            k: Number of documents to retrieve

        Returns:
            Generated response
        """
        contexts = self.retrieve(query, k=k)
        return self.generate(query, contexts)

    def stats(self) -> Dict:
        """
        Get comprehensive statistics about the RAG engine.

        Returns:
            Dictionary containing various statistics including service health
        """
        m = self.metrics.summary()
        service_status = self.get_service_status()

        return {
            "total_docs": len(self._doc_titles),
            "total_chunks": self._chunk_count,
            "embedding_model": settings.embedding_model,
            "llm_model": self.llm_name,
            "vector_store": settings.vector_store,
            "collection_name": settings.collection_name,
            "service_health": {
                "all_healthy": service_status["all_healthy"],
                "any_degraded": service_status["any_degraded"],
                "status_message": service_status["status_message"],
                "services": service_status["services"]
            },
            **m
        }

    def reset_metrics(self):
        """Reset all collected metrics."""
        self.metrics = Metrics()
        logger.info("Reset all metrics")

def create_rag_engine(**overrides) -> RAGEngine:
    """
    Factory function to create RAG engine with optional component overrides.

    Args:
        **overrides: Optional component overrides (embedder, vector_store, llm_provider)

    Returns:
        Configured RAGEngine instance
    """
    return RAGEngine(**overrides)