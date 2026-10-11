# Current Monster Rewards and Capture: Lane C

This is a bounded producer step, **not completion of all-monster recovery**.
No identity-bound base EXP or server capturability was recovered. Both fields
remain null for every source occurrence. No record is eligible for DB integration.

## Delivered Files

- `tools/strike_lab/current_monster_rewards_capture.py`
- `tests/research/test_current_monster_rewards_capture.py`
- `docs/research/current-monster-rewards-capture-20260920.md`

The tool reads only current pinned sources, uses main's
`current_monster_inventory.pinned_catalog`, and emits JSON on stdout. It does
not run the heavyweight whole EnyName loader or write reports, databases,
runtime files, shared files, or original sources. The native oracle uses the
existing `current_battle_entry.NativeRun` memory adapter and bundled Unicorn
under `artifacts/tooling/crypto-oracle-python`. There are no child agents,
live processes, UI calls, network operations, or retired-source dependencies.

## Source Authority

| Current source | SHA-256 |
| --- | --- |
| Server `artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin` | `149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763` |
| Client `Data2/Patch/Comm/gamedata.csvZ` | `70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731` |
| Client `Data2/Patch/Comm/message.csvZ` | `5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598` |

Decoded gamedata SHA-256:
`75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815`.
Decoded message SHA-256:
`370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8`.
Base VA is `0x400000`; all native RVAs below equal mapped-image file offsets.
The output includes exact instruction bytes, span hashes, source hashes,
decoded row offsets, physical line numbers, and hashes including original CRLF.
Changed source hashes fail closed.

## New Native Producer Proof

RVA `0x128DD4..0x128DEC` contains a conditional result relay:

```text
128DD4  cmp  bl, 96h
128DD7  jne  128DECh
128DD9  mov  eax, [esp+1Ch]
128DDD  test eax, eax
128DDF  je   128E60h
128DE1  mov  cl, [edi+286h]
128DE7  mov  [eax+0Bh], cl
128DEA  jmp  128E60h
```

The read is exactly **one byte** from an existing actor state slot. The high
byte at `+0x287` is not read. The condition is action byte `0x96` and a non-null
output pointer. This is a condition for copying a result, **not a capture
eligibility gate, probability, level comparison, or monster base property**.

Static caller evidence ties the output slot to battle context `+0x53`:
`0x1140CD` constructs context `+0x48`, `0x1140E2` calls `0x129020`, and
`0x1291E4..0x1291EC` forwards its output argument to `0x128B10`.
Within that helper, `0x128DA0` obtains BL from a different selected actor's
`+0x232`. The native proof stores these spans separately; it does not claim
continuous execution across the intervening animation/graphics helpers.

Original selector instructions `0x11411B..0x1141BC` read context `+0x53` and
choose a SystemMessage. Execution stops before the UI call at `0x1141BF`.

| Result byte | Message ID | Current label meaning | Decoded message offset |
| ---: | ---: | --- | ---: |
| 1 | 884 | Capture succeeded | 38591 |
| 2 | 655 | Pet inventory full | 29757 |
| 3 | 882 | Capture failed | 38555 |
| 4 | 883 | Cannot capture | 38575 |
| 5 | 1151 | Monster level above player; cannot capture | 51478 |
| 6 | 1390 | Transformation-card copy completed | 64020 |
| 7 | 41 | Item inventory full | 6396 |
| 8 | 1391 | Copy failed | 64043 |
| 9 | 1392 | Cannot copy | 64060 |

Other byte values leave this message switch without selecting a message.
The shared slot includes copy results as well as capture results. Even the
level-related label does not establish a native level-comparison producer.
All oracle operands are synthetic branch/width probes. No observed monster,
capture attempt, awarded EXP, or server behavior is inferred from them.

## Complete Field-Domain Coverage

Current source parsing independently rechecks these denominators using the
shared parser, without reexecuting or duplicating the original loader:

| Domain | Count | Base EXP verified | Capturable verified |
| --- | ---: | ---: | ---: |
| All EnyName source occurrences | 7815 | 0 | 0 |
| Final lookup-visible occurrences | 7791 | 0 | 0 |
| Superseded occurrences | 24 | 0 | 0 |

There are 97 source scene descriptors and 96 final lookup-visible groups.
The later area-7 declaration replaces the earlier descriptor table. All 24
superseded rows remain individually represented with `lookup_visible=false`.

The lane owns only `base_experience` and `capturable`. Every one of the 7815
rows includes both fields with status
`unresolved_no_identity_bound_original_producer`, `value=null`, and null value
source hash, value offset, producer RVA, and monster-value identity join.
Identity provenance remains populated separately from value provenance.

Exact aggregation join:
`(source_sha256, source_record_index, area_generation, area, scene, ordinal)`.
Source index is zero-based; ordinal is one-based. The raw source record,
all six/ten raw columns, source label, name bytes, source offset, and row hash
are preserved. No name/resource/card/pet join or bank/variant collapse occurs.
These are source/lookup occurrences, not proven wild species or spawn counts.

Normal, boss, elite, quest, event, and summoned domains are all requested and
remain explicit with unknown denominators. Category is null per record; no
classification is inferred from names or artwork. `true_wild_monster_denominator`
is null and `all_monster_systems_enumerated` is false. EnyName does not establish
that every monster system or boss variant has been enumerated. Main owns the
shared identity inventory and aggregation across those systems.

## Exact Remaining Frontiers

**Capture result:** the low byte read at `0x128DE1` from actor `+0x286` now has
an executed output consumer/producer. A concrete upstream writer candidate is
`0x12B3C2..0x12B3DB`: it loads a DWORD from current ESP `+0x60`, stores its low
WORD to actor `+0x286` at `0x12B3CD`, and stores another supplied WORD at `+0x288`.
This is a static candidate inside `0x12B060`, not an executed or proven
capture-specific path. Qualify its caller and the actual `0x96` branch before
binding this candidate to the relay. The upstream source of that result and
its exact monster identity remain unresolved.

**Capturable:** no pre-command capture target-selection gate has been proved
by this step. Its RVA is null. Recover that gate separately from the original
server eligibility producer; neither the result relay nor labels authorize
setting a boolean for any monster. Capture probability remains null as well.

**Base EXP:** the identity side is current EnyName loader `0x5A1A0` and lookup
`0x5A0A0`, supplied by main's qualified inventory. The next required producer
is an original monster-definition or reward-calculation input with a preserved
identity join. No qualifying base-EXP producer RVA or source offset was found
in this bounded pass, so both remain null. The adjacent current source envelope
was also inspected: `SpecialEnyInfo,1` follows EnyName at physical line 29625,
with row `1,IGS_SPECIAL,0,0,149,1`. Those unqualified numbers are not promoted
to EXP or monster categories. Opcode 89 display recovery was not reimplemented
or used to claim progress on base EXP. This is no claim of global absence.

## Verification

```powershell
python -B -m unittest discover -s tests/research -p test_current_monster_rewards_capture.py -v
python -B -m tools.strike_lab.current_monster_rewards_capture --summary
```

Focused suite: **7 tests passed**, 0.617 seconds, exit 0. Tests execute all byte
selectors, the relay with both high-WORD counterfactuals, every alternative
action byte, and a null output pointer. Read/write hooks verify the exact byte
width, untouched surrounding output, and no actor read on rejected relay
branches. Native code is unchanged and read/execute-only; only synthetic VM
data is writable. Tests also check hash rejection and every inventory occurrence,
both explicit unknown fields, exact join uniqueness, area replacement, and
unknown category/all-system denominators. These are coverage and instruction
checks, not recovered monster-value counts.
