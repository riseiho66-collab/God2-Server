# Round337: common-parser text from exact SPI source records

NativePetRoomSourceCatalog now exposes lookup_definition_text over the same
complete qualified22-record dataset. The resulting NativePetRoomDefinitionText
retains its source_record and meaningful CP950 name/caption/description bytes.
This is historical definition-source use in the C++ core. It does not supply a
current native pointer table, player instance, eligible population or B1 action.

## Actual producer and consumer

The complete generic record parser459420..45995E takes selector0 directly to
common tail459933. SPI's historical selector0 still requires the previously
qualified zero-allocation/category-loader precondition. No category token or
display label changes that precondition into an observed current bank.

Common token4 is copied through451AE0 to record+8; BYTErecord+2Dh is then
forced0. Token7 is copied to+2Eh followed by forcedBYTE53h=0. Each meaningful
C string has at most37 bytes, but the native helper first copies the entire
token and its terminator. That force-zero operation is not a general overflow
guard. Actual4DC710 consumes the definition label at+8, so token4 has a direct
qualified text consumer. The lookup key remains independent token0; metadata
DWORD0 is numeric token5, not the key or label.

The common tail concatenates only nonempty tokens8..12 with literalLF between
them, without leading/trailingLF. It forces temporary byteBDh to0 only after
its unbounded appends, then copies the resulting C string to record+54h.
The token temporary has256 bytes; the forced byte limits the final meaningful
string to189 bytes. The code's general overflow behavior is not implemented.

Actual451BE0 tokenization finds comma/LF byte boundaries with native byte
strchr5489A0 and copies through547B80. It has no quote/escape/CP950 conversion.
548990..548994 is a pre-entry return stub needed by5489A0, not the strchr entry.
451BE0 caps an extracted token at379 bytes and explicitly terminates it.
These byte-boundary semantics do not establish a resource-decoding algorithm
or prove how an original CRT file read treats line endings.
If neither comma nor LF remains,451BE0 clears the remaining slots; it does not
accept a final unterminated chunk as another native token. The C++ API reads
the retained normalized source fields and projects tokens4/7/8..12, all before
the final field. It does not pass a normalized body through the native file
tokenizer or assert that its last field is accepted without an original LF.

## Finite source qualification and C++ implementation

All22 normalized raw records and every field remain exact to the336 pins:
name/token4 lengths6..24 bytes, caption/token7 lengths20..32, each raw field at
most34 and nonempty description joins26..89. No retained raw field contains
NUL, CR, LF or comma. Every field therefore fits the applicable native token,
name/caption and description buffers without taking truncation/overflow paths.
Source provenance remains historical70a4/75c3 with parser149c association;
decoded row offsets and full396 output remain unavailable.

lookup_definition_text first invokes lookup, which checks actual main source
tables, the complete envelope and all22 exact pins in one consistent read.
Only a qualified selected record reaches the private projection helper. An
absent key returns no result after the same complete qualification. The helper
splits all26 normalized fields, rejects line/NUL boundaries, checks field count
and relevant native buffer limits, and copies raw bytes. It does not decode,
convert text or apply display preference. Description LF is inserted only
between nonempty fields. Returned vectors contain meaningful string bytes;
neither terminators nor unknown396 padding are manufactured.

The returned source_record keeps independent native key, ordinal, line, record
hash, exact raw bytes and unknown offset. No numeric/source token is converted
by this projection, no common definition ID is assigned, and no source record
is changed. The finite checks are implementation guards for these exact pins;
they do not claim a new native resource validation rule.

The source importer and its envelope/storage checks remain unchanged. No Main,
Migration, gameplay request or Application calls this new text API. Existing
NativeMapItemCatalog twoSPI rows, C28/custody/companion behavior and all saved
state remain unchanged. Neither catalog read, projection nor importer was run.

## Numeric and resource boundary

451BA0 initializes its numeric local to0. A missing token returns0; the output
is used only when the native numeric scanner returns1, otherwise0. Its `%d`
child5480B4 delegates to55027D. A historical Python/VM adapter is not proof of
the actual CRT scanner's selected digit/write/return behavior. Source store
widths can be qualified independently of that conversion: token5/6 DWORD0/4,
token3 WORD114h, token13 WORD112h, token14..21 low bits inBYTE11Ah and22..25 low
bits inBYTE11Bh. WORD118h is separately forcedFFFF at45994A. This round's text
API supplies none of these numeric outputs.

The bounded actual scanner cuts qualify the `%d` dispatch55048F/550492 to550990,
DWORD accumulator EDI*10+(input byte-30h) at550B25..550B6B, match-count increment
550BBB, DWORD output write550BDD and count return550C9A. They do not close its
entire CFG. Input/whitespace helpers550CD9/550D0A, ctype pointer5A1B6C and the
multibyte branch through5A1D78/550D2E still require qualification. These are
conditional arithmetic/store/return facts; the finite raw decimal tokens alone
do not prove native classification, end-of-input or complete numeric output.

RomMaps lookup459FC0 chooses the first inclusive unsigned range from its actual
loaded bank using the lowWORD icon and returns an ordinal forWORD116h. The
original bank and allocation/load state remain a separate source gap. SPI has
no direct common-parser write toBYTE11Ch; preserve it as unqualified rather
than assigning a category, type or default value. Full396 construction and
PetEgg operation eligibility therefore remain unavailable.

## Publication and accounting

Static capture/review evidence is retained outside the desktop God2 tree.
tools/reconstruction/tw_native_spi_common_text_capture337.py is the exact copy
of successful sealed capture_selector0_text.py and is not rerun. Existing C++
header/implementation now use three real text fields
from22 source records; no packet/format/parser/phase/handler/complete-route
increment follows from this source projection. Frontierv23 and all prior
ledger fields remain unchanged; whole-game denominator/completion remain null.

Next: actual numeric conversion/resource bank/current396 qualification,
eligible owned population/F4 issuer/B1 rules/full ordered reply/storage/recovery
and Application hosting. FullTW/CN/fourWS/common tables/shared64,
coin99999999999/qualifiedstack99/native levels/fonts/text conversion/frozen
requirements persist. PHASE1 static source/hash/PE/Capstone/report only; no
build/compiler/tests/runtime/native/VM/codec/gameDBSQL/migrate/activate/deploy.
