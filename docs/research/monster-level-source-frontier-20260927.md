# Monster level source continuation, 2026-09-27

Original, current-build, identity-bound levels newly recovered: **0**.
Production monster level rows written: **0**. Full original recovery remains open.

## Additional current local sources

The previous numeric-source discovery covered Data2. This continuation decoded
all nine current CSVZ tables in Data/Patch and Data3/patch, preserving original
file hashes, decoded hashes, byte offsets and matching literal rows. Eleven
lexical hits were found. Cat/God headers concern player/immortal data;
FightGodDoll/GodDoll/SpgEft enemy labels concern animation resource namespaces.
These hits supply no qualified monster-to-level join. Other file families and
unresolved loaders are not globally excluded by this bounded result.

## Historical reference leads

Owner-supplied Bahamut namespace8591 indexed map tables yielded **76 distinct
observations** in the retained excerpts: **50 exact historical numbers** and
**26 star-only labels**. Sixty-five observations have one or more exact current
CP950 name candidates. Names do not authorize an identity join; normal, baby,
special, quest and other variants must remain distinct.

Examples of reference pages:

- https://wiki2.gamer.com.tw/wiki.php?n=8591:鴻濛境怪物資料
- https://wiki2.gamer.com.tw/wiki.php?n=8591:聖樵原野怪物資料
- https://wiki2.gamer.com.tw/wiki.php?n=8591:天樞結界怪物資料
- https://wiki2.gamer.com.tw/wiki.php?n=8591:冰霜高地怪物資料

These are incomplete historical search excerpts, not a build-matched native
server database. Cached response hashes, source URLs, exact row strings,
character offsets, map hierarchy/floor and all current name candidates are
retained. This count is observations, not recovered unique species or imported
original levels. Direct Bahamut fetch returned403; direct17173 fetch returned567.
No access challenge was bypassed. Indexed references are marked incomplete.

## Owner star clarification

The owner clarified that one star starts30, two stars40, three stars50, four
stars60, and so on. Reference annotations retain ranges30..39,40..49,50..59,
60..69 etc, using minimum20+10*stars and maximum minimum+9. Star labels retain
`historical_exact_level=null`, with `OWNER_CLARIFICATION_20260927` range authority.
A bare asterisk is retained as one star. No lower-bound number is fabricated
into an exact original level or encoded into production78/1C packets.

The independently verified current-client formatter shows numeric30 and bands
for31..99; its native boundary is unchanged. The owner's description of a
historical star range does not overwrite the pinned instruction behavior.

## Repairs and verification

The initial reference parser missed a newline before the attribute cell and
could absorb short map headings into a name. Both were repaired. Nested map
headings are retained so identical names in different caves remain separate.
Three focused tests pass, covering fullwidth/star notation, invalid notation,
exact-versus-range separation, same-name multiple current identities, distinct
submaps, and refusal to promote reference candidates.

Reproduce from the server root:

```powershell
python -B -m unittest discover -s tests/research -p test_monster_level_source_frontier.py -v
python -B -m tools.strike_lab.monster_level_source_frontier_20260927 --output artifacts/research/monster-level-source-frontier-next --indexed-dir artifacts/research/monster-level-source-frontier-20260927-01
```

Accepted result: `artifacts/research/monster-level-source-frontier-20260927-04/result.json`.
Earlier results are retained as superseded diagnostics. No client was launched,
no desktop input was used, and no production code, accounts, saves or balance
database was modified. Existing tested78 transport/storage remains operational.

## Exact remaining evidence

Current build's original sender or a current identity/variant-bound authoritative
table must corroborate the exact level. World78 caches a server-supplied WORD
(low BYTE in the client record); battle1C receives a level BYTE. Our own server's
RAM demonstrates those supplied values only. Neither the wire consumer nor a
historical star range supplies the missing original encounter value. Original
recovery coverage of the known7791 visible EnyName lookup records remains0/7791
(0%); the all-monster species denominator is still unqualified.
