# Native round lifecycle and producer follow-up: pass9

Status: PHASE1 SOURCE_STATIC_ONLY. This pass used static REA and read source;
no build, test, target/game/native execution, VM, codec, game SQL/schema or
deployment ran. No production source or original client changed. An actual
client initialization path is not an original server scheduling producer.

## Inputs and bounded recovery

The current Taiwan original remains God2.exe SHA256
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
Pass7's closed independent analysis input is reused, SHA256
`e447ed88994f5716182c8d44a099d835080f608cb627d0002ac3ee1acf51020c`.
New evidence D is
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass9/native-round`.
All addresses and offsets prefixed0x are hexadecimal. B is the CWar allocation;
P is its containing Play owner, M=B+0x144938, and L=B+0xA9E9C6C.

Pass8's caller provider had reported only the analyst seed for5109D0/5112C0.
That did not prove the functions had no native callers. This pass follows
the missing lifecycle rather than repeating the FIFO, S88 consumer or269
displacement search.

Searching initialized original-address memory for absolute little-endian
function pointers to5109D0 and5112C0 returns no matches in the selected
0x400000..0x72FFFF range. Both receipts report complete coverage of their
selected initialized blocks. This is only a literal-pointer result, not a
global indirect-call or computed-alias proof.

A separate read-only original-file scan finds two E8 relative candidates:

| Original PC | Destination | Original bytes |
| --- | --- | --- |
|0x46514E|0x5109D0|`E8 7D B8 0A 00`|
|0x465836|0x5112C0|`E8 85 BA 0A 00`|

The first raw-scan helper filtered section execute flags and scanned zero
sections: this original has no0x20000000 flag on its13 file-backed sections.
Its empty v1 result has **zero coverage** and is retained as such. Corrected
v2 scans all13 file-backed sections, records every E8/E9 candidate to the two
destinations, and reports only these two. Scanning arbitrary bytes is not
instruction proof; the subsequent REA bodies confirm both CALL instructions.

The original analysis could not resolve either callsite to a function. The
first bounded added seed used earlier aligned stack-prologue candidates:
464820 is actually a preceding function ending464905, and4655E0's initial
decompile stops at an unresolved switch. These inadequate results remain in
D, including the per-item errors; they are not credited as lifecycle coverage.

The final seed uses the original SEH prologue464910 after the preceding RET
and NOP padding, plus465644, an actual case3 address from table465A14.
The latter is an interior case seed, **not** a new native function call.
This makes the provider recover the shared switch/default body containing
465836. No further seed expansion was performed.

Two small analysis copies have explicit function-recovery purposes:
`lifecycle-callers-seeded-v1.analysis-pe.bin` SHA256
`bf8c1b26ef6c5f83fcab5eb5783edeab003107ce4ad611d00a096a1b4e327599`, and
`lifecycle-callers-seeded-v2.analysis-pe.bin` SHA256
`64c98e76f0e164acd2d600f36da43e0ee565aa2675d07e5b929aa8c1a21db9f7`.
Each3238912-byte input has a provenance receipt proving all13 original
sections byte-identical; only the existing extra analyst seed is rewritten.
The original is never modified or executed. Analyst730200 edges are excluded
from all native-caller claims.

## Actual allocation and retained CWar owner

The recovered464910 body is a Play initialization path: its own final log
references `Play::Init - End`. Calling it a whole-allocation zeroing
constructor would be incorrect. Its selected allocation chain is now exact:

| PC / actual source | Observed operation |
| --- | --- |
|0x465104..0x465109|Push0xAB3B8C4 and call55B406; allocation result is EAX.|
|0x55B406|Calls `_malloc(size)`; on failure it can invoke the registered allocation callback and retry. No zero initialization is provided by this wrapper.|
|0x465124..0x46514B|Obtain four resource/source arguments through P+0xA7E05C4, P+0xA7E05DC and P+0xAA36480, then push them. These are not an identity-bound initiative comparator.|
|0x46514C /0x46514E|Set ECX to the allocation and call5109D0. The null allocation branch instead yields zero.|
|0x465164|Store the resulting CWar pointer at P+0xA7E05EC.|

The actual instruction and selected bytes confirm the original raw E8
candidate. The new caller query for5109D0 now returns464910 and the analyst
seed. The allocator's observed children are547973 and55B3E6; the decompiler
identifies the allocation call as malloc. Neither this wrapper nor the
selected enclosing allocation site authorizes assuming a zero-filled B.
No claim is made about every child called by the resource constructor.

Evidence: `native-confirmed-seh-constructor-and-state3-lifecycle-pass9-v5.json`
(`ev_af2bb6392d17a62872336bdaa9c5a3b29a0369f41258bccfc9b87ebd9979477e`),
`native-seh-constructor-allocation-widths-pass9-v5.json`
(`ev_ef80e802bb75040424568852df8b02b2fb183e77a724bce7a43c29185ebbf824`),
and the v6 allocation body/v7 actual-caller receipts.

## Actual entry/reset and loop share the same retained pointer

The original4655E0 prologue establishes EBX=P. At465638, ECX is checked against7,
then indexes DWORD table465A14. The table's case3=465644 calls467860 and
dispatches its returned state again. Case4=46565B reaches the actual battle
entry body. Provider names this shared region `switchD_0046563d::default`;
its synthetic function boundary is not an original source symbol.

| PC | Actual selected lifecycle operation |
| --- | --- |
|0x4657CA..0x465829|Populate a stack entry structure and copy two NUL-terminated strings from P+0x15396903/P+0x153968D2. This is a local entry structure, not a server S83/S88 producer.|
|0x46582B..0x465836|Push address ESP+0x1C, load ECX from P+0xA7E05EC, call5112C0.|
|0x4658C6..0x4658D9|Reload ECX from that same retained field and call515770 with output/context pointers.|
|0x4658DE..0x465957|Run post-battle/display cleanup, call465BC0 with the loop result, then dispatch state3 again.|

The new5112C0 caller query reports465638 plus the analyst seed. This closes
the native callsite/owner gap: a selected entry invokes5112C0 before515770
using the already allocated CWar. It does not establish a fresh allocation
or blanket reset of B on every entry. No runtime outcome, unbounded string
copy safety or server-side entitlement follows from this path.

Evidence: `native-cwar-allocation-and-init-containment-pass9-v6.json`
(`ev_33fe9fc6101732acfe941fdc5cd75a5ff9ed9e92dea7192c37b431bb8791ee47`),
`native-cwar-state-default-init-widths-pass9-v6.json`
(`ev_c834ae268e176769276eb72f4f97d156148d320b0b99f1bc777ff04937bf5e33`),
the original table/read-bytes v4 and recovered caller receipts v7.

## Counter/reset contract and the remaining authority

The new caller chain is checked against the existing current-aaf pass8
5112C0 instruction receipt, `battle-initializer-computed-aliases-pass8-v4.json`.
That receipt is reused, not claimed as another new decompile. Its explicit
write at5117EE sets **B+0xA9E9C64 to DWORD FFFFFFFF** before return. This is
a receiver-side sentinel initialization, now connected to an actual entry
path. It is not a server round-counter value or a reset-to-zero rule.

No direct initialization of B+0xA9E9C68 or L is established by this selected
entry/write-set. The already checked FB-DWORD copy goes to B+0x48..B+0x434;
the constructor's2B-DWORD zero tail begins B+0xA9EA4F0, above L. Manager
51FC40 writes different counter addresses after M rebasing. These bounded
facts do not prove absence of all aliasing writes or child side effects.
The enclosing malloc allocation is not a substitute zeroing proof.

The actual lifecycle thus supports explicit source-owned per-battle
initialization and preserving the existing receiver sentinel/queue contract.
It does not authorize replacing the supplied S88 value with an actor speed,
server grant epoch, allocation counter, constant zero or inferred initial K.
Pass6/7's K pulse and pass8's network FIFO remain separately qualified prior
evidence. No new identity-bound speed input, comparator, tie breaker, RNG
ordering, original S83 grouping rule or S88 sender was recovered here.

Multiple server schedules can produce streams accepted by the same client
loop. Learning this client reset cannot uniquely select the original one.
The present explicit CUSTOM scheduling remains CUSTOM; it is not upgraded
to original-server provenance by the newly recovered native callers.

The next bounded native frontier is a computed/child write to L or68 on this
retained CWar, with exact owner rebasing through the already recovered entry
structure. Further original server ordering still requires a server-owned
producer/rule input or an independently qualified capture; actor playback
slot scanning alone cannot supply it. No new production change is justified
solely by these initialization observations.

## Lifecycle and review receipt

Sessions `round-pass9-a`, `round-pass9-b`, and `round-pass9-c` each retain
actual close_binary plus helper/CLI natural exit0 receipts. No process was
force-terminated; no original target was executed. Complete inline evidence,
failed/incomplete attempts, helper sources, input/section hashes, author
second review and independent review are retained under D. The separate
equipment source lane was reviewed read-only; its runtime-appearance gate
does not implement an original equipment or transformation mapper.
