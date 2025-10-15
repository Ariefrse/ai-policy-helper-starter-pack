import time
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import hashlib
from functools import lru_cache

from .utils import retry_with_backoff

# Import Qdrant client if available
try:
    from qdrant_client import QdrantClient, models as qm
    from qdrant_client.http.exceptions import UnexpectedResponse
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    # Create dummy classes for type hints
    class QdrantClient: pass
    class qm:
        class VectorParams: pass
        class Distance:
            COSINE = "cosine"
        class PointStruct: pass
    class UnexpectedResponse(Exception): pass

# Configure structured logging
logger = logging.getLogger(__name__)

class VectorStore:
    """Base class for vector stores."""

    def upsert(self, vectors: List[np.ndarray], metadatas: List[Dict]):
        """Upsert vectors with metadata."""
        raise NotImplementedError

    def search(self, query: np.ndarray, k: int = 4) -> List[Tuple[float, Dict]]:
        """Search for similar vectors."""
        raise NotImplementedError

class InMemoryStore(VectorStore):
    """
    In-memory vector store using NumPy for similarity calculations.

    This is a simple implementation suitable for development and testing
    or when an external vector database is not available.
    """

    def __init__(self, dim: int = 384):
        """
        Initialize the in-memory store.

        Args:
            dim: Dimension of the embedding vectors
        """
        self.dim = dim
        self.vecs: List[np.ndarray] = []
        self.meta: List[Dict] = []
        self._hashes = set()

        # Performance optimizations
        self._precomputed_norms: np.ndarray = np.array([])  # Cached vector norms
        self._query_cache: Dict[str, Tuple[List[Tuple[float, Dict]], float]] = {}  # Simple LRU cache
        self._cache_ttl = 300  # 5 minutes TTL
        self._max_cache_size = 1000

        logger.debug(f"Initialized InMemoryStore with dimension {dim} and optimizations")

    def upsert(self, vectors: List[np.ndarray], metadatas: List[Dict]):
        """
        Insert or update vectors with their metadata.

        Args:
            vectors: List of embedding vectors
            metadatas: List of metadata dictionaries
        """
        vectors_added = 0
        for v, m in zip(vectors, metadatas):
            h = m.get("hash")
            if h and h in self._hashes:
                # Skip duplicate content
                continue
            self.vecs.append(v.astype("float32"))
            self.meta.append(m)
            if h:
                self._hashes.add(h)
            vectors_added += 1

        # Update precomputed norms if vectors were added
        if vectors_added > 0:
            self._update_precomputed_norms()
            # Clear cache since vectors have changed
            self._query_cache.clear()

        logger.debug(f"Upserted {vectors_added} vectors to InMemoryStore (total: {len(self.vecs)})")

    def _update_precomputed_norms(self):
        """Update precomputed vector norms for efficient cosine similarity."""
        if self.vecs:
            A = np.vstack(self.vecs)  # [N, d]
            self._precomputed_norms = np.linalg.norm(A, axis=1)  # Precompute all vector norms
        else:
            self._precomputed_norms = np.array([])

    def _get_query_hash(self, query: np.ndarray, k: int) -> str:
        """Generate a hash for the query and k value for caching."""
        query_bytes = query.tobytes()
        k_bytes = str(k).encode()
        combined = query_bytes + k_bytes
        return hashlib.md5(combined).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached result is still valid."""
        return time.time() - timestamp < self._cache_ttl

    def _cleanup_cache(self):
        """Remove expired entries and enforce size limit."""
        current_time = time.time()

        # Remove expired entries
        expired_keys = [
            key for key, (_, timestamp) in self._query_cache.items()
            if not self._is_cache_valid(timestamp)
        ]
        for key in expired_keys:
            del self._query_cache[key]

        # Enforce size limit (simple LRU - remove oldest entries)
        if len(self._query_cache) > self._max_cache_size:
            # Sort by timestamp and remove oldest entries
            sorted_items = sorted(self._query_cache.items(), key=lambda x: x[1][1])
            excess = len(self._query_cache) - self._max_cache_size
            for key, _ in sorted_items[:excess]:
                del self._query_cache[key]

    def search(self, query: np.ndarray, k: int = 4) -> List[Tuple[float, Dict]]:
        """
        Search for similar vectors using cosine similarity with optimizations.

        Args:
            query: Query vector
            k: Number of results to return

        Returns:
            List of (similarity_score, metadata) tuples
        """
        if not self.vecs:
            logger.debug("No vectors in store, returning empty results")
            return []

        # Check cache first
        query_hash = self._get_query_hash(query, k)
        self._cleanup_cache()

        if query_hash in self._query_cache:
            cached_results, timestamp = self._query_cache[query_hash]
            if self._is_cache_valid(timestamp):
                logger.debug(f"Cache hit for query hash {query_hash[:8]}...")
                return cached_results

        # Ensure precomputed norms are up to date
        if len(self._precomputed_norms) != len(self.vecs):
            self._update_precomputed_norms()

        A = np.vstack(self.vecs)  # [N, d]
        q = query.reshape(1, -1)  # [1, d]
        query_norm = np.linalg.norm(q) + 1e-9

        # Optimized cosine similarity using precomputed norms
        # (A @ q.T).ravel() / (precomputed_norms * query_norm + 1e-9)
        sims = (A @ q.T).ravel() / (self._precomputed_norms * query_norm + 1e-9)

        # Efficient top-k selection using argpartition (O(N + k log k) instead of O(N log N))
        if len(sims) <= k:
            # If we need all results, just sort normally
            idx = np.argsort(-sims)
        else:
            # Use argpartition for efficient top-k selection
            # Get the k-th largest value threshold
            threshold = np.partition(sims, -k)[-k]
            # Find indices of values >= threshold (may be more than k due to ties)
            top_candidates = np.where(sims >= threshold)[0]
            # Sort these candidates to get final top-k
            candidate_sims = sims[top_candidates]
            final_order = np.argsort(-candidate_sims)[:k]
            idx = top_candidates[final_order]

        results = [(float(sims[i]), self.meta[i]) for i in idx]

        # Cache the results (cleanup first to ensure we don't exceed size limit)
        if len(self._query_cache) >= self._max_cache_size:
            # Remove oldest entry to make room
            if self._query_cache:
                oldest_key = min(self._query_cache.keys(), key=lambda k: self._query_cache[k][1])
                del self._query_cache[oldest_key]

        self._query_cache[query_hash] = (results, time.time())

        logger.debug(f"Search returned {len(results)} results from InMemoryStore (cached: {query_hash[:8]}...)")
        return results

class QdrantStore(VectorStore):
    """
    Qdrant-based vector store with retry logic and health checks.

    This implementation provides production-ready vector storage with
    persistence, scalability, and robust error handling.
    """

    def __init__(self, collection: str, dim: int = 384):
        """
        Initialize the Qdrant store.

        Args:
            collection: Name of the Qdrant collection
            dim: Dimension of the embedding vectors
        """
        self.collection = collection
        self.dim = dim
        self.client = None
        self.service_healthy = False

        # Performance optimizations for query caching
        # Note: Precomputed norms are handled by Qdrant itself, so we only add caching here
        self._query_cache: Dict[str, Tuple[List[Tuple[float, Dict]], float]] = {}  # Simple LRU cache
        self._cache_ttl = 300  # 5 minutes TTL
        self._max_cache_size = 1000

        self._initialize_client()
        logger.debug(f"Initialized QdrantStore for collection '{collection}' with dimension {dim} and query caching")

    def _initialize_client(self):
        """Initialize Qdrant client with retry logic and health check."""
        def _connect():
            client = QdrantClient(url="http://qdrant:6333", timeout=10.0)
            # Test connection with a simple health check
            client.get_collections()
            return client

        self.client = retry_with_backoff(
            _connect,
            max_retries=5,
            base_delay=2.0,
            operation_name="Qdrant connection initialization"
        )

        if self.client:
            self.service_healthy = True
            logger.info("Qdrant client initialized successfully")
            self._ensure_collection()
        else:
            self.service_healthy = False
            logger.error("Failed to initialize Qdrant client - service may be unavailable")

    def _ensure_collection(self):
        """Ensure collection exists with error handling."""
        if not self.service_healthy or not self.client:
            return

        def _create_collection():
            try:
                self.client.get_collection(self.collection)
                logger.info(f"Collection '{self.collection}' already exists")
            except Exception as e:
                logger.info(f"Creating collection '{self.collection}': {str(e)}")
                self.client.recreate_collection(
                    collection_name=self.collection,
                    vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE)
                )
                logger.info(f"Collection '{self.collection}' created successfully")

        retry_with_backoff(
            _create_collection,
            max_retries=3,
            base_delay=1.0,
            operation_name=f"Collection '{self.collection}' setup"
        )

    def _check_service_health(self):
        """Check service health and attempt reconnection if needed."""
        if not self.service_healthy:
            logger.info("Attempting to restore Qdrant connection...")
            self._initialize_client()
        return self.service_healthy

    def _get_query_hash(self, query: np.ndarray, k: int) -> str:
        """Generate a hash for the query and k value for caching."""
        query_bytes = query.tobytes()
        k_bytes = str(k).encode()
        combined = query_bytes + k_bytes
        return hashlib.md5(combined).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached result is still valid."""
        return time.time() - timestamp < self._cache_ttl

    def _cleanup_cache(self):
        """Remove expired entries and enforce size limit."""
        current_time = time.time()

        # Remove expired entries
        expired_keys = [
            key for key, (_, timestamp) in self._query_cache.items()
            if not self._is_cache_valid(timestamp)
        ]
        for key in expired_keys:
            del self._query_cache[key]

        # Enforce size limit (simple LRU - remove oldest entries)
        if len(self._query_cache) > self._max_cache_size:
            # Sort by timestamp and remove oldest entries
            sorted_items = sorted(self._query_cache.items(), key=lambda x: x[1][1])
            excess = len(self._query_cache) - self._max_cache_size
            for key, _ in sorted_items[:excess]:
                del self._query_cache[key]

    def upsert(self, vectors: List[np.ndarray], metadatas: List[Dict]):
        """
        Upsert vectors with error handling and service health checks.

        Args:
            vectors: List of embedding vectors
            metadatas: List of metadata dictionaries
        """
        if not self._check_service_health():
            logger.error("Qdrant service unavailable - upsert operation failed")
            raise RuntimeError("Qdrant service is currently unavailable")

        def _perform_upsert():
            import uuid
            points = []
            for i, (v, m) in enumerate(zip(vectors, metadatas)):
                pid = m.get("id") or m.get("hash")
                point_id: int | str

                if isinstance(pid, str):
                    try:
                        point_id = str(uuid.UUID(pid))
                    except Exception:
                        try:
                            point_id = int(pid[:16], 16)
                        except Exception:
                            point_id = i
                elif isinstance(pid, int):
                    point_id = pid
                else:
                    point_id = i

                points.append(qm.PointStruct(id=point_id, vector=v.tolist(), payload=m))

            self.client.upsert(collection_name=self.collection, points=points)
            logger.debug(f"Successfully upserted {len(points)} vectors to collection '{self.collection}'")
            return True  # Return success indicator

        result = retry_with_backoff(
            _perform_upsert,
            max_retries=3,
            base_delay=1.0,
            operation_name=f"Upsert to collection '{self.collection}'"
        )

        if result is None:
            self.service_healthy = False
            raise RuntimeError(f"Failed to upsert vectors to collection '{self.collection}' after retries")

        # Clear cache since vectors have changed
        if result:
            self._query_cache.clear()
            logger.debug("Cleared query cache after upsert operation")

    def search(self, query: np.ndarray, k: int = 4) -> List[Tuple[float, Dict]]:
        """
        Search vectors with error handling, service health checks, and query caching.

        Args:
            query: Query vector
            k: Number of results to return

        Returns:
            List of (similarity_score, metadata) tuples
        """
        if not self._check_service_health():
            logger.error("Qdrant service unavailable - search operation failed")
            return []

        # Check cache first
        query_hash = self._get_query_hash(query, k)
        self._cleanup_cache()

        if query_hash in self._query_cache:
            cached_results, timestamp = self._query_cache[query_hash]
            if self._is_cache_valid(timestamp):
                logger.debug(f"Cache hit for query hash {query_hash[:8]}... (QdrantStore)")
                return cached_results

        def _perform_search():
            res = self.client.search(
                collection_name=self.collection,
                query_vector=query.tolist(),
                limit=k,
                with_payload=True
            )
            out = []
            for r in res:
                out.append((float(r.score), dict(r.payload)))
            logger.debug(f"Successfully searched collection '{self.collection}', returned {len(out)} results")
            return out

        result = retry_with_backoff(
            _perform_search,
            max_retries=2,  # Fewer retries for search to maintain responsiveness
            base_delay=0.5,
            operation_name=f"Search in collection '{self.collection}'"
        )

        if result is None:
            self.service_healthy = False
            logger.warning(f"Search in collection '{self.collection}' failed - returning empty results")
            return []

        # Cache the results (cleanup first to ensure we don't exceed size limit)
        if len(self._query_cache) >= self._max_cache_size:
            # Remove oldest entry to make room
            if self._query_cache:
                oldest_key = min(self._query_cache.keys(), key=lambda k: self._query_cache[k][1])
                del self._query_cache[oldest_key]

        self._query_cache[query_hash] = (result, time.time())
        logger.debug(f"Search returned {len(result)} results from QdrantStore (cached: {query_hash[:8]}...)")

        return result

def create_vector_store(store_type: str, collection_name: str, dim: int = 384) -> VectorStore:
    """
    Factory function to create appropriate vector store instance.

    Args:
        store_type: Type of store ("in_memory" or "qdrant")
        collection_name: Name of the collection (for Qdrant)
        dim: Dimension of the embedding vectors

    Returns:
        VectorStore instance
    """
    if store_type == "qdrant":
        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant client not available. Falling back to InMemoryStore.")
            return InMemoryStore(dim=dim)
        try:
            return QdrantStore(collection=collection_name, dim=dim)
        except Exception as e:
            logger.warning(f"Failed to create Qdrant store: {e}. Falling back to InMemoryStore.")
            return InMemoryStore(dim=dim)
    else:
        return InMemoryStore(dim=dim)