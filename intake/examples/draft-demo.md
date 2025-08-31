---
title: "Demo Draft — Intake"
author: "Your Name"
timestamp: 2025-08-31T12:30+03:00
ledger_stream: "DemoStream"
semantic_domain: "Operational Canon"
attestation: false
validated_by: []
witness: []
slug: "demo-draft-intake"
version: "0.2.0"
status: "draft"  # draft | review | ready
hashes:
  body_sha256: ""   # will be filled by tools/compute_body_hash.py
  attachments:
    - path: "../attachments/sample-evidence.txt"
      # sha256/size will be filled by tools/hash_attachments.py
provenance:
  evidence_chain:
    - path: "../attachments/sample-evidence.txt"
    - href: "https://example.org/reference/ticket/123"  # optional external context
tags: ["demo", "intake", "reference"]
---

# Demo Draft — Intake

This reference draft illustrates a **policy-compliant** intake entry. It demonstrates:

- Required frontmatter fields
- Local evidence declaration & provenance
- Deterministic hashing workflow
- Clear structure with review-friendly sections

## 1. Summary
- **What:** Example intake entry exercising the ledger pipeline.
- **Why:** Provide a canonical starting point for new contributors.
- **Scope:** Non-sensitive, redacted sample only.

## 2. Context
The sample evidence (`../attachments/sample-evidence.txt`) contains a short, **redacted** log extract used to validate hashing and link/anchor checks. No secrets or PII are present.

## 3. Evidence
- Local: `../attachments/sample-evidence.txt` (declared in frontmatter under `hashes.attachments[]` and `provenance.evidence_chain[]`).
- External (optional): `https://example.org/reference/ticket/123` (declared as `href` in provenance).

## 4. Observations
- Startup sequence completes successfully; health endpoint returns 200.
- Sensitive values (IPs, tokens) are **redacted** as policy requires.

## 5. Risks & Mitigations
- *Risk:* Accidental secret inclusion in logs.
  - *Mitigation:* Redaction policy + `tools/secret_scan.py` in CI.
- *Risk:* Evidence file drift (hash mismatch).
  - *Mitigation:* Deterministic hashing & CI verification before merge.

## 6. Integrity Verification
Run locally before opening a PR:
```bash
python tools/compute_body_hash.py --root . \
  --canon-eol --strip-trailing-space --strip-html-comments \
  --update-frontmatter --format text --report -

python tools/hash_attachments.py --root . \
  --update-frontmatter --sidecar --format text --report -
```

## 7. Attestation Plan
- Required: **2** independent signatures (PGP or Sigstore) once content is **ready**.
- Store signature artifacts/links in the PR and reference in frontmatter (e.g., `provenance.evidence_chain` nodes with `href:`).

## 8. Decision Log {#decision-log}
- 2025-08-31: Initial draft created; hashing & link checks validated.

## 9. Next Steps {#next-steps}
1. Replace placeholder author/title/links with real values.
2. Add real evidence under `intake/attachments/` and update frontmatter paths.
3. Request review; when ready, set `attestation: true` and collect signatures.

---
*This demo conforms to QuietWire Ledger policies (governance, security, and CI enforcement).*