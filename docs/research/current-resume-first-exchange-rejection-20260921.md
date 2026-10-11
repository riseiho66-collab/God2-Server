# Fresh-client resume: first exchange accepted, receipt rejected

Run: `artifacts/runs/native-player-checkpoint-resume-20260921-01`.
Source: `native-player-pending-checkpoint-20260921-01/diagnostic-accounts.db`,
copied read-only into the isolated run. Own loopback server only.

The runner indentation error was repaired and its CLI loads successfully.
Fresh client entered the saved battle and issued one skill. Three native
resource updates were observed. Durable state advanced from active revision3
to active revision5: player HP88/MP42 became HP76/MP34, enemy HP96 became HP42.
Resource revision advanced from4 to5. Source state is unchanged. Neither
database has a settlement. All gameplay values remain CUSTOM-0012 fixtures.

The subsequent native control receipt is captured in packet-decode-0383.json:
`140035000b0000000001000000000000000000c9`. Checksum and client plaintext
comparison passed. Server log reports type_index6 rejected, then closes the
connection. Runner ends EVENT_BUDGET_END, not successful resume acceptance.

Current service selects the special three-round receipt using absolute battle
revision5/6. A fresh client's first local exchange is not the original client's
second local exchange, despite identical durable battle revision. Application
also carries absolute round count into bulk counters. Both need evidence-led
separation of connection-local protocol state from durable gameplay state.
Do not relax all receipt masks or reset the saved battle/RNG to make tests pass.

Next: qualify this exact receipt against the decoded control schema, introduce
explicit resume-local policy/counter handling with negative replay tests, then
run a new isolated client through the remaining exchange, terminal settlement
and world movement. Full resume, normal UI and production balance remain open.

Saved-evidence regression: InterruptedResumeEvidence in
tests/research/test_current_battle_resource_persistence.py. This regression
records a known failed run; passing it does not certify live resume success.
