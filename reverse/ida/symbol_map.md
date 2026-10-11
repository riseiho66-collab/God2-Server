# IDA Symbol Mapping

Canonical map: [docs/SYMBOL_MAP.md](../../docs/SYMBOL_MAP.md). No tool-specific symbols have been recovered or imported.

| Preferred VA | RVA | Proposed label | Status |
| --- | --- | --- | --- |
| 0x00702001 | 0x00302001 | PackedEntryPoint | Observed PE metadata |
| 0x0054A3E8 | 0x0014A3E8 | OEP_Candidate | Unverified user hypothesis |

Bind future exports to executable hash, project/database revision, tool version and actual analysis base. Record function extents and naming rationale. Use module-relative RVAs when sharing across rebased analyses. Wrapper/codec/dispatcher addresses remain unknown; do not insert zero-address stand-ins that tools might interpret as real labels.
