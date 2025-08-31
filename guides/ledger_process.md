# Ledger Process — From Draft to Canon

## Flow
1. **Draft:** Create from `templates/_TEMPLATE.md` under `intake/`.  
2. **Evidence:** Attach artifacts; compute `sha256`; list under `provenance`.  
3. **Review:** Open PR; CI validates frontmatter, security, links.  
4. **Attestation:** Collect **2** signatures (PGP/Sigstore); add artifacts/URLs.  
5. **Canonize:** Maintainer merges; CI updates `INDEX.md`; freeze `body_sha256`.  
6. **Disputes/Amends:** Follow governance protocols.

## Verification Snippets
```bash
# Body hash
sha256sum intake/<entry>.md

# Attachments
sha256sum attachments/*

# PGP verify
gpg --verify entry.sig intake/<entry>.md

# Sigstore (example)
cosign verify-blob --signature entry.sig --certificate entry.pem intake/<entry>.md