# Actual Socket Battle Outcome

## Isolated Diagnostic

CUSTOM-0011 adds default-off `diagnostic_battle_terminal`, requiring existing
loopback/diagnostic-database/participants gates and exactly one round.
The existing synthetic attack31 uses power1000 percent and defense13, producing
297 raw damage and150 clipped HP loss against the synthetic enemyHP150.
These are deliberately lethal test parameters, NOT native or balanced values.

C++ Battle reaches Finished, then its precommit encoder appends the existing
57-byte89 layout with56 explicit zero fixture bytes after the17-byte86 HP
update. No EXP/items are granted or persisted. Failed encoding rolls back the
terminal action; replay after a committed terminal action is rejected. A dead
enemy does not retaliate. Session remains InBattle: no unproven world return.

## Actual Original Receiver

Run `native-socket-outcome-20260921-01`, PID7136/TID1780:

1. Original HP receiver returned with enemyHP0/maxHP150, sequence508.
2. Actual89 receiver518BF0 entered, sequence509, with exact57-byte zero-award
   logical record. Its return address was51459F.
3. Receiver returned EAX1 and ESP+8, sequence510; battle+A9DF6BC was1.

This is actual socket-fed original execution, not just successful server send
or independently invoked89 consumer. Native basic action is still invoked via
the existing diagnostic thunk rather than normal player UI input.

## Actual Result Panel Function

`native-socket-outcome-panel-20260921-01` was a TOOL_ERROR at the panel entry:
new event `ui` integer collided with existing structured warning-event data.
No client crash is inferred. Renamed the pointer to `panel_owner` and reran;
the failed artifact remains intact.

Fresh `native-socket-outcome-panel-20260921-02`, PID3140/TID9684, completes
the same lethal action and89 receiver, then enters original485070 at sequence511
and returns to515A25 at512 with ESP+4. Panel latch is1, mode0, handles14/15.
No code or control-state write forces the result panel or stage5. Test-owned
client/debugger/server processes were absent after cleanup.

This proves the panel function's execution/return, NOT rendered panel pixels,
result confirmation, stage5 cleanup, re-entry into world, actual death/action
animation, awards, persistence or balanced production gameplay. Next work is
the original result confirmation and battle-loop cleanup/world return. Do not
promote this diagnostic into normal service operation.

## Tests

- Release `config`, `recovered_battle_bootstrap`, `recovered_battle_service`.
- Config denies terminal mode without participants or with multiple rounds.
- Outcome encoder failure preserves active state, HP and revision; retry commits
  once and a repeated command cannot generate another result.
- Live artifact regressions validate receiver bytes/PCs/stack, result flag,
  ordered same-thread execution and panel function return.

## Natural Cleanup And Post-Battle Movement

Run `native-socket-battle-exit-20260921-01` continues from panel return without
input, flag writes or additional thunks. Original stage5 reaches515C40, then
battle loop returns to4658DE with EAX0 and ESP+68 relative to cleanup entry.
Original world loop467860 is entered again. No user confirmation was needed
on this diagnostic path; bit20 polling is not itself evidence of a click.

Trusted CUSTOM-0011 release now requires the same bound session/account/
character, diagnostic policy, InBattle state, committed action and Finished
snapshot. It removes the diagnostic battle and restores InWorld. It is not a
client-triggered transition or a production exit policy. Failed outcome encoding,
wrong owner, active battle and repeated release are rejected by tests.

`native-post-battle-movement-20260921-01` exposed a real missing message:
post-return C2S decoded frame `08 00 1C 01 00 00 00 C9`, followed by a movement
request. The unsupported1C caused `World frame contract rejected`; no ACK was
received. Preserve this failed run, whose overall outcome is EVENT_BUDGET_END.

Original return path65DF2 calls157F0. That producer queues opcode1C with4bytes:
caller lowWORD and the flag returned by original131C10 in the highWORD. The
helper returns1 only when original globals59DFD8/DA equal4/2, else0. Bounded
native execution proves these queue arguments; the actual packet capture
proves socket transmission. It is also used during initialization, so it is
NOT a universally valid battle-exit acknowledgement.

Parser appends ContextNotification without reindexing existing record variants.
Normal world service still rejects it. Only the isolated terminal route allows
one observed lowWORD1/configuration0-or1 notice after committed release, with
no reply/state/reward mutation. Other contexts and general gameplay remain
unqualified; the constant1 is an explicit diagnostic restriction.

Fresh `native-post-battle-movement-20260921-02`, PID7220/TID2020, completes
the whole diagnostic chain and three original path requests/ACKs. Final client
position is18,12, motion-state0, ring010304. Read-only DB regression verifies
recovered_positions=(character1,area2,scene15,x18,y12,revision3). Native battle
exit itself used no input; movement uses the existing diagnostic native-call
thunks, not physical mouse/keyboard. No battle reward or combat stat was saved.
All test-owned client/server/debugger processes exited.

This closes this isolated combat-to-world-movement path, not complete gameplay,
rendered animation, normal battle selection, balanced rules or durable rewards.

## Fresh-Process Post-Battle Restore

`native-post-battle-restore-20260921-01` opens the previous run's isolated DB
read-only and uses SQLite backup into a new run-specific DB. It starts a fresh
server and original client, authenticates the existing lab account, selects
the one existing character and restores native position18,12. No character
creation or new movement probe occurs. Battle diagnostic flags are disabled.

Source DB SHA256 before and after the restore:
`0a5211d6ca1a2d3bfe0996978acf9b51271014e02f824f26ccddf152be8e7b42`.
Regression compares the source/restored character rows and position revision3,
not merely the result label, and requires a different client PID. The original
source file remains unchanged; no production database is involved. Test-owned
client/server/debugger processes are absent after cleanup.

This proves saved position and character continuity after the isolated battle,
not persisted combat HP/MP, loot, EXP, quest state or reconnect during combat.

## Split Terminal Receipt Handling

The trusted diagnostic release additionally requires both action and control
receipts. If a lethal action arrives alone, keep InBattle and the Finished
snapshot until its one authorized standalone Control0B arrives. This narrowly
admitted receipt returns no payload and does not reapply damage or encode
another result. Wrong context, new attacks, repeated control and repeated
release remain rejected. Normal/non-diagnostic finished battles remain closed.
Domain tests cover the separate delivery path; it is not claimed as a captured
official split-packet policy. The real client runs currently coalesce the two
records. All of this remains CUSTOM-0011 diagnostic lifecycle behavior.

Fresh run `native-post-battle-movement-20260921-03` verifies the updated
executable with combined native records: outcome, natural cleanup, world return
and all three path ACKs/idle completion still pass. The live movement regression
now uses03; the independent restore regression retains source02 and restore01
so its actual backup provenance is not silently changed.
