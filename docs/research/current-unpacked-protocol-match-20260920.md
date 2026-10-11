# Supplied Taiwan Unpacked Client: Protocol Evidence Binding

The supplied `../God2/God2.unpacked.exe` matches the retained current-client
image byte-for-byte in five selected regions (2,830 bytes total):

| Region | RVA interval, exclusive end |
| --- | --- |
| Battle command builder prefix | 118E50..1191EE |
| HP consumer region | 117230..1173A0 |
| MP consumer region | 1173A0..117540 |
| Outbound queue prefix | 132E0..13340 |
| Logical dispatch table | 6B5D4..6B9D4 |

The PE is read using RVA-to-file mapping; the reference is a mapped image.
Full input hashes and individual slice hashes are recorded in
`artifacts/research/current-unpacked-protocol-match.json`. Neither PE file was
modified. No game, desktop input or public-server connection was used.

Reproduce:

```powershell
python -B -m tools.strike_lab.current_unpacked_protocol_match
python -B -m unittest discover -s tests/research -p test_current_unpacked_protocol_match.py -v
```

Four tests passed, including mutation of each region, truncated reference and a
different full image with otherwise matching regions. New/different builds do
not silently qualify. This validates reuse of the selected existing evidence;
it does not establish whole-program equivalence, all transitive callees, original
damage formulas, battle initialization or live own-server acceptance.

## Concrete Integration Gap

### Formula Evidence Build Binding Extension

The current audit additionally matches six regions byte-for-byte against the
owner-supplied unpacked PE: selected MP predicate A9070..A90C2, indexed predicate
A90D0..A9110, projection candidate 11A08F..11A10E, received action producer
12C520..12CC39, effect consumer 12B060..12B847 and RNG core 147D84..147DA1.
All ends are exclusive RVAs. Total coverage is now 11 regions / 6972 bytes;
full hashes and individual slice hashes remain in the generated JSON report.

Four audit tests pass, including mutation of each of all eleven regions.
Five CTests (current_damage_formula, current_critical_formula,
current_skill_effect_amount, current_skill_mp_gate, current_skill_mp_sync)
pass in 8.42 seconds. These names do NOT mean five formulas are recovered.
They rerun bounded native evidence using the pinned mapped image; exact PE
matches qualify only the specified code bytes, not all transitive dependencies.

The known original eligibility predicate is BYTE definition+67 != 0 and unsigned
current MP >= WORD definition+42, after menu/index/entry availability checks.
It performs no debit. Damage projection still lacks a qualified populated input
producer and authority; the effect consumer copies a transmitted amount; RNG
alone establishes no critical threshold or gameplay multiplier. Continue tracing
those producers rather than installing CUSTOM formulas as native equivalents.

`src/core/Application.cpp` now installs `RecoveredCharacterHandlers::world_records`
through `RecoveredWorldService` when recovered world entry and movement are enabled.
CUSTOM-0004 routes movement/ticks and rejects unsupported batches before callbacks.
The native bootstrap retains CharacterSelected after the tail; movement authority
still requires the existing service's world-ready binding. The transport already
requires InBattle for basic/skill commands; an isolated fixture service is not
called by that native path. Enabling a parser flag or directly substituting
fixture JSON responses would not implement playable native combat.

Next implementation must supply a session-owned battle lifecycle and world
record service, validated participant initialization/results for this client,
and C++ authoritative mutation with Lua rules. Missing gameplay formulas may
now be custom designs, each registered with a CUSTOM ID, without relabeling
packet layouts or unverified initialization fields as proven native behavior.
Preserve movement routing and transactional rejection of invalid commands.

## World Routing Regression (2026-09-20)

Release build succeeded. The following focused CTest selection passed 8/8 in
102.24 seconds after the CharacterSelected compatibility fix:

```text
ctest --test-dir build -C Release -R "recovered_world_service|recovered_movement_service|session_state|session_skill_sequence|recovered_world_records|fixture_" --output-on-failure
```

The new session_state case uses real loopback sockets through login, selection,
coalesced initialization tail/movement, ACK and heartbeat, then verifies an
unsupported mixed batch closes without committing its movement prefix. The
movement callback is synthetic; separate movement-service tests exercise domain
validation. This is not an Application process or original-client E2E test.
No production battle callback, native monster initialization, or live playable
combat is certified by these results. The fixture combat remains isolated.
