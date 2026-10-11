# CN character mutation records in the shared server source

PHASE1: static PE/source reads and source integration only. No compilation,
tests, native execution, server execution, production DB access or deployment.
The preceding goal turn made progress: ten source files changed the three
existing login/selection output-queue continuations and were sealed. This round
adds four read-only record views to the main server; it does not finish those
records' authoritative gameplay routes.

## Preserved evidence and actual increment

The old CN project's CnCharacterRequests and lifecycle research already contain
ordinary17, delete19 and location18 layouts. The retained
cn-character-create-fields-agent-01 further corrects the special1B caller and
records opaque fields. These are reused evidence, not discoveries in this round.
The old snapshots and their conclusions remain unchanged. The current delivery
copies that retained request source and findings with their own hashes, alongside
23 current pinned CN PE/decompiled spans. Metadata-sized linear disassembly is
navigation evidence, not fragment-aware function/whole-game closure.

The shared main project's current CN protocol sources previously included1A
only; they did not contain these mutation record views. Added:

- CnCharacterCreate: ordinary17 only, full44-byte payload preserved. UI name
  reading is optional and limits only that accessor. Existing selection-word
  meanings remain neutral; unknown bytes are not Lua inputs or server rules.
- CnCharacterDelete: native19 with53 payload bytes, exact original account,
  credential and character name strings, low3 slot domain. The owned copy is
  wiped on destruction. Native padding/string tails have no zero requirements.
- CnCharacterLocationChoice: distinguishes two-byte C2S18 from three-byte S2C18;
  both bytes of the confirmation are retained. Neither choosing an offered
  location nor interpreting the opaque second reply byte is implemented.
- CnCharacterDeleteReply: keeps fixed23-byte02 and two-byte1E as separate
  alternative records. Control8's recovered decoder return is named narrowly;
  it does not provide a server deletion outcome or generic success projection.

No new S2C serializer, native value supplier, data table, storage transaction,
rule, permission or handler is added. These views have no current gameplay
caller; source availability is tracked separately from route connection. The
main native1A decoder and frozen TW character behavior are unchanged.

## Bounded owner and continuation facts

004450B3..C5 copies main+458 to login UI+16180 and main+454 to UI+1617C.
The current primary callsites below use UI+16180 as their network ECX; these
are world-network operations, not accountA6 operations merely sharing opcodes.
All addresses refer to CN SHA256
582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.

| branch | qualified native chain | records and limits |
|---|---|---|
| ordinary create | 0043D2A5/0043D308/0043D319 ->0047E900;0043D324/334 ->0047DCC0 | C2S17 payload44, marker payload40=4; waiter consumes S2C02 status word. Already recovered in prior create-fields delivery. |
| ordinary choice | 0043D472 send18;0043D489/494 ->0047DB70 | C2S18 payload1 comes from low8(UI+1612C)+1; S2C18 first payload byte is copied at0047DC8E, then only low3 bits update the cached07 row. Second reply byte remains opaque. |
| special shape | 004489C0/D5 and00448D10/25 ->00481390 | This builder sends1B, not17, despite matching44-byte payload shape. The second caller's complete upstream operation is still open. |
| special followup | 004489E0/F0 ->0047E330;00448AC3 send18;00448B03 ->004813C0 | On status0, this caller sends18 then1A using the existing07 selection; it does not call the ordinary18 waiter. Do not give1B ordinary-create behavior. |
| delete | 004483BD..E4 uses summary row+15h AND7, name row+2 and ECX UI+16180 ->0047E960 | Producer sends19 at0047E9FA with53-byte payload. It copies each string throughNUL; it does not use1A's strncpy/truncation behavior. |

19 payload layout: account[0..15], credential[16..31], native slot[32],
literal4[33], unwritten stack[34..36], name[37..52]. The caller supplies a
slot from summary row19&7, not an ordinal or shared DB character ID. The main
TW delete parser restricts its qualified subset to two slots; importing that
restriction would discard CN structural values without proof.

0047E960 branches on S2C02 or1E at0047EAA6..B2. On02, its WORD status
starts at network+2CC5, with the message selector at+2CD9 masked7F on failure.
The other02 bytes remain opaque; no zero-filled success reply is generated.
Its1E path calls0047ED00 at0047EAEE. That function subtracts3 from the first
payloadBYTE, range-checks<=1C, and dispatches at0047ED19 via29 DWORDs from
0047F29C. This table is outside the1433-byte metadata function span. The table
is preserved separately and supplied explicitly to a static CFG trace. Control8
targets0047EF89: XOR EDX,EDX;MOV EAX,EDX;POP ESI;POP EBP;RET8. It returns0.
The deletion caller tests that return at0047EAF3 and takes its distinct local
branch on0. Therefore this receive1E cannot simply be a generic failure.

That branch's raw0047EB58 is an indirect call through00AAF25C, followed by
DB10 C0F143 at0047EB5E..62 (linear FIST [EAX]/SAL CL,43). The decompiler calls
this DeleteFileA followed by an unusual x87 write. That annotation is not proof
of a correctly recovered import/call target or executable continuation. The
The current on-disk pointer at00AAF25C is006AF246, with no matching PE import
directory entry at that pointer address. Its96-byte native window begins with
0000 (ADD BYTE PTR[EAX],AL), before a jump and other code. This does not establish
DeleteFileA. Loaded binding/loader rewrites were not observed or executed;
follow the actual initialization/write owner of00AAF25C next. The current call
binding, code boundary and complete wrapper result remain OPEN.

**2026-10-07 import-boundary correction:** the preceding paragraph records the
earlier incomplete parser interpretation, superseded by
cn-delete-import-binding-01. Primary descriptor883 at00AAE4FC declares
kernel32.dll, FirstThunk RVA006AF25C and OriginalFirstThunk RVA006AF254.
The on-disk thunk006AF246 is an IMAGE_IMPORT_BY_NAME RVA, whose hint0/name is
DeleteFileA atVA00AAF246. It is not a callableVA006AF246. A general import
parser stopped after90 descriptors amid its error diagnostics, while the bounded
primary descriptor/ILT reader obtains1009 declarations and their terminator.
Absence from that partial parser result did not prove absence of a binding.
There is no need to infer a client-side writer for this declared IAT slot;
actual loader resolution is a distinct stage and was not executed or observed.
The earlier96-byte window at006AF246 is retained as a historical misinterpretation,
not the DeleteFileA target. The post-call0047EB5E..62 bytes and complete wrapper
outcome remain unresolved. None of this proves a server deletion transaction.
Do not use this branch to generate a guessed1E08 successful deletion. Cached07
compaction after a successful wrapper result is a client display change, not
proof of any official server deletion transaction. Historical findings are
retained; this additional primary boundary qualification does not refresh them.

## Actual gaps and accounting

The read-only views are not connected handlers. Ordinary create must obtain
actual server permission/rules, common identity and source-qualified CN data;
TW CUSTOM profile validation/zero-filled summary generation is not CN proof.
Its40-byte data shape alone does not justify populating07/1F/2A.

Deletion still needs current owned world admission and the exact offered07
slot/common-ID association, identity echo qualification, real permission and
current resource/online restrictions, atomic shared saved-state deletion and
generation invalidation, and complete native02/1E data from the real source.
Names/slots in19 cannot locate or authorize an arbitrary saved character.
Location18 needs a pending owned create operation and an actual offered-choice
source plus complete reply data; BYTE arithmetic does not define its game domain.

The missing issuer paths are maintained as OPEN, with no placeholder or
arbitrary-success handler. Four new protocol header files and one static
delivery tool; newly completed gameplay routes0, newly hosted source handlers0,
newly discovered opcode values0. Existing156 TW and156 CN C2S values,252 TW
S2C length entries and280 CN S2C phase entries remain unchanged. Native fields
and create continuations from earlier findings are reused, not new completions.
Whole-game route total/completed count/percentage remain null. Levels, native
fonts, saves and CP950/CP936/UTF-8 text conversion remain unchanged.
