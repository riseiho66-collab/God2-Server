# CN deletion status, local cache and pre-world connection lifecycle

PHASE1 static PE/source recovery only. No build, test, client/server execution,
DB access, migration or deployment. Previous goal work made progress by fixing
the IAT/name-RVA interpretation; the latest level acknowledgement alone changed
no implementation. Levels remain unchanged throughout this increment.

## Distinct local return branches and UI consumer

Pinned CN SHA256:
582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.
The new immutable cn-delete-completion-lifecycle-01 retains eight metadata-sized
PE/C/disassembly spans, three bounded CFGs and six conditional return records.
These are local source/instruction facts, not whole-program exception closure
or six new gameplay routes. The native security-cookie and called functions
still retain their own execution conditions.

| 0047E960 condition | local result/continuation |
|---|---|
| world object's +2CB8 is zero at entry | EAX1 before final cookie check |
| S2C02 status WORD at +2CC5 is zero | 0047EC3B sets EAX0 before final cookie check |
| S2C02 status WORD is nonzero | 0047EC09 zero-extends that WORD into EAX; +2CD9 &7F selects a message field |
| S2C1E decoder result is nonzero | same EAX1 return branch |
| S2C1E decoder result is zero | builds local filename, calls declared DeleteFileA, then unresolved exceptional tail |
| unsigned elapsed >=30000 while receive polling remains nonzero | separate jump0047EA6D->0047EB63; EDX=D0 and EAX=EDX before final cookie check |

0047F530 returns a message pointer only when the unsigned status is nonzero,
does not exceed the object's signed16 message-table count, and the selector is
less than3. Other cases return null; the caller subsequently copies through
that pointer. Native invalid-message/crash cases are not server reply defaults
or permission to invent statuses.

UI004483E9 tests the actual deletion-wrapper EAX. Only its zero branch starts
004483F1's local summary-list update. For the selected ordinal it shifts later
36-byte rows: two16-byte copies and a4-byte copy move next-row+2 to current-row+2.
It decrements summary byte0 only if nonzero, then clears UI's selected ordinal
WORD+1792D4. These are local07 row positions, not common character IDs. A decoded
1E08's own EAX0 is earlier than this UI test and must never be substituted for
the complete deletion wrapper's return. No common save/character deletion,
ownership rule, transaction or official reply-supplier has been recovered here.

## File-return boundary and local cache

The exact FF15 call at0047EB58 has the next instruction address0047EB5E.
The file bytes are DB10 (FIST DWORD PTR[EAX]), then C0F143 (SAL CL,43h), then
0047EB63's separate timeout/message block. Between the call and FIST there is
no EAX assignment. The independent timeout branch reaches0047EB63 directly;
it does not establish a skip over the FIST for the API-return path. This narrows
the old open boundary: the on-disk linear instruction start is now qualified,
while loaded-code mutation/exception continuation and actual1E outcome remain
unknown. No guessed skip or exception repair is inserted into our source.

Primary literals007F1624="Save" and007F162C="%s\\%s.hky" qualify the local
cache filename.0053FEE0 replaces filename-forbidden ASCII characters with an
underscore in this local copy.0053FF40 constructs a local path using the cached
current directory (except its leading-backslash variant). These operations
do not rename protocol identities, authorize a shared database delete or justify
altering CP936/CP950/UTF-8 conversion. The prior IAT correction is reused: declared
DeleteFileA is an API identity, not proof of the whole wrapper result.

## Follow-on controls belong to their own connections

After local-list compaction, if the world flag+2CB8 is nonzero,00448475 calls
00480B10 with explicit arguments(2,4,1) and ECX=UI+16180. The wrapper copies the
low byte of its second argument into its one-byte payload and calls00481440:
the qualified C2S logical record is0204. With the third argument nonzero it
waits for S2C03, clears receive state and writes WORD+2CB8=0100; opcode2 also
clears BYTE+2CB8. A timeout locally returns1, S2C03 locally returns0. The UI
ignores this control wrapper's EAX at this call site. Native03 payload semantics
and official response-generation policy remain unqualified.

00440CA0's separate recovery branch calls the same wrapper(2,0,1) only when
the account flag is absent and the world flag is present: qualified C2S0200.
These two caller contexts are captured by new CnPreWorldCloseControl, a bounded
read-only view. Neither form is the23-byte S2C02 status layout. Other calls and
control values, gameplay-phase semantics and an authority handler remain open.

00448488 then calls0047F310 with ECX=UI+1617C (account owner), name UI+58C and
send flag1. Its conditional C2S0A has16 payload bytes copied through the first
NUL, then flush/transport close. This existing account-disconnect evidence and
SharedAccountSelection integration are reused from cn-account-success-owner-01;
the new fact is the delete-UI caller/ordering. A world control may not detach a
different account or browser tab, or treat a claimed name as authority. Browser
cache clearing likewise creates no character-delete permission.

## Source increment and accounting

Added one bounded protocol view and one static delivery tool; annotated the
existing delete-reply view. No gameplay handler, hosted listener, new opcode,
owner chain or complete bidirectional route is added. Existing native opcode
counts remain TW/CN C2S156 each; TW S2C supported length entries252; CN account6,
world206 and battle68 phase entries. State/variant exhaustion and the whole-game
total/completed count/percentage remain unknown/null. Eight functions and six
return records must not be counted as eight/six completed gameplay paths.

Next authority work still needs native19's offered slot/common-ID and current
account/connection/generation lineage, real deletion rules, shared atomic save
mutation, online-owner invalidation and full qualified02/1E response data. Native
17/18/1B suppliers, actual pre-world close/03 composition, global inventory and
Application hosting remain open. This source view has no gameplay caller.
