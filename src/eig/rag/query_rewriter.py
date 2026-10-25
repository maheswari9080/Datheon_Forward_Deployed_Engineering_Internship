"""Query rewriting and expansion for ambiguous or underspecified questions."""

import re
from typing import Dict

# Enterprise term and acronym expansion dictionary
ACRONYM_EXPANSIONS: Dict[str, str] = {
    "hr": "Human Resources",
    "sla": "Service Level Agreement",
    "kpi": "Key Performance Indicator",
    "crm": "Customer Relationship Management",
    "erp": "Enterprise Resource Planning",
    "po": "Purchase Order",
    "nda": "Non-Disclosure Agreement",
    "mou": "Memorandum of Understanding",
    "gdpr": "General Data Protection Regulation",
    "soc2": "System and Organization Controls 2",
    "arr": "Annual Recurring Revenue",
    "ebitda": "Earnings Before Interest, Taxes, Depreciation, and Amortization",
}


class QueryRewriter:
    """Preprocesses and disambiguates user query prior to retrieval."""

    def rewrite_query(self, query: str) -> str:
        """Expand domain acronyms and normalize query for maximum retrieval recall."""
        cleaned = query.strip()
        tokens = re.findall(r'\b\w+\b', cleaned)

        expanded_terms = []
        for token in tokens:
            lower = token.lower()
            if lower in ACRONYM_EXPANSIONS:
                expanded_terms.append(f"{token} ({ACRONYM_EXPANSIONS[lower]})")
            else:
                expanded_terms.append(token)

        # Formulate expanded search query if acronyms were detected
        expanded_query = " ".join(expanded_terms)
        return expanded_query if expanded_query != " ".join(tokens) else cleaned
