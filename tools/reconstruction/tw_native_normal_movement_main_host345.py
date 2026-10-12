"""Static source capture only; no native/server/API/SQL/C++ execution."""
from pathlib import Path
import hashlib, json, difflib
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def emit(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
manifest=json.loads((OUT/'source-manifest.json').read_text(encoding='utf-8'))
hunks=[];delta=[]
for ref in manifest:
    path=ref['path'];name=Path(path).name
    old=(OUT/('before-'+name)).read_bytes();new=(ROOT/path).read_bytes()
    assert len(old)==ref['before_bytes'] and sha(old)==ref['before_sha256']
    assert len(new)==ref['after_bytes'] and sha(new)==ref['after_sha256']
    assert new==(OUT/('after-'+name)).read_bytes()
    a=old.decode('utf-8').splitlines(keepends=True);b=new.decode('utf-8').splitlines(keepends=True)
    for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if tag=='equal':continue
        hunks.append({'path':path,'tag':tag,'old_first_line':i+1,'old_lines':j-i,
            'new_first_line':k+1,'new_lines':l-k,
            'removed_sha256':sha(''.join(a[i:j]).encode()),'added_sha256':sha(''.join(b[k:l]).encode())})
    delta.extend(difflib.unified_diff(a,b,fromfile='before/'+path,tofile='after/'+path))
(OUT/'source-delta.diff').write_bytes(''.join(delta).encode('utf-8'))
emit('source-hunks.json',hunks)
app=(ROOT/'src/core/Application.cpp').read_text(encoding='utf-8')
cfg=(ROOT/'src/core/Config.cpp').read_text(encoding='utf-8')
assert cfg.index('if(!owned_whole_bag_moves_enabled)return;')<cfg.index('if(diagnostic_town_map_probe')
assert 'whole_bag_moves->transaction,database.accounts(),database.recovered_characters(),*recovered_movement' in app
assert app.count('whole_bag_moves->transaction=std::make_shared<SqliteOwnedEquipmentTransaction>')==1
assert 'auto committed=movement->move_committed_with_owned_material(session,*transaction,requests);' in app
assert 'return std::move(committed.reply);' in app
assert 'service.reset();binding.reset();movement=nullptr;transaction.reset();' in app
first=app.index('                if(whole_bag_moves) {')
last=app.index('                character_server=std::make_unique<TcpServer>',first)
block=app[first:last]
assert 'install_' not in block
assert 'std::holds_alternative<RecoveredInventoryMoveRequest::Request>(record) ||\n                                std::holds_alternative<RecoveredMovement::Request>(record)' in block
assert block.index('movement->move_committed_with_owned_material')<block.index('host->transaction!=transaction')<block.index('return std::move(committed.reply)')
assert 'Whole bag move committed but host facade became stale' in block
emit('static-source-facts.json',{
    'scope':'actual default-off normal-entry same-map movement and C24 Main host',
    'same_transaction':'one strong joint transaction field passed unchanged to C24 and typed movement',
    'admission':'outer C24 OR Movement batch before old consumers, existing service rejects mixed C24/move before mutation',
    'reply':'actual typed CommittedMove.reply unchanged, stale facade after successful typed call throws',
    'lifetime':'game-only weak facade; borrowed actual movement pointer; source callbacks cleared before pointer/transaction, before owners',
    'stop':'accepting=false/invalidate C24 before drain; actual typed method has local synchronous guard; existing remove poisons active opted method',
    'default':'validate early return; no host/tx/wrapper created whenfalse; old routing and default shutdown unchanged',
    'credits':{'native_method':0,'opcode':0,'format':0,'whole_route':0}})

# Actual selected code and source reference hashes, not target invocation.
specs=[('src/handlers/RecoveredWorldService.cpp',84,101),
       ('src/handlers/RecoveredWorldService.cpp',130,187),
       ('src/core/Application.cpp',2400,2535),
       ('src/core/Application.cpp',5338,5422),
       ('src/core/Application.cpp',5440,5506)]
refs=[]
for n,(path,first,last) in enumerate(specs):
    raw=(ROOT/path).read_bytes();cut=b''.join(raw.splitlines(keepends=True)[first-1:last])
    name=f'dependency-{n:02d}-{Path(path).stem}-{first}-{last}.txt';(OUT/name).write_bytes(cut)
    refs.append({'source':path,'source_bytes':len(raw),'source_sha256':sha(raw),'first_line':first,'last_line':last,
                 'excerpt':name,'excerpt_bytes':len(cut),'excerpt_sha256':sha(cut)})
movement=(ROOT/'src/handlers/RecoveredMovementService.cpp').read_bytes()
movement_h=(ROOT/'src/handlers/RecoveredMovementService.h').read_bytes()
assert b'move_committed_with_owned_material(Session&' in movement_h
lines=movement.splitlines(keepends=True)
start=next(i for i,line in enumerate(lines) if b'RecoveredMovementService::move_committed_with_owned_material(' in line)
end=next(i+1 for i,line in enumerate(lines[start:],start) if line.rstrip()==b'}')
cut=b''.join(lines[start:end]);(OUT/'typed-movement-method.txt').write_bytes(cut)
refs.append({'source':'src/handlers/RecoveredMovementService.cpp','source_bytes':len(movement),'source_sha256':sha(movement),
             'first_line':start+1,'last_line':end,'excerpt':'typed-movement-method.txt','excerpt_bytes':len(cut),'excerpt_sha256':sha(cut)})
refs.append({'source':'src/handlers/RecoveredMovementService.h','source_bytes':len(movement_h),'source_sha256':sha(movement_h)})
emit('dependency-references.json',refs)

# Verify each individual member of the two sealed source/correction packages.
archive=OUT.parent
packages=['round345-normal-entry-movement-custody-source','round345-normal-entry-movement-custody-source-correction']
receipts=[]
for name in packages:
    package=archive/name
    if not package.exists():
        raise FileNotFoundError('exact source correction package path requires qualification: '+name)
    raw=(package/'seal.json').read_bytes();seal=json.loads(raw)
    for member in seal['members']:
        body=(package/member.get('path',member.get('name'))).read_bytes()
        assert len(body)==member['bytes'] and sha(body)==member['sha256']
    assert seal['member_count']==len(seal['members'])
    total=seal.get('member_bytes',seal.get('total_bytes'))
    assert total==sum(member['bytes'] for member in seal['members'])
    receipts.append({'package':name,'seal_sha256':sha(raw),'member_count':seal['member_count'],'member_bytes':total})
emit('prior-seals-verified.json',receipts)
emit('capture-success.json',{'status':'static source custody success','hunks':len(hunks),'dependencies':len(refs),
                            'helper_sha256':sha(Path(__file__).read_bytes())})
print(json.dumps({'status':'static source custody success','hunks':len(hunks),'dependencies':len(refs)}))
