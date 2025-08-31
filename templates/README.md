# Templates — How to Create a Canon-Ready Ledger Entry

1) Copy `_TEMPLATE.md` to: `intake/<your_entry>.md`  
2) Fill **all** YAML fields (IDs, timestamps, classification, retention, attestation threshold).  
3) Write sections (Summary, Context, Evidence, Risk, Validation).  
4) Put attachments under `attachments/` and compute `sha256` for each; add to frontmatter.  
5) Open a Pull Request. CI will validate frontmatter, content security, and links.  
6) Obtain **two** verifiable signatures (PGP/Sigstore); attach artifacts/links in the PR.  
7) Maintainers will move the entry to `canonized/` and the index will auto-update.

**Notes**
- Absolute dates (Asia/Aden); never include time in file names.
- English-first in repo; Arabic mirrors as `*_AR.md` after approval.
- Disallow raw HTML/iframes/scripts. External links must be reputable or canon-internal.