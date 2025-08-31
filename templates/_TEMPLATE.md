---
schema_version: "1.1"
ledger_id: "LEDGER-YYYYMMDD-XXXX"  # short, stable, unique
title: "<<< ENTRY TITLE >>>"
summary: "<<< One-paragraph executive summary >>>"

authors:
  - name: "<<< Full name >>>"
    role: "<<< Role (e.g., Node Custodian) >>>"
    email: "<<< optional >>>"

owner: "<<< Accountable maintainer/team >>>"
created_at: "2025-08-31T00:00:00+03:00"   # ISO 8601 (Asia/Aden)
updated_at: null
canonical_status: "draft"  # draft | under_review | canonized | archived
status_transitions:
  - at: "2025-08-31T00:00:00+03:00"
    from: "draft"
    to: "under_review"
    by: "<<< maintainer >>>"
    pr: "https://github.com/.../pull/<id>"
    ci_run_id: "github-actions:<run-id>"
    commit: "<commit-sha>"

ledger_stream: "<<< e.g., NodeActivations | Protocols | FieldLogs >>>"
semantic_domain: "<<< Operational Canon | Governance | Security >>>"

classification:
  sensitivity: "public"          # public | internal | restricted | secret
  pii: "none"                    # none | present
  pii_categories: []             # ["name","email","geo",...]
  legal_basis: null              # e.g., "consent","contract","legitimate_interest"
data_residency:
  region: ["YE"]
  storage_location: "GitHub"

retention:
  policy: "canonical"            # canonical | timeboxed | event_based
  review_after: "2026-01-01"
  ttl: null

attestation:
  threshold: 2
  signers:
    - name: "<<< Reviewer/Witness 1 >>>"
      role: "reviewer"
      method: "pgp"              # pgp | sigstore | sha256
      signature: "<<< base64 or transparency log URL >>>"
      key_fingerprint: "<<< hex >>>"
      tsa_rfc3161: "<<< optional timestamp token >>>"
      attested_at: "2025-08-31T00:00:00+03:00"
    - name: "<<< Reviewer/Witness 2 >>>"
      role: "maintainer"
      method: "sigstore"
      signature: "<<< sigstore transparency log entry >>>"
      key_fingerprint: "<<< hex >>>"
      tsa_rfc3161: null
      attested_at: "2025-08-31T00:00:00+03:00"

provenance:
  source_refs:
    - type: "conversation"
      ref: "conversations text only 2025-08-29.zip#<pointer>"
    - type: "issue"
      ref: "https://github.com/quietwire/QuietWire-Ledger/issues/<id>"
  evidence_chain:
    - type: "log"
      path: "attachments/syslog_2025-08-31.txt"
      sha256: "<sha256>"
      captured_at: "2025-08-31T00:05:00+03:00"
      tool: "journalctl"
      observer: "<<< name >>>"
  hashes:
    body_sha256: "<<< fill after final text is frozen >>>"
    attachments:
      - path: "attachments/<filename>"
        sha256: "<<< checksum >>>"

related: []
dependencies: []

governance:
  policy_refs:
    - "governance/ledger_governance.md"
    - "governance/ledger_retention_policy.md"
    - "governance/ledger_dispute_resolution.md"

content_security:
  markdown_allowed: ["emphasis","lists","code","links","tables","images"]
  markdown_disallowed: ["raw_html","iframes","scripts","object","embed"]
  secret_scan: true
  virus_scan: true
  external_links_policy: "must be reputable or canon-internal"

risk:
  model: "STRIDE"
  severity:
    likelihood: "low"   # low | medium | high
    impact: "low"       # low | medium | high
    score: 2
  mitigations: ["<<< key mitigations applied >>>"]

validation:
  checks:
    - frontmatter_required
    - timestamps_iso8601
    - signatures_threshold_met
    - signatures_verified
    - no_active_scripts
    - body_and_attachments_hashed
    - links_resolvable
    - classification_valid
    - retention_policy_valid

exceptions: []   # [{id:"GOV-EX-2025-001", scope:"entry", waiver_note:"...", effective_from:"2025-09-01", expires_on:"2025-09-07"}]

locale: "en"
mirrors:
  - locale: "ar"
    path: "<<< when approved, *_AR.md >>>"
    parity: "pending"   # pending | verified

amends: []
redactions: []
---

# {title}

> **Ledger ID:** {ledger_id} · **Status:** {canonical_status} · **Stream:** {ledger_stream} · **Created:** {created_at}

## 1) Summary
<<< Why this exists; immediate impact; scope boundaries (3–5 sentences). >>>

## 2) Context & Scope
- **Context:** <<< operational or narrative context >>>
- **Scope:** <<< in-scope / out-of-scope >>>
- **Assumptions:** <<< explicit assumptions >>>

## 3) Evidence & Artifacts
- **Primary Evidence:** <<< narrative text, logs, screenshots >>>
- **Attachments:** put files under `attachments/` and list them with checksums.
- **Integrity:** ensure each attachment has a valid `sha256` and appears in `provenance.evidence_chain`.

## 4) Attestation Block (Human-Readable)
- **Threshold:** {attestation.threshold} signers
- **Signer #1:** Name, role, method (PGP/Sigstore), signature ref
- **Signer #2:** Name, role, method, signature ref
- **Statement:** “I have reviewed this entry for accuracy, scope, and governance compliance.”

## 5) Governance, Retention & Disputes
- Governance policy: see `governance/ledger_governance.md`
- Retention policy: see `governance/ledger_retention_policy.md`
- Disputes: see `governance/ledger_dispute_resolution.md`

## 6) Risk & Mitigations
- Model: {risk.model}
- Severity: L={risk.severity.likelihood} / I={risk.severity.impact} / Score={risk.severity.score}
- Key mitigations: {risk.mitigations}

## 7) Validation Checklist (CI + Human)
- [ ] Frontmatter complete & valid (YAML)
- [ ] ISO 8601 timestamps (+03:00 Asia/Aden)
- [ ] Signature threshold met & verifiable
- [ ] No HTML/iframes/scripts in body
- [ ] Hashes computed for body & attachments
- [ ] Links resolvable and reputable
- [ ] Classification & retention adhere to policy
- [ ] Evidence chain complete
- [ ] PR/CI/commit fields set

## 8) Reproducibility Steps
1. Fetch artifacts & verify `sha256`.
2. Re-run tools listed in `provenance.evidence_chain`.
3. Compare results; note deltas.
4. Recompute `body_sha256` and confirm match.

## 9) Change Log
- **2025-08-31:** Initial draft (author: …)
- **YYYY-MM-DD:** Canonized (maintainer: …) — commit `<hash>`

## 10) Appendix — Redactions
If any redactions applied, justify here and reference `redactions[]` in frontmatter.