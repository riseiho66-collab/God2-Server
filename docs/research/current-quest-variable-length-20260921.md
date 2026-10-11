# Current quest dialogue variable record length

Pinned mapped x86 image:
artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin
SHA256149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
All locations below are RVAs at base0x400000. No retired corpus used.

## Receive path

World loop68B1C calls13420, then13650 retrieves the assembled logical record;
68B4E dispatches its opcode. Length table1324+4*7A points to1318, whose
`B8 FE FF FF FF C3` returns sentinel-2. At134E3 the receiver selects its
variable-length branch. It accumulates opcode and two length bytes into
network object+2CC4 and tracks total bytes in+2CC0.

1351F zeroes EDI;13521 reads an unsigned little-endian word at network+2CC5,
which is logical record offset1.13558 compares accumulated bytes against EDI;
13566..13590 reads until that total is reached. Thus the declared length is
the full logical record size including opcode and length word, not an extra
payload size and not the encrypted outer frame length.

13528 compares with0xA00. Values above2560 reach assertion setup13534.
1354B/13551 rejects values greater than or equal to2560 at1359A. The usable
capacity is therefore strictly below2560, despite the earlier strict-greater
assertion check. Values0,1,2 are not rejected by this slice; this does not make
them safe dialogue records. A server encoder must impose a content-aware
minimum. Mode1 consumer reads through logical offset11 in the previously
qualified branch; UI/rendering and other modes still need qualification.

## Verification and limits

tests/research/test_current_quest_variable_length.py checks image identity,
7A table pointer/sentinel and the original134E3 comparison. Unicorn executes
unchanged code1351F through actual branch boundaries for lengths
0,1,2,3,11,12,26,27,28,255,256,2559,2560,2561,32767,32768,65535.
Assertions/error calls are stopped at entry, not stubbed. EDI must retain the
exact unsigned input. Two tests pass,17 boundary cases. No socket, game
process, UI rendering, partial-arrival behavior or assertion continuation is
emulated. Native full receive-loop/live-client acceptance remains pending.

This closes the previously unknown length-word interpretation, not the whole
7A encoder or quest protocol. The earlier27-byte fixture is not a universal
packet size. Next: bounded mode1 construction, real text-table identity,
live own-server consumer and action request, then server-owned conversation
authorization and transactional quest rules/rewards with provenance.

## C++ mode1 candidate construction

src/protocol/RecoveredQuestDialogue.h now constructs the previously executed
27-byte non-formatting mode1 candidate. Its length word is computed from the
record size. This does not assert27 is a universal dialogue length. Request,
reply and context are checked at full u32 width before narrowing; text key must
be nonzero and inside the caller-supplied matching table count, conservatively
bounded to32767. The caller remains responsible for actual table identity,
world state and conversation authorization. Unused candidate bytes are zero;
no gameplay or text payload is invented. No Application activation yet.

recovered-quest-sync --dialogue-mode1 emits compiled candidate bytes. The
variable-length research suite now feeds those bytes to the pinned original
decoded dispatcher, header consumer and request producer for five header
combinations including high-bit replies and FFFF close-only sentinel. Native
85 output retains request/context, normalizes reply as previously observed,
and preserves the explicitly poisoned scratch byteA5. Eight invalid input
cases produce no bytes. Three targeted CTest suites pass.

This links the C++ candidate to original instruction slices, not a complete
socket/render interaction. Tests still use a synthetic one-entry text table
with the native empty-text pointer and stop before rendering; only text key1
has native execution coverage here. Other in-range keys have arithmetic bounds
coverage, not content/render qualification. Live client text-table lookup,
visible dialogue and own-server C2S exchange remain the next acceptance steps.

## Real loaded text-table evidence

New default-off --observe-quest-text-table flag reads the current native table
at the first observed world frame. It requires world-frame observation and
does not write client state or enable a quest server handler. It records the
resource owner, signed count at+B2C48, table pointer at+B2C4C, and up to256 bytes
from keys1..4, explicitly recording whether a terminator was observed.

artifacts/runs/native-quest-text-table-20260921-01 launches a fresh client against
the own server and reaches NATIVE_SAVED_POSITION_RESTORED/error null. The native
table count is14600. Source NPCMission01.csvZ declares1000 entries and has
SHA2561ff497204b5cf77cbbccffdf1836d7aeee30e46980ac1e85d8d0a08a0a4bcda7.
Regression checks decode that current file and compare keys1..4 byte-for-byte:
key1 matches its first256 bytes and is explicitly truncated; keys2,3,4 match
their entire NUL-terminated strings. Key3 is therefore a bounded nonempty text
candidate for the next dialogue experiment. Count14600 does NOT mean all14600
contents, mission relationships or quest rules have been verified.

The three targeted CTest suites pass. This removes reliance on a synthetic
empty string for selecting the next live input, but does not establish dialogue
rendering, NPC ownership, quest acceptance/completion or awards. No such state
is changed by the observer. Next: send bounded mode1/key3 from the own server
and observe actual consumer/input behavior without replacing the loaded table.
