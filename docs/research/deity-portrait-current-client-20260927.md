# Current deity portrait resource guard

## Original evidence

The prior mixed E3/FB hidden fixture emitted one nonfatal native diagnostic:
`action.cpp {img} line2289`. It occurred during world restoration before the
inventory opened. A same-candidate control without synthetic deity fixtures
(`private-pet-native-icons-20260927-01`) emitted none. This isolated the trace;
it did not justify removing real owned deities or changing pet artwork.

Unchanged native `004A9AC0` maps every deity portrait to bank5:

- signed integer key <=100: action = key-1;
- key >100: action = key-67.

FieldComm3 physical line10 assigns bank5 to `Data3/Flow/Pic_God.ROM`.
The current compressed ROM SHA256 is
`b24167375a7ad1de614bb4d41e55190d7a9e6538e9e0b6064f284c8f569f8b4e`;
decoded SHA256 is
`590693a6d7a5ad47c5addd3d36ea9352ea8ca22c658060d935c26dbe16ed1570`.
It contains42 ACT_DATA rows:34 named native deities and8 profession portraits.
Current gamedata GOD records have metadata keys2801..2834, matching row keys1..34.
These source names/IDs do not certify recruitment, initial stats or growth.

`004A9E33` updates god panel control25 through mapper `004A9AC0` then
`005068C0`. `004AE150` updates the deity HUD control0 only in mode1.
The original `0041E710` image selector returns0 when action >= bank.action_count
at+108C. Its caller `0041EABB` emits action.cpp/img line2289 on a zero image.
Thus synthetic key100 maps action99 outside42; a terminated name alone never
made this fixture visually valid. Custom named keys101..108 map actions34..41,
with actual ACT IDs1101..1108. No drawing patch is needed.

`tools/strike_lab/current_deity_portrait.py` executes the pinned original mapper
for keys0..127 and actual image selector for every nonnegative mapped action.
All42 source images are used (including the8 named profession aliases).
Relocated ROM chunks are read-only; output/stack guards remain enforced. This
qualifies the mapper/image selector, not ROM file-loader execution or blitting.
The complete receipt is `artifacts/research/deity-portrait-20260927/native-proof.json`.

## Server integration

`RecoveredDeityState::valid` now rejects unrenderable/unqualified identities
before owned persistence, selection and restore. Current native rows1..34
still require separately qualified template catalog entries; named rows101..108
still require a terminated name, matching status, qualified learned skill bank
indices, explicit ownership and provenance. Lossless raw codecs retain all
original bytes, including out-of-range keys for research/diagnostic use.

Only disposable fixtures were changed from100/101 to101/102. Historical accepted
evidence and live player data remain intact. Clone-based socket regressions
rewrite those fixture keys within the clone only. The C++ regression enumerates
all1..127 keys and checks missing catalog, bad owner, boundary skills, atomic
selection rollback and exact restoration. Seven same-candidate socket checks
exercise owned selection, both pet generations, movement, journal/clock and
restart preservation.

## Pet icon binding

Original `00481700` adds41h to preloaded metadata bank+116 and resolves icon ID
at+114 to its action index at+118. Preload FFFF is a binding sentinel, not proof
of absent artwork. Live read-only resource checks qualify COM24001:
bank83/action80/ACT28110; NCP28002: bank84/action9/ACT28210, including valid
sprite image pointers/resources through all five mixed transfers.

## Acceptance status

`private-deity-portrait-20260927-04` passed against candidate SHA256
`cbe14bdad5428258c3973c51f7782380a7c7127cab0d674b63bd78c65b6b2588`.
The bounded hidden fixture runs actual five bag drags before switching UI contexts;
VK_F11 reaches original004AB5AD ->004AD800 and enables the native deity HUD.
Earlier experiments proved its actual image but interrupted bag input by
switching contexts before the drags; they are failures, not acceptance.

The accepted run verifies12 occupied pet sprite resources and two actual
deity HUD entries with key101 -> bank5/action34/ACT1101. No native diagnostic
was emitted. Source saves, both client files and the input desktop were unchanged.
`artifacts/releases/deity-portrait-20260927-02` is formally INSTALLED; the
service listener was PID2684 on127.0.0.1:2592. Schema37, all existing tables,
their rows and revisions, production configuration and client binary were
preserved;4 accounts/3 characters,1165 NCP and2070 COM definitions remain.
No owned instance was granted and no player save migration was performed.
The staged clone must retain the town-diagnostic-accounts.db basename required
by the existing isolation gate; failed release01 did not alter the live service.

Full deity acquisition, templates, stats/growth and skills execution remain
OPEN. Pet growth and combat rules remain OPEN. This fixes a concrete native
resource boundary; it is not whole-game or all-black-screen qualification.

Later same-day follow-up: all34 native GOD definitions are now formally
imported, and hidden native keys1/2 restore/selection/HUD acceptance passes.
See `native-deity-metadata-current-client-20260927.md`. Templates are no longer
an open catalog item; acquisition, original stats/growth and skills remain open.
The new observer qualification also establishes actual widget input flag20h
and list order. F11 mode1 opens the GOD panel, mode0 closes it; no earlier
informal open/close interpretation should be used as input authority.
