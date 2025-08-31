---
title: "Canonized Folder Policy"
timestamp: 2025-08-31T12:00+03:00
slug: canonized-folder-policy
semantic_domain: "Operational Canon"
ledger_stream: "Governance"
attestation: false
status: guide
---

# Canonized Folder Policy

The `canonized/` directory is reserved **exclusively for approved ledger entries** that satisfy all Canon gates:

- `status: ready` and `attestation: true`
- Validation and security checks pass in CI
- Two independent signatures (PGP and/or Sigstore) recorded in the PR

## Rules

- Do **not** place guides, READMEs, or non-entry documents in `canonized/`.  
  Put such documents in `guides/` instead.
- Each canonized entry **must** include a complete frontmatter as per the template.
- Evidence must be referenced via `provenance.evidence_chain` and small, redacted attachments only.

## Rationale

Keeping `canonized/` strictly for finalized entries prevents accidental validator noise and preserves a clean audit trail.

