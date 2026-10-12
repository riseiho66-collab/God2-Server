# Round338: exact historical locations and conditional SPI scalar source

The shared NativePetRoomSourceCatalog now supplements its returned22 source
records with independently proven historical decoded offsets, and exposes
physical scalar fields under an explicit stable-classification requirement.
Raw SQLv1 pins/importer/envelope are unchanged. This is source implementation;
no API, database, importer, native code or resource decoder was executed.

## Exact retained decoded source

Nonretired round314 retains source-entry/inputs/exact-restored/
gamedata.csvZ.decoded with SHA256
75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815.
Its receipt/seal preserve the historical70a4 encoded source lineage. It is
distinct from the current ef297 encoded bank; this round does not decode or
observe that current bank. The retained decoded file was hashed in place.

All22 SPI source lines8695..8716 independently match every normalized336 body
and all26 fields. The exact CRLF-inclusive window[673207,676763) is3556 bytes,
SHAe15b3f4e4533aae776dad7fbe4218e95583ee8df1f9ab4f7f5973fed26b3f257.
Only this bounded window is retained; original336 NULL-offset records/seals
remain intact. SPI header physical8177/offset611197 declares737 rows.

lookup still validates the complete installed SQLv1 dataset with its original
NULL offsets and raw pins. It then enriches a returned copy using the exact
key-ordered22 historical offsets. source_location_sha256 identifies a separate
proof, not the unchanged v1 catalog fingerprint8435556d.... The supplement's
canonical ASCII sorted-key compact JSON includes decoded hash, window hash,
CRLF identity and each key/ordinal/line/offset/line length/line hash/body hash.
Its SHA256 is
e9c54a0f4dfac81fa630513d352574b9c888cf2b2cbc52dac147baf19191e8b7.
Neither stored SQL rows nor earlier source observations are rewritten. The new
optional proof remains empty in read()/original pins, preserving their exact
equality checks. Text and scalar returned records share this supplemental proof.

## Actual finite numeric input and classification

5480B4 creates a string descriptor with input pointers at+0/+8, byte strlen
550140 at+4 and flags49h at+0Ch. Full550CD9 decrements remaining count, reads
and zero-extends the next BYTE when count remains nonnegative, otherwise calls
54EAE3. With descriptor49h its40h bit selects the direct EOF returnFFFFFFFF;
opaque file-refill children are not taken.550CF3 does not ungetEOF-1.550D0A
reads a byte then applies5484AF whitespace classification. Five complete input
cuts total428 code bytes.374 selected source numeric tokens are nonempty
ASCII digits, at most5 bytes, maximum58025; flags are0/1.

The selected scanner's decimal accumulator/output/count stores remain the337
source. After the final digit reachesEOF and the format reachesNUL, the exact
success path550C31->550C37->550C89->550C8E->550C9D returns assignment count1.
Prior337 conditional return550C9A remains valid for its other termination
branch; its original seal is preserved.451BA0's initialized local0 and
scanner-return1 guard still apply. No historical VM adapter is promoted.

550D2E handles unsigned(input+1)<=256 through WORD[current table+2*input]&mask.
ASCII andEOF therefore avoid its opaque multibyte child.5484AF uses equivalent
mask0008h for these finite values through either direct or helper path. The
global multibyte mode need not equal1 for this bounded equivalence.

NativePetRoomDefinitionScalars explicitly returns qualification
CONDITIONAL_EXACT_INPUT_AND_STABLE_CLASSIFICATION, required_input and
required_classification. Native conversion must receive the exact normalized
1..5 digit field bytes in the ordinary flags49h string descriptor. The retained
original lines end CRLF, while the source inventory strips that ending. Whether
the actual line reader removes CR before token25 is unresolved: a retained CR
would take a non-EOF pushback path through opaque553158. The finite digit-to-EOF
proof therefore does not close actual original-file final-token conversion.
The table
must remain valid for-1..255 and stable during the whole native call: '%' has
mask0008h clear, 'd' mask0004h clear, digits0..9 mask0004h set/mask0008h clear,
EOF both masks clear. This API does not observe or satisfy that requirement.

The PE initial pointer5A1B6C=5A1B76 and mode5A1D78=1 match these masks. Actual
553BB3..553DF7 can publish a generated table/mode or restore the initial pointer,
with opaque conversion/API children. Thus initial file values do not establish
current locale/classification invariance. Three complete direct bodies total
738 bytes; initial data totals522 bytes(4+4+514). The original classification
report's518-byte prose error is corrected in a separate immutable appendix;
its original seal and already-correct522-byte validation remain intact.

## Concrete C++ projection and scope

lookup_definition_scalars first calls the same complete qualified lookup. The
private source_fields helper, shared with the text projection, rejects NUL/CR/LF
and checks26 fields before indexing. finite_decimal accepts only the exact pins'
1..5 nonnegative ASCII digits and checks the signed32 accumulation bound. This
is restricted source arithmetic under the declared native classification
and exact-input conditions, not a general sscanf replacement or current numeric
observation. The API observes neither native input preparation nor classification.

The result exposes token5/6 as physical DWORD0/4, token3 lowWORD114h, token13
lowWORD112h, all8 directly written bits ofBYTE11Ah from14..21, and onlyLOW4 bits
ofBYTE11Bh from22..25. The preserved high4 bits of11Bh are excluded. No price,
effect rule, item category, common definition ID, default11Ch, resource ordinal,
padded/full396, player instance, ownership or action permission is inferred.
Native field widths remain their qualified widths; this is independent of the
owner's shared64 gameplay extension.

The same retained decoded source also proves57 RomMaps raw5-field rows in
original order: header line57/offset4374, rows58..114, raw token0 literal0..56.
Header+rows[4374,7887) total3513 bytes, SHA
1a5c850ba16876b8c28c67d2b1f36c7bcf0670643364f29edc029c6b9cc214e2.
Both path fields are retained without inventing token4 semantics. Existing
459F47..459FA3 is an interior row fragment; actual full loader/allocation/order
and stored range conversion remain next native source work. This raw evidence
does not yet supplyWORD116h or close full396/current loading.

No Main/Migration/request or Application calls the added API. Existing source
SQL/importer, MapItem twoSPI records, C28/custody/companion behavior and saves
remain unchanged. The new physical source values remain conditional definition
data; they do not issue F4 populations or authorize B1 operations.

## Publication and accounting

The retained successful capture sources are published as
tw_native_spi_numeric_input_capture338.py,
tw_native_spi_numeric_classification_capture338.py and
tw_native_spi_rommaps_retained_capture338.py under tools/reconstruction.
Input and RomMaps copies are byte-exact. The classification publication changes
only its final CRLF to LF; the sealed original remains intact. Its publication
receipt records both hashes and this one-byte transformation. The initial copy
attempt stopped at that CR before changing the goal or ledger; its draft is
retained. All three retain archive placement semantics and are not rerun. Heavy
evidence, failed drafts and correction appendices remain outside desktop God2.

Two existing C++ files gain22 supplemental locations and6 physical scalar
fields per selected source record. No packet/format/parser/phase/handler/full
route count increases. Frontier v23 and all prior parsed ledger fields remain
unchanged; whole-game denominator/completion stay null. Next actual classifier
initialization lifetime/RomMaps loader/current-bank396, eligibleowned population,
F4 issuer/B1 rules/full ordered reply/storage/recovery and Application hosting.
FullTW/CN/fourWS/common tables/shared64/coin99999999999/qualifiedstack99/native
levels/fonts/text conversion/frozen requirements persist. PHASE1 static
source/hash/PE/Capstone/report only; no build/compiler/tests/runtime/native/VM/
codec/gameDBSQL/migrate/activate/deploy.
