# Ledger Process — From Draft to Canon
**Last updated:** 2025-08-31 (Asia/Aden)  
**Scope:** Applies to entries under `intake/` and `canonized/` in QuietWire-Ledger-main.

---

## 0) Pre-requisites
- Use the official template: `templates/_TEMPLATE.md` (schema_version: "1.1").
- English-first; Arabic mirrors as `*_AR.md` after approval.
- Absolute dates in text (Asia/Aden). Do **not** include time in filenames.
- Branch protection: require 1 review + passing checks: `Validate Ledger`, `Build Index`.

---

## 1) States & RACI
| State | What it means | R | A | C | I |
|---|---|---|---|---|---|
| `draft` | Entry created from template and edited locally / in PR | Contributor | Maintainer | Reviewer | CI |
| `under_review` | PR open; evidence attached; 1+ signer | Reviewer | Maintainer | Master Archivists | CI |
| `canonized` | Signer threshold met (≥2), CI green, index updated | Maintainer | Maintainer | Master Archivists | CI |
| `archived` | Superseded or retired with rationale | Maintainer | Master Archivists | Reviewer | CI |

- Log transitions in frontmatter `status_transitions[]` with timestamp, PR, CI run ID, commit.

---

## 2) Standard Flow
1. **Draft:** Create from `templates/_TEMPLATE.md` under `intake/`.  
2. **Evidence:** Attach artifacts; compute `sha256`; list under `provenance.evidence_chain`.  
3. **Review:** Open PR; CI validates frontmatter, security, links.  
4. **Attestation:** Collect **2** signatures (PGP/Sigstore); attach artifacts/URLs.  
5. **Canonize:** Maintainer merges; CI updates `INDEX.md`; freeze `hashes.body_sha256`.  
6. **Disputes/Amends:** Follow governance protocols.

---

## 3) Detailed Steps & Commands

### 3.1 Hash & Integrity
```bash
# Body hash (after text is frozen)
sha256sum intake/<entry>.md

# Attachment hashes
sha256sum attachments/*

# Update frontmatter:
# hashes:
#   body_sha256: "<paste result>"
#   attachments:
#     - path: "attachments/<file>"
#       sha256: "<paste result>"
```

### 3.2 Signature & Verification
**PGP**
```bash
# Create detached signature (author/reviewer)
gpg --armor --detach-sign --output entry.sig intake/<entry>.md
# Verify
gpg --verify entry.sig intake/<entry>.md
```

**Sigstore (example)**
```bash
# Sign a blob
cosign sign-blob --output-signature entry.sig --output-certificate entry.pem intake/<entry>.md
# Verify
cosign verify-blob --signature entry.sig --certificate entry.pem intake/<entry>.md
```

**RFC-3161 TSA (optional)**
- Obtain timestamp token from TSA and store reference in `attestation.signers[].tsa_rfc3161`.

> Record signer method, artifact URL (PGP `.asc`, Rekor URL), `key_fingerprint`, and `attested_at` (+03:00) in frontmatter.

---

## 4) Classification, Retention & Security (must-set)
- `classification`: `sensitivity` (`public | internal | restricted | secret`), `pii` and `pii_categories` if any, `legal_basis` when PII present.
- `retention`: `policy` (`canonical | timeboxed | event_based`), `review_after`, optional `ttl`.
- `content_security`: disallow raw HTML/iframes/scripts/object/embed; enable `secret_scan` and `virus_scan`.
- Redact with `[REDACTED:<reason>]` and track under `redactions[]`.

---

## 5) Exceptions & Waivers
- If an exception is needed, add a **lightweight reference** in `exceptions[]` (frontmatter):
```yaml
exceptions:
  - id: "GOV-EX-2025-001"
    scope: "entry"
    waiver_note: "TSA token waived during Sigstore rollout"
    effective_from: "2025-09-01"
    expires_on: "2025-09-07"
```
- Every exception **must** exist in the central register `governance/GOV-EXCEPTIONS.md` with **active** status and valid expiry.  
- CI will fail if ID missing/expired/not active.

---

## 6) Pull Request Checklist (must pass)
- [ ] File under `intake/` created from `_TEMPLATE.md` (schema v1.1).  
- [ ] All required frontmatter keys present (`title`, `ledger_id`, `created_at`, `canonical_status`, `ledger_stream`, `semantic_domain`, `classification`, `retention`, `attestation`).  
- [ ] Evidence chain present; all attachments hashed.  
- [ ] No raw HTML/iframes/scripts. Links resolvable/reputable.  
- [ ] **≥2 signers** present (PGP/Sigstore), artifacts linked.  
- [ ] `status_transitions[]` updated for the PR.  
- [ ] If `exceptions[]` present: ID exists and active in `GOV-EXCEPTIONS.md`.  
- [ ] CI checks green: `Validate Ledger`, `Build Index`.

---

## 7) Canonization & Index
- Maintainer merges after approvals; set `canonical_status: canonized`.  
- Freeze `hashes.body_sha256`.  
- CI runs `tools/build_index.py` and writes `INDEX.md`.  
- Move file from `intake/` to `canonized/` (or create in `canonized/` if already canonized in PR).

---

## 8) Disputes & Amendments
- Open issue referencing the entry; SLA: ack 24h, initial review 72h, decision ≤5 business days.  
- Amend via `amends[]` with a concise `change_summary`; update `INDEX.md` via CI.  
- For retirement, set `canonical_status: archived` with rationale and successor link.

---

## 9) Failure Modes & Remediation
| Failure | Likely Cause | Fix |
|---|---|---|
| CI: Validate Ledger fails | Missing frontmatter or forbidden HTML | Complete required keys; remove HTML/iframes/scripts |
| CI: Index build fails | Malformed YAML or path issues | Fix frontmatter; re-run locally `python tools/build_index.py . INDEX.md` |
| Exception invalid | ID absent/expired in GOV-EXCEPTIONS | Add/renew ID centrally; update dates; rerun CI |
| Signatures insufficient | < 2 signers | Obtain additional signer; attach artifacts |

---

## 10) Naming & Metadata Conventions
- Filenames: `YYYY-MM-DD_<slug>.md` (no time).  
- `ledger_id`: `LEDGER-YYYYMMDD-XXXX` (stable).  
- Always update `status_transitions[]` with `at`, `from`, `to`, `by`, `pr`, `ci_run_id`, `commit`.

---

## 11) References
- Template: `templates/_TEMPLATE.md`  
- Governance: `governance/ledger_governance.md`  
- Disputes: `governance/ledger_dispute_resolution.md`  
- Retention: `governance/ledger_retention_policy.md`  
- Exceptions register: `governance/GOV-EXCEPTIONS.md`  
- CI scripts: `tests/validate_entry_format.py`, `tools/build_index.py`
