# GOV-EXCEPTIONS — Ledger Waivers & Exceptions Register

**Owner:** QuietWire Ledger Team  
**Effective:** 2025-08-31 (Asia/Aden)

> Source of truth for all waivers. Each entry must be time-bounded, justified, and reference compensating controls.

| ID | Scope | Affected | Reason | Approved By | Effective | Expires | Status | Controls | Link | Signature |
|---|---|---|---|---|---|---|---|---|---|---|
| GOV-EX-2025-001 | entry | canonized/2025-08-30_Ledger_Room_Guide.md | Allow missing tsa_rfc3161 while Sigstore rollout | Master Archivists | 2025-08-31 | 2025-09-07 | active | branch protection + 2 signers | PR #123 | rekor://... |

### Status Legend
- **active**: waiver currently in effect.
- **expired**: end date passed; must bring entry into full compliance.
- **revoked**: waiver cancelled early; compliance required immediately.

### Notes
- Waivers MUST be time-bounded.
- Prefer narrow scope (`entry`) over broad (`stream` or `repo`).
- Keep artifacts/links auditable (issue/PR, signatures, rekor/pgp).