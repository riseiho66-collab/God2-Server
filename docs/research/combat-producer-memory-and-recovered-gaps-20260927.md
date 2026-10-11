# Combat producer memory and recovered code gaps — 2026-09-27

## Executed work

`tools/strike_lab/current_combat_producer_memory_20260927.py` ran the current
port-only client copy on the existing hidden God2Lab desktop against our isolated
loopback server. It used VM_READ, took no screenshots, and did not switch the
input desktop. The owned client and isolated server were closed. The formal
client, server executable, configuration and source fixture remained unchanged.

Evidence: `artifacts/research/combat-producer-memory-20260927-01`.
The entire loaded 448-record skill source again matched its original asset.
The independently published skill pointer identifies the skill manager; the
native `+144938` relation identifies the battle object used by the projection
candidate. Its 32-byte command region and 172-byte planning region were read
directly from the running client. Planning count was zero and both regions were
zero in this world-only scene. These are inactive runtime values, not native
zero coefficients or proof about all battle states.

## Missing reconstruction repaired separately

The earlier reconstruction omitted the complete `00519B40` and `00519E30`
functions. Further targeted recovery covered sixteen more omitted functions.
Nineteen functions total, including the existing `0051A980` one-byte return,
were reconstructed or checked in a transient, read-only Ghidra project session.
Eighteen are newly created analysis functions. The saved project was not modified.

`tools/strike_lab/qualify_combat_gap_functions_20260927.py` verified every full
function address span and all **2,641 instruction records** against both the
current formal PE and the actual running client's `.text`. Constants were also
read from RAM and matched against the formal PE. Normal and optimized Python
runs produced identical manifests. Four invalid memory receipts (failed capture,
memory writes, desktop change, or missing client cleanup) were rejected.

Qualified pseudocode is kept separately at:

`C:/Users/risei/Desktop/God2-解殼EXE原始碼重建/recovered-memory/20260927-combat-functions`

It is reconstructed pseudocode, not the original C++ source and not certified
server balance logic. Evidence directories are
`artifacts/research/combat-gap-producers-20260927-01` and
`artifacts/research/combat-gap-functions-20260927-02`.

## Producer boundaries established

- `00519B40` tokenizes a space-delimited command, checks ASCII `H/T/S/N/F`,
  and parses decimal numbers. There is no qualified direct caller yet.
- `00519E30` works on temporary projected actor HP, chooses targets and formats
  a command. Its float comparison constant is the binary32 value represented
  by `3333333F` (approximately 0.7). This is a target-selection comparison,
  not a damage multiplier or critical chance.
- Its final sink is `00496990`, the already qualified outgoing `2F` text path.
  No authoritative actor attack/defense writeback was recovered.
- Full actual `.text` direct-reference and mapped-image pointer-literal scans
  found no direct call/function pointer for `00519E30` or `00519B40`.
  The normal battle initializer calls `0051A980`, which is a single `RET`.
  This does not exclude indirect calls or a differently biased pointer writer.
- The visible direct coefficient-address writer outside the candidate is the
  constructor's zero initialization at `00510EFE`. Scanning the actual `.text`
  with the known `±144938` owner bias did not reveal a populated coefficient
  writer. Generic copies and unqualified aliases remain a recovery boundary.
- Newly recovered `00518A90` is reachable from the `88` receive dispatch at
  `00514550`. It copies the incoming round/vital snapshot; it does not calculate
  attack versus defense. Its `+44` DWORD is manager state, not skill WORD `+46`.
- Newly recovered `0052BC50` formats stored HP/MP deltas and applies them using
  `00528A70/00528AC0`. `00514760` and `0052DD30` enumerate/select actor slots.
  These are consumers/selection helpers, not server damage generators.

Whole skill records also get copied into UI buffers by `00489DE0`. Those copied
buffers and rebased readers must be included in further field-use tracing; a
direct small-displacement census alone is not an exhaustive alias proof.
The inspected `0048A2C0` use selects displayed names/categories from copied
record identities, without producing attack/defense values.

## Formal service and completion

The installed 448-row `native_skill_catalog` and existing C++/Lua lookup were
reverified through `native_skill_memory_release_20260927 verify`. Every raw
110-byte record and MP threshold matched. No player table changed and no skill
ownership was granted. The formal service remained PID 26992, listening on 2592.

New authoritative original damage/hit/critical formulas: **0**.
New qualified original NPC/monster placements: **0**.
The full native reconstruction remains open; estimated overall engineering
completion stays approximately **11%**, not a measured all-content acceptance.

Next useful traces are the complete received-result producer/consumer boundary,
source-qualified copied skill buffers, and any populated coefficient writer in
a naturally entered battle. Our server's synthetic values must retain their own
authority and must never be fed back as recovered original balance values.

## Owner's precision directive

The additional active-battle capture attempt in
`artifacts/research/active-battle-producer-memory-20260927-01` failed during the
isolated configuration gate, before launching a game: door routes require guide
mode. The fixture preparation now keeps guide mode with the native-only
placement gate. This attempted run is **not accepted** and is not counted as
actual battle memory coverage. Following the owner's request to avoid repeated
empty captures, its rerun was cancelled. No production configuration was changed.

Further work should start from a concrete nonzero producer or a qualified
source/call-chain change, not repeat the unchanged catalog or inactive planner
snapshot. Client memory can expose loaded source data and received results;
it does not by itself supply an original server calculation that has not been
loaded into that process. No full-formula or placement completion is claimed.
