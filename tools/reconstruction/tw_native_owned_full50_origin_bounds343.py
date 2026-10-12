from pathlib import Path
import hashlib,json
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round343-owned-full50-bank-source')
SERVER=Path('C:/Users/risei/Desktop/God2/God2-Server');sha=lambda b:hashlib.sha256(b).hexdigest()
refs=[];parts=[]
for name,first,last in [('src/db/SqliteArmorSlotRepository.cpp',43,105),('src/db/SqliteBeastSnapshotRepository.cpp',25,35),('src/db/SqliteBeastSnapshotRepository.cpp',242,253),('src/db/SqliteOwnedInventoryRepository.cpp',69,81)]:
    raw=(SERVER/name).read_bytes();lines=raw.decode('utf-8-sig').splitlines()
    parts.append(f'FILE {name} L{first}..{last}\n'+'\n'.join(f'{i+1}: {lines[i]}' for i in range(first-1,min(last,len(lines))))+'\n')
    refs.append(dict(path=str(SERVER/name),bytes=len(raw),sha256=sha(raw),first_line=first,last_line=last,copied_full=False))
(OUT/'legacy-origin-cuts.txt').write_text('\n'.join(parts),encoding='utf8',newline='\n')
(OUT/'legacy-origin-manifest.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(numbered_cuts=len(refs),target_execution=0)))
