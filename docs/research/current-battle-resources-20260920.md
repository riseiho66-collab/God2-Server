# Current Battle Resource Binding, 2026-09-20

## Result And Scope

The current client reads all ten FightComm3 records, preloads all ten original
ROMZ assets through its own decompressor/parser, and uses the resulting table
in the original initializer call island `11149B..1114AF`. The real calls
`1114AA -> 11FBF0 -> 11DA10` create 25 control-strip sprites through `1AFE0`
and run `1B560` for each. No game callee is stubbed or patched.

This is an offline native proof with explicit CRT/MFC/file/Win32 adapters and
an RGB555 fixture surface, not an operating graphics device, complete battle
initializer, official gameplay rule, or original-client E2E acceptance.
The normal `1112C0` initializer suite independently reaches `11149B`; combining
the stages into that single normal-entry execution is still open.

## Sources And Callers

Current mapped image SHA256:
`149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763`.
All addresses below are RVAs; base is `400000`.

`God2/Data2/Patch/FightComm3.csvZ`:

- Raw SHA256: `fd96359b66809968ad8454350417a9aad1a7e0e15cacbaa4788215ef22fb3578`.
- Decoded SHA256: `4fe7f229c7a7d95a76f51a8ee7a710763f75f0e3a83a96b79fbaa895cdfbac8c`.
- Header `FightCommon,1,5`; ten rows, indices 0..9.
- Record stride `108`: DWORD index/handle, then bounded filename storage.

Constructor `110A3A` selects reader `B+71268`; `110A4A -> 546E0` initializes it.
Native caller `110BB9..110BEC` resolves FightComm3 and calls `54720` with count
10. `54776` stores the allocated record pointer at reader+`121F0`, which is
exactly **B+`83458`**, the previously missing initializer source. Native CSV
parsing executes; the file adapter exposes read-only decoded text after its
contents are independently checked against original `1760/1EC0` decompression.

The bounded original name-registry constructor island `11F4EF..11F55C`
allocates the real `410`-byte registry and 252 filename buffers, storing its
pointer at manager+`14`. Other manager construction is not inferred.

Native preload loop `110DF2..110E72` calls `120650` for each resolved filename.
That function searches existing names or calls `29820`, then appends the name
and returns the runtime handle. `110E52` overwrites the CSV record's DWORD with
that return value. In this fresh registry the actual handles are 0..9; their
coincidence with CSV indices does **not** authorize substituting indices for
handles in another session. Cache-reuse checks execute `120650` again and
verify that existing names neither reload ROMs nor increment registry count.

## Original Assets

All raw and decoded SHA256 values are pinned in `current_battle_resources.py`.
Each decoded byte sequence is compared with the actual original decompressor
output immediately before `2A1D0` parses it. Missing files are not synthesized.

| Index | Literal CSV path | Decoded bytes | Initializer use |
| ---: | --- | ---: | --- |
| 0 | Data3/Fight/Gui/FightGUI2.rom | 263781 | `+0`, copied at `1114B5` after the current island |
| 1 | Data2/ItmImg/Ski01.rom | 303659 | No additional gameplay meaning inferred |
| 2 | Data2/ItmImg/Ski02.rom | 268361 | Same |
| 3 | Data2/ItmImg/Ski03.rom | 194033 | Same |
| 4 | Data2/ItmImg/Ski04.rom | 230095 | Same |
| 5 | Data2/Fight/Gui/Eft2_8301.rom | 8399606 | `+528`, later `1117B1` |
| 6 | Data3/Fight/Gui/StateIcon2.rom | 36483 | **`+630`, executed `1114A3` -> control strip** |
| 7 | Data2/Fight/Gui/rusebottom.rom | 331002 | `+738`, later `1114D5` |
| 8 | Data3/Fight/Gui/Eft2_8302.rom | 2262740 | `+840`, later `1114E8/111528` |
| 9 | Data3/Flow/motion.rom | 567998 | `+948`, later `1114C3` |

These are **client graphics resource handles**, not HP/MP, damage multipliers,
monster stats, or authority for any server combat formula. No database fields
were populated from these handles.

## Control Consumer

The existing original ROM bank uses the explicit `2000000` capacity also seen
at current constructor `110DDF/110DE4`. Native renderer constructor `1AA10`
receives that bank and a fixture RGB555 format, not a live graphics device.

The separate initializer island uses the actual preloaded record pointer and
calls `11FBF0` with record6's runtime handle. `11DA10` stores the handle at
strip+4, creates one sprite and 24 more sprites, storing all 25 sprite handles
at strip+6. The fresh renderer returns distinct handles 0..24. Its actual
resource lookup supplies the spacing source; no Python replacement calculates
or invents it. Strip+`3C` points to the native renderer. Poisoned unowned bytes
and surrounding guards are preserved. The island stops at `1114AF` before the
next initializer instructions, with the original stack restored.

## Reproduce

From the server root:

```powershell
python -B -m unittest discover -s tests/research -p test_current_battle_resources.py -v
ctest --test-dir build -C Release -R "^current_battle_resources$" --output-on-failure
```

Tests cover source parsing, all real decompression outputs and handles,
unchanged paths, cache reuse, actual control creation, original call witnesses,
unchanged native instructions, and fresh-stage lifecycle guards. CTest gives
the ROM-loading test a bounded 240-second timeout. There is no live connection,
host file mutation, runtime packet deployment, or gameplay-completion claim.

Independent review found and main corrected attempted/completed stage
bookkeeping: a failing native preload can no longer authorize control creation
or a retry on partial state. The bookkeeping regression does not emulate a
successful game callee; it injects a failure solely to check the Python guard.

A separate counterfactual preserves record6's handle but zeroes its ROM bank
action count at `bank + handle*1514 + 108C`. Original `1AE20` finds no bound
action and returns `FFFFFFFF`; the same initializer caller reaches `1B078`,
before its assertion call, rather than completing 25 sprites. This test stops
at the real failure boundary and restores the VM fixture afterward. It does
not patch any code, modify a host asset, or fake an assertion return.

Final verification: all **7 resource tests pass in65.671s**, via the registered
CTest target (65.92s total). The six selected adjacent suites passed earlier
in103.30s; after the two review fixes, the resource target was rerun in full.
The separate normal-entry initializer suite passes20/20. Neither percentage
nor test count measures gameplay completion.
