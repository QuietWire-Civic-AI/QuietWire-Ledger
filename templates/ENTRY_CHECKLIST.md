# ENTRY_CHECKLIST — Canon Readiness (v1.1)

**Last updated:** 2025-08-31 (Asia/Aden)  
**Scope:** Applies to entries created from `templates/_TEMPLATE.md`.

---

## A) Draft (author)
- [ ] File path under `intake/` and filename `YYYY-MM-DD_<slug>.md` (no time).
- [ ] YAML frontmatter present and valid.
- [ ] Required keys set: `title`, `ledger_id`, `created_at`, `canonical_status`, `ledger_stream`, `semantic_domain`.
- [ ] `classification` block set (`sensitivity`, `pii`, `pii_categories?`, `legal_basis?`).
- [ ] `retention` block set (`policy`, `review_after`, `ttl?`).
- [ ] Evidence added; each attachment has `sha256` and is listed in `provenance.evidence_chain`.
- [ ] No raw HTML/iframes/scripts/object/embed in body.
- [ ] External links are reputable or canon-internal.

## B) Under Review (reviewers/maintainer)
- [ ] At least **1 signer** added; signer record complete (name, role, method, signature URL/artifact, key_fingerprint?, attested_at).
- [ ] Risk section filled (`STRIDE`, likelihood/impact/score, mitigations).
- [ ] `status_transitions[]` updated (to `under_review`) with `at`, `by`, `pr`, `ci_run_id`, `commit`.

## C) Canonization Gate
- [ ] **≥2 signers** (independent) present; artifacts verifiable (PGP/Sigstore/TSA).
- [ ] `hashes.body_sha256` computed after freeze.
- [ ] CI green: `Validate Ledger`, `Build Index`.
- [ ] If `exceptions[]` present → ID exists & active in `governance/GOV-EXCEPTIONS.md` and not expired.
- [ ] Maintainer updates `status_transitions[]` to `canonized` and merges.

## D) Post-Canon (maintainer)
- [ ] Move entry to `canonized/` (or ensure created there via PR).
- [ ] Confirm `INDEX.md` updated by CI.
- [ ] Add/close any follow-up issues (amendments, supersession).

## Quick Commands
```bash
# Hashes
sha256sum intake/<entry>.md
sha256sum attachments/*

# PGP
gpg --armor --detach-sign --output entry.sig intake/<entry>.md
gpg --verify entry.sig intake/<entry>.md

# Sigstore
cosign sign-blob --output-signature entry.sig --output-certificate entry.pem intake/<entry>.md
cosign verify-blob --signature entry.sig --certificate entry.pem intake/<entry>.md