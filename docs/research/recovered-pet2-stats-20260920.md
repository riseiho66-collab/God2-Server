# Recovered FB pet2 stats contract

`src/protocol/RecoveredPet2Stats.h` provides a C++20 read-only, owning parser
for the original73-byte opcode-first FB logical record. It follows the current
original receiver and the label evidence in current-pet2-stat-labels-20260920.

Structural acceptance requires exact length/opcode, slot42..44 and key range
6D61..7F57(hex). It does NOT guarantee that an actual metadata row exists.
The original receiver separately resolves59A60; callers must retain that
metadata-existence and instance-ownership boundary. No absent row is invented.

Named accessors expose13 unsigned WORDs: four combat display values, four
attributes and five elements. Body offsets and original label positions are
documented in the label audit. No base/buffed value, combat formula or wild
conversion meaning is inferred. All72 body bytes are retained and accessible
read-only, including currently unclassified bytes.

No default Record construction or field mutation is exposed. Encoding only
roundtrips a previously parsed record. Both runtime emission and mutation
flags are false. No dispatcher handler, database data, gameplay or Lua formula
was enabled. A client displaying values sent by our server would not establish
those values as official original monster values.

## Verification

The standalone C++ fixture compiles with C++20 and warnings-as-errors via the
existing instance-codec test compiler helper (now accepting an optional source
path). It overwrites its input buffer after parsing to verify owned storage.

Two Python tests pass:

-15 source/slot/value cases run the original FB receiver, record selector and
 all original numeric consumer slices, comparing C++ results against the13
 label-bound controls. Values include unsigned high-bit/maximum boundaries;
 these are synthetic diagnostics, not recovered gameplay values.
-890 structural/opaque cases cover lengths0..74, all256 slot byte values,
 six metadata-key boundaries, each bit in body bytes3..71, and wrong opcode.
 Accepted inputs roundtrip exactly and expose the correct13 WORDs.

```powershell
python -B -m unittest tests.research.test_current_pet2_stats_codec -v
```

Initial fixture compile failed under /WX because std::fill used an int literal
for byte storage. This was corrected to uint8_t{0}; compiler diagnostic decoding
now uses replacement for unrepresentable host characters instead of hiding the
compiler failure with a Python decoder exception.

Capture-result research was reviewed: its known success path forwards a result
byte. No wild-to-pet ability copy/conversion has been established. This parser
does not close that gap. Original wild attack/defense recovered remains0.

## Capture pipeline integration

`tools/strike_lab/recovered_packet_pipeline.py` now identifies a standalone
76-byte S2C frame containing a73-byte FB logical record. Frame length/checksum
validation precedes structural parsing. Exact direction/length/opcode, slot
and key range are required before the13 unsigned named values are exposed.
This does not split concatenated logical records or compressed frames.

`record_packet` carries the decoded fields into its existing private packet
JSON and adds the identification `PET2_STATS_RECORD_CANDIDATE` to the existing
protocol-core.csv row. It does not put raw plaintext, keys or login fields in
general logs. The required native context is WORLD, but capture state names
are not yet bound to that dispatcher: state consistency remains unknown.
Metadata resolution, ownership, wild-value verification and database promotion
all remain explicitly false. This is identification, not a gameplay handler.

The C++ differential suite also compares the Python fields against C++ and
native consumers across its15 original-instruction cases, and checks matching
accept/reject results across890 structural cases. Pipeline tests additionally
cover wrong direction, invalid slots/keys, corrupt checksum, and actual private
JSON/CSV serialization using synthetic bytes. Eight tests pass via:

```powershell
python -B -m unittest tests.research.test_recovered_packet_pipeline tests.research.test_current_pet2_stats_codec -v
```

No new live FB packet or official monster values were captured in this step.
