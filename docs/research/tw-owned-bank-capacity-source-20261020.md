# CUSTOM-0163 explicit offline bank capacity source

The owner requested a real capacity producer for the existing CUSTOM-0160
whole-instance bank. This source adds an actual `god2-server` CLI caller,
not a login default, native unlock reconstruction or an unhosted factory.
PHASE1 remains source/static only; none of these commands were executed.

The two exclusive modes are:

```
god2-server --export-owned-bank-capacity --account-id N --character-id N --output new-manifest.json --config config/server.json
god2-server --provision-owned-bank-capacity --manifest approved-manifest.json --config config/server.json
```

The first mode requires existing complete0092 inventory and native equipment.
It writes a new local English-field JSON file containing the entire original
material and actual database file identity. `approved` is false and
`new_bank_indices` is empty. There is no inferred list of authorized slots.
The operator must review the draft, enter an explicit ASCII `permit_id`, an
`operator_note`, explicitly list every missing bank index, and set approved.
The second mode freezes and strictly parses that bounded file before DB/SQL;
duplicate keys, floats, extra fields, bad owner/indices or unapproved input fail.
Neither mode continues into migrations, logger, Lua or networking. Output is
exclusive-create, never overwrites an existing file, and keeps partial output
on IO failure for diagnosis. Unicode Windows command paths use actual wide
arguments; JSON configuration paths retain UTF-8/native conversion.

`SqliteDatabase` owns a shared actual-file lifetime for ordinary initialize and
the existing skill importer. The new capacity-only initializer requires an
existing regular file and obtains exclusive ownership before opening SQLite.
Windows uses an actual file handle with READ/WRITE sharing and no DELETE
sharing, plus LockFileEx on one byte at0x7ffffffe00000000. This is beyond SQLite
data/lock bytes and does not allocate file capacity. Distinct handles in the
same process and hardlink spellings still conflict on the same underlying file.
POSIX uses flock on separate open file descriptions rather than process-wide
fcntl. A shared current host therefore blocks offline provisioning even when
its SQL is idle and it retains only cached Sessions. The lock outlives all
repositories and the SQLite connection. Explicit private :memory: normal
fixtures keep their prior behavior; capacity refuses memory/URI/create modes.
The dedicated SQLite connection additionally selects locking_mode=EXCLUSIVE
and obtains/releases an exclusive transaction before constructing its minimal
readers/writers. No schema or migrations run. This additional SQLite lock
refuses active foreign SQLite users; arbitrary external legacy programs which
never adopted the lifetime protocol are not certified offline Session owners.
On POSIX an external unlink/rename cannot be prevented by flock; the retained
and named inode are checked before/after open and at the operation boundary.
Such external filesystem manipulation is outside the supported owner protocol.

Provision compares `expected_material` to a deterministic complete JSON
serialization of both existing full snapshots. The serialization includes
every root/profile/codepage/privilege value, full inventory cells and absence,
all IDs, definitions, quantities, revisions, acquisition metadata, full alias
records, source metadata, native client/kind/record, full DA/unknown cache
bytes, actor handle and saved pose/revision. The original source SHA remains
unchanged; both snapshot revisions advance and bounded provenance records
append `;CUSTOM-0163:capacity:<permit_id>`. The note and exact authorization
list remain in the reviewed manifest; this is a local operator record, not a
new database table or a native item acquisition.

Only explicitly requested previously absent `bank` cells can be added, with
null instance and zero stored quantity/revision. Existing populated or empty
cells cannot be overwritten. Every other cell and every instance/alias/native
record is retained. The resulting existing bank namespace must contain exactly
indices0..299 because CUSTOM-0160 currently projects six backing pages of50.
The operator must enumerate all missing indices; a partial grant does not
silently mark the full bank ready. This300 backing requirement does not enable
native ordinary mutations on pages3..5 or special local0/1. Current mutation
eligibility remains pages0..2/local2..49 and qualified bag0..29.

The actual same-connection `SqliteOwnedEquipmentTransaction` performs full
expected-before CAS, common account/root/position/no-battle checks, issuer
checks and readback of both staged complete populations. A pure retained
offline-owner fence runs after all SQL observers immediately before the sole
COMMIT. No first inventory/equipment creation, schema repair, missing item,
acquisition, split, merge or legacy mirrored bank store is supplied. A real
COMMIT remains reported as committed if later qualification fails; there is no
automatic replay. Reusing the old manifest fails full-before equality.

REA was immediately used for the remaining native capacity question. Current
original EXE pin aaf0fae66e89c4547244304ecd8f4c2755746ffa6c9b9dfe68a0ff3fd2b4cd48
is tied by the retained section-byte provenance to the existing seeded analysis
image a306ab3d6d1707982cb4e9d7311b7112b39f59ab12e538bc01bb32dde76e88ba.
This round's evidence ev_f4d20eaa60f3f31e7578e54c26697a54fa36909479f705448e2883d71a539aef
follows S48 receive/update0x471e50 into0x471310 and0x471610. 471310 only checks
the existing pane visible flag0x20;471610 indexes page*50+local, refreshes the
item/count display and asserts local<50. Existing471e50 asserts page<6 on
received records. These client cache/pane operations do not recover a server
paid/unlocked capacity rule. Full raw output and close receipt are archived
under sos-room-formation-capacity-pass4/capacity. No original bytes were changed,
no resources decoded and no game executed. Native unlock/economy/split/merge,
reserved-slot eligibility and actual client/server acceptance remain OPEN.

`tests/test_owned_bank_capacity.cpp` is unexecuted focused regression source:
explicit approval and full opaque bytes, bad manifest/replay/overflow/absence,
same-process and child-process ownership, no file growth, actual dedicated
Database-to-joint-CAS fixture and normal-host lifetime exclusion. Synthetic
fixtures are explicitly separate from native unlock/feather population proof.

This is a source implementation with post-edit review. Initial owned item and
native equipment populations still require their genuine original producer;
this operator deliberately cannot fabricate them. No game DB was opened and
no capacity was installed during this round.
