# Same-session battle → supply → battle candidate

The original client had previously completed two battles in one process under
the `CUSTOM-0014` level/EXP fixture, and separately completed battle → original
slot use under `CUSTOM-0016`. Neither run established the combined path.

This change adds a separate, default-off configuration for exactly two
movement-triggered, durable three-round battles with world resources and slot
use. It excludes the level snapshot, progress/EXP award and checkpoint-resume
experiments. It remains loopback-only with `diagnostic-accounts.db`; no normal
configuration or persistent playtest database was changed.

The first isolated socket run found a real admission conflict: after the first
post-battle context notice, `Application.cpp` erased `diagnostic_vitals_sent`
before the second fight began. The supply callback required that marker and
therefore rejected a valid `C2S 26` while HP28/MP56 and an owned 3107 slot were
already saved. The marker now remains through the world supply window and is
cleared only when the second `S2C 82` entry is emitted, before its own Timer36
bootstrap. The pending-battle and completed-context checks remain in place.

`test_same_session_battle_supply_server.py` uses an isolated own-server TCP
session and exact captured client command shapes. It verifies:

- first entry uses saved HP52/MP80, then three skill rounds settle to HP28/MP56;
- post-battle native-shape `26` consumes one owned 3107, saves HP28/MP80 and
  clears slot0;
- a new committed movement triggers the second entry in the **same socket**;
- second Timer36 reads HP28/MP80, then three rounds settle to HP4/MP56;
- two distinct reservations and settlements persist, a third movement does not
  start another battle, and SQLite `quick_check` returns `ok`.

The test uses a synthetic socket peer carrying recorded original-client packet
shapes. It proves server route/state/persistence integration, **not** acceptance
by an executing original client. Existing native runs cover each constituent
path separately; the original-client combined run still needs its own isolated
probe. The existing `apex.py` observer explicitly assumes either one battle
with supply or two battles with level/EXP, so a combined run must rearm its
second-battle observation after the supply result before drawing a native
acceptance conclusion. No general encounter balance or production item-use
policy is inferred from this test.

Verification on Release `build-supply-chain`: `god2-server`, `god2-tests`,
`recovered-battle-service`, `diagnostic-supply` build; config, battle-service,
supply-service and same-session socket checks pass. The persistent port 2592
server executable was not replaced or restarted.
