# CUSTOM-0058 skill name and F1 prompt repair

The supplied skill126 cbspec2 name was already correct CP950:
`c0febc76a454b7d9b1d9` = 瞬影三煞斬. Neither clone_hooks.cpp nor
target_selection.h supplies Chinese prompt literals. This defect is a missing
native display metadata lookup, not evidence of UTF-8 being passed to Big5.

Native `005154E0` calls `0051BE90` when the F1 skill is selected. `0051BE90`
calls `004A8E10(kind,id,&output_item_id)`, then formats `%s MP:%d` from
the returned item record's name at +8 and skill definition's MP WORD at +42.
`004A8E10` generates `SpcA126`, scans item IDs6501..6899 using `00459A60`,
and compares the metadata alias at +11C (7 bytes for skill IDs>=100).
The original gamedata SKB section has381 rows and no SpcA126 alias.
On a miss, native code leaves its output_item_id untouched and looks up that
value. The caller has not initialized it or its local prompt buffer, explaining
the undefined name/prompt without changing the catalog's correct name bytes.

`tools/skills/build_shunying_client.py` now adds one SKB display row at6897,
inside the original ItemType SKB interval6501..6900 and unoccupied in both
source languages. Its alias is SpcA126, name is 瞬影三煞斬 (CP950) / 瞬影三煞斩
(CP936), and icon21126 selects the existing custom icon. The new row copies
native blade3 SKB6508 and changes only columns0,2,3,4,26 (item id, label,
icon, display name, skill alias). All other source bytes are preserved except
the SKB row count381->382. This does not grant/sell an item, change the server
skill registry, or establish balance for the inherited book fields. Existing
visual resources, selection logic, and native records are unchanged.

The new files are isolated candidate outputs `Data2/Patch/Comm/gamedata.csvZ`
and `gamedata-gb.csvZ`. Source hashes are pinned by the builder; decoded
restoration removes only the new row/count and must equal the original source.
The handoff manifest includes both files. No live installation, process control,
or client UI operation was performed by this repair worker.

Validation: `python -B -m tools.skills.verify_shunying_display` passes for both
languages. It runs the pinned native tokenizer, complete59420 metadata parser,
index store, icon lookup, and complete4A8E10 resolver plus native strncmp. Only
the resolver's CRT sprintf is adapted. Native skill8 still resolves6508;
missing126 leaves a seededFFFF output untouched; the new record makes126
resolve6897 with the exact name bytes; reserved125 remains missing. Original
records and all other decoded gamedata bytes are verified preserved. Evidence:
`artifacts/custom-skills/shunying/client-candidate/display-name-verification.json`.
Graphical own-server F1/name acceptance remains the parent task's deployment
and black-box check; offline native execution does not certify that UI result.

Parent deployment/live follow-up: installed both candidate gamedata files in private client. Native battle F1 screenshot displayed `瞬影三煞斬 MP:20` correctly; user subsequently confirmed 「目前都正常」. Name/prompt repair accepted.
