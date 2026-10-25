"""Deterministic, L2-normalized embedding provider for air-gapped testing and local development."""

import hashlib
import math
import re
from typing import List
from eig.ingestion.embeddings.base import BaseEmbeddingProvider


class DeterministicMockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Generates deterministic, unit-normalized dense vectors.
    Uses hashed character n-grams and term buckets to maintain cosine similarity
    proportional to lexical and term overlap without external network or GPU dependencies.
    """

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _hash_token_to_vector(self, token: str, vector: List[float], weight: float = 1.0) -> None:
        """Hash a token or n-gram into multiple vector dimensions using MD5 & SHA1."""
        h1 = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        h2 = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16)

        dim = self._dimension
        idx1 = h1 % dim
        idx2 = (h1 >> 16) % dim
        idx3 = h2 % dim

        sign1 = 1.0 if (h1 & 1) == 0 else -1.0
        sign2 = 1.0 if (h2 & 1) == 0 else -1.0
        sign3 = 1.0 if ((h1 ^ h2) & 1) == 0 else -1.0

        vector[idx1] += sign1 * weight
        vector[idx2] += sign2 * weight * 0.7
        vector[idx3] += sign3 * weight * 0.5

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []

        for text in texts:
            vec = [0.0] * self._dimension
            tokens = re.findall(r'\w+', text.lower())

            if not tokens:
                # Fallback for empty text: stable small vector
                vec[0] = 1.0
                embeddings.append(vec)
                continue

            for t in tokens:
                self._hash_token_to_vector(t, vec, weight=1.0)
                # Substring 3-grams for morphological similarity
                if len(t) >= 4:
                    for i in range(len(t) - 2):
                        sub = t[i:i + 3]
                        self._hash_token_to_vector(sub, vec, weight=0.3)

            # L2 Normalize
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 1e-9:
                vec = [x / norm for x in vec]
            else:
                vec[0] = 1.0

            embeddings.append(vec)

        return embeddings
