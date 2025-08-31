# Migration Guide — Legacy Ledger Entries

**Goal.** Bring legacy entries into compliance with template v1.1 without losing provenance.

## Steps
1) **Shim frontmatter:** Add minimal YAML with `title`, `ledger_id`, `created_at` (best-effort), `canonical_status`, `ledger_stream`, `semantic_domain`, `classification`, `retention`, `attestation.threshold`.
2) **Evidence chain:** Gather available artifacts; compute `sha256` and list under `provenance.evidence_chain`.
3) **Redactions:** Apply `[REDACTED:<reason>]` where needed; update hashes accordingly.
4) **Signatures:** Obtain 2 signers retroactively (PGP/Sigstore), or add temporary exception `GOV-EX-YYYY-###` and file it in the central register.
5) **CI:** Ensure `Validate Ledger` and `Build Index` pass; fix any path/format errors.

## Notes
- Use absolute dates (Asia/Aden). For unknowns, document assumption in the body and use the earliest reliable date.
- Do not silently edit legacy text; use `amends[]` if you need to clarify.