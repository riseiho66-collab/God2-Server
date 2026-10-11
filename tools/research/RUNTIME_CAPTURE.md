# Runtime Evidence Intake

This is an offline intake adapter, not a live debugger plugin or automatic
unpacker. No x32dbg/WinDbg hooks are installed. The external producer must export
observations into `god2-normalized-v1` and preserve its native trace. Never infer
an observation from a packed file and label it runtime evidence.

## One External Deliverable

Provide one controlled x86 capture directory bound to original artifact
`fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1`.
For Gate 02 it needs the manifest, normalized event timeline, native debugger
trace, full mapped image and distinct unpacked PE candidate. Include the actual
module base, process/thread IDs, capture time and tool version. To assess later
gates in the same bundle, also include OEP continuation, resolved IAT observations,
the actual imported module binaries, a separate repaired PE, disassembly probes
and observed Winsock callers. Missing later evidence keeps those gates blocked;
it does not prevent accepting a valid partial capture.

Run only a working copy with its client resources in an offline or loopback-only
environment. Do not execute or modify the archived original. The preparation
template deliberately contains null fields and no invented events.

## Workflow

### Approved Environment First

The [environment matrix](../../docs/RUNTIME_ENVIRONMENT_MATRIX.md) records the
actual Microsoft x86 CDB probe and the later GOD2 policy denial. Do not retry the
denied client in this environment. Owner/admin must supply an isolated lab whose
policy permits the exact original executable; the agent does not change policies.

`tool_inventory.py --output NEW_JSON` inventories known installations without
executing candidates. `runtime_environment_probe.py --sandbox-id ID --debugger
APPROVED_CDB_PATH --output-directory HOST_OUTPUT` probes an already mapped
sandbox. Required guest mappings are read-only `C:\Input\Client`,
`C:\Input\Debugger` (Microsoft x86 CDB directory), `C:\Input\Scripts` (this
directory) and writable `C:\Output`. Do not expose other writable host folders.

The probe uses the Sandbox CLI and ordinary native commands, never adjusts
execution policy, and never launches GOD2. It checks networking, mappings,
identities, CDB startup and debugging of the system's benign x86 cmd.exe.
`RUNTIME_ENVIRONMENT_READY` is operational only, scoped to that sandbox. It
does not predict whether the client is allowed and is not a gate certificate.

After a fresh successful probe, `capture_cdb.py` rechecks identities and isolation
before launch. `--copy-resources` copies resources inside the sandbox. A timeout
or policy denial is failure, not evidence. Preserve outputs, stop the sandbox,
and use the existing seal/validate/ingest workflow only for actual observations.
The startup command file has not executed against GOD2 because policy denied
process creation; its memory/entry commands remain unvalidated for this client.

### Evidence Intake

Commands run from the server project root; default vault is `artifacts`.

```powershell
python tools/research/runtime_evidence.py prepare fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1 artifacts/capture_requests/new-session
# External capture: complete the worksheet and place observations in that directory.
python tools/research/runtime_evidence.py seal artifacts/capture_requests/new-session artifacts/capture_inbox/sealed-session
python tools/research/runtime_evidence.py validate artifacts/capture_inbox/sealed-session
python tools/research/runtime_evidence.py ingest artifacts/capture_inbox/sealed-session
python tools/research/runtime_evidence.py assess CAPTURE_SHA256
python tools/research/runtime_evidence.py status fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1
```

`seal` recalculates attachment sizes/hashes into a NEW directory, validates it,
and leaves the worksheet untouched. Worksheet entries still need syntactically
valid size/hash placeholders (0 and 64 zeroes are allowed before sealing).
The capture ID is SHA256 of exact manifest bytes; attachment hashes are inside
the manifest. Changing content requires a new session ID. `ingest` archives the
bundle, indexes events/function candidates and automatically emits a new report
snapshot. API callers use `report(artifact_id, new_destination)` explicitly.

Existing captures are reverified, not overwritten or silently repaired. An
interrupted first ingest can leave an unindexed immutable directory; retrying
the identical bundle indexes it. SQLite commits and filesystem publication are
not a distributed transaction. These are tamper-detection checks, not a digital
signature or proof that the producer truthfully described execution.

## Manifest Contract

`runtime_contract.py` is the executable source of truth. Version 2 rejects
unknown/missing fields, duplicate JSON keys, NaN, invalid types and path escapes.

| Object | Required fields |
| --- | --- |
| Root | schema_version=2, artifact_id, session_id, provenance, process, scope, files |
| provenance | tool (x32dbg/windbg/other), tool_version, operator, captured_at (ISO with timezone), environment_id, isolation (offline/loopback-only), source_kind (runtime/synthetic), adapter=god2-normalized-v1 |
| process | pid, architecture=x86, module_base (actual VA), image_size (original SizeOfImage) |
| scope | purpose=network-reconstruction, ranges (half-open main-image VA intervals) |
| files[] | path (relative POSIX), role, size (bytes), sha256 (lowercase hex) |

Roles: `events`, `raw_trace`, `memory_image`, `unpacked_pe`, `repaired_pe`,
`module_pe`, `disassembly`. Exactly one events attachment is required. A
memory_image is a flat mapped image of exactly SizeOfImage bytes, not a raw PE
or minidump container. Preserve separate dumps for different observation times.
No unreadable memory may be silently replaced with zeroes and claimed observed.

Version 2 also requires provenance `working_copy_sha256` matching the artifact,
measured from the executable actually launched, and `handling` with boolean
`sensitive`, `redacted`, `restricted` fields. Sensitive evidence must be marked
restricted; these flags do not configure filesystem ACLs. Legacy version 1 is
still readable but cannot become consistency-ready; neither can redacted images.

The sandbox helper and `capture-startup.txt` support a bounded initial snapshot,
not an unpack proof. See the [actual setup attempt](../../docs/CAPTURE_ATTEMPT_20260918.md).

Limits: 64 files, 128 MiB per file, 256 MiB total, 32 MiB event file,
20,000 events, 16,384 bytes per JSONL line, 4,096 captured bytes per event.
Split longer captures into separate sessions; do not silently truncate evidence.
This version handles x86 main-image observations, not arbitrary process-wide traces.

## RuntimeEvent

Each JSONL row has exactly `id`, `seq`, `timestamp_ns`, `thread_id`, `pc`,
`state`, `type`, `details`. IDs are unique ASCII alphanumeric/underscore/hyphen;
seq starts at 0 and is contiguous; timestamps are nondecreasing nanoseconds from
one producer clock. `pc` is the client instruction/caller within declared scope,
not the external API address. State is an unreviewed observed label.
Addresses/RVAs/counts are JSON integers; bytes are contiguous hexadecimal.

| Type | Exact details fields |
| --- | --- |
| function_enter | bytes_hex (nonempty observed entry bytes) |
| function_exit | return_value (raw unsigned x86 register value) |
| call | target_va |
| memory_read | buffer_va, size, after_hex |
| memory_write | buffer_va, size, before_hex, after_hex |
| buffer_created | buffer_va, size |
| socket_send / socket_receive | buffer_va, size, after_hex, api, target_va, direction |
| unpack_transition | from_va, to_va, region_va, before_hex, after_hex, memory_file |
| oep_candidate | rva, bytes_hex, memory_file, unpacked_file, continued_event_ids |
| import_resolved | iat_rva, target_va, module_base, module_file, module_name, symbol, memory_file, repaired_file |
| analysis_probe | image_file, rva, bytes_hex, disassembly_file, decoder, instruction_count |
| counter_evidence | gate, related_event_ids, reason |

Socket directions are TX (send/WSASend) and RX (recv/WSARecv). Receive bytes must
come from successful completion, not pre-call capacity or an outstanding
overlapped request. A scatter/gather operation needs separate observed buffer
rows with producer context retained in the native trace. Version 1 does not
reconstruct asynchronous completion relationships or certify socket outcomes.
`symbol` is the exact export name or integer ordinal; ordinal hints are not proof.
Forwarded exports are blocked until explicit final-target support is implemented.

## Gate Checks And Limits

| Gate | Mechanical checks |
| --- | --- |
| 02 unpack | Changed bytes, transfer into changed region, mapped bytes, distinct candidate |
| 03 OEP | Runtime-base-relative PC, memory/raw executable bytes, PE entry, same-thread later execution and earlier unpack observation |
| 04 IAT | Mapped slot, actual module export/name/address, repaired import slot/name/ordinal |
| 04.5 quality | Raw section bounds/overlap, parser warnings, repaired entry bytes, all imports evidenced, attached disassembly probe |
| 05 network | Winsock export name AND address match; capture-local function identities |

Successful checks return `READY_FOR_REVIEW`, never `VERIFIED`. Disassembly
attachments are preserved, not independently decoded by this tool. Native trace
authenticity, module load provenance, stable OEP execution, full image quality and
API completion semantics still require independent review. The tool cannot
certify an unpacked image by trusting an imported JSON declaration. Synthetic
sources always block real gates. Counter-evidence blocks the affected gate and
its dependents; missing evidence is not a contradiction or proof of absence.

Function IDs are immutable `FUNC-<uuid>` candidates scoped to artifact + capture
+ RVA + observed byte hash. They remain HYPOTHESIS. They are not recovered
function boundaries, semantic matches across builds or verified network roots.

## Reports And Acceptance

The research SQLite extension owns `runtime_schema`, `runtime_captures`,
`runtime_events`, `runtime_functions`; artifact-vault schema/version stays intact.
Server runtime does not import these tools. Generated snapshots contain all six
APEX reports plus status.json and deliberately do not overwrite mock-protocol docs.
The [ZENITH review extension](GATE_REVIEW.md) adds explicit human approval,
promotion, certificate dependencies and revocation. Intake still never promotes
by itself. Global acceptance currently stays L1, Gate 02 BLOCKED: there is no real
capture or owner-installed review policy. New reports incorporate current certificate
audit results; old generated snapshots remain historical and are not overwritten.
No percentage is fabricated: verified packet/field counts are zero and totals unknown.
