from pathlib import Path
import hashlib,json,subprocess,difflib

ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/round346-owned-mutation-receipt-implementation')
BASE='f5ab47fa8e55ff8c7438284caa23f61c26ca0efe'
sha=lambda data:hashlib.sha256(data).hexdigest()
norm=lambda data:data.replace(b'\r\n',b'\n')
def save(name,text):
    (OUT/name).write_text(text,encoding='utf-8',newline='\n')
manifest=json.loads((OUT/'implementation-manifest.json').read_bytes())
inverse={row['path']:(OUT/('final-'+Path(row['path']).name)).read_bytes() for row in manifest['sources']}
for change in reversed(manifest['inverse_replacements']):
    path=change['path']; after=bytes.fromhex(change['after_hex']); before=bytes.fromhex(change['before_hex'])
    assert inverse[path].count(after)==1
    inverse[path]=inverse[path].replace(after,before,1)
delta=[]
for row in manifest['sources']:
    path=row['path']; name=Path(path).name
    before=(OUT/('before-'+name)).read_bytes(); final=(OUT/('final-'+name)).read_bytes()
    assert inverse[path]==before and sha(before)==row['before_sha256'] and sha(final)==row['after_sha256']
    assert (ROOT/path).read_bytes()==final
    assert norm(before)==norm(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT))
    delta.extend(difflib.unified_diff(norm(before).decode().splitlines(keepends=True),
        norm(final).decode().splitlines(keepends=True),fromfile=path+'@'+BASE,tofile=path+'@candidate346'))
save('source-delta.patch',''.join(delta))

# The old recipes, native guard/current order and one COMMIT remain exactly
# within the reversible source replacements; dependency cuts prove the token
# constructor is private and the originals are already-framed response bytes.
ranges={
 'src/db/SqliteOwnedEquipmentTransaction.h':[(28,50)],
 'src/db/SqliteOwnedEquipmentTransaction.cpp':[(36,89),(168,190)],
 'src/game/SharedTaiwanWorldRecordSource.h':[(22,45)],
 'src/protocol/RecoveredMovement.h':[(76,95)],
 'src/protocol/RecoveredWorldFrame.h':[(1,51)],
 'src/net/Session.cpp':[(2318,2358)],
}
refs=[];cuts=[];pieces=[]
for path,spans in ranges.items():
    raw=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
    lines=raw.decode().splitlines()
    refs.append({'path':path,'revision':BASE,'bytes':len(raw),'sha256':sha(raw),'copied_full':False})
    for first,last in spans:
        assert 1<=first<=last<=len(lines),(path,first,last,len(lines))
        body='\n'.join(str(i)+': '+lines[i-1] for i in range(first,last+1))+'\n'
        cuts.append({'path':path,'revision':BASE,'first_line':first,'last_line':last,
                     'bytes':len(body.encode()),'sha256':sha(body.encode())})
        pieces.append('SOURCE '+path+' @ '+BASE+' L'+str(first)+'..'+str(last)+'\n'+body)
save('dependency-source-cuts.txt','\n'.join(pieces))
save('dependency-source-manifest.json',json.dumps({'source_epoch':BASE,'references':refs,'cuts':cuts},indent=2)+'\n')
upstream=[]
for folder_name,seal_name in [('round345-normal-entry-movement-implementation','SEAL.json'),
                            ('round346-initial-owned-material-source-plan','SEAL.json')]:
    directory=OUT.parent/folder_name;raw=(directory/seal_name).read_bytes();seal=json.loads(raw)
    total=0
    for row in seal['members']:
        data=(directory/row['name']).read_bytes()
        assert len(data)==row['bytes'] and sha(data)==row['sha256'];total+=len(data)
    assert total==seal['total_bytes'] and len(seal['members'])==seal['member_count']
    upstream.append({'package':str(directory),'seal_sha256':sha(raw),
        'members_verified':len(seal['members']),'integer_bytes':total,'unchanged':True})
save('source-custody-receipt.json',json.dumps({'baseline_revision':BASE,'inverse_exact_original_raw_bytes':True,
    'four_current_files_equal_captured_candidate':True,'upstream_seals':upstream,
    'no_target_execution':True,'no_db_sql_api_compiler_tests':True,
    'generic_binding_mutations':False,'original_ACK_and_prepare_reply_recipes_unchanged':True},indent=2)+'\n')
print('Four scoped source inverse and immutable dependencies verified without target execution.')
