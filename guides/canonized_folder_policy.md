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

> Scope: This document defines **what is allowed** inside `canonized/`, **how an entry qualifies** for canonization, and **what controls** (governance, security, CI) enforce the rules.

## 1) Purpose & Scope
The `canonized/` directory is reserved **exclusively for approved ledger entries** that satisfy all Canon gates and are ready for long‑term retention and citation. It **MUST NOT** contain guides, READMEs, operational notes, or non‑entry artifacts.

### Out of Scope
- Authoring templates (`templates/`), operational guides (`guides/`), governance documents (`governance/`), tools (`tools/`), and drafts (`intake/`).

---

## 2) Canonization Gates (Acceptance Criteria)
An entry **MUST** meet **all** of the following before it is placed in `canonized/`:

1. **Frontmatter completeness** (see schema below) with valid ISO‑8601 timestamp including timezone offset (`+03:00` preferred for Asia/Aden).
2. **Status & attestation:** `status: ready` **and** `attestation: true`.
3. **Validation clean:** CI validation passes (frontmatter schema, body hash normalization, attachments integrity, security checks).
4. **Signatures:** At least **two** independent signatures are recorded (PGP and/or Sigstore). References to signatures **MUST** be captured in frontmatter or PR metadata.
5. **Evidence policy:** Attachments are small/redacted, declared under `hashes.attachments[]` with `path`, `sha256`, and `size`, and augmented by `provenance.evidence_chain` for large/off‑repo sources.
6. **Links & security:** No forbidden schemes (`javascript:`, `file:`, `data:`), no `<script>` tags, and link checks pass (internal anchors **MUST** resolve).
7. **Indexation:** Eligible for inclusion in the generated `INDEX.md` (metadata sufficient to render group/sort).

> CI workflows that enforce the above: `validate.yml`, `check_links.yml`, `secret_scan.yml`, `build_index.yml`.

---

## 3) Required Frontmatter Schema (Entries Only)
```yaml
---
title: "<short descriptive title>"
author: "Full Name"
timestamp: 2025-08-31T12:30+03:00        # ISO‑8601 with timezone
ledger_stream: "<e.g., NodeActivations>"
semantic_domain: "<e.g., Operational Canon>"
attestation: true                        # canon requires true
validated_by: ["Name A", "Name B"]       # optional but recommended
witness: ["Name C"]                      # optional
slug: "kebab-case-short-slug"
version: "1.0.0"
status: "ready"                          # ready | canon (set to 'canon' on merge if policy prefers)
hashes:
  body_sha256: "<filled by tools/compute_body_hash.py>"
  attachments:
    - path: "attachments/20250831-ui-login-redacted.png"
      sha256: "4a01...77b2"
      size: 103422
provenance:
  evidence_chain:
    - path: "attachments/20250831-ui-login-redacted.png"
    - href: "https://tracker.example.com/tickets/456"
signatures:
  - type: "pgp"
    signer: "KeyID/Email"
    artifact: "path-or-url-to-signature"
  - type: "sigstore"
    signer: "identity@example.com"
    artifact: "path-or-url-to-bundle"
---
```

**Notes**
- `signatures` may be stored in the PR description; include minimal references here (type, signer, artifact) for auditability.
- `status` MAY be transitioned to `canon` by maintainers upon merge; policy can keep `ready` and rely on directory placement as the indicator.

---

## 4) Directory Invariants (Hard Rules)
- `canonized/` **MUST contain only** entry files (`*.md`) that pass the gates above.
- **No** `README.md` or generic guides here. Place such documents in `guides/`.
- When moving a draft to `canonized/`, **do not** lose the `body_sha256` or attachments metadata.
- File naming **SHOULD** match the `slug` and may be prefixed with a date for sorting, e.g.:
  ```
  canonized/
  ├── 2025-08-31-nodeaid-testimony.md
  └── 2025-07-20-field-observation-yemen.md
  ```
- Attachments co‑located with entries are discouraged; prefer `intake/attachments/` during review and keep canonized entries minimal. If attachments are preserved for canon, keep them under a controlled subfolder and ensure hashes are recorded.

---

## 5) Process: Promotion to `canonized/`
1. **Draft & Review** in `intake/` using `templates/_TEMPLATE.md` with required frontmatter.
2. **Quality gates (local):**
   ```bash
   python tools/compute_body_hash.py --root .      --canon-eol --strip-trailing-space --strip-html-comments --update-frontmatter
   python tools/hash_attachments.py --root . --update-frontmatter --sidecar
   python tools/check_links.py --root . --format text --report -
   python tools/secret_scan.py --root . --format text --report -
   python tools/validate_entry_format.py --root .
   ```
3. **PR review:** two maintainers sign off; collect two signatures (PGP/Sigstore).
4. **CI pass:** `validate.yml`, `check_links.yml`, `secret_scan.yml` pass; `build_index.yml` will update `INDEX.md` post‑merge.
5. **Merge & Move:** Maintainer moves the file to `canonized/` (or merges PR targeting `canonized/`). Update `status` to `canon` if your policy requires.
6. **Recordkeeping:** PR description should state signatures, any redactions, and provenance notes.

---

## 6) Amendments, Redactions, and De‑canonization
- **Minor corrections** (typos, formatting) **MAY** be committed with a new `version` and updated `body_sha256`.
- **Substantive changes** (content affecting meaning) **MUST** open a new PR with clear rationale and updated evidence/signatures if applicable.
- **Redactions**: permissible when required for privacy/safety. Mark the change in PR and keep a note in the entry body, e.g., “Redacted for privacy; original retained by Master Archivists.”
- **De‑canonization**: in rare cases (policy breach, evidence invalidation), entries **MAY** be moved out of `canonized/` following `governance/ledger_dispute_resolution.md`.
- All changes **MUST** keep the audit trail (Git history + updated frontmatter).

---

## 7) Security & Compliance Requirements
- **Forbidden content**: no `<script>` tags; no `javascript:`, `file:`, `data:` links.
- **Secrets**: credentials/tokens **MUST NOT** appear; `secret_scan.yml` enforces. Use `.secretignore` and `.secret-baseline.json` sparingly.
- **Attachments**: target ≤ 5 MB (hard upper bound 10 MB). Prefer redacted screenshots/log excerpts + `provenance.evidence_chain.href` to the full source.
- **Licensing**: third‑party content requires attribution and license compliance; if unclear, include a minimal excerpt and link to source.

---

## 8) CI Enforcement (Mapping)
- **validate.yml** → frontmatter schema, normalization checks, attachments declared.
- **check_links.yml** → anchors resolve; external links validated (PR/light vs scheduled/deep).
- **secret_scan.yml** → secret patterns + entropy; fails on HIGH unless allowlisted/baselined.
- **build_index.yml** → regenerates `INDEX.md` sorted by `timestamp desc` and grouped by `ledger_stream`.

---

## 9) Pre‑Canon Checklist (Maintainers)
- [ ] Frontmatter complete and valid (timestamp with TZ, required fields present).  
- [ ] `status: ready` and `attestation: true`.  
- [ ] Body hash computed and up to date (`hashes.body_sha256`).  
- [ ] All attachments hashed and declared; evidence chain present.  
- [ ] Two independent signatures recorded (PGP/Sigstore).  
- [ ] CI green: validate, links, secrets.  
- [ ] Entry name matches `slug` (date prefix optional).  
- [ ] `INDEX.md` rebuilt (automated on merge).

---

## 10) Frequently Asked Questions
**Q: Can I keep large binaries in `canonized/`?**  
A: Avoid it. Prefer small redacted artifacts. For large evidence, include a short excerpt locally and a `provenance.evidence_chain.href` to the full, access‑controlled source.

**Q: Do we require both PGP and Sigstore?**  
A: Any **two independent** signatures suffice. Using both is encouraged; using two PGP signers is also acceptable if independently verifiable.

**Q: May I include a README in `canonized/`?**  
A: No. Place guides in `guides/`. This keeps `canonized/` free of validator noise and focused on entries only.

---

## 11) Change Management
- Update this policy via PR. Keep the `timestamp` current and append a brief change note in the PR body.
- Cross‑references:
  - `governance/ledger_governance.md`
  - `governance/ledger_dispute_resolution.md`
  - `governance/ledger_retention_policy.md`
  - `guides/ledger_process.md`
  - `intake/attachments/README.md`

---

## 12) RFC‑2119 Language
Keywords **MUST**, **MUST NOT**, **SHOULD**, **MAY** are to be interpreted as in RFC‑2119 for normative strength.
