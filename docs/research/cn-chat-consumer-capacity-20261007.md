# CN5C primary consumer capacity and phase boundaries, 2026-10-07

Prior round: catalog42 added the conditional CN2F -> required native authority
-> CN/TW5C source. This round recovers primary receiving/display bytes and
integrates an actual CN display destination budget. This is static native/source
recovery, not tests, runtime acceptance, database inspection or deployment.

## Primary world/battle consumers

The branch filename suffix is an ordinal, not the opcode value: CN world5C is
`0048fcc0-switch-0-case-60.c.txt`, battle5C is
`005485f0-switch-0-case-26.c.txt`. The catalog's opcode92 selects them.
The initial lookup of ordinal92 instead returned an unrelatedF6 branch; it was
discarded before source decisions. The current artifact copies the authoritative
phase records and their actual paths, and recovers bytes directly from the pin.

World entry00492278..004923E6 uses EDI as the actual native record. Direct packet
reads are DWORD5 for self/peer actor matching and byte9 for channel/tag; text13
is passed to consumer functions. Normal exits return to the existing dispatch
loop, not into another invented phase. Battle entry005488BC..00548906 uses ESI
and reads byte9/text13, without the world actor lookup. Its epilogue returns to
the actual battle receive loop. Callees are retained as edges, not executed.
No bytes3/4/10/11/12 are read by these bounded branches; this observation does
not prove their original server values, semantics or unusedness in every path.
No default/zero header is authorized by lack of a consumer read.

| Consumer condition | World behavior | Scope still missing |
| --- | --- | --- |
| channel0..9 or18 and foreign tag | Native0053FB30 conversion before world routing | Actual authority/identity, no tag-based client detection |
| channel18 | Direct0049A020 display | Actual server audience and privilege |
| channel0/6, `: $` marker | Special string search/conditional display suppression | Full named/control producer semantics |
| channel0/6, `: /board ` marker | Own retained board state and peer00531EA0 bubble; suppress ordinary display | Board persistence/permission/state |
| channel0/6 ordinary text | Self native actor match, own bubble; peer00531EA0;0049A020 display | Actual actor visibility/name linkage |
| channel12 | Text13 begins time32,005225E0 formats remaining bytes through0049DA00 | Binary/timestamp/template contract; not plain chat |
| other channels |0049A020 channel-specific display/template/global branches | All server issuance/state variants |

Battle converts only channels0..9, then0054B470 handles channel1's structured
05/16 grammar or calls0049A020. World18 conversion is not a battle18 contract.
The native channel gates004F5CC0 are local client settings, not server permissions.
0/1/3 use bits4/5/6 of the client's WORD at profile+449C,2/18 return1, other
inputs return0. They do not establish party/guild membership or broadcast scope.

## Recovered display destination

0049A020 first calls004A9590 with a256-byte local name buffer. It scans legacy
text, skips a second byte after a negative lead byte, and copies the prefix
before the first single-byte `: ` without a capacity check. It then calls the
actual004A7270 formatter for the plain display branches.

The old metadata declares only160 bytes for004A7270 because it stops near the
switch. Primary recovery instead follows its CFG through004A7612, with the real
19-byte channel selector map at004A7638 and nine target DWORDs at004A7614.
004A72D0..004A72DE clears256 bytes at `[ebp-0x104,ebp-4)`.
004A739B..004A73C0 copies the fixed per-channel prefix there; for channels<12
it selects four-byte slots at00899978, each containing exactly `1Ax\0`.
004A73C7..004A73DC writes channel18's eight CP936 bytes and terminator from
007F2CF8. 004A73E2..004A7423 finds input/destination NULs and appends all input
bytes including terminator using REP MOVSD/MOVSB, without a destination limit.
These primary operations justify the exact upper bound:

`full reply text bytes + native client prefix bytes + 1 <= 256`.

Thus native plain display channels0/1/2/3/5/6/8/9 have a252-byte maximum full
reply text,13 has255,18 has247. This includes source-provided speaker/identity
prefixes and suffixes; it is not just a message-body budget. It is a necessary
bound for this sink, not proof of all downstream UI/template destinations.
Additional native name/bubble and special005/013 output owners remain required.
The client-side transport limit below0xA00 is a different bound.

00531EA0 separately scans128 actual actor entries at stride268, compares their
DWORD+18 with the reply's world DWORD5, obtains name+1C and bubble handle+60.
This is not evidence that DWORD5 is a common database ID or a truncated handle.
00453BD0 requires handle<1000 hex and valid actual model/bubble owners; it has a
1024-byte copy destination, native board state and renderer calls. The recovered
plain display budget is smaller, but does not replace real actor/state qualification.

## Source increment

New `CnChatConsumerContract.h` encodes the recovered mandatory display bound.
SharedNativeChat now uses it for CN recipients before reserving space for raw
native speaker/identity prefix and suffix and encoding the converted body.
Unknown template/timestamp/global/default consumers require their own contract;
they are not processed as player prose. The original text is retained internally;
character-boundary display truncation/replacements remain exposed to the actual
qualifier. The frozen TW path and its254-byte envelope budget are unchanged.

No additional route, owner chain, phase binding or opcode is claimed. Catalog43
records the new source/native evidence. Actual source header values, native chat
audiences/rules, Board/battle/control variants, concrete shared suppliers and
Application hosting remain open. Whole-game total/completion percentage stay
unknown. Next work follows actual native identity/visibility links and supplied
reply issuance rather than inferring permissions from client display switches.
