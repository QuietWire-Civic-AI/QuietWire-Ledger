# Draft Entry Checklist (Intake)
Use this *before* opening or updating a PR.

## Metadata & structure
- [ ] File name reflects `slug` (`YYYY-MM-DD-kebab-slug.md` preferred).
- [ ] Required frontmatter present: `title`, `author`, `timestamp` (with TZ), `ledger_stream`, `semantic_domain`, `attestation`.
- [ ] `status` ∈ {draft, review, ready} and `version` set.

## Integrity
- [ ] Body hash computed with normalization:
  ```bash
  python tools/compute_body_hash.py --root .     --canon-eol --strip-trailing-space --strip-html-comments --update-frontmatter
  ```
- [ ] Attachments exist locally and are hashed:
  ```bash
  python tools/hash_attachments.py --root . --update-frontmatter --sidecar
  ```

## Security & hygiene
- [ ] No `<script>` tags or forbidden schemes (`javascript:`, `file:`, `data:`).
- [ ] `tools/secret_scan.py` shows no active findings (or allowlisted with rationale).
- [ ] `tools/check_links.py` passes (anchors + external URLs).

## Attestation (for canonization)
- [ ] Two signatures (PGP/Sigstore) captured; artifacts/URLs in frontmatter.
- [ ] `attestation: true` and validators/witnesses listed when ready.

## PR
- [ ] PR description includes context, evidence summary, and (if any) waiver link.
