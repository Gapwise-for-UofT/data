# Public distribution contract

`data/utm` is the canonical UTM distribution subtree. A production build copies that validated tree to `https://data.gapwise.ca/datasets/utm/latest/` and generates `manifest.json` with SHA-256 hashes and byte sizes. UTSG and UTSC source-backed identities and geometry remain canonical repository data but are not yet part of this production raw-data channel.

This is a distribution surface, not a runtime dependency of Gapwise. The web app and public API ship with a tested snapshot so a Data-site outage does not break student routing.

Prefer:

- `api.gapwise.ca/v1` or official SDKs for stable campus-intelligence semantics;
- `data.gapwise.ca/datasets/utm/latest/` for raw source-level artifacts;
- `docs.gapwise.ca/data/` for schemas, provenance, uncertainty, versioning, and reuse guidance.
