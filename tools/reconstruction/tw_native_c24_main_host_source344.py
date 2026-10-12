"""Static source custody only; no server/API/native/SQL/compiler execution."""
from pathlib import Path
import hashlib, json, difflib

ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).parent
def sha(raw): return hashlib.sha256(raw).hexdigest()
def emit(name, value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

manifest=json.loads((OUT/'source-manifest.json').read_text(encoding='utf-8'))
hunks=[]
diff=[]
for ref in manifest:
    path=ref['path']; name=Path(path).name
    old=(OUT/('before-'+name)).read_bytes()
    new=(ROOT/path).read_bytes()
    assert sha(old)==ref['before_sha256'] and len(old)==ref['before_bytes']
    assert sha(new)==ref['after_sha256'] and len(new)==ref['after_bytes']
    assert new==(OUT/('after-'+name)).read_bytes()
    # keepends preserves mixed original newlines, so unrelated LF->CRLF
    # substitutions cannot masquerade as equal source.
    a=old.decode('utf-8').splitlines(keepends=True)
    b=new.decode('utf-8').splitlines(keepends=True)
    for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
        if tag=='equal': continue
        removed=''.join(a[i:j]); added=''.join(b[k:l])
        if removed:
            assert removed=='                stopping=true; spdlog::info("Stopping server and draining sessions");\r\n'
        hunks.append({'source':path,'tag':tag,'old_first_line':i+1,'old_lines':j-i,
            'new_first_line':k+1,'new_lines':l-k,'removed_sha256':sha(removed.encode()),
            'added_sha256':sha(added.encode())})
    diff.extend(difflib.unified_diff(a,b,fromfile='before/'+path,tofile='after/'+path))
(OUT/'source-delta.diff').write_bytes(''.join(diff).encode('utf-8'))
emit('source-hunks.json',hunks)

app=(ROOT/'src/core/Application.cpp').read_text(encoding='utf-8')
config=(ROOT/'src/core/Config.cpp').read_text(encoding='utf-8')
header=(ROOT/'src/core/Config.h').read_text(encoding='utf-8')
outer=app.index('                if(whole_bag_moves) {')
listener=app.index('                character_server=std::make_unique<TcpServer>',outer)
block=app[outer:listener]
assert app.rfind('game_handlers.world_records=',0,outer)>app.index('if(owned_client_options)')
assert block.index('RecoveredInventoryMoveRequest::Request>(record)')<block.index('return original(session,records)')
assert block.index('host->binding->release(*session)')<block.index('previous(std::move(session))')
assert 'install_' not in block and 'create_with_item_material(' not in block
assert 'create_for_normal_entry_with_item_material(' in block
assert 'return reply->bytes();' in block
assert 'if(!owned_whole_bag_moves_enabled)return;' in config
assert 'bool owned_whole_bag_moves_enabled=false;' in header
assert app.index('WholeBagMoveHostGuard whole_bag_move_lifetime')>app.index('std::unique_ptr<TcpServer> character_server;')
assert app.index('auto whole_bag_moves=')>app.index('std::unique_ptr<RecoveredMovementService> recovered_movement;')
assert app.index('config.validate_owned_whole_bag_moves();')<app.index('asio::io_context game;')
emit('static-source-order-facts.json',{
    'review_kind':'source inspection/custody, no API/target execution',
    'whole_batch':'exactly one C24 plus Tick via existing RecoveredWorldService, otherwise nullopt before observers',
    'reply':'already-framed Reply.bytes passed to same existing Session response path',
    'disconnect':'null Session safe; actual binding release precedes previous observers, first exception preserved',
    'lifetime':'weak facades; stop acceptance then invalidate; guard clears owning functions on game before listener, movement and DB destruction',
    'default':'false => validation early return, null shared host, no callback wrapping/storage access/invalidation',
    'native_methods_opcodes_formats_routes_credit':0})

# Source dependencies are hashed in place. Retain only needed exact text spans.
specs=[('src/handlers/RecoveredWorldService.cpp',17,26),
       ('src/handlers/RecoveredWorldService.cpp',84,101),
       ('src/game/SharedTaiwanOwnedBagMoveSource.cpp',205,303),
       ('src/game/SharedTaiwanOwnedBagMoveSource.h',17,32),
       ('src/db/SqliteOwnedEquipmentTransaction.cpp',6,18),
       ('src/db/SqliteDatabase.cpp',200,224),
       ('src/net/Session.cpp',1957,1968)]
refs=[]
for index,(path,first,last) in enumerate(specs):
    raw=(ROOT/path).read_bytes(); lines=raw.splitlines(keepends=True)
    cut=b''.join(lines[first-1:last]); target=f'dependency-{index:02d}-{Path(path).stem}-{first}-{last}.txt'
    (OUT/target).write_bytes(cut)
    refs.append({'source':path,'source_bytes':len(raw),'source_sha256':sha(raw),
        'first_line':first,'last_line':last,'excerpt':target,'excerpt_bytes':len(cut),'excerpt_sha256':sha(cut)})
emit('dependency-references.json',refs)
emit('capture-success.json',{'status':'static custody success','sources':len(manifest),'hunks':len(hunks),
     'dependencies':len(refs),'capture_sha256':sha(Path(__file__).read_bytes())})
print(json.dumps({'status':'static custody success','hunks':len(hunks),'dependencies':len(refs)}))
