# Monster attack/defense frontier, 2026-09-26

**Original wild-monster physical attack, magical attack, physical defense and
magical defense values recovered in this lane: zero.** No server code, balance
data, SQLite database or running client was changed.

This follows the newly available decompilation, then verifies the original
instruction bytes against both the pinned mapped image and the current executable.
It narrows one previously listed battle numeric candidate; it does not establish
that all client resources lack combat values.

## Prior evidence kept separate

The following were read before selecting this frontier:

- `current-monster-inspect-identity-20260920.md`: FB fields belong to pet2 records,
  with no wild-to-owned identity/value-preservation join.
- `current-monster-combat-stats-20260920.md`: ChangeDollCard numeric values are
  signed card-display additions, not wild-monster base stats.
- `current-monster-base-stats-20260920.md` and
  `current-monster-local-stat-fallback-20260920.md`: EnyName selects appearance;
  constructor constants and resource sequence numbers do not supply combat stats.
- `current-monster-complete-attributes-20260920.md`: received action-result WORD
  banks are not four-stat records. Its S2C83 action7 resource branch remained a
  static candidate, rather than a followed CSV-source chain.
- `current-attack-defense-producer-search-20260920.md`: 2C, 31 and D2 update role
  or owned-companion fields. Battle forwarding does not change that ownership.
- `current-battle-scalar-semantics-audit-20260920.md`: 86 subtype6 is already a
  known subordinate vital path; side1 reaches the HP wrapper before subtype
  discrimination. This lane does not relabel that old finding as new stats.

## New bounded edge: S2C83 action7 to GodEft resource table

All addresses below are hexadecimal **RVAs**; add `400000` for the executable VA.
Source and disassembly offsets were checked against the actual PE section mapping.
Decompiler output is a navigation aid, not the authority for instruction widths.

| Edge | Original operation | Boundary |
|---|---|---|
| `116EFE / 116F0B` | Read logical WORD+9 and call `12DCC0` with four output byte pointers | Call-site static verification |
| `12DCC0..12DD2F` | Split one supplied argument into four selector bytes, using bits9,7..8, low7/low4 and a threshold100 | Original helper executed with output guards |
| `116F10..116F34` | Signed WORD must be positive; low10 bits replace actor metadata DWORD+DB4 low10 | Static, no intrinsic stat arithmetic |
| `116F95 / 117008..117013` | Third output BYTE, if <=100, becomes key for `4FDD0`; ECX is battle+BC294 | Actual object identity retained |
| `4FDD0..4FDFC` | Scan table owner+121F0 in stride110, matching WORD key against count owner+121EC | Static full lookup body |
| `117039..117044` | When cached WORD+2 is negative, pass row+C to `12F550` before ROM-loader path | String/path input, not four numeric capabilities |
| `110CE9..110D19` | Literal `GodEft.csv` plus `./Data2/Patch/`; call `4FC50` with owner battle+BC294 | Same table owner as action7 lookup |
| `4FCDB / 4FCF4` | Source column0 converted by integer reader; AX stored to row+0 | Key |
| `4FCFC / 4FD11` | Source column1 converted; AX stored to row+4 | Source resource ID |
| `4FD29..4FD35` | Source column2 copied to row+C | Resource path |
| `4FD4A` | Set row+2 to FFFF | Runtime cache sentinel, not source stat |

The helper has three actual branches. For low WORD `v`:

1. Output0 starts as bit9; output1 is bits7..8.
2. If bit9 is set: output2=`(v & 15)+16`, output3=`(v>>4)&7`.
3. Otherwise, if unsigned WORD `v>100`: output0=1, output2=`v&127`, output3=1.
4. Otherwise: output2=`v&127`, output3=0.

These are selector semantics. The helper does not read a monster row, HP, damage,
role/companion stat block, or any source resource at all. The caller additionally
tests the WORD as signed, so the standalone helper experiment must not be described
as full action7 acceptance. Remaining appearance construction and action playback
are not executed or supplied with fabricated successful returns.

### Current source table

`../God2/Data2/Patch/GodEft.csvZ` is already decodable with the existing current
CSVZ decoder; it is not an unresolved encrypted stat file.

- Raw SHA256: `9c8a1977355e096f72924a36ccf61dfea9940af75b4816d0d56727e63a7acf27`.
- Decoded SHA256: `479861b2034da6f27d5bf9e0f7f38facf19ee6b71cee7eaf01d7a0fd4e8fec97`.
- Decoded bytes: 2085; data lines27..60: **34 rows**.
- Keys1..34; resource IDs5601..5634; paths `data2\fry\fry5601.rom` through
  `data2\fry\fry5634.rom`. Fourth column is a label, not a numeric four-stat tuple.
- The tool retains each raw row including line ending, SHA256, decoded byte
  offset, line, key, resource ID and exact path.

The loader reads only columns0,1,2 into these fields. No EnyName area/scene/ordinal
join is present in this path. Matching a name or divine/monster artwork would not
create such a join. The separate next loader call at110D4E targets battle+A7844
and `FightAnmEft.csv`; it is a different table and is not conflated with this one.

## Additional narrow exclusions from the new decompilation

86 subtype2 handler117500 selects126060 for payload control byte1, or1202D0
for control byte2. Full direct bodies were read and PE-byte matched:

- 126060 clears an indexed manager attachment and iterates14 side1 actors to
  hide their display handles using109200. It does not receive four stat values.
- 1202D0 loops both sides and14 slots through the already documented120000 reset,
  then clears manager+2F4/+2F8. This is teardown/reset, not a source of intrinsic
  monster attack/defense.

These are static bounded observations. The transitive render/reset subtrees
were not exhaustively re-executed, and no absence claim is made for other messages.

## Reproduction and evidence

Run from the server root:

```powershell
python -B -m tools.strike_lab.current_monster_stat_frontier_20260926
```

The tool verifies pinned image SHA256
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`, compares
eight code spans to the actual current PE, verifies both source hashes, and runs
the original pure selector. JSON contains span hashes and exact native PCs.
Every check uses explicit exceptions and remains enabled under Python `-O`.

Execution is limited to12DCC0..12DD2F, 128 instructions and one second per case;
only the stack and four single-byte destinations can be written. Destination
guards, original image preservation and `RET14` stack balance are checked.
Inputs are synthetic probes, never observed monster values. Native CSV file I/O,
complete battle dispatch, renderer and live game are outside this experiment.

Retained result: `artifacts/research/current-monster-stat-frontier-20260926.json`.
Completed run: **6144 synthetic native vectors passed**, eight PE span matches,
34 pinned source rows, exit0. Vector result SHA256:
`ef3b4298feb311ffd2ec4df76884b44c456a31496b7ba1c1560042d119e527c6`.
This count measures selector extraction checks, not recovered stat tuples.

## Specific remaining work

1. A source-backed producer for wild actors' four attack/defense fields is still
   missing, including the actual destination offsets and field labels. Do not
   transplant role2C, companion31 or pet2FB offsets onto battle actors.
2. Recover the original server sender or an independently identified source row
   connecting those values to the exact EnyName tuple/variant or another proven
   monster identity. Client art keys and supplied outcome operands are insufficient.
3. For unresolved local resources, first prove a loader/call-site that reads a
   numeric capability field. GodEft is now traced to ROM selection and should not
   be queued for speculative stat decryption merely because its rows contain IDs.
4. Action7 beyond117044 remains a resource-load/playback continuation; examining it
   may recover visual behavior, but there is currently no positive attack/defense
   producer evidence there. Arbitrary indirect aliases or other message families
   have not been globally excluded.
