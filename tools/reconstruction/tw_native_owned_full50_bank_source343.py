from pathlib import Path
import hashlib,json,re
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round343-owned-full50-bank-source')
SERVER=Path('C:/Users/risei/Desktop/God2/God2-Server');sha=lambda b:hashlib.sha256(b).hexdigest()
HEAD='43f4d294b8f017d2b00d697aa68a9c2e3726d8d5'
cuts={
 'src/db/OwnedInventoryRepository.h':[(10,60)],
 'src/db/NativeEquipmentSnapshotRepository.h':[(10,52)],
 'src/db/SqliteOwnedInventoryRepository.h':[(13,58)],
 'src/db/SqliteNativeEquipmentSnapshotRepository.h':[(21,58)],
 'src/db/SqliteOwnedInventoryRepository.cpp':[(25,65),(77,119),(120,166),(169,212),(283,293)],
 'src/db/SqliteNativeEquipmentSnapshotRepository.cpp':[(25,35),(54,120),(121,176)],
 'src/db/SqliteOwnedEquipmentTransaction.cpp':[(7,34),(36,89),(192,261)],
 'src/db/SqliteOwnedEquipmentTransaction.h':[(87,101),(118,128)],
 'src/db/SqliteOwnedEquipmentEntryTransaction.cpp':[(83,110)],
 'src/db/SqliteDatabase.cpp':[(204,225),(263,300),(398,414)],
 'src/game/SharedTaiwanOwnedBagMoveSource.cpp':[(19,106),(114,183)],
 'src/game/SharedTaiwanOwnedItemSelectionSource.cpp':[(34,73)],
 'src/game/SharedTaiwanOwnedItemRequestSource.h':[(13,30)],
 'src/db/SqliteRecoveredCharacterRepository.cpp':[(613,640),(650,674)],
 'src/db/SqliteWeaponSlotRepository.cpp':[(27,47),(62,75)],
 'src/db/SqliteArmorSlotRepository.cpp':[(25,42)],
 'src/db/SqliteBeastSnapshotRepository.cpp':[(255,267),(280,290)],
 'src/db/SqliteOwnedInstanceTradeRepository.cpp':[(272,304)],
 'src/db/SqliteOwnedPkRoomRepository.cpp':[(74,101)],
 'src/core/SharedTaiwanNativeWorldHostPlan.cpp':[(404,411)],
 'src/core/Application.cpp':[(699,705),(732,744),(7361,7374)],
 'src/main.cpp':[(83,88)],
 'tools/reconstruction/tw_native_item_custody_source_delivery.py':[(14,18)],
 'docs/research/tw-native-owned-bag-move-source-20261010.md':[(1,13)]}
raws={name:(SERVER/name).read_bytes() for name in cuts};refs=[];rows=[];pieces=[]
for name,ranges in cuts.items():
    raw=raws[name];lines=raw.decode('utf-8-sig').splitlines()
    refs.append(dict(path=str(SERVER/name),bytes=len(raw),sha256=sha(raw),copied_full=False))
    for first,last in ranges:
        last=min(last,len(lines));body='\n'.join(f'{i+1}: {lines[i]}' for i in range(first-1,last))+'\n'
        rows.append(dict(path=str(SERVER/name),first_line=first,last_line=last,source_sha256=sha(raw),rendered_bytes=len(body.encode('utf8')),rendered_sha256=sha(body.encode('utf8'))))
        pieces.append(f'FILE {name} L{first}..{last}\n{body}')
(OUT/'retained-source-cuts.txt').write_text('\n'.join(pieces),encoding='utf8',newline='\n')
(OUT/'source-cut-manifest.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8',newline='\n')
symbols=[]
for name,raw in raws.items():
    for line,text in enumerate(raw.decode('utf-8-sig').splitlines(),1):
        if re.search(r'acquisition_(sha256|record)|replace_from_issuer|observe_(before|committed)|stage_replace|CUSTOM_TEST_NOT_NATIVE|EMPTY_SLOT_POLICY|install_owned_equipment_schema',text):
            symbols.append(dict(file=str(SERVER/name),line=line,text=text))
(OUT/'bounded-symbol-references.json').write_text(json.dumps(symbols,indent=2)+'\n',encoding='utf8',newline='\n')
for name,raw in raws.items():
    assert (SERVER/name).read_bytes()==raw,'Source changed during snapshot '+name
(OUT/'source-reference-manifest.json').write_text(json.dumps(dict(snapshot_head=HEAD,sources=refs,source_stable_during_capture=True,target_execution=0,sql_executed=0,repository_mutations=0),indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(referenced_files=len(refs),numbered_cuts=len(rows),bounded_symbols=len(symbols),target_execution=0,sql_execution=0,new_population_sources=0)))
