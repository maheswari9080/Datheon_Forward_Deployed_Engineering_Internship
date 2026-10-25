"""Heading-aware Markdown parser that preserves structural section hierarchy."""

import re
from typing import List, Optional
from eig.ingestion.models import ExtractedSection
from eig.ingestion.parsers.base import BaseDocumentParser, safe_decode_text


class MarkdownDocumentParser(BaseDocumentParser):
    """Parses Markdown content preserving hierarchical heading trees."""

    def parse(self, content_bytes: bytes, filename: str) -> List[ExtractedSection]:
        if not content_bytes or len(content_bytes.strip()) == 0:
            raise ValueError(f"Markdown file {filename} is empty.")

        text_content = safe_decode_text(content_bytes)
        lines = text_content.splitlines()

        # Extract optional date from frontmatter or top header lines
        detected_date: Optional[str] = None
        date_regex = re.compile(r'(?i)(?:date|effective_date):\s*["\']?(\d{4}-\d{2}-\d{2})["\']?')
        for line in lines[:25]:
            match = date_regex.search(line)
            if match:
                detected_date = match.group(1)
                break

        sections: List[ExtractedSection] = []
        current_heading_stack: List[str] = ["Document Overview"]
        current_body_lines: List[str] = []

        def flush_current_section():
            if current_body_lines:
                body_text = "\n".join(current_body_lines).strip()
                if body_text:
                    section_title = " > ".join(current_heading_stack)
                    sections.append(
                        ExtractedSection(
                            text=body_text,
                            section_header=section_title,
                            extra_metadata={
                                "format": "markdown",
                                "heading_depth": len(current_heading_stack),
                                "detected_date": detected_date
                            }
                        )
                    )
                current_body_lines.clear()

        heading_pattern = re.compile(r'^(#{1,6})\s+(.*)$')

        for line in lines:
            # Check for Markdown heading
            match = heading_pattern.match(line)
            if match:
                flush_current_section()
                hashes, title = match.groups()
                depth = len(hashes)
                title = title.strip()

                # Adjust hierarchy stack based on heading depth
                if depth == 1:
                    current_heading_stack = [title]
                else:
                    # Truncate stack to depth - 1, then append new heading
                    current_heading_stack = current_heading_stack[:depth - 1]
                    current_heading_stack.append(title)
            else:
                current_body_lines.append(line)

        flush_current_section()

        if not sections:
            # If no headings existed, treat entire content as single root section
            plain_text = text_content.strip()
            if plain_text:
                sections.append(
                    ExtractedSection(
                        text=plain_text,
                        section_header="Document Content",
                        extra_metadata={"format": "markdown", "detected_date": detected_date}
                    )
                )
            else:
                raise ValueError(f"Markdown file {filename} contains no readable content.")

        return sections
