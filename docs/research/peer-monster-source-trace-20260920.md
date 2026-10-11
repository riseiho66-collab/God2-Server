# Peer Package Source Trace

## Local Reproduction

Read-only tool: `tools/strike_lab/peer_monster_trace.py`. The supplied ZIP and
current client catalog are hash-pinned. No ZIP member is executed/extracted,
and no values are imported into production.

Archive SHA256:
6a3cd33fd33f99f001768bdc0898d34d6c8d0095e9d0f4625213b05a8275cabb.

The raw gamedata hashes differ, but7791 peer entries can be compared with7815
current source occurrences by area/map/ordinal and full original field lists.
Results:7780 exact field matches, all currently lookup-visible;11 entries with
invalid CP950 bytes remain undecoded, NOT declared changed monster records.
Their peer names contain escaped byte text. Do not silently replace bad bytes.
Reported source line numbers do not match the current parser's line numbers;
the matching above is based on identity and fields, not trusting those numbers.

All137 peer unique guide bindings match current native identity/name/appearance,
including composite appearances with more than four fields.139 remaining guide
rows were not uniquely bound by the peer and remain unresolved. Identity matches
do not validate HP/speed, prove a captured official packet, or establish formulas.

## External Source Follow-Up

On2026-09-20, direct webpage open returned403. Web search subsequently returned
indexed content for the same archived source URL, allowing limited cross-check:
[Bahamut Hongmeng monster guide](https://wiki2.gamer.com.tw/wiki.php?n=8591%3A%E9%B4%BB%E6%BF%9B%E5%A2%83%E6%80%AA%E7%89%A9%E8%B3%87%E6%96%99).

The duck example's level1/HP38/speed10 matches the package. The indexed page
also lists HP933/speed42 for Jin Mei Shou, whereas the peer JSON leaves those
two numbers null. This is a concrete extraction omission, not proof of missing
original game data. Different table layouts need separate parsing rules.

The guide additionally distinguishes wild skills from skills after capture,
and lists drops and pet growth. For example it records three skills for the
thousand-year tree monster. These are useful external leads, not authoritative
formula code or exact drop probabilities. No skill-ID mapping is certified here.

External results are indexed webpage evidence, not a hash-matched copy of the
peer's original downloaded HTML. Numeric discrepancies can also reflect edits;
do not overwrite the peer's original source claims. Store later supplements as
separate external evidence with URL, date, identity and field-level provenance.

## Verification

```powershell
python -B -m unittest discover -s tests/research -p test_peer_monster_trace.py -v
python -B -m tools.strike_lab.peer_monster_trace <path-to-supplied-zip>
```

Four focused unit tests cover exact matching despite changed line numbers,
duplicate occurrences, undecodable bytes, missing keys and changed values.
The archive CLI was also run against the supplied ZIP; counts above are actual
results, not the peer's report repeated as a new verification.

## Boundary

These materials now support tracing identities and checking external stat/skill
claims more efficiently. They still do not contain native dual attack/defense,
damage/critical formulas or a service-side data-generation implementation.
