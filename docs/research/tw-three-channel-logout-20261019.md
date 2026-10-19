# Taiwan native logout cleanup ordering (round497)

The owner requires three selectable independent channels with shared saved
progress. The current native switch evidence uses logout/relogin/reselection,
not an invented in-place target opcode. This round repairs the actual WORLD02
reason0/1/2 branch. CUSTOM-0159 applies; full switching is still incomplete.

Previously Session queued the existing03 immediately, then closed the socket,
then posted common cleanup/abandon/Application disconnect to GAME. A client
could receive03 before the old character claim and local sources retired.
The private terminal attempt now stops new read/feed/resume, drains prior FIFO
and game work, retires public readiness and runs one GAME cleanup. Application
on_disconnect, common cleanup and lifecycle abandon are exchanged once before
callbacks and all attempted, in that order. Full64 account/character and atomic
phase/battle are read on GAME before and after; drift or any throw makes clean
false. No additional bare NET read of GAME identity is introduced.

Only successful cleanup in the same live Session/listener terminal phase can
queue the original03 once. The actual Write is checked again before async_write.
A timeout, source stop, failed cleanup or late output cannot acquire a success
reply. The exact03 is the only permitted newly queued output after cleanup.
The original disconnect completion remains after final socket close AND complete
GAME cleanup, once, with callback destruction on GAME. Unrun/dropped work does
not manufacture a completion receipt. Ordinary close shares the once cleanup
custody. No target channel, admission permission or final-save token is minted.

During terminal cleanup public closing is true and recovered readiness is false,
while private stop remains distinct from the permitted final03. This preserves
the old harmless treatment of party cleanup broadcasts to the leaving Session:
plain self-send is dropped and Accepted self-send reports false once without a
new observation component or NET post. Earlier FIFO during Draining is retained.
Application cleanup now attempts each stage despite earlier exceptions, retains
the first failure and rethrows after all stages. Existing warning catches no
longer hide failure. A retired weak host reports failure without invoking dead
borrowed callbacks. Party departure is published once; a delivery failure cannot
move an already-moved candidate over the live party registry a second time.

Future source tests use separate real NET/GAME executors and an actual socket,
full64 authentication/selection/2A/tail, a physically blocked GAME cleanup and
12 reason/failure combinations. They check earlier FIFO, no early03 or completion,
App/common/abandon/complete once, late-input exclusion and self-broadcast refusal.
They are authored and registered through the existing session_state suite, not
built/run in PHASE1. Identity drift, stopped listeners, dropped posts, every PK
and every host shutdown/abort path still need concentrated verification.

Durability limits: movement/position operations already commit before replies;
App disconnect is not a final save. PK retirement intentionally retains durable
tickets/holds/checkpoints/outboxes/locks for recovery. The common lifecycle still
releases its claim even when another cleanup fails. Exact terminal claim hold,
failure quarantine/recovery, per-domain durable qualification and target admission
remain OPEN. This repair must not be advertised as a complete safe handoff or
successful six-direction switch/client acceptance. Default native Main remains
unselected. Other full Taiwan gameplay/formula/MySQL requirements stay active.

REA follow-up reuses the matching current EXE and existing analysis image with
all13 original section headers and bytes verified. Three opened/closed static
batches inspect16 selected codec addresses, including request410980 resolving
inside actual410960, plus two dossiers. No target or codec ran. Observed BYTE
checksum is the pre-encryption header/body sum plus0x3c per byte modulo256.
Encryption uses the key at this+2420, BYTE negative-key-sum bias at2556, a DWORD
enable flag at+8 and previous plaintext chaining; the current outbound compression
predicate4108F0 returns0, while receive410A10 checks byte1 bit7. Transport4124D0
uses the exact codec output with its SOCKET+64C. These facts do not prove all
negotiated peer profiles. Next trace410500/410570 through actual seed/flag inputs;
no silent promotion of the fixed zero-seed encoder or legacy149c asset lineage
to a general current aaf0 native profile is made. Raw evidence is retained under
three-channel-logout-round497/native-profile/findings-v1.json outside the project.
