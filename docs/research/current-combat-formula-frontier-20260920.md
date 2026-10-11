# Authoritative combat formula frontier

## Completion status

Original server MP charge timing, base damage, defense reduction and critical
trigger/formula are NOT reconstructed. Client MP eligibility and received-MP
synchronization are qualified separately; neither defines when the original
server commits a cast. No invented rules were installed.

An explicitly enabled, isolated CUSTOM_TEST_NOT_NATIVE battle loop now exists
in `src/handlers/BattleHandler.cpp`; see `../fixture-combat.md`. It uses custom
Lua formulas and a placeholder TCP protocol, not the native client protocol.
Research tests and this custom loop do not establish original combat formulas.

## MP synchronization result

See `current-skill-mp-sync-20260920.md` and its executable tests. In retained
native memory, S2C2B updates role MP absolutely and later native MP eligibility
uses that new value without charging it. The receive prefix stops before
refresh and is not a live action-to-server transaction.

## New damage arithmetic lead

Read-only subagent investigation identified original 119E30, specifically
11A08F..11A10E. It reported six executions using unchanged RX image bytes,
read-only input tables, no memory-write hooks, and a 100-instruction bound.
Main independently inspected the instructions and table references, but did
not turn this into a production formula or claim a full-function execution.

An upstream actor lookup at 119F50 and read at 119F59 supply actor+DE8 to a
temporary stack array. A descriptor byte is read from
owner+A9EA505+0x20*i+8*j; supplied DWORD K is at owner+A9EA508+0x20*i+8*j.
The record stride is32 decimal. Follow-up executable qualification and
input-producer limitations are in `current-projection-arithmetic-20260920.md`.

For low-nibble descriptor types other than 3/4, the isolated arithmetic is:

```text
D = mode != 0 ? low32(K * (descriptor >> 4)) : K
projected = int32(current) > int32(D) ? low32(current - D) : 0
```

The zero branch also sets EBX=1. Reported examples include mode1/descriptor31h,
current100/K20 ->40; mode0 with the same inputs ->80; current50/K20 ->0.
Diagnostic overflow examples distinguish this from ordinary saturation:
descriptor21h/K40000000h/current100 ->80000064h, and descriptor11h/KFFFFFFFFh
->101. These do not establish valid gameplay ranges.

Slice SHA256 (exclusive end 11A10E):
eab22c1e2a8535a23911dfbdc51d8e86a59b2c0d0692790721ba47e496cbdd77.

Missing: populated K producer, reachable entry, attack/defense binding, and
authoritative actor writeback. Bounded direct-reference scans of 1000..147000
find zero initialization at 110EF7..110F04, not a populated K producer.
The routine later formats strings and calls 96990 at 11A96C. Its external
meaning has not been assigned. Absence of a direct E8 caller/absolute function
pointer in this scan does not prove global unreachability.

## New master-skill dispatch check

The second read-only subagent reports native execution of 1290E7..129186 with
actual source descriptors and synthetic actor live-ins, stopping at the called
routine's entry. All 16 selected master records reach 126890:

- kind0 IDs96..103, compared at 12910C/129110;
- kind1 IDs89..93, compared at 12913F/129143;
- kind3 IDs99..101, through the broader kind3 branch.

Kind3 controls 98/102/104/109 also reach 126890, while 105/108 reach 124820.
Therefore reaching 126890 alone does NOT mean a critical attack occurred.
Main independently inspected the kind0/kind1 dispatch and 126890 prefix.

Dispatch slice SHA256:
43e4e76b36b9f2cc1a36a9d9a0a1c54fcaace241f669e14ae83c3ab59ca10906.

The master records' WORD+42=50 is an independently qualified MP value, not
50% critical probability. WORD+46=60 is still unclassified, not assumed 60%.
The reported downstream 126DE5..126E25 edge supplies a received/stored WORD
to 128A70; it does not demonstrate a doubled attack/defense calculation.

## Next evidence required

1. Trace the populated K producer and indirect reachability of 119E30 before
   assigning gameplay authority to its multiplication.
2. Locate a native stat-to-threshold/multiplier producer, not master-ID dispatch
   or packet-result display, for critical calculations.
3. Qualify the original charge decision and commit/refund event; neither a
   client cost display nor an injected absolute MP update proves that timing.

Both read-only agents were closed after their reports. No retired Classic/XJZ
archive, public server, desktop automation, production database mutation or
custom fallback combat formula was used.

Regression result: CTest current_damage_formula, current_critical_formula,
current_skill_mp_gate, current_skill_mp_sync all passed (3.19 seconds total).
These names include earlier bounded result-consumption proofs and must not be
interpreted as four completed authoritative gameplay formulas.
