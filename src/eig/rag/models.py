"""Data models for RAG queries, citations, and responses."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Verifiable source citation matching strict enterprise specification."""
    document_name: str = Field(..., description="Source filename")
    page_number: Optional[int] = Field(default=None, description="Page number when available")
    row_number: Optional[int] = Field(default=None, description="Row number when available")
    section_header: Optional[str] = Field(default=None, description="Section heading context")
    chunk_id: str = Field(..., description="Stable unique chunk identifier")
    snippet: str = Field(..., description="Brief representative text excerpt")

    def format_citation(self) -> str:
        """Produce standardized citation string."""
        provenance = []
        if self.page_number is not None:
            provenance.append(f"Page {self.page_number}")
        if self.row_number is not None:
            provenance.append(f"Row {self.row_number}")
        if self.section_header:
            provenance.append(f"Section: {self.section_header}")

        prov_str = ", ".join(provenance) if provenance else "Full Document"
        return f"[{self.document_name} | {prov_str} | ID: {self.chunk_id}]"


class RAGQueryRequest(BaseModel):
    """Enterprise RAG query request payload."""
    query: str = Field(..., min_length=2, max_length=1000, description="User's natural language question")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum retrieved chunks to include")
    enable_reranking: bool = Field(default=True, description="Whether to apply cross-encoder reranking")
    include_raw_chunks: bool = Field(default=False, description="Include raw chunk payloads in response")


class RAGQueryResponse(BaseModel):
    """Grounded RAG response with verifiable citations and evidence classification."""
    query: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    insufficient_evidence: bool = False
    chunks_evaluated: int = 0
    execution_time_seconds: float = 0.0
    debug_trace: Optional[Dict[str, Any]] = None
