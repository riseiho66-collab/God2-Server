# Retired legacy sources

The owner withdrew all reference authority from the previously provided XJZ
and Classic server data, then explicitly authorized deletion. Current client,
current C++20/Lua source, live databases and independently captured current
client evidence are not deletion targets.

## Exact deletion targets

| Target | Checked size in bytes | Result |
| --- | ---: | --- |
| C:/Users/risei/Desktop/XJZ-Server-Cpp-clean-20260820.zip | 57184072 | Tool policy rejected deletion before process launch |
| C:/Users/risei/Desktop/God2-Classic-Server-Formal-Handoff-20260820-020345.zip | 29006637 | Not deleted |
| C:/God2Evidence/classic-20260820 | 191272075 (1587 files) | Not deleted |
| artifacts/legacy-evidence/xjz-20260820 | 486239560 (182 files) | Not deleted |
| artifacts/legacy-evidence/classic-20260820 | 2075083 (33 files) | Not deleted |

The third extraction is the explicitly labeled incomplete original extraction,
whose index-location.json points to the shorter C:/God2Evidence root. All three
resolved directory paths matched the allowlist and contained no reparse points.
Deletion was attempted using native PowerShell Remove-Item with literal paths,
exact-path checks and recursive bounds. The execution tool rejected the command
before it ran. No alternative shell, Python deletion or other policy bypass was
attempted. Existing files are retained physically but retired logically.

## Current work policy

- Stop reading, importing or deriving formulas from either retired corpus.
- New growth, EXP, combat and incubation extraction must run on current-client
  input alone. Old indices/formulas are not accepted provenance.
- Keep already-proven current-native behavior only where its proof is independent
  of old scalar values. Record native parser compatibility separately from truth
  of the data carried in a packet.
- Pure historical runtime bootstrap values require retirement, not substitution
  with another guessed value. This is tracked separately in the runtime audit.
- Historical reports/tests that require removed/retired corpora are historical
  diagnostics, not current acceptance commands. Previous successful test results
  remain dated records, not permission to reuse the retired source.

All four active growth/combat/EXP workers were redirected immediately. A bounded
additional worker is checking the active historical scalar bootstrap. No current
client or database was deleted or altered by the retirement attempt.

## Actor regression cleanup

During the later embedded-world change, main ran the old actor regression
suite before noticing that one test still opened the retired Classic SQL
name-comparison file. That read did occur; its result is NOT accepted as
current-only proof and no associated value entered runtime or new evidence.
The old test and its now-unused CSV/hash imports were removed. The remaining
11 current-source tests then passed in 80.478 seconds.

The actor suite now additionally intercepts `Path.open` for its complete
class lifetime, rejecting the retired Classic extraction, repository legacy
evidence tree and old archive names before I/O. A regression exercises that
rejection without opening a retired file. This guard is local to that suite;
it is not a claim that every historical diagnostic elsewhere was removed.
The original guarded deletion attempt remains blocked and was not retried.

Final guarded actor suite: **12/12 passed in 86.550 seconds**, including the
before-I/O rejection test. This supersedes the first mixed-authority run.
