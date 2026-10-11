# Original selector constructor and window continuation

Subsequent qualified segment: see
`current-battle-selector-population-20260920.md` for retained11BC95 execution
through original11BB80 return at1116A9. The boundary and results below describe
this earlier segment, not the latest overall battle frontier.

The same bootstrap VM now executes original selector constructor `11B7B0`
before S2C30/34 preparation and normal `1112C0`. The constructor calls original
`10C310` for the three embedded list controls at +2E38/+3080/+32C8. It writes
the actual vtable at +0, zeros `[+4,+2D10)`, clears renderer +2E10 and initializes
handle +2E1C to FFFF. The exact351C-byte result is compared, including retained
unknown bytes and the lists' original zero/FFFF fields. In particular, page
DWORD +8 comes from this original constructor, not a fabricated zero live-in.
Native SEH registration/restoration also executes through the existing adapter.

The baseline normal initializer still starts exactly once at1112C0 and pauses
at11BC2A. `continue_selector_windows()` requires that exact EIP/ESP and resumes
the retained stack without rebuilding arguments, copying another VM, calling
the initializer again, or replacing any game-function result. This is a second
execution segment, not falsely described as a single uninterrupted emulator call.

Executed continuation:

1. Original character count -> signed division-by-six page calculation, stores
   +C. The explicit one-row fixture produces page count1.
2. Original11A9D0 returns through11AC91 after building the first selector window.
3. Original11ADB0 returns through11B09E after building the second selector window.
4. Original IDIV at11BC8A normalizes the constructor-produced page index0.
5. Original11C4B0 resets all16 selection banks and returns through11C4EA.
6. Stop at11BC95, BEFORE the11BF40/11C050 label/icon population and later third
   selector window. Full11BB80/1112C0 return and live rendering remain unproved.

Both window constructors use already loaded original resources, rectangle
adapters, actual control creation, list construction, and formatting functions.
There are no fabricated handles or intercepted game callees. Additional native
calls are two104EA0 panels, twenty-one106550 controls, four1057D0 controls,
two106C70 controls, and two list initializations with twenty-one list entries.

The retained character, its nonzero S2C34 learned pointer, complete448-definition
catalog, selector neighbors, stack depth and source read-footprint guard survive.
Fixture names/packets are synthetic and establish no captured character or
monster repertoire. The native menu initially clears its own selection tables;
ownership/source population and displayed selection state must not be conflated.

The initial combined run passed21 baseline assertions/tests plus4 window tests
in216.777s. Test imports were subsequently narrowed so the registered window
suite does not redundantly collect the baseline class; its setup still checks
the old entry/source/catalog contracts before continuing. The final registered
run additionally checks native call deltas and both list manager bindings.
Final registered window suite passes4/4 in111.00s. The selected CTest batch
(window continuation plus drop-rule suite) passes2/2 in116.92s. All processes
finished normally; the latter suite is not live monster-drop acceptance.

```powershell
ctest --test-dir build -C Release -R '^current_battle_selector_windows$' --output-on-failure
```

No C++/Lua runtime, production database, client file, real UI, server connection
or gameplay rule was changed. This is progress on original initialization, not
playable battle completion. Next is original11BF40/11C050 and subsequent11BD70
with the same nonzero learned source retained, not a shortcut via empty ownership.
