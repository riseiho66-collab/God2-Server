# Current world role-resource chain

## Scope

`current_world_role_resources.py` connects original HeroDoll lookups, the world
cache wrapper, real ROM loading, complete 61270 resource selection and the
normal 2A appearance-consumer slice. No game lookup/cache/loader/setter result
is substituted. It remains an offline original-code oracle, not live-world
rendering or original-client end-to-end acceptance.

Source image SHA256:
149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763.
RVAs are relative to base 400000. Both retained corpora were searched first for
63DE0, 52680, RoleDoll and 4B70; no corresponding native wrapper implementation
was found in their source subsets. Existing Classic world-frame evidence is
used below, not reinterpreted as a current runtime capture.

## Native initialization inputs

AppearanceResources executes the current HeroDoll tokenizer/row loader for all
918 rows and the Drv row loader for all 92 rows. Its native-produced records
and hash-container memory are copied into this VM. As in that earlier oracle,
hash-container allocation/insertion is reconstructed; original hash/comparison
lookup executes. These are explicit isolated resource-bank inputs, not a
claim that the entire application initialization has executed.

All 120 current DrvDoll rows also execute original 51BE0 and 6382E..63947 here.
The original row writes include WORD fields, FPU scaling, filename copying,
cache FFFF initialization and count increments. Tests compare every row with
source data. Only the calloc-like destination allocation and header-derived
column/count environment are supplied by the fixture.

DrvDoll CSVZ SHA256:
502df5822b376ac57c4bf8460bf6d646a3cb6d706b1be36396e73bf69ced1042.
Decoded SHA256:
de9510e0c5b1171e164b407c931b41e7fc3c5a7b5ffa3aba9193a51063f2dd9f.
First row 26, count 120. Row zero has a genuinely empty filename. Drv row zero
also has an empty filename. Native 63640/63AD0 consequently return FFFF for
the tested unmounted/unaccessorized inputs; those results are not stubs.

## Cache and path chain

63DE0 executes 526C0/52460. On a cache miss and next-slot WORD below 512, it
executes 526F0, original path helper 12F550, 29820 -> 1EC0 -> 2A1D0, then
52680's cache WORD write at 526A7 and the counter increment at 63EC7.
Successful ACTINDEX zero remains a success, not a false failure.

The isolated bank starts empty, with a 4 MiB native ROM-pool capacity and an
explicit RGB555 surface-format input. Tests cover:

- Genuine first loads and unchanged image/action data on cached reuse.
- Independent world cache entries for different HeroDoll keys sharing a file.
- No cache publication/counter advance when a qualified file is missing;
  restoring it allows retry through the original path.
- Slot 511 succeeds and advances to 512. A miss at 512 returns FFFF before
  file opening, while an already-loaded record still returns its real slot.
- HeroDoll memory writes are allowed only for the two-byte cache field at
  original 526A7; other fields and counter canaries are unchanged.

This differs from the preview filename cache, which deduplicates identical
filenames. Numeric handles need not agree between independently initialized
preview and world banks. Resource identity, not handle-number equality, is the
valid comparison. See current-preview-role-resources-20260919.md.

## Complete resource selection and 2A consumer

Original 61270 executes to its real return, including all four HeroDoll
components, both 63780 action queries where applicable, and 63640/63AD0.
No jump skips the mount/accessory tail. The returned six WORDs are checked
with input and output canaries.

Original 68315..68558 then runs this complete resource path and real FF450 and
FFA20 setters. All 98 zero-selector preview blocks (two binary values and
7x7 variants) resolve to actual loaded resources. The native override flag
sets all four variants to 7 without loading new resources. This slice starts
after scene setup and stops before later actor/scalar/world initialization.

The retained production-candidate body is separately tested:

`d900800005101b020000000001800160016031006000310cc203000046001a0000000000`

SHA256 79e98fef8d5e97c16eb60b52ba806cf965509f46e230b6010ff9671bea8e8aa7.
It has Drv selector 27, not zero. Original code requests:

| Native selection | Actual file |
| --- | --- |
| r2b600 | Data2/Rom/RoleDoll/r02b600.romz |
| r2f102 | Data2/Rom/RoleDoll/r02f102.romz |
| r2h900 | Data2/Rom/RoleDoll/r01w800.romz |
| r2w800 | Data2/Rom/RoleDoll/r02w800.romz |
| Drv ordinal 27 | Data2/Rom/Drv/drv5477.ROMZ |

The table names the last file as .ROM; original 29820 opens its real compressed
.ROMZ representation. The fixture does not invent a plain file. All raw and
decoded hashes are pinned in the helper; original decompression is compared
byte-for-byte before native ROM parsing. Existing RoleDoll tests separately
validate the original shared image/action parsing paths against source chunks.

For all 49 supported profile-variant pairs, the existing C++ world-entry test
executable emits the real encoder's wire bytes. The current original decoder
and checksum path recover their body before it enters the native appearance
chain. Local IDs rotate across 1,217,16383. Source bits, projected variants,
four component handles, the real mount handle, empty accessory handle, cache
reuse and unchanged input guards are checked. This strengthens the existing
two variant-field projections; it does not qualify any additional profile
field or make the retained mount the selected character's owned mount.

## Platform adapters and limits

Inherited bounded CRT read-only streams/allocation and guarded FS:[0] model are
unchanged. New adapters cover decimal sscanf, the exact HeroDoll CString
format, bounded sprintf path formats, and GetCurrentDirectoryA. The latter
uses an explicit virtual root, never host filesystem state; its IAT target
76601060 matches captured KERNEL32 base 765D0000 plus current SysWOW64 export
RVA 31060. Original 12F550 still builds and caches paths. Native temporary-file
cleanup receives no matches and cannot search/delete host files.

Code and lookup-container pages are non-writable; private new banks are
non-executable. Inherited execution/time/allocation limits remain active.
Exact stop hooks guard sliced consumer boundaries. This is not a general
malformed-ROM security assessment or proof that original code validates all
arbitrary selectors. Public fixture entry points admit only proven subsets.

## Remaining acceptance

No process/UI/socket is involved. The actual retained 2A resource dependency
is now tested, but whole scene-to-actor construction, camera, animation,
composition, device drawing and live world initialization still need evidence.
The historical resource descriptors remain a candidate, not complete owned
character appearance, equipment or mount state. No production payload, Lua
rule, stat, coordinate or persistence behavior was changed by this oracle.

Run: `python -B tests/research/test_current_world_role_resources.py -v`.
The C++ fixture must be freshly built with `cmake --build build --config Release`.

Final integration: fresh Release build passed; 32 core CTest suites passed
(excluding the five pre-existing artifact/gate/environment research aggregates).
Combined world-wrapper 8, preview-wrapper 7 and direct-ROM 7 tests passed in
79.661 seconds. The 12 existing world-entry/appearance regressions also passed,
including retained-source hash/checksum validation. These are 34 distinct Python
tests, not 34 gameplay acceptance scenarios. The single preview subagent was
closed after delivery. No production runtime or gameplay policy was changed.

## Follow-up: Native common actor tail

`current-world-actor-20260919.md` now qualifies the pre-scene scalar phase and
continuous post-scene tail through `68851`, with native Cat/ProgramMsg loading,
localization, Petdrv offsets and actor/UI clearing. Its scene phase remains
explicitly unjoined. The older bounded `consume_world_appearance` API and its
coverage remain unchanged; this follow-up does not claim full world rendering.
