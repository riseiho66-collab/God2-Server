from pathlib import Path
import hashlib,json

OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round339-rommaps-common-source-implementation')
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
cpp=ROOT/'src/db/NativeRomMapSourceCatalog.cpp'
previous=cpp.read_bytes()
assert previous==(OUT/'source-final/NativeRomMapSourceCatalog.cpp').read_bytes()
assert hashlib.sha256(previous).hexdigest()=='619cd15c3a2be9b500aae22ff1bf143c3be6b66cbb46a4a1aaefc9ee4e3a48eb'
text=previous.decode('utf8')
for anchor,replacement in [('WHERE name IN(','WHERE name COLLATE NOCASE IN('),("OR (type='trigger' AND tbl_name IN(","OR (type='trigger' AND tbl_name COLLATE NOCASE IN(")]:
    assert text.count(anchor)==1;text=text.replace(anchor,replacement)
cpp.write_text(text,encoding='utf8',newline='\n')
snapshot=OUT/'source-final-case-guard';snapshot.mkdir(exist_ok=True)
modified=[]
for rel in ['src/db/NativeRomMapSourceCatalog.h','src/db/NativeRomMapSourceCatalog.cpp']:
    p=ROOT/rel;raw=p.read_bytes();(snapshot/p.name).write_bytes(raw)
    modified.append(dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),retained='source-final-case-guard/'+p.name))
(OUT/'final-source-case-guard-manifest.json').write_text(json.dumps(dict(initial_cpp_sha256='bfdb6ab0eff5596775f5357f7fb52b1448923d70066353484f6098985fd109a9',intermediate_temp_guard_cpp_sha256=hashlib.sha256(previous).hexdigest(),change='Main schema name/trigger tbl_name COLLATE NOCASE; importer TEMP trigger tbl_name already COLLATE NOCASE; reader query/transaction and pins unchanged',modified_files=modified,api_db_execution=0),indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(modified))
