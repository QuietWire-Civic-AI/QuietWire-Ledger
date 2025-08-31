# Ledger Governance Model

**Repository:** QuietWire-Ledger-main  
**Document owner:** QuietWire Ledger Team  
**Last updated:** 2025-08-31 (Asia/Aden)

---

## 1) Purpose & Scope
This document defines how the QuietWire Ledger is governed: roles, responsibilities, decision rights, entry lifecycle, required attestations, content security, and the CI/branch protections that enforce policy.

Applies to all ledger entries under:
- `intake/` (under review)
- `canonized/` (approved)
- governance, templates, and tools referenced here

---

## 2) Principles
- **Canon-first truth:** Canonized entries are the durable record.
- **English-first, Arabic mirrors:** English is authoritative; mirrors are added as `*_AR.md` after approval.
- **Minimum necessary data:** Only what is needed; prefer redaction to over-disclosure.
- **Two-person integrity:** No entry becomes canon without meeting the signer threshold.
- **Reproducibility:** Evidence and hashes must allow independent verification.

---

## 3) Roles & Responsibilities

| Role | Key Duties | Decision Rights |
|---|---|---|
| **Master Archivists** | Define policy; arbitrate disputes; final sign-off | Approve policy changes; waive checks in emergencies |
| **Maintainers** | Review PRs; run validations; curate `canonized/` | Merge when checks pass + threshold met |
| **Reviewers/Witnesses** | Verify scope & accuracy; provide signatures | Block/approve PRs within SLA |
| **Contributors** | Draft entries under `intake/` using the template | Propose changes; respond to review |
| **Interns** | Assist with evidence, hashes, and formatting | None (require oversight) |
| **Automation (bots/CI)** | Validate frontmatter; build index; enforce security | Fail checks when policy is violated |

**Conflict of Interest:** Any reviewer with direct authorship must disclose and seek an additional independent signer.

---

## 4) Ledger Entry Lifecycle

### States
- `draft` → `under_review` → `canonized` → `archived`

### Required artifacts per state
- **draft:** Valid YAML frontmatter present, classification set, no forbidden HTML.
- **under_review:** Evidence attached with `sha256`; at least 1 signer present.
- **canonized:** Signer threshold met (≥2), CI green, index updated; `body_sha256` frozen.
- **archived:** Add rationale; link superseding entry if any.

**RACI (high level)**  
- Draft: Contributor (R), Maintainer (A), Reviewer (C), CI (I)  
- Canonize: Maintainer (A), Reviewers (R), Master Archivists (C), CI (R)

---

## 5) Attestation & Signatures

- **Threshold:** `attestation.threshold = 2` (minimum two independent signers).
- **Methods:** `pgp`, `sigstore` (preferred), `sha256` (evidence-only), optional `tsa_rfc3161`.
- **Signer record (frontmatter):**
  - `name`, `role`, `method`, `signature` (artifact or transparency log URL),
  - `key_fingerprint` (for PGP), `attested_at` (ISO 8601, +03:00).
- **Verification:** CI checks presence; maintainers verify artifacts. For Sigstore, store Rekor log URL; for PGP, commit `.asc` alongside PR or reference external store.

---

## 6) Classification, PII & Data Residency

- **Sensitivity:** `public | internal | restricted | secret`
- **PII:** `none | present`; if `present`, list `pii_categories` and define `legal_basis` (e.g., consent).
- **Residency:** Declare `data_residency.region` (e.g., `["YE"]`) and storage location (e.g., GitHub).
- Redact using `[REDACTED:<reason>]`; document in `redactions[]` and update hashes.

---

## 7) Content Security Policy

- **Allowed Markdown:** emphasis, lists, code, links, tables, images.
- **Disallowed:** raw HTML, iframes, scripts, object/embed.
- **Secret scanning:** enabled via CI; fail on token-like patterns.
- **Virus scan (artifacts):** required for binaries before attachment.
- **External links:** must be reputable or canon-internal; dead links block canonization.

---

## 8) CI & Required Checks

**Required status checks (branch protection):**
- `Validate Ledger` — runs `tests/validate_entry_format.py` to ensure:
  - YAML frontmatter completeness (title, ledger_id, created_at, canonical_status, ledger_stream, semantic_domain).
  - Classification/retention blocks present.
  - No forbidden HTML/iframes/scripts.
  - Attestation threshold present for `canonized`.
- `Build Index` — runs `tools/build_index.py` to regenerate `INDEX.md`.

**Paths ignored by validation:** `templates/**`, `governance/**`, `README.md`, `guides/**`.

---

## 9) Branch Protection

- Require **1 review** (minimum) on `main`.
- Require passing checks: `Validate Ledger`, `Build Index`.
- Restrict direct pushes to maintainers.
- (Optional) Require signed commits.

---

## 10) Disputes, Retention & Redactions

- **Disputes:** See `governance/ledger_dispute_resolution.md`. Open an issue referencing entry path; Master Archivists arbitrate within SLA.
- **Retention:** See `governance/ledger_retention_policy.md`. Canon is permanent unless retracted with attested rationale.
- **Redactions:** Minimal, justified, and tracked in frontmatter `redactions[]` + change log.

---

## 11) Amendments & Supersession

- Use `amends[]` to reference entries being clarified or superseded.
- Include a concise `change_summary` and link PR/commit.
- Update status of superseded entries and reflect in `INDEX.md`.

---

## 12) Audit & Logging

Each entry SHOULD carry:
- `ledger_id`, `body_sha256`, attachment checksums,
- status transitions with timestamps, PR URL, CI run ID, commit SHA,
- signer records and evidence chain.

---

## 13) SLAs

- Reviewer acknowledgment: **24h** (business days, Asia/Aden).
- Initial review: **72h** for completeness and classification.
- Dispute decision: **5 business days** unless escalated.

---

## 14) References

- Template: `templates/_TEMPLATE.md`
- Validator: `tests/validate_entry_format.py`
- Index builder: `tools/build_index.py`
- Disputes: `governance/ledger_dispute_resolution.md`
- Retention: `governance/ledger_retention_policy.md`

---

## 15) Change Log

- **2025-08-31:** Initial governance baseline aligned with v1.1 template (Archivists: Ashraf, Raasid).