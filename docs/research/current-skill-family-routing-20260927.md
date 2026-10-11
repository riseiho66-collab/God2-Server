# Current skill family routing, 2026-09-27

## Native contract

Pinned image SHA256149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763,
builder00518E50: kinds0/1/3 all enter0051913D mask-target branch. Kind2
depends on definition WORD+3E==0xFF5; other kind2 records use a distinct
direct-target format and remain outside this source-independent parser.

The source cbspec2.bin SHA2567676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51
contains448 definitions. All361 kind0/1/3 records were supplied unchanged to
the original builder for two mode states and targets0/13/14/27. Native output
retains actual kind/id, target masks and continuation bytes, and passes the
current C++ parser. This is361/448=80.6% source-definition mask-format coverage,
not a playable-skill or recovered-formula percentage.

## Integration

RecoveredSkillCommand parses those three families. RecoveredBattleService uses
uint16 keys(kind<<8)|id rather than ID alone. Only explicitly configured kinds0/1
attack policies route into existing Lua calculations. An unconfigured family
or a same-ID different-kind request is rejected without resource/battle mutation.
Kind3 retains the existing separate diagnostic revival route; parsing does not
turn general kind3 commands into damage, healing or learned permission.

CUSTOM-0012 diagnostic_battle_skill_kind defaults0. Kind1 requires a named
private-skill-family-* loopback database plus seed/settlement and forbids revival.
The seed34, selectable87 and83/03 result all use the same identity. The initial
implementation still fixed87 to8001; inspection found and repaired that mismatch
before promotion. Test power150%, MP8 and synthetic ownership are not original
spell rules. No production configuration, client EXE or player saves changed.

## Verification

- Build server-native-results, recovered-battle-service, recovered-world-records
  and recovered-skill-command succeeded.
- Three core CTest contracts passed3/3.
- Original-builder/guard-page/sequence/transport tests passed14/14 in33.782s.
- Config gates passed1/1, including invalid types/ranges, wrong database,
  missing seed/settlement and revival conflicts.
- Bootstrap and Session checks passed3/3, including actual TCP skill sequences
  and authoritative battle service routing. These are synthetic peers, not UI casts.
- Hidden current-client fixture private-skill-family-20260927-04 accepted the
  actual seed34 and selectable87 through normal receive processing. Original
  selector held current bank0,count1,entry count1,state8101 and a pointer to
  the full unchanged kind1/id1 definition (SHA256
  7855ad60402fc194c44d281e890a024941d89ece2aef037e343590d6a9584408).
  Input desktop stayed Default; no screenshots, memory writes or external
  connections. Source database, formal config and both client files were unchanged.
- Failed01 used wrong indoor map-kind anchor; source movement code proves saved
  scene15 uses kind2. Failed02/03 applied battle offsets to the separate world
  allocation. Correct04 derives battle from the role-published complete skill body
  minusA924D7C, then independently verifies battle+14==role and battle+20==UI.
  No empty bank from those incorrect addresses is interpreted as gameplay state.

Client learned/selectable acceptance is1/1 tested fixture. Window-input command
acceptance is now1/1 tested kind1/id1 route; terminal/world receipt acceptance
remains pending after the repair below. No formula-recovery claim follows.

Next acceptance: native window-input selection, target, command35 emission,
MP/damage result and natural battle/world return on our isolated server. Until
that complete path is qualified, this candidate is not promoted to production.

## Initial receipt and actual selection

The real client first sends35/0B after the entry grant. Original005191EE..
0051921B clears the role command flagA9E9C38. The prior empty server reply left
all three command flags zero and action modeFFFFFFFF, despite the valid skill
bank. CUSTOM-0012 now reissues native86/5 role permission only after the exact
initial control receipt in the existing private kind1 fixture. The callback is
validated before publication; malformed reply rollback, successful retry and
replay refusal are covered by recovered_battle_service. Default policies remain
empty; this is not evidence of original-server timing or a production grant.

Hidden input04 confirms flags0/1/0, action mode1 and enabled role panel. Native
window keyboard S did not change mode in cast02: the native key-edge poll is
not proved equivalent to queued key messages. Cast04 instead resolves the
actual role control12 hit bounds and opens mode3. Selector+2E24 independently
matches the battle GUI owner; WORD[DWORD(selector+2E30)] identifies skill widget4,
not the assumed widget3. Cast05 uses its enabled control0 and actor14 projection
from battle+A940604+14*8 to select and target through ordinary window inputs.
The original client emits35 kind1/id1, enemy mask0001, and the server replies173
bytes. Natural animation completion emits0B with the retained target mask and
releases the terminal battle. No memory writes, injected calls, screenshots or
input-desktop changes occur; the owner receipt preserves all pinned source files.

Cast05 subsequently emits context04/00/00/00 after a committed win. The earlier
town-result assumption expected byte2=1 and rejected it. This receipt is now
admitted only for the named kind1 fixture with a same-session committed victory;
byte2 remains uninterpreted. It neither awards again nor mutates resources.
The terminal fixture uses existing CUSTOM-0012 fee8 and lethal power1000%,
not the general probe150% and not an original skill formula. Full MP/storage/
natural world return recheck is still required after this context repair.
