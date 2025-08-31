# Intake — Staging Area for Draft Ledger Entries
**Scope:** Under-review (non-canon) content prior to canonization.  
**Timezone baseline:** Asia/Aden • **Dates:** absolute (YYYY-MM-DD) • **Language:** English-first

> `intake/` is the only permitted location for drafts. Anything here is *not* canonical and is subject to change following review, validation, and attestation.

---

## 1) What belongs here
- Drafts created from `templates/_TEMPLATE.md` (or type-specific templates).
- Small evidence artifacts required for review under `intake/attachments/`.
- Iterations (diff-friendly changes). Avoid force-push rewriting history once a PR is open.

**Never place here**
- Canonized artifacts (move to `canonized/`).
- Large binaries not referenced by a draft.
- Live secrets/tokens/credentials (ever).

---

## 2) Directory layout
```
intake/
├── README.md
├── CHECKLIST.md
├── .gitignore
├── .gitkeep
├── attachments/
│   ├── README.md
│   └── sample-evidence.txt
└── examples/
    ├── README.md
    └── draft-demo.md
```

---

## 3) Authoring rules (required frontmatter)
Every draft must start with YAML frontmatter that satisfies the repository schema:
```yaml
---
title: "<short descriptive title>"
author: "Full Name"
timestamp: 2025-08-31T12:30+03:00           # ISO-8601 with timezone
ledger_stream: "<e.g., NodeActivations>"
semantic_domain: "<e.g., Operational Canon>"
attestation: false                          # drafts usually false; set true when canon-ready
validated_by: []                            # string or list of strings
witness: []                                  # optional; string or list
slug: "kebab-case-short-slug"
version: "0.1.0"
status: "draft"                              # draft | review | ready
hashes:
  body_sha256: ""                            # set by tools/compute_body_hash.py
  attachments: []                            # list of {path, sha256, size} by tools/hash_attachments.py
provenance:
  evidence_chain: []                         # optional: [{path: "..."} or {href: "https://..."}]
---
```

### Body conventions
- Include at least one `# H1` heading.
- Use relative links for local files and anchors for sections.
- Prefer short paragraphs; reference evidence via frontmatter rather than inline raw URLs when possible.

---

## 4) Local evidence policy
- Store small evidence under `intake/attachments/` (or a sibling `attachments/` near the draft).
- Reference via frontmatter. Example item:
  ```yaml
  hashes:
    attachments:
      - path: "attachments/example.log"
        sha256: "<auto>"
        size: <auto>
  ```
- For large/licensed media: include a short local extract (if permitted) + a `provenance.evidence_chain` node with `href:` to the full source.

---

## 5) Integrity workflow (deterministic hashing)
Run these commands before opening a PR:
```bash
# Compute normalized body hash (LF EOL, no trailing spaces, strip HTML comments)
python tools/compute_body_hash.py --root .   --canon-eol --strip-trailing-space --strip-html-comments   --update-frontmatter --format text --report -

# Verify & fill attachment hashes/sizes; write sidecar reports
python tools/hash_attachments.py --root . --update-frontmatter --sidecar --format text --report -
```

---

## 6) CI gates (what PRs must pass)
- **validate_entry_format.py**: schema & security (frontmatter fields, timestamp format, disallow `<script>`, block forbidden URI schemes).
- **compute_body_hash.py**: recompute & compare `hashes.body_sha256` using the same normalization.
- **hash_attachments.py**: `sha256` & `size` verification for local evidence.
- **check_links.py**: anchors + external links (private/localhost blocked).
- **secret_scan.py**: signature + entropy-based secret detection.

> See `.github/workflows/*.yml` and `governance/ci_policies.md` for enforcement details.
