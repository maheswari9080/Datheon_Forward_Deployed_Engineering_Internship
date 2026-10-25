"""Structure-aware and semantic chunking engine with provenance preservation."""

import re
from typing import List, Optional
from eig.ingestion.models import ExtractedSection, DocumentChunk, DocumentMetadata


class DocumentChunker:
    """Splits extracted sections into contextual chunks with boundary awareness and overlap."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 60):
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """Split raw text respecting natural boundaries (paragraphs, sentences, spaces)."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Search backwards for optimal split boundary: double newline > newline > period > space
            split_idx = -1
            boundary_candidates = [
                text.rfind("\n\n", start, end),
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end),
                text.rfind("; ", start, end),
                text.rfind(" ", start, end),
            ]

            for candidate in boundary_candidates:
                if candidate != -1 and candidate > start + (self.chunk_size // 3):
                    # For punctuation, include punctuation in chunk
                    if text[candidate] in [".", "?", "!", ";"]:
                        split_idx = candidate + 1
                    else:
                        split_idx = candidate
                    break

            if split_idx == -1 or split_idx <= start:
                split_idx = end

            chunk = text[start:split_idx].strip()
            if chunk:
                chunks.append(chunk)

            # Advance with overlap
            start = split_idx - self.chunk_overlap
            if start < 0 or start >= split_idx:
                start = split_idx

        return chunks

    def chunk_sections(
        self,
        sections: List[ExtractedSection],
        metadata: DocumentMetadata
    ) -> List[DocumentChunk]:
        """Transform extracted sections into indexed DocumentChunk models with provenance."""
        all_chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for section in sections:
            # Prepend context header if section header exists and is informative
            section_prefix = ""
            if section.section_header and not section.text.startswith(f"[{section.section_header}]"):
                section_prefix = f"[{section.section_header}]\n"

            raw_text = section.text
            sub_pieces = self._split_text_with_overlap(raw_text)

            for piece in sub_pieces:
                formatted_text = f"{section_prefix}{piece}".strip()
                chunk_id = f"{metadata.document_id}_{global_chunk_idx}"

                # Infer document date: metadata date or section-level detected date
                effective_date = metadata.document_date or section.extra_metadata.get("detected_date")

                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=metadata.document_id,
                    tenant_id=metadata.tenant_id,
                    text=formatted_text,
                    page_number=section.page_number,
                    row_number=section.row_number,
                    section_header=section.section_header,
                    department=metadata.department,
                    access_tier=metadata.access_tier,
                    document_date=effective_date,
                    source_filename=metadata.source_filename,
                    content_hash=metadata.content_hash,
                    chunk_index=global_chunk_idx,
                )
                all_chunks.append(chunk)
                global_chunk_idx += 1

        return all_chunks
