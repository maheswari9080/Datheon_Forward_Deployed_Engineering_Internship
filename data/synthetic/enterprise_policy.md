# Enterprise AI and Data Access Control Policy

Date: 2026-01-10
Department: security
Clearance: Tier 1

## Purpose and Principles
This document establishes rules for autonomous AI agent tool execution, retrieval-augmented generation (RAG), and data provenance.

## Permitted Operations
1. AI agents may execute read operations against inventory and customer catalogs without prior human confirmation.
2. Irreversible or high-risk writes, including lead status updates and support ticket filing, must obtain cryptographic human approval via HMAC tokens.

## Abstention Mandate
When authorized context contains insufficient evidence to substantiate a factual answer, the RAG service must explicitly abstain using the standard INSUFFICIENT_EVIDENCE response rather than hallucinating facts.
