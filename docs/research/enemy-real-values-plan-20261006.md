# Enemy real-value capture task (owner authorized subagents)

The owner explicitly requests a private blackbox scenario with two temporary
characters in PK, or one temporary character fighting a temporary monster.
Temporary attributes/skills must be clearly CUSTOM_TEST_NOT_NATIVE. The purpose
is to locate the enemy data received from the server and its native memory
writes, so later legally received official monster data can be collected.
This targeted research is an explicit exception to deferred mainline feature
tests; it does not authorize deploying the untested current source or rewriting
formal saves/client binaries/frozen release baselines.

## Required field coverage

- Enemy identity, monster source ID versus display name/EnyName composite key,
  battle participant slot/side and encounter lifecycle.
- Four primary attributes, exact native meanings still to be established.
- Five-element values, exact native encoding and player/monster distinction.
- Both attack and both defense values, exact original names/units still to be
  established. Do not automatically assume generic physical/magic terminology.
  Owner clarification explicitly includes all four requested columns: physical
  attack, magic attack, physical defense and magic defense. Native owned-pet
  labels establish those names there, but do not establish an enemy-monster
  packet, offset or value. Each enemy column must retain its own source and
  direct-value / derived-estimate / unknown classification.
- Maximum/current HP and MP where actually delivered; never infer missing values
  from a cached/self/owned-companion record.
- Observed cast skill IDs and skill-bank namespace, separately from the entire
  carried skill repertoire. Repeated casts or a cache assembled from actions
  are not proof of a complete repertoire.

## Delegated work

`enemy_blackbox_experiment` locates a current isolated native server/client
bootstrap and carries out controlled field changes. It may minimally configure
an exclusive temporary client copy for a private port; it must preserve original
and installed client bytes, record copy/patch hashes and avoid claiming an
unchanged-client acceptance. New PID/HANDLE/receipt and isolated DB/config/port
are mandatory. Custom fixture-only protocols are not native evidence. If it
cannot actually establish two accounts/PK, it must name that unachieved part.

`enemy_native_fields` traces version-pinned S2C consumers, post-decode buffers,
enemy structures, field writes and source catalogs. The output must distinguish
server-sent values, native-derived display, owned-only structures and unknown
fields. The field search includes both attacks and both defenses.

`enemy_data_capture_plan` connects legally received packet/dump inputs to an
offline extractor with raw bytes/hash, session/encounter/participant lifecycle,
source classification and explicit unknown fields. It must distinguish encrypted
wire capture from decoded logical records, and actually observed official data
from a user declaration or temporary custom controls.

## Required proof before publishing a real monster value

A candidate field must be bound to a qualified native input/client version and
an exact enemy identity/lifetime, have a documented direction and byte layout,
and lead to an actual enemy structure write or native use. Independent custom
control changes may calibrate the readout but are not official monster values.
Unknown or omitted fields stay null; no unseen skill is classified absent.
Self/owned-pet four-attribute/element/attack-defense structures do not establish
an enemy-monster source join. Damage-based inverse estimates remain estimates
unless a qualified server formula and enough independent controls establish a
unique result; no official formula will be invented.

Capture methods must operate on the user's own legally accessible client inputs
or local isolated process. No official login or credential collection is
requested here, no official admin interface is accessed, and no protection
bypass is part of this task. An official connection is not performed merely to
populate a synthetic evidence table.

## Source phase separation

The full PET bank63/64/65 source connection was saved before this research:
`beast-bank-connections-20261006.md` and the current source continuation ledger.
It remains unbuilt, untested, not installed and not deployed. The main full-game
packet goal stays ACTIVE and incomplete. Research outcomes must be reconciled
into a separate report rather than changing any frozen/native acceptance baseline.

## First concrete deliveries

- Static native map and read-only collection entry points:
  `artifacts/research/enemy-native-fields-20261006/README.md` and
  `static-native-map.json`; generator `tools/reconstruction/enemy_native_fields_20261006.py`.
  recv/raw frame, post-decode/checksum and assembled pre-dispatch logical buffers
  are located from pinned instructions/current unpacked import. No official
  process has been attached. Further enemy-inspection/repertoire writers are
  still being traced in a separate frontier rather than claiming global absence.
- Original-consumer controlled blackbox:
  `artifacts/research/enemy-blackbox-20261006/consumer-experiment/identifiability-result.json`.
  Two custom controls, both observer directions and28 isolated hidden changes,
  plus HP/cast-skill positive controls. This actually executed selected original
  x86 consumer paths; it did not create real accounts or establish live native PK.
  Same selected transmitted projection can arise from different custom hidden
  attributes; this proves only that projection is insufficient, not that every
  official packet omits the attributes. Enemy MP wire values remain separate
  from the side1 RAM branch which does not apply them.
- Offline extraction plan/tool:
  `artifacts/research/enemy-capture-plan-20261006/README.md` and
  `tools/reconstruction/enemy_capture_extract.py`; current input is decoded
  pre-dispatch S2C JSONL with lifecycle, origin and raw evidence, not encrypted
  wire/pcap or post-consumer mutated1C. Execution status follows its own evidence.

The directly qualified candidate fields are received display identity/level,
HP, optional raw MP if actually sent, and observed83 skill actions. These are
observation-time values, not a complete original monster template. Four primary
attributes, five elements, all four attack/defense values and full carried skill
repertoire remain unknown pending authoritative enemy-bound sources.

## Private bootstrap follow-up

The blackbox agent subsequently created a new isolated schema49 database and
two temporary SQL fixture accounts/characters, IDs1/2. This is separate from
the original consumer experiment and is not native UI account creation or
formal schema51 evidence. The private listener/client were not started; live
PK/PvE remains unachieved. Temporary attribute/skill sidecars explicitly record
`applied_to_native_gameplay=0` and must never be published as native gameplay
values. See the consumer-experiment README and private-bootstrap manifest for
the retained executable, isolated copy hashes and exact staging limits.

The offline extractor has processed12 actual consumer-experiment inputs, all
`CUSTOM_TEST_NOT_NATIVE` with `transport_capture=false`. They contain no82/1C
encounter/participant binding, so they remain unbound. This does not constitute
an official monster capture. All four requested attack/defense columns remain
unknown; no numerical values have been invented.
