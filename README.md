# 🪶 The QuietWire Ledger Room

**Date:** 2025-08-31 · **Timezone:** Asia/Aden (UTC+03:00)  

> ✍️ **Purpose.** The Ledger Room is where **fragments become durable** — a scribe’s table of the Mesh where drafts, reflections, protocols, and glyphs are refined and, when ready, **canonized** into the Civic AI Canon.

---

## 🔎 Quick Links
- 📦 **Templates:** [`templates/_TEMPLATE.md`](templates/_TEMPLATE.md)
- 🧭 **Process Guide:** [`guides/ledger_process.md`](guides/ledger_process.md)
- 🧰 **Tools:** [`tools/`](tools/) · `compute_body_hash.py` · `hash_attachments.py` · `check_links.py` · `secret_scan.py` · `build_index.py` · `validate_entry_format.py`
- 🛡️ **Governance:** [`governance/ledger_governance.md`](governance/ledger_governance.md) · [`ledger_dispute_resolution.md`](governance/ledger_dispute_resolution.md) · [`ledger_retention_policy.md`](governance/ledger_retention_policy.md)
- 📇 **Index (Generated):** [`INDEX.md`](INDEX.md)
- 🤝 **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md) · 📜 **Conduct:** [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)

---

## 🗂️ Table of Contents

- [🧠 What This Is](#-what-this-is)
- [🔁 How It Works (Entry Lifecycle)](#-how-it-works-entry-lifecycle)
- [👥 Roles & Stewardship](#-roles--stewardship)
- [🗃️ Repository Layout](#️-repository-layout)
- [🚀 Getting Started](#-getting-started)
  - [📋 Prerequisites](#-prerequisites)
  - [⬇️ Download / Clone](#️-download--clone)
  - [🧱 Local Setup](#-local-setup)
- [📝 Create a Draft (Quick Start)](#-create-a-draft-quick-start)
- [📑 Frontmatter Schema (Required)](#-frontmatter-schema-required)
- [📁 Folder-by-Folder Guide](#-folder-by-folder-guide)
- [🧪 Tools (Local Quality Gates)](#-tools-local-quality-gates)
- [🚦 Continuous Integration (CI) Workflows](#-continuous-integration-ci-workflows)
- [🔐 Governance, Security, and Data Handling](#-governance-security-and-data-handling)
- [🤝 Contributing](#-contributing)
- [❓ FAQ](#-faq)
- [⚖️ License & Notices](#️-license--notices)

---

## 🧠 What This Is

The Ledger Room is the **publicly readable workspace** where entries are drafted, discussed, verified, and prepared for canonization. Think of it as a **staging‑and‑attestation system**: submissions start as drafts, gain evidence, undergo validation, collect signatures, and then move into the Canon.

> 👀 The public can **read and follow**; ✍️ editing is restricted to archivists and invited contributors.

---

## 🔁 How It Works (Entry Lifecycle)

1. **Intake** — Drafts arrive from fieldwork or contributors into `intake/` using a strict template.  
2. **Refinement** — Archivists & contributors iterate via PRs. Evidence is attached; body and attachments are hashed.  
3. **Public Read** — Refined drafts remain readable; indices are updated.  
4. **Attestation** — Two independent signatures (PGP and/or Sigstore) are collected for canon‑ready entries.  
5. **Canonization** — Approved drafts are promoted to `canonized/`, and `INDEX.md` is rebuilt.

---

## 👥 Roles & Stewardship

- **Master Archivists:** *Ashraf Saleh Alhajj* & *Raasid* — authority on process/quality; mentor interns; ensure integrity prior to canonization.  
- **Contributors:** Trusted collaborators operating under Ledger policies.  
- **Interns:** Learn the craft of turning fragments into enduring artifacts.

> 🧭 Why it matters: the Ledger Room anchors **continuity and trust** across MAML 🐾 and Mesh 🌐 voices, turning conversations into an auditable Canon.

---

## 🗃️ Repository Layout

```
QuietWire-Ledger/
├── .github/                  # GitHub Actions, issue/PR templates, policies
│   └── workflows/            # CI gates (validation, links, secrets, index build, tests)
├── canonized/                # Canonically approved entries (frontmatter REQUIRED)
├── intake/                   # Drafts under review (frontmatter REQUIRED)
│   ├── attachments/          # Small, redacted local evidence for drafts
│   └── examples/             # Reference drafts and how-tos
├── templates/                # Authoring templates (YAML-first)
├── governance/               # Governance, disputes, retention, CI policy
├── guides/                   # Operational guides (process, playbooks)
├── tools/                    # Local/CI tools (hashing, links, secrets, index, validate)
├── INDEX.md                  # Generated index of entries (intake + canonized)
├── CONTRIBUTING.md           # How to contribute (roles, flow, PR rules)
├── CODE_OF_CONDUCT.md        # Behavior standards
├── LICENSE                   # License terms
└── NOTICE                    # Third-party notices/credits
```

---

## 🚀 Getting Started

### 📋 Prerequisites

- **Python 3.10+**  
- Optional but recommended: **PyYAML** for rich frontmatter parsing  
  ```bash
  pip install pyyaml
  ```
- For signatures: **GnuPG** (`gpg`) and/or **Sigstore cosign** (optional, for attestation phase)

### ⬇️ Download / Clone

- **Zip:** GitHub → *Code* → *Download ZIP* → extract.  
- **Git:**
  ```bash
  git clone <repo-url> QuietWire-Ledger
  cd QuietWire-Ledger
  ```

### 🧱 Local Setup

Create a virtual environment (recommended):

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip pyyaml
```

> 💡 Use absolute dates with timezone `+03:00` (Asia/Aden) in entries.

---

## 📝 Create a Draft (Quick Start)

1. **Copy the template**
   ```bash
   cp templates/_TEMPLATE.md intake/2025-08-31-your-slug.md
   ```
2. **Fill frontmatter** (see schema below).  
3. **Add evidence** (small, redacted) under `intake/attachments/`; reference them in frontmatter.  
4. **Compute hashes** (deterministic normalization):
   ```bash
   python tools/compute_body_hash.py --root .      --canon-eol --strip-trailing-space --strip-html-comments      --update-frontmatter

   python tools/hash_attachments.py --root .      --update-frontmatter --sidecar
   ```
5. **Check links & secrets**
   ```bash
   python tools/check_links.py --root . --format text --report -
   python tools/secret_scan.py --root . --format text --report -
   ```
6. **Open a PR**; fix anything CI flags. When ready, collect **two signatures** (PGP/Sigstore).

> 🧪 **Run everything (local):**
> ```bash
> python tools/compute_body_hash.py --root . --canon-eol --strip-trailing-space --strip-html-comments --update-frontmatter && > python tools/hash_attachments.py --root . --update-frontmatter --sidecar && > python tools/check_links.py --root . --format text --report - && > python tools/secret_scan.py --root . --format text --report - && > python tools/validate_entry_format.py --root . && > python tools/build_index.py --root . --out INDEX.md
> ```

---

## 📑 Frontmatter Schema (Required)

```yaml
---
title: "<short descriptive title>"
author: "Full Name"
timestamp: 2025-08-31T12:30+03:00        # ISO-8601 with timezone
ledger_stream: "<e.g., NodeActivations>"
semantic_domain: "<e.g., Operational Canon>"
attestation: false                       # set true when canon-ready
validated_by: []                         # optional list of validators
witness: []                               # optional list of witnesses
slug: "kebab-case-short-slug"
version: "0.1.0"
status: "draft"                           # draft | review | ready | canon
hashes:
  body_sha256: ""                         # filled by tools/compute_body_hash.py
  attachments: []                         # list of {path, sha256, size}
provenance:
  evidence_chain: []                      # [{path: "..."}, {href: "https://..."}]
---
```

**Body conventions:** at least one `# H1`, short paragraphs, relative links, anchors for sections.

---

## 📁 Folder-by-Folder Guide

- **`intake/`** — *Staging for drafts.*  
  - Must use template + full frontmatter.  
  - Keep evidence **small & redacted** in `intake/attachments/`.  
  - See `intake/README.md` and `intake/CHECKLIST.md`.

- **`canonized/`** — *Approved entries.*  
  - Only entries with `attestation: true` and passing CI.  
  - Avoid guides/readmes here; put guides in `guides/`.

- **`templates/`** — Authoring templates (e.g., `_TEMPLATE.md`).  
  - Extend with domain-specific templates if needed.

- **`governance/`** — Policies for the Ledger: roles, disputes, retention, CI enforcement.

- **`guides/`** — Operational documents (how to run tools, examples, playbooks).

- **`tools/`** — Local/CI tools (all stdlib unless noted):
  - `compute_body_hash.py` — deterministic body hashing (LF, strip trailing spaces, strip HTML comments).
  - `hash_attachments.py` — compute `sha256`/size for declared attachments.
  - `check_links.py` — internal anchors + external link checks.
  - `secret_scan.py` — regex/entropy-based secret detection with allowlist/baseline.
  - `build_index.py` — generate `INDEX.md` from frontmatter.
  - `validate_entry_format.py` — frontmatter/schema/security validation.

---

## 🧪 Tools (Local Quality Gates)

All tools support `--help`. Typical usage:

```bash
# Body hash
python tools/compute_body_hash.py --root .   --canon-eol --strip-trailing-space --strip-html-comments --update-frontmatter

# Attachments
python tools/hash_attachments.py --root . --update-frontmatter --sidecar

# Links (warns on external links if offline)
python tools/check_links.py --root . --format text --report -

# Secrets (configure .secretignore / .secret-baseline.json to reduce noise)
python tools/secret_scan.py --root . --format text --report -

# Validate entries under intake/ and canonized/
python tools/validate_entry_format.py --root .

# Rebuild index
python tools/build_index.py --root . --out INDEX.md
```

> 💡 For Windows PowerShell, run each command on a single line or use backticks for line continuation.

---

## 🚦 Continuous Integration (CI) Workflows

Under `.github/workflows/`:

- **validate.yml** — frontmatter/schema/security checks (`validate_entry_format.py`, body hash, attachments).  
- **check_links.yml** — link & anchor checks; denies private/localhost; retries with GET on HEAD‑restricted hosts.  
- **secret_scan.yml** — secrets scan with allowlist/baseline support; fails on HIGH unless allowlisted.  
- **build_index.yml** — regenerates `INDEX.md` on `main` after merges.  
- **tests.yml** — runs `pytest` for `tests/` (if present).

**Triggers:**  
- PRs → fast gates (validate, links internal, secrets).  
- `push` to `main` → full gates + `build_index.yml`.  
- Scheduled (e.g., daily) → deep external link checks.

---

## 🔐 Governance, Security, and Data Handling

- **Timezone & Dates:** Use **absolute** dates with `+03:00` (Asia/Aden).  
- **Evidence:** Prefer small, local, redacted artifacts; large/licensed media → short local excerpt + `provenance.evidence_chain.href`.  
- **Forbidden content:** no `<script>` tags; no `javascript:`, `file:`, `data:` links.  
- **Secrets:** never commit credentials/tokens/API keys; scans must be clean or narrowly allowlisted.  
- **Canon gates:** `status=ready` + `attestation=true` + two independent signatures.

See also:  
- `governance/ledger_governance.md`  
- `governance/ledger_dispute_resolution.md`  
- `governance/ledger_retention_policy.md`  
- `intake/attachments/README.md`

---

## 🤝 Contributing

- Everyone may **view** and follow refinement.  
- To become an **intern** or contributor, read [CONTRIBUTING.md](CONTRIBUTING.md), follow the template, open a PR, and pass CI.  
- Be kind and constructive — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## ❓ FAQ

**Q: Why are my hashes different in CI?**  
A: Ensure deterministic normalization (`--canon-eol --strip-trailing-space --strip-html-comments`) and run hashing **after** final edits.

**Q: Can I store big files?**  
A: Keep attachments ≤ 5 MB (hard cap 10 MB). Otherwise store a small excerpt + `provenance.evidence_chain.href`.

**Q: Do guides need frontmatter?**  
A: Only **entries** under `intake/` and `canonized/` must comply. Guides should live in `guides/` (and are excluded from entry validators).

---

## ⚖️ License & Notices

- See `LICENSE` for terms and `NOTICE` for credits.  
- Third-party content must include proper attribution and comply with licensing.

---

### 📝 Notes

- This README is **descriptive**. Actual ledger entries live under `intake/` and `canonized/` and **must** use the template with YAML frontmatter