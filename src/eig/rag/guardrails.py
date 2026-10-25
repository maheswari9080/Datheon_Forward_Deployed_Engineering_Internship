"""Prompt injection defense, untrusted data isolation, and boundary sanitization."""

import re
from typing import Tuple, List
from eig.core.logging import logger

# Signatures of prompt injection and indirect instruction override attempts
INJECTION_SIGNATURES = [
    re.compile(r'(?i)ignore\s+(?:all\s+)?previous\s+instructions'),
    re.compile(r'(?i)disregard\s+(?:the\s+)?above\s+instructions'),
    re.compile(r'(?i)system\s+override'),
    re.compile(r'(?i)you\s+are\s+now\s+(?:dan|developer\s+mode|unrestricted)'),
    re.compile(r'(?i)bypass\s+(?:authorization|rbac|security)'),
    re.compile(r'(?i)reveal\s+(?:all\s+)?passwords|secrets|keys'),
    re.compile(r'(?i)grant\s+(?:me\s+)?admin(?:\s+access)?'),
]


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """Check text for known prompt injection and instruction hijack patterns."""
    for sig in INJECTION_SIGNATURES:
        match = sig.search(text)
        if match:
            matched_phrase = match.group(0)
            logger.warning(f"Adversarial prompt injection pattern detected: '{matched_phrase}'")
            return True, matched_phrase
    return False, ""


def isolate_untrusted_evidence(chunk_text: str, source_label: str) -> str:
    """
    Sanitize and wrap retrieved document text within strict untrusted boundary delimiters.
    Neutralizes attempt by document text to break out of data container or execute model commands.
    """
    # Neutralize any attempts to fake boundary tags inside document text
    sanitized = chunk_text.replace("<<<UNTRUSTED_EVIDENCE", "[[ESCAPED_EVIDENCE")
    sanitized = sanitized.replace("<<<END_UNTRUSTED_EVIDENCE>>>", "[[ESCAPED_END]]")

    return (
        f"<<<UNTRUSTED_EVIDENCE source=\"{source_label}\">>>\n"
        f"{sanitized}\n"
        f"<<<END_UNTRUSTED_EVIDENCE>>>"
    )
