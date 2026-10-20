# Native identity and appearance producer follow-up: pass8

Status: PHASE1 SOURCE_STATIC_ONLY. This pass performed static REA and source
reading, with no build, test, game/native execution, VM, codec invocation,
game SQL/schema, deployment or production-source change. It adds an actual
definition-section input chain, a ChangeDoll record writer and a concrete
native text-safety contract. It does not recover the original server's full
player/pet identity or equipment-to-battle-appearance producer.

## Exact inputs and qualification

Original Taiwan God2.exe remains SHA256
`aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48`.
Evidence root D is
`C:/Users/risei/.codex/artifact-archives/god2-server/20261021/native-scheduling-material-generation-pass8/native-material`.
The first session reuses pass7's closed analysis input, SHA256
`f42f71f20cc7c4d05cbe4b2bc3d3f51c3b942b1c4f7323f46db41776d881e52f`.
The second uses `parser-upstream-seeded-v1.analysis-pe.bin`, SHA256
`466df9fab4ebcdb4bd3fa507aa96720e95b1120feff21deccf408667946c88a0`.
Its sole added analyst entry is `0x456130`. The provenance receipt compares
all13 original PE sections byte for byte with the original. Analyst CALL seeds
are analysis aids, not evidence of a native caller. No original file changed.

Both TTY worker sessions, `material-pass8-a` and `material-pass8-b`, completed
`close_binary`, then helper/CLI exit0 without forced termination. Individual
unresolved/empty queries remain in the evidence rather than being relabelled
successful analysis. All addresses and `0x` offsets below are hexadecimal;
unprefixed column indices, byte widths and wire offsets are decimal.

The current compressed csvZ byte pin remains the pass7 observation, not a
newly decoded dataset. This pass did not invoke a codec or compare decoded
rows. It does not replace the older149c/old-data qualification of
`NativeEnemyDisplayCatalog` with current-aaf authority.

## Actual section input before the26-byte EnyName writer

Pass7 established `0x45A1A0` as an actual local26-byte display-definition writer.
This pass follows its concrete source instead of re-reading the battle consumer.

| Actual function/PC | Recovered source contract |
| --- | --- |
| `0x456130` | Sets parser capacity to52 fields through `0x451920`, opens its filename argument through `0x451960`, reads a header through `0x4519C0`, then dispatches section-name column0 and count column1. |
| `0x456DA4..0x456DE5` | Compares the literal `EnyName` at `0x589F08`, then calls `0x45A1A0` with the section count. This is an actual call in the original code, not the added analysis seed. |
| `0x456E3A..0x456E7B` | Compares `ChangeDollCount` at `0x589EE8`, then calls `0x45BB10`. This independently identifies the transformation definition's source section. |
| `0x451960 -> 0x402530` | Opens the caller-supplied pathname through the native file wrapper. Exact outer filename selection remains unproved. |
| `0x4519C0` | Reads an initial line into a512-byte buffer, tokenizes it, copies selected header fields, parses numeric fields, rejects the selected zero header value and conditionally skips header lines. This is not proof that an arbitrary file is a valid current dataset. |
| `0x451A90 -> 0x451BE0` | Reads each subsequent line into a4096-byte buffer. The tokenizer splits on comma or LF, copies at most0x17B bytes per parser field and appends NUL. No quote-aware CSV algorithm was established by this body. |
| `0x451B60` | Returns a nonempty field pointer only for an in-range column; otherwise null. |
| `0x451BA0 / 0x451B50` | Decimal `%d` helper starts its temporary at0 and returns0 unless exactly one conversion succeeds. This is distinct from the unchecked composite-token conversion inside the EnyName writer. |
| `0x451AE0` | Copies the chosen field as a NUL string without a destination-width argument, or writes a zero first byte for a missing field. Tokenizer bounds do not make every downstream destination safe. |

`0x402530` copies the pathname, appends the literal `Z` (`0x58236C`), and first
tries that path with `rb` (`0x582350`). It tests two leading read values against
`0x05` and `0x16`; on the matching branch it rewinds, obtains a temporary path,
calls `0x401D20`, closes/rewinds streams and opens the temporary path with
`rt` (`0x582378`). If that route does not yield a usable stream, it clears the
selected wrapper flag and opens the original argument with `rt`. These are
static control-flow observations. The transform algorithm, temporary-file
contents and a successful decode of the owner's csvZ were not executed or
claimed. The literal `Z` makes the observed `<argument>Z` candidate concrete;
the parser argument's actual filename still needs its outer caller.

The new raw E8 scan found an original `CALL 0x45A1A0` at `0x456DE5`. Adding a
separate analysis seed for the enclosing `0x456130` allowed REA to recover and
confirm that whole dispatcher. Original relative-call bytes also nominate
`0x4557CD` and `0x4558A0` as callers of `0x456130`, but the candidate containing
entry `0x455780` was not recognized in this session. Its one failed batch item
is retained. Raw candidates alone do not establish its argument, filename or
complete native lifecycle. The next bounded trace is that outer entry with
separate input provenance, not another identical failed query.

Evidence: `definition-parser-upstream-and-tokenizers-pass8-v3.json`
(`ev_5ec7dbba7df82c8ae848e64498e88b4afb97bcccdd7d5516550f8d6188173f3c`),
`assembly-actual-section-dispatch-pass8-v5.json`
(`ev_d4d419087c585ee360375b84e050709de8e278288390aef597058582905ab2b9`),
`parser-file-input-and-morph-record-source-pass8-v5.json`
(`ev_e2028a3abccb3cb0835de85a171bedd0b20417eda364ff0190674fb728a64b466`),
`file-input-and-world-initialization-candidates-pass8-v6.json`
(`ev_bebf5eec66b1c677144ce376c496c9a45979cf566e5411d6f91a00b53277e307f`)
and exact constant bytes in `file-input-suffix-and-modes-pass8-v7.json`.

## ChangeDoll has a real48-byte local definition writer

`0x45BB10` allocates `(count+1)*0x30` through `0x547E23` and stores the table at
definition-owner `+0xD2AAC`. The successful allocator zeroing is the existing
current-aaf pass7 proof; allocation failure is not a successful material source.
For each admitted row, numeric column0 must be nonnegative and below the
section count. It selects the0x30-byte record by that column, not by loop order.

| Record offset | Width/source written by `0x45BB10` |
| --- | --- |
| `+0x00` | WORD: column0, the row key. |
| `+0x04` | WORD: column1. Meaning not assigned here. |
| `+0x08` | Native pointer to a newly allocated NUL-terminated copy of nonempty column2. This pointer is process-local, not serializable wire material. |
| `+0x0C` | BYTE: column3. |
| `+0x0E`, `+0x10` | WORDs: columns4 and5. |
| `+0x12..+0x2E` | Consecutive WORDs: columns8 through22. Columns6/7 are not directly stored by this body. |
| Other initially untouched bytes | Successful zero-initialized allocation, not a universal wire default or evidence of additional meanings. |

The owner also retains a signed-short high-water value at `+0xD2AB0`, updated
to the row key plus1. `0x45C100` checks a low16-bit requested value against that
high-water value; it is not an exact row-presence check. `0x45C060` copies all48
bytes only after the record's first WORD matches the key. `0x45C000` supplies
an8-byte local value: key WORD, record byte`+0x0C` as output byte2 and record
DWORD`+0x0E` as output DWORD4. The observed body does not initialize the spare
output byte3; the failed-key paths of both getters also copy stack temporaries
without establishing valid record contents. A safe source recipe must retain
exact row presence and complete valid source; it cannot invent zero for a
missing key or treat a copied native pointer as portable data.

New incoming references for `0x45C000` include actual calls from the world
dispatcher and `0x503D30`. This confirms use of the same local transformation
definition, not a new derivation of all player/pet wire fields. The existing
world and battle appearance consumers use transformation data differently.
Neither this definition writer nor these getter call edges supplies the
server's selected pet S1C WORD7, full status DWORD or complete17-byte wire
appearance. In particular, a transformed display does not prove that the
saved pet's key equals its battle name reference.

The pass7 WORD7 alias result remains intact: the two high flags have an
observed priority, and multiple words can reach equal lookup keys while
selecting different definition contexts. This is a decoder, not a unique
inverse or a mandatory original-instance identity predicate. No new Catalog
key-equality rule follows from the ChangeDoll table.

Evidence: `identity-text-and-morph-definition-pass8-v1.json`
(`ev_fa1ff51044aca047c7cb471b3ca3304d974a1b7a924018b0be7421e45361c6fc`),
`parser-file-input-and-morph-record-source-pass8-v5.json`, and
`morph-eight-byte-getter-callers-pass8-v7.json`
(`ev_b7375a5257c16bfce1d92302e4b75dce524344510d6ebbd5f3c8833d044166a5`).

## Equipment packet sources do not yet supply ordinary components

`0x496550` is an actual current-aaf C28 producer. After the observed modal/UI
guards it sets the pending flag and sends exactly a WORD key, a slot BYTE and
a flag BYTE using `0x4132E0(0x28, ..., 4)`. It does not serialize an8-byte
appearance or turn metadata into a battle86/4 in this body.

`0x498DD0` handles the observed S3B instance update: after its slot checks it
copies20 bytes into the inventory entry at UI-owner `+0x85610+slot*0x18`, looks
up item metadata through `0x459A60`, adjusts the adjacent count/state and calls
the relevant UI refresh helpers. `0x4991E0` handles the observed S41 update to
count and low-WORD key, with inventory/modal refreshes. These are real source
updates. Their transitive refresh graph has not been exhausted; absence of an
in-body battle86/4 writer is not a global no-conversion proof.

Two bounded full-text literal searches found the selected ordinary component
state displacements only in `0x503D30`: `0x503F43/0x503FFC` for `0x1539ADC0`,
and `0x503F4E/0x50400F` for `0x1539ADC4`. Computed bases, aliases, bulk copies
and intermediate wrappers are not excluded by those searches. A literal
`0xDBC` search in the selected battle interval had no matches; that does not
prove the species field has no aggregate-copy writer. These searches narrow
the next trace without pretending to inventory every assignment.

The two attempted world-entry candidates were also bounded: `0x467860`
resolved to the WORLD loop, and the containing procedure for `0x468130` is
`0x468120`, which clears a selected structure and calls `0x497FE0`. Neither is
new proof of the complete2A initializer or its filename/appearance source.

Known packed shapes remain World2A logical13..20, DA logical7..14 and battle
86/4 logical4..11. Equal shapes are insufficient source authority. World
`0x461270` has mounted/Drv selection, while battle `0x5177C0` selects Fight
resources through `0x454F60/0x454E50`. Full root40/2A capture pins and complete
qualified battle prototypes therefore remain necessary. This pass did not
derive unknown selectors from equipment keys or reinterpret old datasets.

Evidence: `native-entry-and-equipment-data-producers-pass8-v4.json`
(`ev_2b00603399e6c0eace62dbe5458a7ff2aea22b7844ad0ca380d001e94f816629`),
the two ordinary-component literal receipts, and
`battle-species-field-literals-pass8-v3.json`.

## A concrete related native text-safety defect

Normal player S1C wire variant`0x2000` becomes normalized descriptor
variant`0x4000` in the existing current-aaf `0x515C90 -> 0x52CCD0` path.
`0x515C90` copies wire9..40 to the descriptor. The existing caller assembly
then selects the two fields independently:

| Caller | Source slice | Actual callee behavior newly traced |
| --- | --- | --- |
| `0x52D19A -> 0x52D1A1 CALL 0x5097D0` | Descriptor`+0x0E`, i.e. wire9..24 | Scans to NUL at `0x50980E`, computes centered padding, scans again at `0x509851`, then copies `strlen+1` with MOVSD/MOVSB at `0x509864/0x50986B` into renderer`+0x70`. |
| `0x52D1AD -> 0x52D1B4 CALL 0x509E70` | Descriptor`+0x1E`, i.e. wire25..40 | Equivalent unbounded scans at `0x509EAE/0x509EF4` and copies at `0x509F0A/0x509F11` into renderer`+0x81`. |

These routines do not cap the source at16 bytes or add a missing terminator.
Requiring a NUL inside each actual16-byte player source is a conservative
qualification before using a complete prototype. It is not an observed
native decoder rejection or a recovered official name-length rule. A scan
crossing into an adjacent field might find a later zero; that possibility is
not a safe fixed-field source contract.

The pet variant has a different32-byte text source. Existing current-aaf
pass7 assembly shows `0x5164E0` variant`0x4000`, source wire+9 at `0x5164F6`,
unbounded SCASB at `0x516503` and copy at `0x516512/0x516519`. Thus the related
pet qualification must be checked independently rather than claiming that
player two-field validation closes every text route. Enemy variant wire9..
contains parameters; a blanket NUL predicate would wrongly reinterpret them.
This lane supplied the native evidence to the source-owning agent; any actual
source patch and its review have separate receipts. This document makes no
claim that a source predicate has been compiled or accepted in the game.

New text evidence: the two `assembly-*-text-unbounded-copy-pass8-v2.json`
receipts (`ev_103aa5e91b32f7fd31298029c8ba7b8efd1c8da557069e2c139939f7fa329ca2`
and `ev_2e52afd309af5f37bf411f19fb2961af70e2b6e4bd7d993cb3cb0b6a0ddf1869`).
Caller/normalization reuse is explicitly pass7's
`assembly-pet-species-word-pass7-v4.json`
(`ev_e16b5a3a5d010c722f8a9dbd5f10669da329807b90942ecf757794ab6c200d9b`)
and `assembly-identity-complete-pass7-v3.json`, not a newly executed capture.

## What this actually removes, and what remains unknown

| Material question | Concrete new result | Remaining authority/next trace |
| --- | --- | --- |
|26-byte EnyName local definition | Its real section dispatcher, parser columns and native file-wrapper input are now traced. | Recover actual outer filename caller `0x455780`; qualify complete current dataset without borrowing old pins. No decoder was run. |
| ChangeDoll local material | Full48-byte row writer and exact8-byte getter dependencies are known. | Full row/source presence, safe allocation, actual transform selection and server wire construction remain separate. Native process pointers are not portable material. |
| Ordinary equipment components | Actual C28 producer and S3B/S41 source updates, plus bounded state-write candidates. | Follow refresh `0x49B850`, slot-specific callees and metadata fields to the actual component writer; do not infer equipment-to-Fight conversion from packet shape. |
| S1C player/pet text | Exact unbounded native reads justify per-variant bounded-termination source qualification. | Identity/name authority, encoding, receiver-specific values and all other opaque fields still need full qualified material. |
| Pet WORD7/morph | Definition and lookup alias boundaries are clearer. | No actual instance-to-wire producer proves a unique word or required equality to saved metadata. Trace the real selection writer instead of inverting the consumer. |
| Full86/4/root40/2A linkage | No new complete producer was established. | Preserve complete source pins; trace actual equipment/initialization writes and every unknown wire byte. |

No opaque byte, status flag, identity or species word is synthesized
as zero. The existing explicit saved-vitals/level adapter remains CUSTOM,
not an original growth or display-identity formula. A local26/48-byte
definition recipe does not remove complete S1C/86/4 capture requirements or
authorize a current server encounter with guessed enemy/person statistics.

The unresolved packet/appearance rules remain OPEN. Source-only proof is not
Windows compatibility, animation timing, gameplay or original-server rule
acceptance. Complete evidence hashes, author review and owned-session cleanup
are retained under D; formal reporting and publication belong to the parent.
