# Artifact Integrity Gate

This offline tool implements the first reconstruction gate: immutable, content-addressed
client snapshots with provenance and repeatable static PE inspection. It never runs,
patches or unpacks an executable. The Python research tooling is separate from the
C++ server and its game database.

Requires Python 3.10+ and `python -m pip install -r tools/research/requirements.txt`.
The parser is pinned pefile 2024.8.26. PE interpretation follows the
[Microsoft PE specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).

From the server project root:

```powershell
python tools/research/artifact_vault.py ingest ..\God2\God2.exe
python tools/research/artifact_vault.py verify
python tools/research/artifact_vault.py list
python tools/research/artifact_vault.py compare <sha256-a> <sha256-b>
python tools/research/artifact_vault.py candidate <sha256> --va 0x0054A3E8
python -m unittest discover -s tests/research -p "test_*.py"
```

Global `--root PATH` selects a separate vault for experiments. Global
`--output NEW_FILE.json` writes a report without replacing existing files.
CTest registers the Python tests when the pinned parser is available at configure time.

## Storage

Each `artifacts/clients/<sha256>/` contains `metadata.json`, `hashes.json`,
`original/`, `unpacked/`, `memory_images/`, and `imports/`. Only acquired files
are populated. Empty directories do not represent successful analysis.
The recorded binary is named `client.exe` in its kind-specific directory.
Metadata includes SHA256, MD5, size, PE timestamp, architecture, base, entry,
sections and their raw hashes, imports, parser warnings, statuses and parent ID.
MD5 is informational; identity and integrity decisions use SHA256.

`artifacts/research.db` indexes artifact IDs, manifest hashes, source locations,
parent relationships and static evidence records. It is the initial artifact/evidence
index, not the complete future protocol knowledge graph. `CONFIRMED_STATIC` here
labels confidence in recorded PE declarations only; no runtime semantics are inferred.
Game persistence remains in the separate game database.

Reimporting identical bytes reuses the artifact and records another source location.
Source observations retain their first ingestion time. A captured `original` is an
acquired on-disk image, not a claim of an official unmodified release. In particular,
God2-run is not assigned a parent merely because its filename resembles God2.exe.

For a future separately acquired dump:

```powershell
python tools/research/artifact_vault.py ingest C:\Research\God2_unpacked.exe --kind unpacked --parent <original-sha256>
```

This records `UNVERIFIED_CANDIDATE`, never verified unpack/OEP status. The parent
must exist and pass verification. An identical child/parent hash or conflicting
provenance is rejected. A crash between directory publication and index insertion
can leave an unindexed complete artifact; rerunning the same ingest repairs that
index entry after validating its manifests. Existing mismatched index entries are
never silently replaced. Use one writer per vault.

`verify` rereads binaries, metadata, manifests and the existing research index, and
repeats PE inspection. It does not repair corrupt artifacts. Verify the whole vault
to validate every artifact; a child check also walks and verifies its ancestors,
rejecting cycles and chains deeper than 64. This is accidental-corruption detection, not
signed proof against an attacker able to replace both files and the index. Keep an
independent backup. Binary dumps, clients and runtime databases are ignored by Git;
back up the entire vault, not only tracked metadata.

## Evidence Boundaries

Comparison reports PE-header, section and import differences only. They explicitly
report function matching as not performed and protocol differences as unknown.
Sparse imports, parser warnings, ordinal imports and ASPack-like section names are
preserved without claiming a repaired IAT. In the raw parser metadata, `symbols.name`
may be a pefile lookup-table hint when `ordinal` is non-null. Such hints are not
verified symbol resolutions. Comparisons always use the on-disk ordinal in that case.

OEP candidate inspection only maps preferred VA to RVA and checks section/raw backing.
An address in virtual section memory may have no bytes on disk. A backed address is
also not proof of an OEP. Runtime module base, unpack transition, dump provenance,
repaired imports and controlled execution must be established next.

The remaining reconstruction gates are documented in
[RECONSTRUCTION_STATUS.md](../../docs/RECONSTRUCTION_STATUS.md).
# Runtime Intake Extension

See [RUNTIME_CAPTURE.md](RUNTIME_CAPTURE.md) for APEX capture preparation,
sealing, ingestion, consistency assessment and generated reports. It preserves
the existing artifact-vault schema and never promotes imported claims to VERIFIED.

[GATE_REVIEW.md](GATE_REVIEW.md) documents the separate ZENITH local human-review
workflow, immutable certificates, revocation and audit. No trusted reviewer policy
is supplied by default, and intake alone still cannot promote evidence.
