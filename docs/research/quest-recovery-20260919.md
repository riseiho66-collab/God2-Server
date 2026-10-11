# Current-client quest definition extraction

Run from the server root:

```powershell
python -m tools.strike_lab.recover_quests --client ..\God2 --output artifacts/world-atlas/quests.json
python -m unittest discover -s tests/research -p test_recover_quests.py -v
```

Authority: current `Data2/Patch/Comm/Mission_data.csvZ`, `ActMis.csvZ`,
and `DayMissionDesc.csvZ`. Exact column headers gate normalization. Each
table retains its header, column mapping, preamble, raw field bytes, line
endings, source/decoded SHA-256 and physical line numbers. CP950 is a display
projection. Tests reconstruct all decoded bytes, not client execution.

Observed: 418 mission definitions, 2014 objective text rows, 169 ACTMIS rows,
85 daily rows, 676 item slots (169 nonzero), 170 NPC slots. Five daily rows
omit columns 13-19; these remain null. Zero item slots are retained without
assuming their sentinel behavior. Structural checks report no issues.

Both legacy roots were searched before extraction:

- Classic `db/imports/official/quests/quests.official.json` explicitly marks
  rewards/NPC/state unverified and gameplay import false. Its ACTMIS joins
  are not proof of the current client's namespace relationship.
- XJZ `evidence-quest-service-template-v0.md` records 418/2014/169 and no
  authoritative rewards; inferred names are not imported here.

No NPC placements, monster IDs, prerequisite edges, reward rules, eligibility
rules or transitions are derived from text. No cycle or missing-target verdict
is possible without established target namespaces/edges; these are UNKNOWN,
not passed validation. Definition extraction is implemented; server integration
and client behavioral equivalence are not implemented or claimed. No Lua rules
are emitted.

Next executable hook: invoke `build_catalog(client)` from the owner's catalog
integration and retain this qualification. For consumer investigation, XJZ
`cpp/xjz_evidence_repository.hpp:1454` (`GetQuestTemplate`) and `:1459`
(`LoadQuestServiceTemplates`) expose the repository contract;
`cpp/xjz_evidence_models.hpp:4329` carries its template fields. Classic
`src/God2.ClassicServer.Runtime/QuestRuntime.cs:495` blocks unproved prerequisite
eligibility and `:2035` blocks unproved rewards. Those reconstructed contracts
are investigation targets, not evidence of original-client transition behavior.
