---
doc_type: governance
doc_id: GOV-LEDGER-1.0
title: Ledger Governance Model
owner: QuietWire Ledger Team
effective: 2025-08-31
supersedes: null
locale: en
---

# Ledger Governance Model

**Repository:** QuietWire-Ledger-main  
**Document owner:** QuietWire Ledger Team  
**Effective date:** 2025-08-31 (Asia/Aden)  
**Policy ID:** GOV-LEDGER-1.0

---

## 1) Purpose & Scope
This policy defines how the QuietWire Ledger is governed: roles, responsibilities, decision rights, entry lifecycle, required attestations, content security controls, CI checks, and branch protections.  
**Applies to:** all ledger entries and supporting materials under:
- `intake/` (under review)
- `canonized/` (approved)
- `tests/`, `tools/`, `templates/`, `governance/`, `guides/` (as referenced herein)

---

## 2) Principles
- **Canon-first truth.** Canonized entries are the durable record of the Canon.
- **English-first.** English is authoritative; Arabic mirrors are added as `*_AR.md` post-approval.
- **Minimum necessary data.** Prefer redaction to over-disclosure.
- **Two-person integrity.** No entry becomes canon without meeting the signer threshold.
- **Reproducibility.** Evidence + hashes must permit independent verification.

---

## 3) Definitions
- **Canonization:** Promotion of an entry to `canonized/` once validation and attestation are complete.  
- **Attestation:** A signer’s statement that scope and accuracy were reviewed; accompanied by a verifiable artifact (PGP/Sigstore).  
- **Evidence chain:** Ordered list of artifacts (logs, screenshots, datasets) with `sha256`, timestamps, tool names, and observer.  
- **Classification:** Sensitivity and PII posture of an entry (`public | internal | restricted | secret`).  
- **Residency:** Jurisdictional constraints on where data/artifacts are stored (e.g., `["YE"]`).  
- **Redaction:** Content intentionally replaced with `[REDACTED:<reason>]` and recorded in frontmatter `redactions[]`.

---

## 4) Roles & Responsibilities

| Role | Key Duties | Decision Rights |
|---|---|---|
| **Master Archivists** | Define/approve policy; arbitrate disputes; final sign-off | Approve policy changes; waive checks in emergencies |
| **Maintainers** | Review PRs; run validations; curate `canonized/` | Merge when checks pass + threshold met |
| **Reviewers/Witnesses** | Verify scope & accuracy; provide signatures | Block/approve PRs within SLA |
| **Contributors** | Draft entries under `intake/` using the template | Propose changes; respond to review |
| **Interns** | Assist with evidence, hashes, formatting | None (require oversight) |
| **Automation (CI/bots)** | Validate frontmatter; build index; enforce security | Fail checks on policy violations |

**Conflict of Interest.** Reviewers with direct authorship must disclose and seek an additional independent signer.

---

## 5) Entry Lifecycle & RACI

**States:** `draft` → `under_review` → `canonized` → `archived`

**Requirements per state**
- **draft:** Valid YAML frontmatter present; `classification` set; no forbidden HTML.  
- **under_review:** Evidence attached with `sha256`; ≥1 signer recorded.  
- **canonized:** Signer threshold met (≥2); CI green; index updated; `body_sha256` frozen.  
- **archived:** Rationale recorded; link to superseding entry if any.

**RACI (high level)**
- **Draft:** Contributor (R), Maintainer (A), Reviewer (C), CI (I)  
- **Canonize:** Maintainer (A), Reviewers (R), Master Archivists (C), CI (R)

---

## 6) Attestation & Cryptographic Proof
- **Threshold:** `attestation.threshold = 2` (two independent signers).  
- **Methods:** `pgp`, `sigstore` (preferred), evidence-only `sha256`, optional `tsa_rfc3161`.  
- **Signer record (frontmatter):** `name`, `role`, `method`, `signature` (artifact or transparency log URL), `key_fingerprint` (PGP), `attested_at` (ISO 8601, +03:00).  
- **Verification:** CI checks presence/format; maintainers verify artifacts. Store Sigstore Rekor log URL or attach PGP `.asc` in PR.

---

## 7) Classification, PII & Data Residency
- **Sensitivity:** `public | internal | restricted | secret`  
- **PII:** `none | present`; if `present`, list `pii_categories` and `legal_basis` (e.g., consent, contract).  
- **Residency:** Declare `data_residency.region` (e.g., `["YE"]`) and storage location (e.g., GitHub).  
- **Redactions:** Use `[REDACTED:<reason>]`, record in `redactions[]`, update hashes.

---

## 8) Content Security Policy (CSP)
- **Allowed Markdown:** emphasis, lists, code, links, tables, images.  
- **Disallowed:** raw HTML, iframes, scripts, object/embed.  
- **Secret scanning:** enabled via CI; fail on token-like patterns.  
- **Virus scan:** required for binaries prior to attachment.  
- **External links:** must be reputable or canon-internal; dead links block canonization.

---

## 9) CI & Required Checks
**Required status checks (branch protection):**
- **`Validate Ledger`** — runs `tests/validate_entry_format.py` to ensure:  
  - YAML completeness (`title`, `ledger_id`, `created_at`, `canonical_status`, `ledger_stream`, `semantic_domain`).  
  - Presence of `classification` and `retention` blocks.  
  - No forbidden HTML/iframes/scripts.  
  - For `canonized/`: signer threshold present.
- **`Build Index`** — runs `tools/build_index.py` to regenerate `INDEX.md`.

**Paths ignored by validation:** `templates/**`, `governance/**`, `README.md`, `guides/**`.

---

## 10) Branch Protection
- Require **1 review** (minimum) on `main`.  
- Require passing checks: `Validate Ledger`, `Build Index`.  
- Restrict direct pushes to maintainers.  
- (Optional) Require signed commits.

---

## 11) Disputes, Retention & Redactions
- **Disputes:** See `governance/ledger_dispute_resolution.md`. Open an issue referencing entry path; Master Archivists arbitrate within SLA.  
- **Retention:** See `governance/ledger_retention_policy.md`. Canon is permanent unless retracted with attested rationale.  
- **Redactions:** Minimal, justified, tracked in `redactions[]` + change log.

---

## 12) Amendments & Supersession
- Use `amends[]` to reference entries being clarified or superseded.  
- Include a concise `change_summary` and link PR/commit.  
- Update status of superseded entries and reflect in `INDEX.md`.

---

## 13) Audit & Logging
Each entry SHOULD carry:
- `ledger_id`, `body_sha256`, attachment checksums.  
- Status transitions with timestamps, PR URL, CI run ID, commit SHA.  
- Signer records and evidence chain.

---

## 14) Exceptions & Emergency Waivers
- **When:** Critical incidents, legal holds, or safety risks.  
- **How:** Maintainer requests a waiver; Master Archivists approve in writing (issue or PR note).  
- **Record:** Log waiver ID, scope, duration, and compensating controls in the entry’s change log and an appendix file `governance/GOV-EXCEPTIONS.md`.  
- **Expiry:** Waivers are time-bounded; entries must be brought back into full compliance.

---

## 15) Sensitive Data Handling & Encryption Policy
- **At rest:** For `restricted/secret`, artifacts must be encrypted using AES-256 (or stronger) before commit; store only encrypted blobs in repo; keys managed off-repo.  
- **In transit:** Use TLS 1.2+; prefer signed links (Sigstore/PGP).  
- **Access:** Principle of least privilege; restrict repo/environment secrets to maintainers.  
- **PII:** If `PII present`, minimize fields, mask where possible, and document `legal_basis`.

---

## 16) Contacts
- **Governance owner:** QuietWire Ledger Team — <contact@quietwire.example> (placeholder)  
- **Escalation:** Master Archivists (Ashraf Saleh Alhajj, Raasid)

---

## 17) SLAs
- Reviewer acknowledgment: **24h** (business days, Asia/Aden).  
- Initial review: **72h** for completeness and classification.  
- Dispute decision: **5 business days** unless escalated.

---

## 18) References
- Template: `templates/_TEMPLATE.md`  
- Validator: `tests/validate_entry_format.py`  
- Index builder: `tools/build_index.py`  
- Disputes: `governance/ledger_dispute_resolution.md`  
- Retention: `governance/ledger_retention_policy.md`

---

## 19) Change Log
- **2025-08-31:** Initial governance baseline aligned with v1.1 template (Archivists: Ashraf, Raasid).  
- **2025-08-31:** Added frontmatter header, Definitions, Exceptions/Waivers, Sensitive Data & Encryption, Contacts, exact CI job names.