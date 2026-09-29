# Acceptance Tests
1. Same FB URL, different name spelling -> merge as same FB identity.
2. Same display name, different FB URLs -> keep separate; do not merge.
3. `@creator` and `https://t.me/creator` -> normalize as same Telegram handle.
4. PH Instagram-only creator -> IG-PH.
5. Non-PH creator with FB+IG+YT -> OTHER COUNTRY_FB-IG-YT with all known links.
6. Conflicting reference prices -> do not silently overwrite; preserve/flag conflict.
7. Blank new email vs populated existing email -> retain populated email.
8. `12.5K` followers -> 12500; ambiguous text -> leave unresolved.
9. Source row cannot establish country -> do not assume Philippines.
10. Final audit count must account for every source row as migrated, merged, excluded, or review required.
