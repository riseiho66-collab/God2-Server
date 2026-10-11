# CN deletion IAT declaration and bounded import-reference recovery

PHASE1 static-only work: no builds, tests, native/server/client execution,
production DB access, migration or deployment. The preceding goal turn is
progress: four read-only protocol views and a control8 CFG were saved. Its
file-IAT interpretation is corrected here without overwriting the old artifact.

## Primary declaration, not a loaded function pointer

Pinned CN SHA256:
582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8.
ImageBase is00400000. Import directory RVA006AA000 has Size00004EE8 and
ends with descriptor1009's NUL record, after1009 nonzero descriptors.

At0047EB58 the primary instruction FF155CF2AA00 calls DWORD PTR[00AAF25C].
Descriptor883 atVA00AAE4FC gives:

| field | primary value |
|---|---|
| DLL name RVA |006AF238, kernel32.dll |
| OriginalFirstThunk RVA |006AF254 |
| FirstThunk RVA |006AF25C (VA00AAF25C) |
| file ILT first cell |006AF246, followed by NUL |
| file IAT first cell |006AF246, followed by NUL |
| IMAGE_IMPORT_BY_NAME RVA |006AF246: hint0, DeleteFileA, NUL |

Thus this is a declared kernel32.dll!DeleteFileA import. The file DWORD
006AF246 is a name reference by **RVA**; it must not be followed as callable
**VA**006AF246. Loaded IAT resolution and actual API behavior were not observed.
There is no source basis for searching for a bespoke client writer solely
because a file IAT initially contains a name RVA: import resolution is a
distinct loader stage. This does not claim the full executable is loadable.

The retained source-recovery imports.tsv and calls.tsv already identify this
declaration/call. Their existing result is reused, not described as a new API
discovery. This round supplies a primary descriptor/ILT chain and fixes the
current shared server's static analysis workflow.

## Earlier interpretation is superseded

cn-character-mutation-contract-01 remains immutable. It recorded a general
parser result without00AAF25C, then decoded a96-byte window atVA006AF246.
The parser had returned only90 descriptors amid errors about oversized/broken
thunk arrays and too many import errors. Absence from that partial result was
not proof of a missing import. The96-byte window belongs to other bytes in the
image; its first ADD[EAX],AL is not the imported API entry.

The new cn_pe_import_directory.py reads the primary descriptor table within
its declared size, follows each ILT toNUL in a unique file-backed section,
reads names asRVA and retains separate file-IAT bytes. It refuses unbacked,
ambiguous, cross-boundary or unterminated inputs. It never loads a DLL or
follows an on-disk thunk as executable code. Metadata resource budgets are
analysis bounds, not recovered gameplay rules.

The updated character-mutation delivery tool now uses this reader, records
the actual declaration and captures the hint/name bytes instead of falsely
disassembling a callable target. CnCharacterDeleteReply's comment points to
the corrected declaration. The narrow control8 decoder-return accessor and
packet formats are unchanged; there is still no deletion authority/handler.

## Bounded indirect-call index and limits

The new immutable receipt reads1009 descriptors and1009 declared bindings.
Across the23 already retained metadata-sized native function disassemblies,
48 FF15 references match declared bindings. The index preserves original bytes,
function/site, IAT VA and DLL/name declaration. These are navigation references,
not48 newly recovered game routes, new packet values or whole-image reachability.
Linear metadata spans may include fragmented bodies/data; native phase and
caller ownership must still be established independently for each use.

Control8's0047ED00 switch still returnsEAX0 at0047EF89. Its caller's post-API
DB10 C0F143 at0047EB5E..62 and its complete wrapper result remain unresolved.
A correct import name does not establish a successful wrapper result or a
server deletion transaction, and does not authorize emitting guessed1E08.
The next native trace is this post-call boundary and its actual control/exception
continuation, rather than the now-qualified import name. Shared native19 slot/
identity ownership, save CAS/deletion rules, complete actual reply data and
source hosting remain open. Native17/18/1B operations remain independently open.

## Accounting and peer coordination

This round adds two static source tools, fixes one existing delivery tool and
qualifies the existing23-function import references. No new gameplay handler,
owner chain, phase/opcode source binding or complete bidirectional route.
TW/CN C2S values remain156 each; TW S2C supported lengths252; CN S2C account6,
world206 and battle68 phase entries. State/variant exhaustion is not established;
whole-game total/completed count/percentage remain null. Original clients,
levels, saves, native fonts and CP950/CP936/UTF-8 conversion remain unchanged.

The authorized web peer's two-tab/different-account and local-resource-clearing
handoff was received. Existing server state is per connection/account/character;
browser Origin is a transport policy, not a single-account identity. Peer mock
transport results are not server acceptance. Browser cache removal does not
create a native character/account deletion packet or permission. Actual shared
TW/TW, CN/CN and TW/CN multi-account acceptance belongs to the later centralized
phase; formal endpoints have not changed.
