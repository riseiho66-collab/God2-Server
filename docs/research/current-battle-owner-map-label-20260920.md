# Battle Owner Map Label Continuation

Follow-up: `current-battle-owner-map-completion-20260920.md` executes the remaining
map controls and returns from the retained C3080 invocation to its real81F0D
caller. This does not yet complete the outer81C20/1112C0 initialization.

Current mapped-image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
Addresses are hexadecimal RVA with image base400000.

## Coordinate Producer

The original world receiver slice68636..68653 reads the DWORD at its ESP+44
(world body offset28 decimal in the existing receiver layout). It writes:

- character+08 DWORD = (input >> 2) & 7FFF;
- character+0C DWORD = input >>17.

The following world/character flag writes at68653/68659 are outside this slice.
The helper does not qualify character+10, infer valid maps, or claim whole-packet
acceptance. The two low bits do not affect these two coordinate outputs.

`prepare_character_map_coordinates` executes those original instructions in the
same character VM on the existing private writer stack. It restores its input
scratch, retains the pending main CPU context, and qualifies only eight character
bytes for subsequent reads. Changed instruction bytes, invalid DWORD input,
wrong pending boundary and repeated preparation are rejected.

The lightweight regression crosses five values per coordinate (0,1,127,16384,
32767) with all four low-bit patterns:100 combinations. It compares whole
character snapshots, exact native write addresses/widths/values and retained
EIP/ESP, not only a host-side decoder result.

## Retained Consumer

After the prior real map resource and control stage, execution resumes atC3331.
The client reads WORDs character+0C/+08, passes them toC3B60, and uses the
original1077C0 text-update chain. The integration fixture uses explicit diagnostic
coordinates60,40; these are not captured original spawn coordinates.

The bounded continuation stops atC3348 after the call, retaining ESP=SP-F0.
The regression requires the real C3B60,1077C0,1E500,26700 andC3C14 return path.
It checks owner write accounting, unchanged separate battle renderer, unchanged
native map catalog, retained character bytes and a single original1112C0 entry.
It does not prove every map-kind branch or final rendered label pixels.

## Limits And Commands

Registered CTest passed2/2 in259.03 seconds: coordinate suite1.75s and retained
label suite257.26s, each containing two test methods. The latter also executes
and asserts the preceding sprite/resource and catalog-preservation regressions
on the same VM before the new continuation. Selected original source row21078
has kind1 (area2,scene0); kind3's layered-label branch is not covered here.

Remaining code builds further map controls afterC3395. Full C3080/81C20 and
1112C0 completion, live original-client battle, server combat policy, native
wild-monster attributes and combat formulas are still unverified. Production
C++/Lua architecture and database data are unchanged.

```text
ctest --test-dir build -C Release -R '^current_battle_(map_coordinates|owner_map_label)$' --output-on-failure
```
