import hashlib
import logging
from typing import List
import numpy as np

# Configure structured logging
logger = logging.getLogger(__name__)

def _tokenize(s: str) -> List[str]:
    """Simple tokenization function."""
    return [t.lower() for t in s.split()]

class LocalEmbedder:
    """
    Deterministic feature-hashing TF embedder for lexical similarity.

    This embedder uses feature hashing to convert text into fixed-dimensional
    vectors without requiring external dependencies.
    """

    def __init__(self, dim: int = 384):
        """
        Initialize the embedder with specified dimensionality.

        Args:
            dim: Dimension of the embedding vectors
        """
        self.dim = dim
        logger.debug(f"Initialized LocalEmbedder with dimension {dim}")

    def _hash_token(self, token: str) -> tuple[int, int]:
        """
        Hash a token to determine its position and sign in the embedding.

        Args:
            token: Token to hash

        Returns:
            Tuple of (index, sign) for the token in the embedding vector
        """
        h = hashlib.sha1(token.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % self.dim
        sign = 1 if (h[4] & 1) else -1
        return idx, sign

    def embed(self, text: str) -> np.ndarray:
        """
        Convert text to embedding vector using feature hashing.

        Args:
            text: Input text to embed

        Returns:
            Normalized embedding vector
        """
        vec = np.zeros(self.dim, dtype="float32")

        # Simple tokenization: lowercase, split on non-alphanum boundaries
        toks = []
        cur = []
        for ch in text.lower():
            if ch.isalnum():
                cur.append(ch)
            else:
                if cur:
                    toks.append("".join(cur))
                    cur = []
        if cur:
            toks.append("".join(cur))

        if not toks:
            return vec

        # Feature hashing with signed counts (TF)
        for t in toks:
            idx, s = self._hash_token(t)
            vec[idx] += s

        # L2 normalize
        n = np.linalg.norm(vec)
        if n > 0:
            vec /= n

        return vec

    def get_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        return self.dim