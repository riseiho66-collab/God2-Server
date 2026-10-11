# CN complete07 selection appearance input source

Round `20261007-cn-selection-appearance-source`, PHASE1 static/source only.
No build, C++ reader, client, API, resource loader, server, codec, test, database
or deployment executed. Native levels and common saves remain unchanged.

## Recovered consumer and ordering

Pinned CN PE SHA256
`582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8`.
Eleven metadata-bounded code envelopes, 3865 bytes, are saved as primary
bytes, Capstone assembly and navigation decompilation. These are bounded
consumer evidence, not whole-image, indirect, exception or deferred closure.

`00443080` obtains the raw07 payload from UI+1792D0, visits active36-byte
rows, and starts each four-part array at payload+1A (row+24). At0044315C
and004431BF it pushes literal ActType0 into004237F0. Selection previews have
no native07 driver, auxiliary or alternate-key operand. In particular,
substituting a fabricated driver0 world2A/6F record is unjustified.

Body/face/head/weapon use actual HeroDoll keys through the already recovered
lookup. Before the face lookup0044318E resolves the head;00443197 reads that
row's byte2A face base. Base0/1 is used directly; otherwise004431B1 adds the
face component's low5 variant using BYTE arithmetic. Actual table keys,
last-row lookup semantics, missing-row qualification and exact native
filenames are reused from CnAppearanceResources. Four resource inputs retain
their own rows even when filenames coincide. This round does not execute
those C++ readers or supply absent assets.

After loading/binding four parts,00443313 uses each selected component's
high3 palette operand;00443325 assigns7 when unselected.004433AB then calls
00443640 with the current ordinal and a nonzero display operand. A palette
operand is not a palette-bank allocation or an accepted rendered image.

## Local mutation differs from authoritative07

The nonzero branch of00443640 writes back into the client-held raw row:

* 00443694 replaces body category row24 low4 with its low bit, preserving
  the high nibble. First preview lookup precedes this write; a later preview
  lookup can therefore see a different body category.
* 004436DF normalizes row20..21: preserve low3 and high8; clear bits3..4;
  apply modulo7 to bits5..7. It does **not** keep only bit0 of this WORD.
* 0044371B preserves row22..23 low4 and applies modulo10 separately to its
  two six-bit fields (bits4..9 and10..15).
* 004438BE compares level row16 withFF;004438C8 writes1 for this existing
  display sentinel. This is not a progression cap change or permission to
  rewrite stored levels. Other level bytes remain unchanged.

CnCharacterSummary::Character now returns an owned original36-byte row and
an independently owned local panel projection. It never edits its complete
received75-byte07, opaque18, flags, inactive rows, names, native slot,
reincarnation, routing bytes, common profile or server publication.

CnSelectionAppearanceRows retains the complete immutable summary, ordinal,
selected actual resource profile and an explicit ReceivedBeforePanel or
AfterPanel stage. CnAppearanceResources::select_native_summary chooses the
stage's corresponding row and the real four HeroDoll rows. Caller must supply
the actual UI stage; no default guesses it. Missing active row is absent;
missing table/path remains an error, rather than default-row success.

CnSelectionAppearanceRomInputs connects these four selected paths to the
existing original preferred-resource/ROM-metadata reader. Its source has no
Drv ROM, auxiliary ROM or synthetic2A/6F actor. It is source integration only;
the reader was not run. The selection cache has a separate owner:004430EA
resets HeroDoll cached WORD+1E toFFFF via owner+d8c, then004432A5 calls00446740
using UI1792CC's case-insensitive filename bank and004197E0. The existing
in-world NPC two-cache/current-bank source cannot stand in for that owner.
Native handle assignment, bank lifetime/order, ACT and actual rendering
remain unresolved here. No cache is reset or manufactured by this source.

## Scope and remaining routes

This adds one static selection-resource input chain and one local panel
projection, using already counted07 and existing lookup/readers. It does not
recover server07 flags/opaque18/inactive data/visibility/row-slot issuance,
map common40-byte TW profiles into CN36, configure an actual native issuer,
or connect a new complete request/authority/storage/reply/client route.
New opcode, native phase bindings, completed owner chains and completed
bidirectional gameplay routes:0. Full denominator and percent remain unknown.

Account/world/authentication, actual repository/Admission/Application/TW
candidate behavior, original resources, frozen fonts/chat/IME/text conversion
and saved characters were not modified. The whole goal remains active.
Next recover actual native07 provider dependencies and selection-bank ownership;
complete1D/0A/world1F/02/2A/6F providers, formal PC/web hosting and gameplay
remain open. The received wire and display projection must remain distinct
when the peer ports this native selection consumer.
