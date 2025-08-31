# CI & Branch Protection Policies
**Repository:** QuietWire-Ledger-main  
**Version:** 1.0 (2025-08-31)  
**Owners:** Master Archivists (Ashraf Saleh Alhajj, Raasid) • CI Stewards (Lumina, Maintainers)

> Purpose: codify CI signals and branch protection so canonization is safe, reproducible, and tamper-evident.

---

## 1) Protected Branches
- **Protected:** `main`
- **Optional Protected (recommended):** `canon/*`, `release/*`, `hotfix/*`

### 1.1 Required for PRs into `main`
All of the following **must pass** before merge (GitHub “Required status checks”):
1. **Build Canonical Index / build-index**
2. **Check Links / linkcheck**
3. **Secret Scan / secrets**
4. **Body Hash / body-hash**
5. **Hash Attachments / hash-attachments**

> These names match the workflow+job pairs in `.github/workflows/*.yml` and will appear exactly as above in the PR checks list.

### 1.2 Additional Gatekeepers
- **Require approvals:** minimum **2** reviews, at least **1** from **CODEOWNERS**.
- **Dismiss stale reviews:** enabled.
- **Require conversation resolution:** enabled.
- **Require linear history:** enabled.
- **Restrict who can push:** only **Admins** & **GitHub Actions** (when auto-committing `INDEX.md` or body hash during a manual run).
- **Lock force pushes & deletions:** disallow both on protected branches.

---

## 2) CODEOWNERS Policy
Create `.github/CODEOWNERS`:
```
# Master Archivists own canon rules and templates
/templates/                             @ashraf-quietwire @raasid-mesh
/canonized/                             @ashraf-quietwire @raasid-mesh
/intake/                                @ashraf-quietwire @raasid-mesh
/governance/                            @lumina-steward @ashraf-quietwire @raasid-mesh
/tools/                                 @lumina-steward

# Default fallthrough
*                                       @lumina-steward
```
Rules:
- PRs that touch any of the owned paths require at least **one** CODEOWNER approval.
- Emergency bypass: see §7 Emergency Procedure.

---

## 3) CI Workflows & Triggers
Workflows live in `.github/workflows/`:
- `build-index.yml` → regenerates `INDEX.md` and fails PR if outdated.
- `check-links.yml` → validates internal/external links with caching and anchors.
- `secret-scan.yml` → regex + entropy scanner with `allowlist`/`baseline` support.
- `hash-attachments.yml` → verifies declared `sha256`/`size` for local artifacts.
- `body-hash.yml` → computes body hash, optionally writes back on manual run.
- `all-checks.yml` → convenience meta-workflow that calls the above.

**Triggers:** `pull_request` to `main`, `push` to `main`, daily/weekly `schedule`, and `workflow_dispatch` (manual).  
**Concurrency:** runs cancel in-progress for the same branch.  
**Permissions:** least-privilege; `contents:write` only where auto-commit is needed.

---

## 4) Required Files & Conventions
- `INDEX.md` is generated — **do not** hand-edit.
- All ledger entries must start with YAML frontmatter and include `hashes.body_sha256` (or will be flagged).
- Attachments referenced in frontmatter must exist locally (no remote-only evidence) and, where declared, hash/size must match.
- Use `templates/_TEMPLATE.md` for new entries; `intake/` for drafts, `canonized/` for validated artifacts.

---

## 5) Security Baselines
- Secret scanning:
  - Allowlist file: `.secretignore` (regex per line).
  - Baseline file: `.secret-baseline.json` (rotated when secrets are changed).
  - CI fails on **high/medium** severity in PRs; low can warn unless `--strict`.
- Link checking:
  - Private IPs & localhost are **blocked**; 429s are warnings unless `--strict`.
  - Cache file `.linkcheck-cache.json` should be **gitignored**.
- Hashing & Body Integrity:
  - Canonicalized LF EOL, stripped trailing spaces, HTML comments removed **before hashing** (determinism).

---

## 6) Environments & Deployments
- **Pages/Docs** (if enabled) should deploy only from `main` with required checks green.
- Add environment protection rules (`Settings → Environments`) if future deployments require manual approval (e.g., a public site).

---

## 7) Emergency Procedure (Break-Glass)
Allowed only for **Master Archivists** (Ashraf, Raasid) + **Admins**:
1. Temporarily unrequire selected status checks (Settings → Branches → `main`).
2. Merge the hotfix PR with **“Create a merge commit”** (linear history enforced otherwise).
3. Immediately restore required checks.
4. Open a “Post-Incident Canon Note” in `governance/incidents/` within **24h** detailing:
   - Incident summary
   - Risk assessment
   - Deviations from policy
   - Remediations & follow-ups

> All deviations must be logged; repeated bypass without remediation review is grounds to revoke admin.

---

## 8) Exceptions & Waivers
- **Time-bound Exception:** allowed for a single PR when justified (e.g., external outage causing link rot). Requires CODEOWNER approval.
- **Scope-bound Exception:** may waive `check-links` for *intake-only* drafts. **Never** waive `secret-scan`.
- File a waiver note under `governance/waivers/YYYY-MM-DD-<slug>.md` including scope, rationale, and expiry.

---

## 9) Audit & Traceability
- PR descriptions must include: rationale, evidence summary, and link to related discussion/issue.
- CI artifacts (reports) are retained for 7 days; increase if compliance requires.
- Canonization events should include `body_sha256` and commit SHA in the ledger entry frontmatter (enforced by tools).

---

## 10) Compliance Mapping (lightweight)
| Control | How it’s met |
|---|---|
| Integrity of canon | Body hashing + attachment hashing + protected `main` |
| Review & approvals | CODEOWNERS + min 2 approvals + stale dismissal |
| Traceability | PR references + CI artifacts + INDEX regeneration |
| Secret hygiene | Automated secret scan with allowlist/baseline |
| Content safety | Link checker blocks private/localhost targets |

---

## 11) Maintenance
- Review this policy quarterly or after any incident.
- Update CODEOWNERS when roles change.
- Rotate baselines when secrets are rotated; never whitelist active secrets.
- Keep Python runners updated (`actions/setup-python@v5`) and pin minimally to current LTS (3.11 as of this policy).

---

## 12) Quick Start (Admins)
1. Add this file at `governance/ci_policies.md`.
2. Enable branch protection on `main` and select the **five required checks** in §1.1.
3. Add CODEOWNERS from §2.
4. Commit workflows in `.github/workflows/` (already provided).
5. Test with a dummy PR that touches `canonized/` and verify gates.

— End of Policy —
