"""Static SOURCE custody/readback only. No target/native/codec/DB API execution."""
from pathlib import Path
import hashlib,json,base64
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server');OUT=Path(__file__).resolve().parent
PINS={
 'src/core/Application.cpp':'c23280c11afd0414dff1a403c498820099d639db90539f18c1afffeb26bd5d43',
 'src/net/Session.cpp':'3f168c3332d90aa22b47d8f9ba4283ffa54d3723e7fa6c044037efe0b183fb94',
 'src/net/Session.h':'fd523727ead64b4924d843b76229964f6c89f01d443a933d3679251ac8ecbd48',
 'src/game/SharedTaiwanOwnedBagMoveSource.h':'31e133b006ca88902814dc2e817ae4145e356acea7323aa67e76ae17702966dc',
 'src/game/SharedTaiwanOwnedBagMoveSource.cpp':'3b7995f6d444150f77a0afd0560950c70ece5e955687472f3d9dd73cd7bba790',
 'src/handlers/RecoveredMovementService.h':'26cdf5db335cf719a562cee41122c9cce04ec09855c0a4d28e04ad7a1769a783',
 'src/handlers/RecoveredMovementService.cpp':'74601229cafb96995640a4b30fee55ccb30208cf0c20d823f032ecf0742dd182',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def put(name,data):
    dest=OUT/name
    if dest.exists():raise RuntimeError('Immutable output exists: '+name)
    dest.write_bytes(data)
def js(name,obj):put(name,(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode())
refs=[];contents={}
for rel,pin in PINS.items():
    p=ROOT/rel;b=p.read_bytes();assert sha(b)==pin
    contents[rel]=b
    refs.append({'path':p.as_posix(),'relative':rel,'bytes':len(b),'sha256':pin})
    # Own final whole files already retained; capture bounded peer source snapshots.
    if rel not in ('src/core/Application.cpp','src/net/Session.cpp','src/net/Session.h'):
        put('dependency-'+p.name,b)
for rel in ['src/core/Config.h','src/core/Config.cpp','src/db/SqliteOwnedEquipmentTransaction.h',
    'src/db/SqliteOwnedEquipmentTransaction.cpp','src/handlers/RecoveredWorldService.cpp']:
    p=ROOT/rel;b=p.read_bytes();refs.append({'path':p.as_posix(),'relative':rel,'bytes':len(b),'sha256':sha(b)})
    contents[rel]=b
js('current-source-manifest.json',{'baseline_HEAD':'f5ab47fa8e55ff8c7438284caa23f61c26ca0efe','scope':'7 scoped source candidates; 3 owned,4 peer; no target execution','sources':refs})

# Actual code spans, exact original bytes and source positions, not pattern tests.
spans=[
 ('Session-TLS-scope','src/net/Session.cpp','thread_local const Session* observed_world_callback=', 'std::shared_ptr<spdlog::logger> logger('),
 ('Session-ResponseData','src/net/Session.cpp','struct Session::WorldResponseWrite::Data {','struct Session::NormalWorldInitialization::Entry {'),
 ('Session-ResponseAttempt','src/net/Session.cpp','    struct WorldResponseAttempt {','    struct SelectionEntry {'),
 ('Session-Write-layout','src/net/Session.cpp','    struct Write {','    std::deque<Write> writes;'),
 ('Session-actual-game-response-handoff','src/net/Session.cpp','        asio::post(game,[self=owner.shared_from_this(),records=std::move(records),requests=std::move(requests),native_batch_generation] {','    void deliver(std::vector<Packet> packets) {'),
 ('Session-real-write-completion','src/net/Session.cpp','    void write() {','    void close() {'),
 ('Session-close-fail','src/net/Session.cpp','    void close() {','    void finish() {'),
 ('Session-observe-current-API','src/net/Session.cpp','Session::WorldResponseWrite Session::observe_world_response(', 'std::optional<Session::NormalWorldInitialization> Session::normal_world_initialization() const {'),
 ('Main-WholeBagMoveHost','src/core/Application.cpp','struct WholeBagMoveHost {','struct WorldLifecycleVaultGuard {'),
 ('Main-actual-outer-host','src/core/Application.cpp','                if(whole_bag_moves) {','                character_server=std::make_unique<TcpServer>'),
]
cuts=[]
for name,rel,start,end in spans:
    b=contents[rel];s=start.encode();e=end.encode()
    assert b.count(s)==1
    at=b.index(s);to=b.index(e,at+len(s));cut=b[at:to]
    put(name+'.txt',cut)
    cuts.append({'name':name+'.txt','source':rel,'source_sha256':sha(b),'byte_begin':at,'byte_end_exclusive':to,
        'first_line':b[:at].count(b'\n')+1,'last_line':b[:to].count(b'\n'),'bytes':len(cut),'sha256':sha(cut)})
js('source-cuts.json',{'scope':'actual source-body/caller/lifetime text cuts only','cuts':cuts})

# Independently reconstruct every exact original source from inverse delta chain.
owned={r['relative']:contents[r['relative']] for r in refs if r['relative'] in (
    'src/core/Application.cpp','src/net/Session.cpp','src/net/Session.h')}
def undo(b,hunks):
    for h in reversed(hunks):
        before=base64.b64decode(h['before_b64']);after=base64.b64decode(h['after_b64']);at=h['offset']
        assert b[at:at+len(after)]==after;b=b[:at]+before+b[at+len(after):]
    return b
reentry=json.loads((OUT/'reentry-correction-manifest.json').read_text())
owned['src/core/Application.cpp']=undo(owned['src/core/Application.cpp'],reentry['hunks'])
correction=json.loads((OUT/'correction-manifest.json').read_text())
for r in correction['changes']:
    b=owned[r['path']];assert sha(b)==r['final_sha256']
    b=undo(b,[r]);assert sha(b)==r['early_sha256'];owned[r['path']]=b
main=json.loads((OUT/'main-source-manifest.json').read_text())
owned['src/core/Application.cpp']=undo(owned['src/core/Application.cpp'],main['hunks'])
base=json.loads((OUT/'apply-source-manifest.json').read_text())
for r in base['changes']:owned[r['path']]=undo(owned[r['path']],r['hunks'])
proof=[]
for rel,b in owned.items():
    old=(OUT/('before-'+Path(rel).name)).read_bytes();assert b==old
    proof.append({'path':rel,'original_bytes':len(b),'original_sha256':sha(b),'exact_inverse':True,
        'final_bytes':len(contents[rel]),'final_sha256':sha(contents[rel])})
js('exact-default-byte-inverse-proof.json',{'scope':'all old source bytes outside authorized hunks retained; no execution/dynamic claim','sources':proof})

peer=OUT.parent/'round346-owned-mutation-receipt-implementation'
sb=(peer/'seal.json').read_bytes();assert sha(sb)=='96543c74cd8d6751540d932084e3cd1be4b8efc2a839f248651bd873c6051b03'
seal=json.loads(sb);verified=[]
for m in seal['members']:
    name=m.get('path',m.get('name'));b=(peer/name).read_bytes()
    assert len(b)==m['bytes'] and sha(b)==m['sha256'];verified.append({'path':name,'bytes':len(b),'sha256':sha(b)})
assert len(verified)==25 and sum(m['bytes'] for m in verified)==269040
js('peer346-individual-verification.json',{'seal_path':(peer/'seal.json').as_posix(),'seal_sha256':sha(sb),
    'member_count':len(verified),'member_bytes':sum(m['bytes'] for m in verified),'members':verified})
print(json.dumps({'owned_exact_inverse':3,'source_refs':len(refs),'source_cuts':len(cuts),'peer_verified':len(verified),
                  'new_native_method_opcode_format_route_credit':0}))
