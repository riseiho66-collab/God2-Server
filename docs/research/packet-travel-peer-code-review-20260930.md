# Packet travel/peer source review — 2026-09-30

## Reviewed source

The review covers the new C2S20/S2C6F peer secondary-text route, the owned
16055 teleport gem C2S25/26→S2C6D→C2S99→S2C3B/41/61 route, SQLite revision/
ownership checks, migration40, source-qualified position commit and scene
receipt. It does not claim an exhaustive audit of unrelated quest/combat code.

The previous isolated candidate is
`b94ea3dda7bd8c5de8023f2dbaa8be7391d1f72f0b3feac66d2cabca84effc2c`.
Manifest comparison found that this review changes only
`src/core/Application.cpp` among its archived source set. The new build is
`21fa46551913eb4d6f55f3b6baa3a5b14a5f18d6e1dddca398840c1d2576118e`.
The formal loopback server still runs the earlier
`1c2a6d090c6759eca2786adba690ab7da60e6a821ff87c73005e7df01ad72fc5`.

## Finding and repair

**Medium: an expired observer could veto the owner's C2S20 save.**
`prepare_role_text` creates 6F deliveries from visibility membership. A socket
may expire before serialized disconnect cleanup removes its member. The earlier
precommit callback threw `DatabaseError` when the recipient weak reference was
missing or expired, rolling back the owner's otherwise valid text update.

The callback now erases deliveries with no live recipient. It still prepares
every surviving recipient's exact language bytes inside the save transaction;
the visibility cache commits and those prepared bytes are sent after SQLite
COMMIT. Ownership, canonical text, language conversion and frozen native chat
dispatch are unchanged. The branch performs no state mutation for the expired
recipient and lets normal disconnect remove its membership.

## Checks

- New candidate compiles in Release.
- `peer_role_text`, `packet_commit_review`, `config`, and
  `owned_role_text_server` CTest: **4/4 pass**.
- `verify_frozen_chat_20260927`: pass; baseline unchanged.
- Final 21fa current-client hidden 936-source dual-language run: **accepted**.
  It verifies CJK projection, clear/edit, movement before and after update,
  observer and owner fresh login, source-file preservation, unchanged Default
  desktop, and closure of all owned processes. Receipt:
  `artifacts/playtests/private-peer-role-text-review-20260930-02/run-result.json`,
  SHA256 `f0416352dc48ce7fd9809c74410f47029f03cfd578007412b39027e896d8ed72`.
- Earlier current-client b94 receipts cover active peer updates in both
  language directions; the post-review candidate's private-client result is
  recorded separately below. No prior receipt is relabeled as testing 21fa.

## Remaining limits

The test suite does not inject an observer transport expiry at the exact
precommit callback boundary. The repaired missing/expired weak-reference branch
is verified by source inspection and the unchanged active-recipient path by
current-client regression. A failed postcommit socket send may be recovered by
relogin from durable state. Teleport gem is still one CUSTOM-0057 destination,
with no formal item acquisition path; full original rules and all packet
families remain open.

The isolated client run, if accepted, proves original-client behavior under its
specified hidden fixture. Its automation reads native UI state and does not
make a pixel-rendering claim. The formal server/config/save were not changed
by this review.

The first 21fa hidden run (`private-peer-role-text-review-20260930-01`) did
not pass: its observer's cold Locale Emulator launch failed to bind within the
15-second harness deadline after the preceding CJK, edit and movement checks.
Its source, desktop and process cleanup guards passed; no server text rejection
was observed. A second run with longer bounded cold-start/login waits passed
in full. The failed run is retained as a failed automation receipt.
