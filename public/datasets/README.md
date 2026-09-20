# Gapwise Data distribution

The currently published UTM source files live under `data/utm`. Production builds publish that complete validated subtree at `/datasets/utm/latest/` with a generated SHA-256 manifest. UTSG and UTSC identity and geometry remain canonical in their own repository directories but are not yet part of this raw distribution. Consumers that need stable application behavior should prefer `api.gapwise.ca` or the official SDKs; raw dataset consumers can use these first-party URLs.
