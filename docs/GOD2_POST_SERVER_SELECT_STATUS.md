# Post-Selection Six-Byte Contract

UI gate is accepted and frozen. The golden request is preserved without
overwriting its original capture metadata in artifacts/golden/server-select.
No UI gate acceptance was repeated for this work.

Wire: `06 00 a3 a3 fd d5`. Zero-seed decoded body: `a6 00 00`; checksum: `d8`.
Header is LE16 length6; opcode is one byte; payload is two bytes. Static builder
RVA0x147d0 writes opcode0xa6 and low bytes of two arguments. The first argument
comes from UI+0x8f4, the second from UI+0xb40. The latter remains unknown, not
"channel ID". See artifacts/contracts/post-server-select-v1.json for all six
wire-byte positions, writer RVAs and qualification boundaries.

The original trace proves UI path A then a matched six-byte send return at
RVA0x12506. It does not prove dynamic execution of the inferred builder,
the state after TX, or a following receive/connect/character transition.

## Server Scope

ParsePostServerSelectRequest accepts only the exact fixture. New opt-in
god2_post_server_select mode reuses the frozen prefix, buffers fragmented
six-byte input only after TerminalSent, records PostSelectReceived, releases
hold, and sends nothing. All other post-selection input remains unsupported.
Original god2_server_list mode retains its prior behavior. No new S2C exists.

## Next Observation

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --ui-gate-rendezvous --post-server-select-follow --run-id post-six-UNIQUE
```

This is a frontier observation command, not another UI acceptance test.
It preserves the process after the frozen six-byte send, snapshots its stack,
rearms select and observes the next network event. RX_POLL means only an actual
select return with a read-set argument, not proof of a blocking receive or a
legal S2C handler. The post-send observation window is bounded at 30 seconds;
the preceding external UI wait remains unbounded. No UI input was added.

This new original-client run was NOT performed: the supported Computer Use
channel still reports native pipe unavailable. The owner was not asked to
repeat manual UI confirmation. Socket fixture tests validate the server path,
not the original client's next direction. CHARACTER_PHASE and CHARACTER_SCREEN
remain unproven; no character candidate or semantic field guessing is allowed.
