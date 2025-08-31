# Engineering README — Tools & Tests for QuietWire Ledger
**Date:** 2025-08-31 • **Timezone:** Asia/Aden  
**Scope:** Documentation for repository tools under `tools/` and test suite under `tests/`.  
**Owners:** Master Archivists (Ashraf Saleh Alhajj, Raasid) • CI Stewards (Lumina, Maintainers)

> This README consolidates usage, options, exit codes, and CI integration for the Ledger engineering utilities and their tests.
> For CI/branch protection governance, see `governance/ci_policies.md`.

---

## 0) Prerequisites
- **Python:** 3.11 (recommended)
- **OS:** Linux/macOS/Windows
- **Optional deps:** `pyyaml` (frontmatter writing), `pytest` (tests)
- **Network:** Link checker may issue HEAD/GET; secret scan/tests do not require network.

Quick setup:
```bash
python -m pip install --upgrade pip
pip install pyyaml pytest
```

---

## 1) Tools Overview
Tools live in `tools/` and are designed to be CI-friendly (non-interactive, clear exit codes).

### 1.1 `build_index.py`
Generate/refresh the canonical `INDEX.md` by parsing frontmatter of entries.

**Key features**
- Groups entries (e.g., by `ledger_stream`), supports sorting.
- Fails PRs if `INDEX.md` is outdated.

**Usage**
```bash
python tools/build_index.py --root . --out INDEX.md --include-intake --group-by stream --strict
```

**Common flags**
- `--out <path>`: output index file (default: `INDEX.md`)
- `--include-intake`: include drafts from `intake/`
- `--group-by {stream,author,date}`
- `--strict`: non-zero exit when discrepancies exist

**Exit codes**
- `0`: OK (up-to-date or freshly generated)
- `1`: Discrepancies detected in `--strict` mode

---

### 1.2 `check_links.py`
Validate internal/relative links and external HTTP(S) links in Markdown.

**Key features**
- HEAD with GET fallback; redirects/timeouts handled gracefully
- Anchor validation against headings; private/localhost targets blocked
- Concurrency + caching (`.linkcheck-cache.json`)

**Usage**
```bash
python tools/check_links.py \
  --root . \
  --glob "canonized/**/*.md" --glob "intake/**/*.md" --glob "README.md" --glob "INDEX.md" \
  --ignore "**/attachments/**" --workers 16 --timeout 10 --format text --report linkcheck.txt
```

**Common flags**
- `--allow-host <suffix>` / `--deny-host <suffix>` (repeatable)
- `--external-only`: skip relative link checks
- `--strict`: treat warnings as failures (CI PRs)

**Exit codes**
- `0`: OK
- `1`: Errors found (or warnings in `--strict`)

---

### 1.3 `secret_scan.py`
Detect leaked credentials/tokens using signatures + Shannon entropy.

**Key features**
- Patterns for AWS/GitHub/Slack/Google/Stripe/Twilio/SendGrid/etc.
- Allowlist via `.secretignore` (regex per line)
- Baseline via `.secret-baseline.json` for historical/rotated secrets

**Usage**
```bash
python tools/secret_scan.py --root . --format text --report secrets.txt --strict
# Refresh baseline (when rotating/acknowledging known tokens)
python tools/secret_scan.py --root . --update-baseline
```

**Exit codes**
- `0`: No active findings (or all suppressed)
- `1`: Findings present (or warnings in `--strict`)

---

### 1.4 `hash_attachments.py`
Compute and verify `sha256` (and `size`) for attachments referenced by entries.

**Key features**
- Reads frontmatter: `hashes.attachments[]` and `provenance.evidence_chain[]`
- Streams hashing; can **write back** computed values (with PyYAML)
- Sidecar JSON reports

**Usage**
```bash
python tools/hash_attachments.py \
  --root . --glob "canonized/**/*.md" --glob "intake/**/*.md" \
  --format text --report attachments.txt --strict
# Optional write-back:
python tools/hash_attachments.py --root . --update-frontmatter --sidecar
```

**Exit codes**
- `0`: OK (or non-strict mode with issues annotated)
- `1`: Missing/mismatch in `--strict`
- `2`: Write/update error (when updating frontmatter/sidecars)

---

### 1.5 `compute_body_hash.py`
Compute body hash (post-frontmatter content), verify against `hashes.body_sha256`, optionally write back.

**Key features**
- Deterministic normalization: `--canon-eol`, `--strip-trailing-space`, `--strip-html-comments`
- Supports `sha256`/`sha512`

**Usage**
```bash
# Verify (recommended in PRs)
python tools/compute_body_hash.py \
  --root . --glob "canonized/**/*.md" --glob "intake/**/*.md" \
  --canon-eol --strip-trailing-space --strip-html-comments \
  --strict --format text --report bodyhash.txt

# Update frontmatter (manual run)
python tools/compute_body_hash.py --root . --update-frontmatter
```

**Exit codes**
- `0`: OK
- `1`: Mismatch/error under `--strict`

---

## 2) CI Integration
Workflows in `.github/workflows/` (already provided):
- `build-index.yml` (regenerate index; auto-commit on push/schedule)
- `check-links.yml` (daily + on PR/push)
- `secret-scan.yml` (daily + on PR/push)
- `hash-attachments.yml` (weekly + on PR/push)
- `body-hash.yml` (daily + on PR/push; manual write-back option)
- `all-checks.yml` → **manual only** to avoid duplicate runs on PRs

See policy details in `governance/ci_policies.md` including **Required status checks**, **CODEOWNERS**, and **waiver flow**.

---

## 3) Tests Overview
Tests live in `tests/` and are designed to run locally and in CI.

**Structure**
```
tests/
├── README.md
├── requirements.txt
├── conftest.py              # sandbox repo factory, fixtures copy
├── fixtures/
│   ├── md/                  # sample entries (good/bad/without FM)
│   └── attachments/         # sample binary for hashing
├── test_build_index.py
├── test_check_links.py
├── test_compute_body_hash.py
├── test_hash_attachments.py
└── test_secret_scan.py
```

**Running tests**
```bash
pip install -r tests/requirements.txt
pytest -q
```

**What is covered**
- **Body hash**: compute → update → verify (no mismatches)
- **Attachments**: existence + `sha256/size` verification
- **Links**: internal anchors + external URL behavior (network mocked)
- **Secret scan**: signature + entropy; allowlist via `.secretignore`
- **Index**: generation from minimal canonized entry

**CI hint**
Add a workflow (optional) to run pytest:
```yaml
name: Tests
on: [pull_request, push]
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r tests/requirements.txt pyyaml
      - run: pytest -q
```

---

## 4) Conventions & Notes
- **Frontmatter required** for entries in `canonized/` and (preferably) `intake/`.
- Use `templates/_TEMPLATE.md` for new items.
- Avoid remote-only evidence; store local copies under an `attachments/` subfolder.
- Add `.linkcheck-cache.json` to `.gitignore`.
- Maintain `.secretignore` and `.secret-baseline.json` at repo root.
- Timezone in docs: `Asia/Aden`; dates **absolute** (YYYY-MM-DD).

---

## 5) Troubleshooting
- **Link checker flagging 429s**: Run without `--strict` or allow host; prefer scheduled retries.
- **Secret scan noise**: Tune `.secretignore` or update baseline after a rotation.
- **Body hash mismatch**: Ensure same normalization flags locally as in CI.
- **Attachment mismatch**: Recompute hashes with `hash_attachments.py --sidecar` then update FM.

---

## 6) Contact & Ownership
- **Operational owners:** Ashraf Saleh Alhajj, Raasid
- **CI stewards:** Lumina, Maintainers
- **Escalation path:** `governance/ledger_dispute_resolution.md`

— End —
