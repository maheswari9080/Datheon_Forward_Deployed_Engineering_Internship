"""Abstract base interface for format-specific document extraction."""

from abc import ABC, abstractmethod
from typing import List
from eig.ingestion.models import ExtractedSection


class BaseDocumentParser(ABC):
    """Abstract contract for document parsing with provenance preservation."""

    @abstractmethod
    def parse(self, content_bytes: bytes, filename: str) -> List[ExtractedSection]:
        """Extract sections with explicit page, row, or heading provenance."""
        pass


def safe_decode_text(content_bytes: bytes) -> str:
    """Safely decode byte streams into UTF-8 text with structured fallback handling."""
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            return content_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return content_bytes.decode("utf-8", errors="replace")
