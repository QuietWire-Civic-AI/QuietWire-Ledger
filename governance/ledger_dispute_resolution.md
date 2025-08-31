# Dispute Resolution Protocol

**Purpose.** Provide a clear path to challenge or clarify ledger entries.

## Steps
1) **Open Issue:** Reference the entry path; state the concern (scope, accuracy, classification, attestation).  
2) **Review Window:** Maintainers assign reviewers; acknowledgment within 24h, initial review in 72h.  
3) **Dialogue & Evidence:** Parties add evidence; update `evidence_chain` and hashes.  
4) **Decision:** Master Archivists arbitrate if needed; result recorded.  
5) **Outcomes:**  
   - Amend entry (use `amends[]` + change summary)  
   - Reclassify / Redact  
   - Revert / Archive with rationale

## Logging
- Link the issue/PR in the entry’s change log and update `INDEX.md` via CI.
