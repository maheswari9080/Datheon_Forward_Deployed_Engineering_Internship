"""Context-window budgeting and duplicate-context removal."""

from typing import List, Tuple
from eig.ingestion.models import DocumentChunk


class ContextWindowBudgeter:
    """Budgets retrieved chunks to fit strictly within model token and context constraints."""

    def __init__(self, max_tokens: int = 4000, max_chunks: int = 5):
        self.max_tokens = max_tokens
        self.max_chunks = max_chunks

    def _estimate_tokens(self, text: str) -> int:
        """Conservative token estimation (~4 characters per token)."""
        return max(1, len(text) // 4)

    def select_budgeted_chunks(
        self,
        scored_candidates: List[Tuple[DocumentChunk, float]]
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Deduplicates context by content/chunk_id and enforces max_tokens and max_chunks.
        Maintains order by relevance score.
        """
        seen_chunk_ids = set()
        seen_texts = set()
        budgeted: List[Tuple[DocumentChunk, float]] = []
        total_tokens = 0

        for chunk, score in scored_candidates:
            if chunk.chunk_id in seen_chunk_ids:
                continue

            # Check near-duplicate text
            normalized_text = " ".join(chunk.text.split())
            if normalized_text in seen_texts:
                continue

            chunk_tokens = self._estimate_tokens(chunk.text)
            if total_tokens + chunk_tokens > self.max_tokens:
                # Context limit reached
                break

            seen_chunk_ids.add(chunk.chunk_id)
            seen_texts.add(normalized_text)
            budgeted.append((chunk, score))
            total_tokens += chunk_tokens

            if len(budgeted) >= self.max_chunks:
                break

        return budgeted
