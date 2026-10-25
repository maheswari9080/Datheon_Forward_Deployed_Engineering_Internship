"""CSV document parser preserving headers and row-level traceability."""

import csv
import io
import re
from typing import List, Optional
from eig.ingestion.models import ExtractedSection
from eig.ingestion.parsers.base import BaseDocumentParser, safe_decode_text


class CSVDocumentParser(BaseDocumentParser):
    """Parses tabular CSV documents into traceable row-level records."""

    def parse(self, content_bytes: bytes, filename: str) -> List[ExtractedSection]:
        if not content_bytes or len(content_bytes.strip()) == 0:
            raise ValueError(f"CSV file {filename} is empty.")

        text_content = safe_decode_text(content_bytes)
        stream = io.StringIO(text_content.strip())

        try:
            # Sniff delimiter with fallback to comma
            sample = text_content[:2048]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
            except Exception:
                dialect = csv.excel

            stream.seek(0)
            reader = csv.reader(stream, dialect=dialect)
            header_row = next(reader, None)
            if not header_row:
                raise ValueError(f"CSV file {filename} does not contain a valid header row.")

            headers = [h.strip() for h in header_row if h.strip()]
            if not headers:
                raise ValueError(f"CSV file {filename} contains empty headers.")

            # Identify candidate date column
            date_col_idx: Optional[int] = None
            date_patterns = ["date", "timestamp", "period", "created_at", "effective_date"]
            for idx, h in enumerate(headers):
                if any(p in h.lower() for p in date_patterns):
                    date_col_idx = idx
                    break

            sections: List[ExtractedSection] = []
            for row_idx, row in enumerate(reader, start=1):
                if not row or not any(cell.strip() for cell in row):
                    continue

                # Format human & embedding readable row summary with headers
                row_items = []
                detected_row_date: Optional[str] = None
                for col_idx, cell in enumerate(row):
                    if col_idx < len(headers):
                        col_name = headers[col_idx]
                        cell_val = cell.strip()
                        row_items.append(f"{col_name}: {cell_val}")
                        if col_idx == date_col_idx and re.match(r'^\d{4}-\d{2}-\d{2}', cell_val):
                            detected_row_date = cell_val[:10]

                row_text = f"Record [Row {row_idx}]: " + " | ".join(row_items)
                sections.append(
                    ExtractedSection(
                        text=row_text,
                        row_number=row_idx,
                        section_header=f"Row {row_idx}",
                        extra_metadata={
                            "format": "csv",
                            "columns": headers,
                            "detected_date": detected_row_date
                        }
                    )
                )

            if not sections:
                raise ValueError(f"CSV file {filename} contains headers but zero data rows.")

            return sections

        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Error parsing CSV file {filename}: {str(exc)}") from exc
