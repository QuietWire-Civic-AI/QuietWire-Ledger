# Ledger Retention & Archiving Policy

**Canon permanence.** Canonized entries are durable; changes occur via **amendment** or **supersession**, never silent edits.

## Policies
- **Canonical (default):** Permanent; reviewed annually (`review_after`) for classification/PII hygiene.  
- **Timeboxed:** Auto-archive after `ttl`.  
- **Event-based:** Archive when successor entry is canonized.

## Archiving
- Move to `archived/` (or mark `canonical_status: archived`) with **rationale** and linking successor via `amends[]`.

## Redaction
- Use `[REDACTED:<reason>]`; record in `redactions[]`; recompute `body_sha256` and attachment hashes.

## Audit
- Retention decisions must cite PR/issue; CI updates the index.

