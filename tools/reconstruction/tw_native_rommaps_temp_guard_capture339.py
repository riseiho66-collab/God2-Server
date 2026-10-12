from pathlib import Path
import hashlib,json

OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round339-rommaps-common-source-implementation')
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
cpp=ROOT/'src/db/NativeRomMapSourceCatalog.cpp'
initial=cpp.read_bytes()
assert initial==(OUT/'source/NativeRomMapSourceCatalog.cpp').read_bytes()
assert hashlib.sha256(initial).hexdigest()=='bfdb6ab0eff5596775f5357f7fb52b1448923d70066353484f6098985fd109a9'
text=initial.decode('utf8')
anchor='struct ReadScope {\n'
helper='''void import_temp_triggers(sqlite3* db) {
    // TEMP triggers can target main tables and perform collateral writes even
    // when the final source pins still match. Guard before any schema/data write.
    sqlite_detail::Statement triggers(db,
        "SELECT name FROM temp.sqlite_schema WHERE type='trigger' AND tbl_name COLLATE NOCASE IN("
        "'native_raw_resource_source_sets','native_raw_resource_source_rows')");
    if(triggers.row())throw DatabaseError("RomMaps source import TEMP trigger collision");
}
'''
assert text.count(anchor)==1
text=text.replace(anchor,helper+anchor)
anchor='    sqlite_detail::Transaction transaction(db);\n    source_schema(db,false);'
assert text.count(anchor)==1
text=text.replace(anchor,'    sqlite_detail::Transaction transaction(db);\n    import_temp_triggers(db);\n    source_schema(db,false);')
cpp.write_text(text,encoding='utf8',newline='\n')
snapshot=OUT/'source-final';snapshot.mkdir(exist_ok=True)
modified=[]
for rel in ['src/db/NativeRomMapSourceCatalog.h','src/db/NativeRomMapSourceCatalog.cpp']:
    p=ROOT/rel;raw=p.read_bytes();(snapshot/p.name).write_bytes(raw)
    modified.append(dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),retained='source-final/'+p.name))
(OUT/'final-source-manifest.json').write_text(json.dumps(dict(initial_cpp_sha256=hashlib.sha256(initial).hexdigest(),initial_cpp_retained='source/NativeRomMapSourceCatalog.cpp',change='Importer-only TEMP trigger guard before DDL/INSERT; reader and native/source pins unchanged',modified_files=modified,api_db_execution=0),indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(modified))
