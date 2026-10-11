# Retained Map Initialization Return

Pinned image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses are hexadecimal RVA; base400000.

`complete_owner_map_panel` continues the same original C3080 invocation from
C3348, without replacing its arguments, stack, instructions or game returns.
It uses the prior loaded world resource bank and native metadata bindings.
The bounded endpoint is the real caller at81F0D, not an injected return address.
Expected stack movement is SP-F0 to SP-34 after the original RET4.

The regression checks eleven calls to106C70: six controls on the primary panel
and five on the secondary panel. It also requires nine1073E0 calls, the original
104E30 secondary-panel constructor,105230, and the C3A50 hide path through
C35E4. These counts cover this retained diagnostic state only, not every panel
visibility branch. The earlier coordinate/source, sprite and label tests execute
and are asserted before continuing on the same VM.

All owner and mouse object changes are reconstructed from native writes.
Character bytes, the separate battle renderer, the full native map catalog and
owner canaries must remain unchanged. The original1112C0 entry count must remain
one. Repeating the continuation or entering from another stack boundary fails.

The first run reached the original205A0 display-region setter and stopped on
its write at205C2 to DISPLAY+8. Its byte index is bounded by the actual comparison
against1E; it writes four DWORDs at DISPLAY+index*10+8 through+14. The write guard
now permits only DISPLAY+8..+1F8 (exclusive upper bound), and the regression
reconstructs the full display snapshot from observed writes as well. Other display
fields remain protected. This extends a known object boundary, not native behavior.

This is offline native instruction execution with previously documented bounded
OS/resource adapters and explicit diagnostic input. It does not prove visible
rendering or live battle acceptance. There is no runtime packet emission,
production database update or change to C++/Lua gameplay rules.

## Remaining Caller

Verification: registered CTest passed1/1 in258.04 seconds, including two test
methods and the prior sprite/label assertions executed on the retained VM.
The expected eleven control calls, nine hide/disable calls, secondary-panel
constructor and original C35E4 RET4 were reached. Final EIP=481F0D and
ESP=SP-34. Full owner/mouse/display write accounting, unchanged map records,
separate battle renderer and owner canaries passed. No live process was run.

At81F0D, owner81C20 still calls B0D20 with character+90, then83A70,B3EC0,AD550,
and reads character+1C before993B0. These sources and calls cannot be inferred
from the map return. Full81C20/1112C0 return, live client E2E, server combat,
native monster attributes and formulas remain incomplete.

Follow-up: [retained toolbar prefix](current-battle-owner-toolbar-20260920.md)
now validates the actual B0D20/B12B0/7E800 path through the pending E72D0 call.
It does not yet complete B0D20 or the outer owner initializer.

```text
ctest --test-dir build -C Release -R '^current_battle_owner_map_completion$' --output-on-failure
```
