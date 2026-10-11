# Battle background recovery after window switching (2026-09-30)

User-reported defect: changing windows during battle leaves a black field while actors/UI continue drawing. Scope: isolated own-server test client; do not change accepted skill visuals.

## Build-matched native cause

`004327A0(renderer, viewport)` renders the background once, copies CDX surface A0 into A4, then calls map cleanup00443D60. Native caller004657BE is the battle entry. Every battle draw00432810 copies A4 into A0 before drawing actors/UI. A4 is a rendered cache with no filename.

Focus recovery0040E3B0 WM_SETFOCUS ->00432D70 ->0053DD40 recreates the registered DirectDraw surfaces. It tries0053A400 to reload each filename, which cannot restore A4's rendered contents. Standard00538B60 loss recovery has the same missing filename issue. This explains intact actors/UI over an empty backdrop.

## Repair

`tools/skills/native_clone/battle_background.cpp` snapshots only A4 pixels after original004327A0. Before00432810, it restores the snapshot only for a screen-rebuild generation, changed COM surface pointer, or DDERR_SURFACELOST. Hook0053DD40 marks generation even if allocator reuses the COM address. Uses native IDirectDrawSurface7 (IID native00573F7C), DDSURFACEDESC2, IsLost24/Lock25/Restore27/Unlock32; preserves row pitch, padding, dimensions and RGB masks. Locks/unlocks are balanced, transient failures retry, and new battle/owner/layout mismatch discards old state. No midbattle map reinitialization or ACT replay. Normal frames do not copy pixels.

Hooks are signature-pinned to native-master-01-stable.bin:4327A0/432810 each ret4,53DD40 ret16. Native original8 and custom126 visual/particle code unchanged.

## Verification and limits

- Actual implementation fake-COM regression: same-address rebuild, replaced surface, negative pitch, padding, lost surface, failed Restore/Lock retry, unrelated device, dimension mismatch and failed new capture passed.
-24 hook/API signatures and27 existing hook regressions passed; Release DLL build passed; frozen chat gate passed.
- Deployed private client DLL SHA2568D1EC1C4D31AF24FE3FF99F8BC452C714F73B327933049D677D891EA61D4A823, client PID20764. Previous accepted DLL preserved at artifacts/custom-skills/shunying/accepted-visual-B368775B.dll.
- Skill text fix installed at the same restart; see shunying-name-prompt-20260930.md.
- Live focus-switch/name check PENDING: Windows helper twice returned `failed to activate captured window`; refreshed target still did not activate. No automated interaction with the unrelated foreground game. Asked user to return to the test window. No live pass claimed.
- This restores a successfully captured battle background. It cannot reconstruct an already missing initial map; it does not alter map assets, fight state or skill timing.

## Subsequent current-client acceptance

After relaunch with normal window style, PID7304/window1116508 entered actual battle. The UI observation showed intact terrain and the F1 prompt `瞬影三煞斬 MP:20` above the battle menu. The client log recorded backdrop capture and restore after surface recovery. Attempted automated switch was interleaved with user input/minimization, so it is not claimed as a fully independent automated switching pass. The owner then explicitly reported **「目前都正常」**, accepting the current fixes. Native-name UI observation and user-operated acceptance supersede the pending status above. No further visual/skill changes made.
