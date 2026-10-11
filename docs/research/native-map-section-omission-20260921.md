# Native Map Section Omission

Status: reproduced startup fault; shared-workcopy startup mitigation accepted
in one four-client run. Not a general client repair. Own-server tests only.

The new `native-mapsection-20260921-01-again0` captures original section
dispatch at4565AB, before the exact-name comparison with Map_City_Coordniate.
Pinned original code has one direct call to459A80 at4565EC; a mismatching name
branches to4565F6 instead. No client branches, table pointers or exception
results were changed by this observation.

The failed process records39 section-dispatch observations for the same owner,
including NPCList, ShopRate and SystemMessage but not Map_City_Coordniate.
FIRST_BIND then records count0/table0; the original459ED2 read dereferences
null table+1A0. There are no observed map loader entry/return events. This is
stronger than merely observing a crash or a missing completion marker.

The current work-copy Data2/Patch/Comm/gamedata.csvZ decodes through the existing
decoder to2783008 bytes and contains Map_City_Coordniate,144 at zero-based
line21018. Thus the source section exists on disk; this does NOT prove the
failed process read that particular file successfully or decoded it completely.
Loader I/O, file selection, sharing and decompression remain open causal paths.
Shared-file contention is a hypothesis, not a confirmed diagnosis.

The first captured trace labels stack+0C as `parser`; its values are scalar
loader arguments, not established pointers. Subsequent instrumentation uses
the neutral `loader_argument` field. Original evidence is left unchanged.

`test_failed_reconnect_dispatched_other_sections_but_not_catalog` retains the
negative trace, the common owner and chronological empty bind. This diagnostic
does not suppress the fault, substitute144 rows or certify stability. The next
target is upstream data-file selection/open/decode before section dispatch.

## Upstream File Evidence And Mitigation

`native-mapfile-20260921-02-again0` and `again1` each retain immutable
`map-file-*.json` records. Both open the workcopy Patch/comm/gamedata.csv,
report a nonzero open result and successful loader return, and reopen the
same absolute `client/tmp/tmp.2` decompression path. One process subsequently
records the empty catalog and original 459ED2 fault. Same-path reuse is proven;
the exact overwrite timing and bytes causing omission are not yet proven.

Original 4029B0 formats `tmp.%d` using process-local counter 5B00B8 modulo100.
4028E0 derives the temp root from GetCurrentDirectoryA (IAT570428). Separate
processes sharing this workcopy therefore do not have unique temp names.

The shared runner now waits for each owned client's FIRST_BIND observation
with count144 and a nonzero table before starting the next client. Readiness
is bounded and bound to the run ID and a live descendant PID. It does not
patch client instructions, invent table entries or suppress exceptions.

`native-mapfile-serial-20260921-01` remains a failed acceptance run: additional
file tracing swallowed the pre-existing TABLE_FILE_LOADER event, so the string
table assertion failed even though movement completed. Breakpoint7 now retains
its original event path. No old report was relabeled.

`native-mapfile-serial-20260921-02` subsequently passed with four distinct
client processes, all publishing count144 and a nonzero table. Fresh peers
2308/3648 restored the first skill checkpoint, finished the remaining skills,
persisted settlement and completed post-battle native movement. Captured
regressions compare the recovery database against the uninterrupted run across
six tables, validate packet checksums and Fight lifecycle, and preserve the
hotbar input. The gameplay remains isolated CUSTOM test combat, not native
damage recovery or production balance approval. Full-world acceptance is false.
