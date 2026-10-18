# Current skill formula frontier: selected-skill reader audit (2026-09-26)

2026-10-19來源警示：本文的「current」、448技能、381技能書與24筆描述是
研究當時的歷史快照。SKB來源為raw70a4...／decoded75c3...，不能綁到現用
raw ef297...，也不能當成現用453技能的權威規則。原雜湊、字面描述與當時
1,792案例保留；本輪未重新驗證或執行舊codec／Unicorn工具。現用來源界線見
[round455](tw-skill-producers-and-source-identity-20261019.md)及
[round460](tw-formula-consumer-closure-and-status-countdown-20261019.md)。

## Result and scope

No executable original server damage, attack/defense, fixed-damage, hit, or critical formula was recovered. This audit adds a verified caller/reader edge and preserves useful original skill-description constants without promoting them to executable server authority. No runtime, balance, database, or client process was changed.

New evidence: VA `005259EF -> 005297D0` selects an animation action from two native byte tables for kind-2 skills. It does not read the skill's numeric fields. The oracle executes 1,792 cases from the pinned native image and stops at renderer entry; it does not execute the renderer or game.

References reviewed first: `current-skill-effect-amount-20260920.md`, `current-skill-effect-fields-20260920.md`, `current-skill-mp-gate-20260920.md`, `current-damage-formula-20260920.md`, `current-hit-formula-20260920.md`, `current-critical-formula-20260920.md`, `current-combat-formula-frontier-20260920.md`, `current-projection-arithmetic-20260920.md`, `current-projection-sink-20260920.md`, and `unpacked-client-skill-damage-boundary-20260924.md`.

## Identity and reproduction

Run from the server root:

```powershell
python -m tools.strike_lab.current_skill_reader_audit_20260926
python -O -m tools.strike_lab.current_skill_reader_audit_20260926
```

Tool: `tools/strike_lab/current_skill_reader_audit_20260926.py`. Saved result: `artifacts/research/current-skill-reader-audit-20260926.json`.

- Mapped native image SHA-256: `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
- Current `cbspec2` source SHA-256: `7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51`.
- Current `Data2/Patch/Comm/gamedata.csvZ` SHA-256: `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731`.
- Current `God2.exe` bytes must match the pinned image at RVA `[1259C2,1259F4)`, `[1297D0,129861)`, and `[19CED0,19CF80)`. The result retains individual span hashes and the current executable hash.
- All checks raise explicit exceptions; optimized Python cannot disable them. Output is emitted only after all cases pass.

## New caller/reader edge

All addresses below are VA (image base `00400000`).

| Address | Proven operation |
| --- | --- |
| `005259D0` | Store actor pointer at manager `+A7FBC70+4*side`. |
| `005259DD`, `005259E6` | Read actor `+EC4` selected skill pointer and store it at manager `+A7FBC78+4*side`. |
| `005259EF` | Call `005297D0`. Caller inspected statically; oracle begins at the callee. |
| `005297D6`, `005297E0` | Read selected definition pointer, then definition BYTE `+1`; return unless kind is 2. |
| `005297E6` | Read definition BYTE `+0` ID, subtract 1, sign-extend the resulting 16-bit index. |
| `005297F9`, `00529803` | Actor BYTE `+234` bit 7 chooses table BYTE `[0059CED0+id-1]` or `[0059CF28+id-1]`. |
| `0052980B..00529813` | Require actor WORD `+10` renderer handle below 1000. |
| `00529815` | Read signed manager WORD `+A7FBC6C`. |
| `00529857` | Call `0041BF30` with renderer pointer `[manager+C]+10+handle*290`, the signed word, action byte, and zero. Oracle stops before this callee executes. |

The 448 original 110-byte definitions comprise 121 kind-0, 129 kind-1, 87 kind-2, and 111 kind-3 definitions. Each runs for both sides, first unchanged and then with every definition byte after the two identity bytes replaced by `FF`: **448 × 2 × 2 = 1,792 cases**. All 174 original kind-2 side mappings are retained in the JSON. Their action values range from 0 to 137; these are renderer arguments, not damage percentages.

Native memory-read hooks prove this reader accesses only definition `+1`, and for kind 2, `+0`. Altering MP `+42`, unknown `+46`, and effect fields `+4C..64` does not change the arguments. Actor state and definitions remain unchanged. Writes outside the private stack are rejected, instructions must remain inside the bounded reader until the renderer boundary, and each case has a 128-instruction budget.

This is a scoped exclusion of one reader, not an exhaustive proof that no other reader computes a formula. Static inspection of `005224C0` and `005241A0` also found selected-skill fields `+45/+66` flowing toward movement/target geometry and resource calls; no new attack/defense producer was established there.

## What is available, and what remains missing

The first six rows consolidate earlier native research; they are not newly recovered formulas.

| Requested quantity | Available native evidence | Missing authority |
| --- | --- | --- |
| Skill MP | Definition WORD `+42`; RVA `A9070..A90C1/A90D0..A910F` compares role MP `+64` unsigned against it, gated by definition BYTE `+67`; RVA `11BED3` displays it. 243 explicit skill-book MP texts agree. Kind 0 / ID 1 has threshold 5. | Original server debit/refund timing, discounts, and enforcement. The separately documented diagnostic server cost 8 is not this source value. |
| Damage / fixed amount | S2C `83/03` WORD `+9` passes through RVA `12C845/12C860`, stored at `12B619`, then displayed from actor `+28A`. Definition WORDs `+4C..64` select labels at `126120`; caller amount is printed unchanged. | Producer of that amount; a fixed-damage formula cannot be inferred from the display. |
| HP/result application | `83/0D` WORD `+9` becomes signed-16 accumulator input at `12CB31/12CB3E/12CB4B`; `128A70/128AC0` apply wrapped sums, zero floor, and signed cap. | Attack, defense, skill coefficients, rounding, and authoritative pre-cap result generation. |
| Hit | Result byte `R+11=8` selects evasion text at `12B412`; 7 selects defense outcome. | Accuracy/evasion probability and roll threshold. RNG path `12A89D -> 147D7F` is not proof of either. |
| Critical / multiplier | Original skill-book text includes conditional 2× damage/healing and special 100% critical/status claims, listed below. | Trigger probability, evaluation order, stacking, eligibility, arithmetic and original server implementation. Master16 dispatch is not itself a critical formula. |
| Attack / defense | Projection path `119E30 -> 11A08F` has coefficient multiplication/subtraction; `11A96C -> 96990` emits text via C2S `2F`. Some skill text explicitly claims doubled defenses. | Proven coefficient producer/reachability and server-authoritative damage calculation. Pet inspection fields and equipment stats cannot supply wild-monster base values. |
| Animation action | New `1259EF -> 1297D0` edge reads only skill kind/ID and two byte tables. | No numeric combat formula comes from this reader. |

### Original descriptive constants

The tool parses 381 current skill-book definitions and retains **24 matching description cells** (columns 7..12 matching `倍`, percentage notation, `百分`, or `固定`). Each cell carries item ID, name, source line, decoded offset, record hash and exact literal. This search is a reproducible literal subset, not an exhaustive natural-language rule extractor.

**Counting correction:** these are 24 description entries from 24 skill-book
IDs, not 24 distinct multipliers, gameplay rules, packet families or formulas.
They contain 21 distinct literal strings; distinct wording also does not imply
distinct mechanics. The grouping below counts entries only:

| Description group | Entries | Item IDs |
|---|---:|---|
| Weapon/element masters sharing conditional2x critical damage, sometimes with additional effects | 12 | 6568..6574;6665..6669 |
| One physical/spell attack at2x | 2 | 6567;6663 |
| Other revival/recovery/status/enhancement descriptions | 6 | 6809;6871;6873;6884;6885;6886 |
| Explicit exclusions: cannot trigger the double-damage ability | 4 | 6890..6893 |

The four exclusions are not four positive multiplier effects. Recovered
executable server formula count remains zero. Do not present this text-match
count as independent effect coverage or implementation progress.

Examples of useful original claims:

- Item 6567, 增長天加持: one physical-skill attack has damage 2×. Item 6663, 大梵天加持, gives the analogous spell claim.
- Items 6568..6574 and 6665..6669 describe conditional critical damage 2×. The actual probabilities are not supplied by these descriptions.
- Item 6571, 斧大師: conditional physical/magic defense 2×; its fifth axe-skill case says a counterattack is 100% critical after the stated attacked-and-hit condition, with critical damage 2×. This is not a global 100% critical rule.
- Item 6884, 狀態大師: describes 100% status hit under its enhancement and non-immunity conditions. It does not replace normal hit chance.
- Item 6885, 回復大師: conditional healing 2× and undead damage 2×. Item 6886, 能力大師: conditional enhancement 2×.
- Item 6809, 活二 蘇生: HP 30%; denominator, rounding and recovery ordering still require evidence.
- Item 6871, 歡喜天加持: recovery 5× for its stated summoning context. Item 6873, 密絡活血, says `效果加2倍`; the wording alone does not resolve additive versus multiplicative implementation.
- Items 6890..6893 explicitly exclude triggering the double-damage special ability for their life-drain skills.

These claims support future acceptance constraints when an original formula producer is found. They are not sufficient to install a server formula now.

### Unknown definition WORD +46

All 448 original values are preserved: `003C` (60) ×116, `013C` (316) ×262, `0203` (515) ×3, `023C` (572) ×19, `033C` (828) ×48. The high byte varies and most low bytes are 60. Neither the selected master-skill value 60 nor this distribution proves a 60% rate. The new reader never accesses the field. A literal `+0x46` decompile search also has unrelated object aliases; indexed/scaled aliases remain to be classified.

## Concrete next evidence needed

1. Original upstream producer of `83/03` and `83/0D` amount WORD `+9`, plus the hit/critical classification bytes, with input stat ownership and rounding visible.
2. A classified native reader of definition `+46` (including indexed/WORD-scaled aliases), before assigning it a rate or coefficient.
3. Original server skill MP debit/refund path, distinct from client eligibility and display.
4. A real identity join to wild-monster physical attack, magic attack, physical defense, and magic defense. Existing pet `FB` inspection and render/resource identifiers remain ineligible substitutes.
5. For the literal 2× rules: probability, ordering relative to defense and rounding, and exclusions such as the life-drain descriptions. The current client reader audit does not supply these missing steps.

## 2026-09-27 direct +46 follow-up (no formula recovered)

A bounded read-operand sweep of the pinned mapped image, RVA1000..170000,
found234 overlapping +46/+47 candidates including unrelated structures,
LEA address calculations and linear-decoded data. This is NOT234 skill readers.
No new native test or original gameplay value follows from that count.

Three candidate contexts were read in the current reconstructed functions:

- VA0045B5B5 belongs to0045B2A0: its pointer walks the owner+D2D60 table in
  4C-byte rows and reads a mode WORD; it is not bound to a110-byte cbspec record.
- VA004FC5A0 belongs to004FC560: the WORD+46 is range-checked against1000,
  passed through render-object destruction using stride290, then reset toFFFF.
- VA0050A6E5 belongs to0050A610: its base is manager+index*A7E0; WORD+46
  selects a render object moved by the same coordinate deltas as other handles.

These specific reads do not qualify the skill definition's unknown WORD+46.
The classification is static source inspection, not live execution or exhaustive
alias analysis. Do not resubmit these three offsets as fresh combat-coefficient
leads solely because their displacement matches. Original requirement tables,
monster intrinsic values, and the skill field's semantics remain unresolved.
