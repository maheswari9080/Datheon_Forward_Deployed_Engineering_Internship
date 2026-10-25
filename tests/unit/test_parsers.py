"""Unit tests for document parsers and provenance extraction."""

import pytest
from eig.ingestion.parsers.pdf_parser import PDFDocumentParser
from eig.ingestion.parsers.csv_parser import CSVDocumentParser
from eig.ingestion.parsers.markdown_parser import MarkdownDocumentParser


def test_pdf_parser_provenance(sample_pdf_bytes):
    parser = PDFDocumentParser()
    sections = parser.parse(sample_pdf_bytes, "security_architecture.pdf")

    assert len(sections) == 2
    assert sections[0].page_number == 1
    assert "Enterprise Security Architecture" in sections[0].text
    assert sections[1].page_number == 2
    assert "Incident Response Protocols" in sections[1].text


def test_pdf_parser_corrupt_stream():
    parser = PDFDocumentParser()
    with pytest.raises(ValueError, match="does not contain valid PDF magic bytes"):
        parser.parse(b"NOT_A_PDF_STREAM", "bad.pdf")


def test_csv_parser_row_traceability(sample_csv_bytes):
    parser = CSVDocumentParser()
    sections = parser.parse(sample_csv_bytes, "quarterly_tx.csv")

    assert len(sections) == 3
    # Check row 1 provenance
    assert sections[0].row_number == 1
    assert "Record [Row 1]" in sections[0].text
    assert "Amazon Web Services" in sections[0].text
    assert sections[0].extra_metadata["detected_date"] == "2026-04-10"

    # Check row 3 provenance
    assert sections[2].row_number == 3
    assert "NVIDIA Enterprise" in sections[2].text


def test_csv_parser_empty():
    parser = CSVDocumentParser()
    with pytest.raises(ValueError, match="is empty"):
        parser.parse(b"", "empty.csv")


def test_markdown_parser_hierarchy(sample_markdown_bytes):
    parser = MarkdownDocumentParser()
    sections = parser.parse(sample_markdown_bytes, "governance.md")

    assert len(sections) >= 2
    # Verify section title breadcrumb preservation
    headers = [s.section_header for s in sections]
    assert any("Access Control Requirements" in h for h in headers)
    assert any("Clearance Tiers" in h for h in headers)

    # Verify date extraction from document
    assert sections[0].extra_metadata["detected_date"] == "2026-05-01"
