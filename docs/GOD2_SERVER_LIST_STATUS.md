# One Server Entry Accepted

SERVER_LIST_READY=true, LOGIN=true, visible count=1, selected entry ID=0.
Selection is automatically highlighted; confirmation has NOT been performed.
No new C2S was observed. Character reconstruction has not begun.

## Evidence

Empty-list anchor: artifacts/runs/server-list-state-01.
Accepted run: artifacts/runs/server-list-one-01.
Golden: artifacts/golden/server-list/server-list-one-01.
Screenshot: window-1789770876425722600-01.png in the accepted run, showing one custom server.
server-list-result.json was derived from the completed run; original run.json is retained unchanged.

- Directory count at VA0x5b489c is already 1; first pointer at VA0x5b48a0.
- UI entry table is UI+0x8c, stride20. The initially zero availability WORD is entry+2.
- UI consumer RVA0x6e45 requires this WORD !=0; RVA0x6e6b adds the directory name; RVA0x6ea1 increments visible count.
- Opcode4 handler RVA0x14234 requires ID<64 and writes the following DWORD to entries[ID] at RVA0x1424d.
- Logical packet: 04 00 00 01 00. Transformed wire: 08 00 01 01 FD FE FE AE.
- Runtime write=0x00010000; visible count=1, enabled0=1, selected=0, directory_count=1.
- The packet has no name/address/port and no explicit count. It enables one existing directory row.
- Name and endpoint remain sourced from the frozen local profile, whose configured IPs are 127.0.0.1.
- Earlier STATE_LOGIN_ACCEPTED snapshots mislabeled UI+0x590 as selected. That was a diagnostic error; selection proof is the UI consumer's WORD at UI+0x8f4. Instrumentation is corrected.

## Required Ordering

The list status must arrive BEFORE terminal opcode0x0a, while the credential receive loop is active.
The terminal returns directly to the UI list consumer. Sending a list only after LOGIN_ACCEPTED is not supported by the observed path.
Actual order: seed S2C, seed C2S, post-seed S2C, credential C2S, opcode29, list status, terminal.
All existing login packet bytes are unchanged. protocol-core.csv records this observed order, not the proposed order.

## Reproduce

```powershell
.\build-strike-lab\Release\god2-strike-runner.exe --mode MODE_COMPAT --network-strike --cpp-server --post-seed --c2s-strike --s2c0003 --login-terminal --server-list --lab-case A --run-id UNIQUE_NAME --timeout 20
```

New god2_server_list mode is loopback-only. Existing configurations remain unchanged.
ServerListSent means completed socket write; client acceptance is separately certified by runtime evidence.
The aggregate reducer was integrated after the accepted client run; packet ordering is additionally tested against the rebuilt C++ binary.

## Next Blocker

SERVER_SELECTION_CONFIRMATION_PENDING. Windows Computer Use reported native pipe unavailable.
Do not claim the confirmation click, server-select request, connection handoff, or character stage succeeded.
Resume with a normal confirmation action once the UI tool is available; never patch UI state.
