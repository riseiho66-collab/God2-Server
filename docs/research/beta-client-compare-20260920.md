# Beta Client Source Comparison

## Result

The user-designated beta client is a genuinely different source tree. Its
release date and exact build designation have not been independently established.
This pass found an older skill-record layout and usable cross-version comparison
anchors, but did not recover wild-monster attack/defense or damage formulas.
Neither client was modified or launched. No production database was changed.

## Reproducible Inventory

- Source: `C:/Users/risei/Desktop/god2-test`.
- Comparison: `C:/Users/risei/Desktop/God2/God2`.
- 5,316 files inventoried; 116 CSVZ/INIZ/MDTZ files decoded, zero decode errors.
- Selected tables, skill binary and executables have hashes in the JSON artifact.
- Other binary/media bodies remain unexamined; inventory is not semantic coverage.
- Artifact: `artifacts/research/beta-client-compare-20260920.json`.

Run from the server root:

```powershell
python -B -m tools.strike_lab.beta_client_compare --beta C:\Users\risei\Desktop\god2-test --current C:\Users\risei\Desktop\God2\God2 --output artifacts/research/beta-client-compare-20260920.json
python -B -m unittest discover -s tests/research -p test_beta_client_compare.py -v
```

Four focused tests passed; the full real-source comparison also completed.

## Monster Catalog

Beta `Data2/Patch/Comm/gamedata.csvZ` SHA256:
`5be88eb0cd34893feb75b3f8373062c778b0992d45bf57ec8a41b070b33414a6`.
Decoded size: 646,482 bytes.

`EnyName` declares 1,401 actual records, all six comma-separated fields.
1,040 beta rows occur byte-for-byte somewhere in the current catalog. This
comparison does not establish equal map placement or matching contextual IDs.
No additional stat columns were found in this section. The identities and
appearance fields cannot be promoted to monster HP, attack or defense values.

Beta-only gamedata ASCII tags are `CBF` and `SMC`. `SMC` declares zero rows;
`CBF` contains card-related item records/descriptions, not a monster ability
table. `FightPetSkill` has 198 rows, versus 254 in the current same-named section;
this is not proof of individual wild-monster skill ownership.

## Skill Binary Lead

Both `Data2/Fight/Spg/cbspec2.bin` files begin with version text `1.03`, but
their record widths differ. The current fixed-width reader correctly rejects
the beta file; it must not be silently reused with current offsets.

| Property | Beta | Current |
| --- | ---: | ---: |
| File bytes | 110612 | 112660 |
| Record width | 108 | 110 |
| Bank stride | 27652 | 28164 |
| Populated bank counts | 98, 84, 68, 83 | 121, 129, 87, 111 |
| Total populated records | 333 | 448 |

All populated records satisfy the bank/ordinal identity bytes. Of 333 beta
records compared at the same bank/id, 224 equal the current first 108 bytes;
109 differ. The artifact preserves every beta record hash, source offset,
current offset and differing byte position. Matching keys alone do not prove
unchanged skill semantics, especially for renamed/replaced entries.

These are data-layout anchors, not recovered damage or critical-hit formulas.
The next useful code target is the beta skill loader and consumers of differing
fields, independently locating their addresses rather than copying current RVAs.

## Executable Boundary

Beta `god2.exe` SHA256:
`1326af232a5280a5bf19cfadb434ba66b8b2b2753bd36097ada3ef66474c5cac`.
It has `.aspack`/`.adata` sections, an entry RVA of `0x1c5001`, and compressed-looking
raw/virtual section-size differences. These are packer indicators. The packed
disk image is not a suitable basis for declaring that computation code is absent.
Unpacking and beta loader/consumer execution were not performed in this pass.

Additional CP950 keyword searches across decoded CSVZ/MDTZ found stat vocabulary
in equipment/card descriptions, menu schemas, effects and dialogue. Such hits
are leads only; no monster-ID-bound dual-attack/defense table was qualified.
No cross-version numeric values were imported into the server.
