import logging
from typing import List, Dict, Tuple

# Import modular components for backward compatibility
from .embeddings import LocalEmbedder, _tokenize
from .vector_store import InMemoryStore, QdrantStore, create_vector_store
from .llm_providers import StubLLM, OpenAILLM, create_llm_provider
from .orchestrator import RAGEngine, Metrics, create_rag_engine
from .ingest import chunk_text, doc_hash
from .utils import retry_with_backoff

# Configure structured logging
logger = logging.getLogger(__name__)

# ---- Backward Compatibility Layer ----
# All existing classes and functions are available through imports above
# This maintains full API compatibility while providing modular architecture

# ---- Helper Functions ----
def build_chunks_from_docs(docs: List[Dict], chunk_size: int, overlap: int) -> List[Dict]:
    """
    Build document chunks from a list of documents.

    Args:
        docs: List of document dictionaries with 'text', 'title', and 'section' keys
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List of chunk dictionaries
    """
    out = []
    for d in docs:
        for ch in chunk_text(d["text"], chunk_size, overlap):
            out.append({"title": d["title"], "section": d["section"], "text": ch})
    return out

# ---- Factory Functions for Easy Component Creation ----
def create_default_rag_engine() -> RAGEngine:
    """
    Create a RAG engine with default components based on settings.

    Returns:
        Configured RAGEngine instance
    """
    return create_rag_engine()

def create_custom_rag_engine(embedder=None, vector_store=None, llm_provider=None) -> RAGEngine:
    """
    Create a RAG engine with custom components.

    Args:
        embedder: Custom embedder instance
        vector_store: Custom vector store instance
        llm_provider: Custom LLM provider instance

    Returns:
        Configured RAGEngine instance
    """
    return create_rag_engine(
        embedder=embedder,
        vector_store=vector_store,
        llm_provider=llm_provider
    )

# ---- Module Info for Debugging ----
def get_module_info() -> Dict:
    """
    Get information about the modular RAG system.

    Returns:
        Dictionary with module configuration info
    """
    return {
        "modules": {
            "embeddings": "LocalEmbedder (deterministic feature hashing)",
            "vector_stores": ["InMemoryStore", "QdrantStore"],
            "llm_providers": ["StubLLM", "OpenAILLM"],
            "orchestrator": "RAGEngine with Metrics"
        },
        "architecture": "Modular design with dependency injection",
        "backward_compatibility": "Full API compatibility maintained"
    }

# Export all public classes and functions for backward compatibility
__all__ = [
    # Core classes
    'LocalEmbedder',
    'InMemoryStore',
    'QdrantStore',
    'StubLLM',
    'OpenAILLM',
    'RAGEngine',
    'Metrics',

    # Utility functions
    'retry_with_backoff',
    '_tokenize',
    'build_chunks_from_docs',

    # Factory functions
    'create_vector_store',
    'create_llm_provider',
    'create_rag_engine',
    'create_default_rag_engine',
    'create_custom_rag_engine',

    # Module info
    'get_module_info'
]