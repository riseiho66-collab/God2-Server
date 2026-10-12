from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
D=Path(__file__).resolve().parent
Q=D/'closed-final'
Q.mkdir(exist_ok=False)
P=D.parent/'round356-party-preview-transport-proposal'
HEAD='6c2d3412e22316d1537323bc13e449f87ddfd03a'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
    p=Q/p;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b);assert p.read_bytes()==b
def js(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
s=(P/'seal.json').read_bytes();assert sha(s)=='219682c6177ed6fbd825d95ad06b81ce57731dc5fa56b1098d9a92e9df0cc701'
prior=json.loads(s)
for m in prior['members']:
    b=(P/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256'],m['path']
assert len(prior['members'])==107 and sum(m['bytes'] for m in prior['members'])==4654221
js('proposal-individual-verification.json',{'seal':str(P/'seal.json'),'seal_sha256':sha(s),'member_count':107,'member_bytes':4654221,'members':prior['members']})
a=json.loads((D/'apply-receipt.json').read_bytes());c=json.loads((D/'containment-receipt.json').read_bytes())
manifest=[];cutmanifest=[];snapshots={}
pins={
 'src/net/Session.h':'732201c66a8094b18d36aff80842aaa94974998c1496f2ceae5a5406dcad1a1d',
 'src/net/Session.cpp':'f37be408dd8dfc1f9c628939fd36a045d97791e16c07dbe3be5683043542af2d',
 'src/core/Application.cpp':'ad8cb48b49c4bb77578750c066ce7fe00f72208c926d7620886bc4a279574f95',
 'src/game/OwnedPartyPreviewTransport.h':'cba9065b8cb0aa6acc62c15780e6e693cf5c2200db07e4349015742f44b78b4d'}
for f,pin in pins.items():
    b=(R/f).read_bytes();assert sha(b)==pin,f;snapshots[f]=b
    put('final/'+f,b)
    if f!='src/game/OwnedPartyPreviewTransport.h':
        inv=b
        for e in reversed(a['edits']):
            if e['source']!=f:continue
            n=bytes.fromhex(e['after_hex']);o=bytes.fromhex(e['before_hex']);assert inv.count(n)==1;inv=inv.replace(n,o,1)
        assert inv==(D/'before'/f).read_bytes()==(P/'complete-final/whole'/f).read_bytes(),f
        put('inverse/'+f,inv)
    else:
        inv=b
        for e in reversed(c['edits']):
            n=bytes.fromhex(e['after_hex']);o=bytes.fromhex(e['before_hex']);assert inv.count(n)==1;inv=inv.replace(n,o,1)
        assert inv==(D/'candidate'/f).read_bytes()==(D/'new-OwnedPartyPreviewTransport.h').read_bytes()
        put('inverse/new-header-to-first-candidate.h',inv)
    manifest.append({'source':f,'retained':'final/'+f,'bytes':len(b),'sha256':sha(b),'old_whole_inverse_equal':f!='src/game/OwnedPartyPreviewTransport.h','new_header_candidate_inverse_equal':f=='src/game/OwnedPartyPreviewTransport.h'})
cuts={
 'src/net/Session.h':[('capture-api','    std::optional<NormalWorldOutputHandle> capture_normal_world_output(', '    bool normal_world_output_current_on_game(')],
 'src/net/Session.cpp':[('trusted-game-capture','std::optional<Session::NormalWorldOutputHandle> Session::capture_normal_world_output(', 'Session::NormalWorldOutputAttempt Session::send_normal_world_records(')],
 'src/core/Application.cpp':[
 ('host-construction','            std::map<std::uint64_t,std::weak_ptr<Session>> party_sessions;', '            std::map<std::uint64_t,std::weak_ptr<Session>> trade_sessions;'),
 ('actual-c91-flight','                                    // Actual C91 peer output custody;', '                                const auto prepared_sources=live;'),
 ('scheduler-settle','            auto scheduler=std::make_shared<Scheduler>', '                world.update(0.05f);'),
 ('stop-before-network','            auto stop=[&] {','                if(web_gateway)web_gateway->stop();')]}
for f,items in cuts.items():
    b=snapshots[f]
    for label,start,end in items:
        sb=start.encode();eb=end.encode();assert b.count(sb)==1,(f,label,'start')
        lo=b.index(sb);hi=b.index(eb,lo)+len(eb);raw=b[lo:hi]
        out='cuts/'+label+'.txt';put(out,raw)
        cutmanifest.append({'source':f,'retained':out,'byte_offset':lo,'bytes':len(raw),'sha256':sha(raw),'first_line':b[:lo].count(b'\n')+1,'whole_function':False})
frozen=['src/game/NativeParty.h','src/game/OwnedPartyDirectory.h','src/handlers/OwnedPartyDirectoryService.h','src/protocol/RecoveredParty.h','src/protocol/TaiwanNativePartyMenu.h','src/protocol/RecoveredWorldFrame.h','src/core/Config.h','src/core/Config.cpp']
unchanged=[]
for f in frozen:
    b=(R/f).read_bytes();assert b==(P/'complete-final/whole'/f).read_bytes(),f
    unchanged.append({'source':f,'bytes':len(b),'sha256':sha(b),'immutable_reference':str(P/'complete-final/whole'/f)})
for f,b in snapshots.items():assert (R/f).read_bytes()==b,f
js('final-source-manifest.json',{'head':HEAD,'members':manifest,'cuts':cutmanifest,'unchanged_upstreams':unchanged,'source_unchanged_at_readback':True,'whole_old_inverse_equal':True,'new_header_separately_labelled':True,'scope':'static source arithmetic/custody; no target/native/API/codec/parser/SQL/compiler/test execution'})
js('capture-complete.json',{'helper':Path(__file__).name,'head':HEAD,'four_final_count':4,'four_final_bytes':sum(m['bytes'] for m in manifest),'cut_count':len(cutmanifest),'cut_bytes':sum(m['bytes'] for m in cutmanifest),'old_full_inverse_count':3,'unchanged_upstreams_count':len(unchanged),'proposal_members_verified':107,'credits':{'method':0,'opcode':0,'format':0,'route':0}})
print(json.dumps({'status':'complete','four_final_bytes':sum(m['bytes'] for m in manifest),'cut_count':len(cutmanifest),'cut_bytes':sum(m['bytes'] for m in cutmanifest)}))
