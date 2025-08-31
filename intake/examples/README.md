# Intake Examples
This folder provides **reference drafts** demonstrating correct frontmatter, local evidence handling, and integrity workflows.

## Contents
- `draft-demo.md` — a minimal, policy-compliant draft that references `../attachments/sample-evidence.txt`.

## How to Use
1. Open and read `draft-demo.md` to see the required **YAML frontmatter**.
2. Run the integrity tools locally (same flags as CI):
   ```bash
   # Compute body hash with deterministic normalization
   python tools/compute_body_hash.py --root . \
    --canon-eol --strip-trailing-space --strip-html-comments \
    --update-frontmatter --format text --report -

   # Hash attachments referenced in frontmatter
   python tools/hash_attachments.py --root . \
    --update-frontmatter --sidecar --format text --report -
   ```
3. Validate links, anchors, and security:
   ```bash
   python tools/check_links.py --root . \
    --glob "intake/**/*.md" --ignore "**/attachments/**" --format text --report -

   python tools/secret_scan.py --root . --format text --report -
   ```
4. Open a Pull Request and ensure all CI gates are green.

## Conventions Recap
- **Frontmatter required** with fields: `title`, `author`, `timestamp(+TZ)`, `ledger_stream`, `semantic_domain`, `attestation`.
- **Relative paths** for local attachments (e.g., `../attachments/sample-evidence.txt`).
- **No forbidden schemes** (`javascript:`, `file:`, `data:`) and **no `<script>` tags**.
- **Asia/Aden** timezone; use absolute dates.

## Next Steps
- Duplicate `draft-demo.md` under your own filename (e.g., `2025-08-31-my-entry.md`).
- Replace the body content with your draft; keep the frontmatter structure.
- Attach your evidence under `intake/attachments/` and reference it in frontmatter.
