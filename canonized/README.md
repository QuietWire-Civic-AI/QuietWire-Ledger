# Canonized — Rules & Format (QuietWire Ledger)

**Last updated:** 2025-08-31 (Asia/Aden)  
**Scope:** This folder contains **only** entries with `canonical_status: canonized`.

---

## Inclusion Rules (must)
- `canonical_status: "canonized"` in YAML frontmatter.
- **Signers ≥ 2** (independent), using **PGP** and/or **Sigstore**. Artifacts must be publicly verifiable (PGP `.asc` / Rekor URL / TSA token).
- `hashes.body_sha256` recorded after text freeze.
- `classification` and `retention` blocks present and valid.
- No raw HTML/iframes/scripts/object/embed.
- Filename format: `YYYY-MM-DD_<slug>.md` (no time in filename).

## Required Frontmatter (minimum)
`title`, `ledger_id`, `created_at`, `canonical_status`, `ledger_stream`, `semantic_domain`, `classification`, `retention`, `attestation.threshold`, `attestation.signers[]`, `provenance.hashes.body_sha256`.

## Amendments & Archival
- Corrections by **amendment**: add `amends[]` in the new entry and link the prior `ledger_id`.
- Retirement: set `canonical_status: archived` (or move to `archived/`) with rationale and successor link.
- Any waiver requires an active record in `governance/GOV-EXCEPTIONS.md` (`Status: active` and not expired).

## Verify Locally (snippets)
```bash
# Body integrity
sha256sum canonized/<entry>.md

# PGP verification (if provided)
gpg --verify entry.sig canonized/<entry>.md

# Sigstore verification (if provided)
cosign verify-blob --signature entry.sig --certificate entry.pem canonized/<entry>.md
```

## Notes
- English is authoritative. Arabic mirrors may be added as `*_AR.md` after approval.
- Absolute timestamps (+03:00). Do not include time in filenames.
