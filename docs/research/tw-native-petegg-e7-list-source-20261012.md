# Round331: E7 raw status and the actual list initialization source

RecoveredPetEggNotice preserves the native S2C E7 logical2/body1 record and
exposes only raw8 and the actual low7 discriminator. Its high bit is retained
because child4D9990 uses it for statuses37/38/39. The format is independently
qualified; no server result, owned selection, B1 acknowledgement, handler or
emission is established. Independent S2C formats rise11->12; unclassified
nondefault WORLD rows fall115->114. New complete bidirectional routes remain0.

## Actual receiver and local branch inputs

Pinned mapped149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763
and originalPE5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde
agree on all15 captured cuts:3220codeB/55dataB. WORLD cell46B970->4691FD;
INC EBX advances to body, ECX=Main+A7F2F6C (primary UI U), CALL4D6340.
Length cell4016C0->401216 MOV EAX2/RET. Complete4D6340..4D68BE is1406B.
It reads body0, not a48B list payload. Full4D6BD0 is a called UI helper,
not the E7 receiver.

Special local branch S uses WORD U3C==0E and BYTE U8561D+24*I==whole1,
or U3C==0F and (BYTE U85621+24*I &7F)==1; I is live signed BYTE U8.
These are row+11h/full20+0Dh and row+15h/full20+11h respectively. Ordinary
branch O handles other state. Neither predicate checks slot bounds/ownership.
All status numbers below are decimal; offsets and masks are hex.

Both O/S delegate30..40 to complete4D9990..4D9BAF with original body pointer.
Its actual11-entry table4D9BB0 is preserved.37/38/39 highbit0 calls4D94A0
with hex(0C,48/49/4A), highbit1 uses hex(0B,4B/4C/4D). This bit is not
a qualified success flag.30 writes U95DB2=1 then4D98B0/4D94D0, U95DAC=0,
4D9830(-1), clock->U95DA8,4D9E80.31/32 additionally clock->U95DA8 before
4D94D0, then reread clock after4D9830. These children remain opaque.

O/S20..27 set U70=1, call4D7DB0(status), conditionally4D53F0, finally
WORD U3C=0F. O's open guard is signed U232E66>=0; S also requires widget
bit10. O/S19/28 with signed handle>=0 and widgetbit10 call4D7DB0 then4D53F0
and return; otherwise reach fallback. Fallback9 sets U44bit29,8 clears it,
then calls4D6BD0 with current bit29. Fallback stores WORD UA6D6=10/11/14/16/17
for those statuses, elseFFFF; S29 instead calls4D6290(global5B7D9C) without
directly storing that WORD. Then4D7DB0 rereads current body low7. Its full
4D7DB0..4D7DD1 writes WORD U52 only with signed handle>=0 and signed WORD
argument0..57. O fallback applies<=28, S<=29; earlier returns take priority.

O93 and S92/93 use declared clock and local U78/U7C/U80/U84 plus UI children;
S92 sets U84=1,93 clears it. S65..89 calls4D6290 on cached pointer table5B7CC0;
S90/91 calls4DAF50/4DBC60. S94 calls4D6BD0(currentbit29), rereads bit29 for
4D5E40, then known4DC830 close. Other higher statuses return except delegated
30..40. Exact order is retained in sealed full TSV/REPORT; opaque children
may alter subsequent reads/state. The codec predicts no final UI state.

## Genuine same-U zero writer, with nonzero population still open

Known329 Main465323->4817C0 supplies U. Its481BB3 invokes481C20 using ESI=U;
complete481C20..481F65 preserves ESI and481E97 invokes complete4DC610..4DC708.
After UI construction and storing AX to U232EA2,4DC6AE zeroes EAX,
4DC6B8 forms EDI=U+0A,4DC6BB sets ECX=0Ch (decimal12),4DC6C7 REP STOSD clears48B
(24WORDs U0A..U39). This excludes U3A/U3C. Later5057D0 children remain opaque:
direct zeroing does not prove later action-time contents.

Bounded raw candidates4D4B80..4DC900 found explicit+0A clear address4DC6B8
and known330 list read4DC744. This covers only selected explicit base/displacement
forms, not every aligned path, alias or computed address. Nonzero filling
remains OPEN. E7 receiver and necessary child contain no direct list copy;
their descendants' effects are not globally excluded. Prior330 compact label
index is still not automatically the original WORD/control index.

The actual initialization chain is preserved as source, not an invented
current-state supplier. E7 cannot populate24WORDs from one BYTE or identify
an owned full20 instance. Common authoritative selection still requires genuine
current owned data; no provider/lease is synthesized from local UI fields.
Next work: actual nonzero list writer,504620 event/control lineage, ordered
owner/state/rules/storage and original issuer; B1/E5/E6/E7 causal pairing is
independent evidence still needed.

## Custody, history and scope

External package:
C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petegg-e7-list-input-source-331.
Its original REPORT/seal remains immutable. REPORT-CORRECTION-01 and its
separate seal clarify hex0C/0B arguments and31/32 clock ordering. All native
cuts already had correct bytes. The capture's initially mistyped doc reference
was corrected and references finished separately, without recapturing native.
The checked-in capture is that corrected reproducible static script; exclusive
output creation prevents overwriting earlier evidence. No full image copy.

Frontier v20 retains every v19 native row and historical named increment;
only E7 gains INDEPENDENT_FORMAT_ONLY. Counts are scoped source accounting,
not whole-game completion: TW C2S156/S2C252/world74(partial50/control11/gap13);
CN C2S156/S2C phase280/length253. Phase bindings, parser/opcode/gameplay counts
are unchanged. Whole denominator/TW/whole completion remain null; goal active.
TW/CN/web/shared tables/common64/coin99999999999/stack99/native levels and
frozen saves/fonts/text/features remain required. PHASE1 static source/hash/
PE/Capstone/report only; no builds/tests/runtime/native/VM/codec/gameDB/SQL/
migrate/activate/deploy occurred.
