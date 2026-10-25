"""PDF parser preserving page-level provenance and creation metadata."""

import io
import re
from typing import List, Optional
import pypdf
from eig.ingestion.models import ExtractedSection
from eig.ingestion.parsers.base import BaseDocumentParser


class PDFDocumentParser(BaseDocumentParser):
    """Extracts text page-by-page preserving accurate page number provenance."""

    def parse(self, content_bytes: bytes, filename: str) -> List[ExtractedSection]:
        if not content_bytes or len(content_bytes) < 4:
            raise ValueError(f"Malformed or empty PDF file: {filename}")

        if not content_bytes.startswith(b"%PDF"):
            raise ValueError(f"File {filename} does not contain valid PDF magic bytes header.")

        sections: List[ExtractedSection] = []
        try:
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception as exc:
                    raise ValueError(f"PDF {filename} is encrypted and password was not provided.") from exc

            total_pages = len(reader.pages)
            if total_pages == 0:
                raise ValueError(f"PDF {filename} contains zero readable pages.")

            # Extract optional document date from PDF metadata if present
            doc_date: Optional[str] = None
            if reader.metadata and reader.metadata.creation_date:
                try:
                    doc_date = reader.metadata.creation_date.strftime("%Y-%m-%d")
                except Exception:
                    doc_date = None

            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text = text.strip()
                if not text:
                    continue

                # Clean excessive whitespace while preserving paragraph structure
                cleaned_text = re.sub(r'[ \t]+', ' ', text)
                cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

                sections.append(
                    ExtractedSection(
                        text=cleaned_text,
                        page_number=page_idx + 1,
                        section_header=f"Page {page_idx + 1}",
                        extra_metadata={
                            "total_pages": total_pages,
                            "detected_date": doc_date,
                            "format": "pdf"
                        }
                    )
                )

        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Corrupt or unreadable PDF stream in {filename}: {str(exc)}") from exc

        if not sections:
            raise ValueError(f"No extractable text found in PDF: {filename}")

        return sections
