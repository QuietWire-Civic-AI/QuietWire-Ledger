# Intake Attachments — Evidence Handling Guide
**Path:** `intake/attachments/README.md`  
**Last updated:** 2025-08-31 • **Timezone:** Asia/Aden

Attachments are the **local evidence files** that support a draft entry in `intake/`.  
This guide sets the **rules, security controls, and integrity steps** for adding and maintaining evidence.

---

## 1) What goes here (and what doesn’t)

**✅ Put here**
- Small evidence required to **review/verify** a draft (logs, text excerpts, screenshots).
- Redacted/blurred copies of sensitive artifacts when a full copy cannot be stored.

**❌ Do not put here**
- Canonized/approved evidence (move draft to `canonized/` first; attachments move with it).
- Live credentials, API keys, tokens, unredacted PII/PHI, malware, or copyrighted media without permission.
- Huge binaries that are not essential for review. Prefer a **short local excerpt + remote link** under `provenance.evidence_chain`.

> Target size: **≤ 5 MB per file** (hard upper bound **10 MB**). For larger assets, store a **≤ 100 KB excerpt** and add a provenance `href` to the full source.

---

## 2) Directory layout & naming

```
intake/
└── attachments/
    ├── README.md
    ├── <slug>-<yyyyMMdd>-<short>.txt
    ├── <slug>-<yyyyMMdd>-<short>.png
    └── ...
```

**Naming convention**
- `kebab-case`, concise, and tied to the draft `slug`.
- Prefix with date if useful for ordering, e.g., `20250831-node-boot-log.txt`.

**Allowed types**
- `.txt, .md, .log, .json, .csv`
- `.png, .jpg` (redact/blur as needed)
- `.pdf` (text-based preferred; avoid heavy scans)

**Discouraged**
- Proprietary binaries (`.psd`, `.ai`, …), raw dumps, archives (`.zip/.rar`) unless strictly necessary.

---

## 3) Declare attachments in frontmatter

Declare every attachment used by a draft in the **draft file’s** YAML frontmatter.  
The hashing tool will fill values.

```yaml
hashes:
  attachments:
    - path: "attachments/20250831-node-boot-log.txt"
      sha256: "<auto-filled by tools/hash_attachments.py>"
      size: 1234
      mime: "text/plain"           # optional (manual)
provenance:
  evidence_chain:
    - path: "attachments/20250831-node-boot-log.txt"
    - href: "https://source.example.com/ticket/123"   # full source if excerpted
```

> Keep local copies **relative** to the draft location. If your draft is in `intake/examples/`, use `../attachments/...` as the path.

---

## 4) Integrity workflow (deterministic, tool-backed)

Run before opening a PR:

**1) Compute normalized body hash for the draft (LF EOL, strip trailing spaces, strip HTML comments)**
```bash
python tools/compute_body_hash.py --root .   --canon-eol --strip-trailing-space --strip-html-comments   --update-frontmatter --format text --report -
```

**2) Hash all declared attachments (writes sha256/size to frontmatter)**
```bash
python tools/hash_attachments.py --root .   --update-frontmatter --sidecar --format text --report -
```

**Manual verification (optional)**
```bash
sha256sum intake/attachments/<file>
wc -c intake/attachments/<file>     # byte size
```

**Sidecars**
- The hashing tool may emit `<file>.hashes.json` next to attachments or drafts.  
- These are **transient** and should be **gitignored**.

---

## 5) Redaction & sensitive data handling

- **Default to redaction.** Remove or blur names, faces, phone numbers, emails, account IDs, GPS, and any non-public data **before** committing.
- For structured logs: replace tokens with `REDACTED` and keep **context** (timestamps, non-sensitive IDs).
- If redaction materially alters meaning, include a short note in the draft body:

> “This attachment is redacted for privacy. Original retained offline by the Master Archivists.”

- If you must store an encrypted copy (rare), do **not** commit the key; declare only the **ciphertext hash** in provenance and keep the object external.

---

## 6) Licensing & attribution

- Include **source attribution** for third-party materials.  
- Respect license terms; if unknown or restrictive, store a **short quote or screenshot excerpt** under fair use (if applicable) and link to the full source in `provenance.evidence_chain.href`.

---

## 7) Chain-of-custody notes

- If an attachment is replaced/updated, include a bullet in the PR description:  
  `Replaced attachments/foo.png with redacted version; original kept offline; new hash recorded.`
- The **commit history** + **frontmatter hash** is the authoritative record of changes.

---

## 8) Security rules (enforced by tools/CI)

- **Secrets scan** (`tools/secret_scan.py`) must be clean.  
  - Suppress false positives via `.secretignore` with **narrow** regexes and explain in the PR.
- **Links** in drafts must not point to `localhost`, private IPs, or forbidden URI schemes (`javascript:`, `file:`, `data:`).  
- **Malware/active content** prohibited. If in doubt, attach screenshots or text extracts, not executables.

---

## 9) Quick checklist (attachments)

- [ ] File size within policy (< 5 MB, never > 10 MB)  
- [ ] Redacted/blurred as needed; no live tokens/PII  
- [ ] Declared under `hashes.attachments[]` with correct **relative path**  
- [ ] `sha256` and `size` computed by tool  
- [ ] Added to `provenance.evidence_chain` (as `path:` and/or `href:`)  
- [ ] Mentioned contextually in the draft body where relevant

---

## 10) Troubleshooting

**Tool can’t find the path**  
- Check the path is **relative to the draft file** location, not repo root.

**Hash mismatch in CI**  
- Ensure you ran the hashing tool **after** the last change to the attachment.  
- Confirm normalization flags for the body hash (section 4).

**Large file reject**  
- Replace with a short excerpt in `attachments/` + add a `provenance.evidence_chain.href` to the full asset.

---

## 11) Examples

**Minimal log attachment**
```yaml
hashes:
  attachments:
    - path: "attachments/20250831-node-boot-log.txt"
      sha256: "af2d...e91c"
      size: 842
```

**Screenshot with external source**
```yaml
hashes:
  attachments:
    - path: "attachments/20250831-ui-login-redacted.png"
      sha256: "4a01...77b2"
      size: 103422
      mime: "image/png"
provenance:
  evidence_chain:
    - path: "attachments/20250831-ui-login-redacted.png"
    - href: "https://tracker.example.com/tickets/456"
```

---

### Final notes
- Keep attachments **minimal**, **relevant**, and **verifiable**.  
- The goal is to make entries **auditable** without exposing unnecessary sensitive data.
