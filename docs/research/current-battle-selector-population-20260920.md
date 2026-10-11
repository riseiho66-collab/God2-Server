# Original selector population and return

## Scope

`NativeBattleBootstrap.continue_selector_population()` resumes the same VM and
retained native stack at11BC95, after the separately qualified selector-window
continuation. It requires ESP=SP-54 and is one-shot. No arguments, registers,
handles or character/catalog contents are rebuilt between these segments.
Normal1112C0 and selector11BB80 each have one entry. This is segmented execution,
not a claim of one uninterrupted emulator call or live rendering.

## Executed path

- Original11BF40 populates the one explicit S2C30 character label, clears the
  remaining five rows and formats pagination. Return11C045 is observed.
- The11BF80 CRT `%s` call uses the original row's name at character root+16B.
  All16 source bytes must belong to the original writer footprint. This extra
  guard is necessary because a CRT host adapter reads memory outside Unicorn's
  memory-read hook. The output and CRT return length are compared; the original
  list consumer call11BF94 returns to11BF99. `Probe100` is a synthetic fixture,
  not an observed account/monster name.
- Original11C050 executes and returns through11C1C9. The selection cache is
  initially empty because original initialization cleared it. The separate
  source row still has a nonzero S2C34 learned pointer into the original-loaded
 448-definition catalog. Empty menu cache does NOT establish empty ownership.
- The native label sprite setup runs, followed by11BD70 and actual third-window
  constructor11B290. Returns11B568,11BDC4 and reset11C4F0..11C515 are observed.
- Three54-byte banks at selector+2D14/+2D68/+2DBC are compared exactly: DWORD+4C
  is1, all other bytes zero. The initial test incorrectly expected+50; inspecting
  the original11BD8F displacement corrected the test, not the client or VM data.
- Actual11BB80 `ret24h` at11BD65 returns to caller1116A9 with ESP=SP-1C.
  Entire character state, complete catalog and selector neighbors remain intact.

Additional original-call deltas: one104EA0 panel, five106550 controls,
two1057D0 controls, one106C70 control, one10C350 list, five10C540 entries,
twenty10CAA0 operations (fifteen skill-cache entries plus five third-list entries),
and one each10D1D0/10D540/10D310. Third-list mouse/renderer bindings and the
native destination pointer to battle+AB3B1D8 are checked.

## Remaining frontier

Stop before1116A9 executes. Next are the28 control creations at1116D7..111777
and subsequent character/UI dependencies81C20,AD880 and112130. These are not
certified by reaching the selector return. Full1112C0 return, actual pixels,
combat commands/results, authoritative damage and live gameplay remain open.
No C++/Lua runtime, production database, current-client file or network changes.

## Reproduction

```powershell
cmake -S . -B build
ctest --test-dir build -C Release -R '^current_battle_selector_population$' --output-on-failure
```

The suite checks the earlier bootstrap and window contracts on the retained VM
before continuing. It imports their modules, not their TestCase classes, to
avoid unintentional duplicate collection of the expensive resource preload.

Final registered suite:5/5 focused tests passed, CTest1/1 in114.52 seconds
(114.55 seconds total). The initial run reached the same original return but
failed the incorrect+50 expectation; no client/VM patch was used to make it pass.
