# Current Battle Owner Clock Continuation

Later continuation: `current-battle-owner-map-sprite-20260920.md` executes the
map metadata lookup, original area-2 resource load and pending map control call,
ending at C3331. It also fixes the offline map loader's insufficient scratch
stack; the earlier clock evidence below is unchanged.

## Result

The retained C3080 stack now enters and RETURNS from the actual C3640 clock
refresh, writes its formatted time through the real text setter, and creates
four further map controls. It stops before C328B reads the character map fields.
This is offline native execution with explicit external time input, not visible
rendering, full initialization, live battle, or recovered monster statistics.

Pinned current image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
RVA=file offset, BASE400000. No retired sources or game instruction patches.

## Same-VM Producer and Consumer

`prepare_character_clock` uses the existing original S2C1A writer in the SAME
character/owner VM. Its two stores at character+453C/+4540 qualify exactly those
eight bytes for the character read guard. CPU and the pending main stack remain
unchanged. Input packet and receive tick are explicit diagnostic inputs, never
read from an old session fixture or invented as missing-state defaults.

`continue_owner_map_clock` starts at the real pending C3640 with ESP=SP-F4.
It executes the original IAT call to WINMM!timeGetTime; a bounded OS adapter
supplies one explicit DWORD at that imported target and accepts only the exact
native stack and C365D return address. Original C3640/C3710 arithmetic and
149630 conversion execute, followed by 1077C0 and the actual CRT formatter.
The 1E500 ->26700 ->26140 chain writes the resulting text into its real surface
text record. The test checks both the supplied label and stored NUL-terminated
bytes, not merely the existence of a call.

Diagnostic example: logical1A010000 at tick10000, observation tick20000, produces
`06:01` under the actual client arithmetic. This is not a recovered server
time policy. The real C36DE return reaches C311E; original106550 and three
1057D0 calls then consume already loaded Cuse/BaseInterface/martrom resources.
No game return is fabricated or resumed past an unresolved game callee.

The exact final boundary is C328B, ESP=SP-F0, before character+14/+18 reads.
The single1112C0 entry count remains one. Character/catalog memory is preserved,
the battle renderer is unchanged, owner writes reconstruct exactly from native
events, and owner canaries survive. Unwritten character map bytes still fail
the source guard.

## Next Producer

`prepare_character_map_selector` separately executes original6865C..68675.
Its input is an explicit DWORD from world-body+24, with no whole-packet receipt
claim. Native6866B writes low6 bits as WORD character+18;68672 writes the low
WORD shifted right6 as DWORD character+14. No other character bytes are written.
All64 low-area values, four scene boundaries and two high-WORD patterns are
tested in512 combinations. These are field-width probes, NOT512 valid maps;
the full world receiver's upstream area gate is outside this writer slice.

The next retained continuation must use the original map catalog on the existing
owner+CFF70 bank, preserve item mappings, and bind each map-panel pointer through
its actual native producer. It must not replace missing map fields with zeros.

## Verification

Registered CTest3/3 passes in163.07s:

- current_world_clock:13 tests,1.10s.
- current_battle_map_selector:3 tests,7.70s.
- current_battle_owner_clock:3 tests,154.25s, including all prior resource and
  retained battle-prefix setup needed by this continuation.

No production C++/Lua architecture, database values, process, network or UI
state was changed by this offline continuation.
