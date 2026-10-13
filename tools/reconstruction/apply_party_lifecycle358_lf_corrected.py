from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path(__file__).resolve().parent
HEAD='81566a8a7efb75e7ea768bb5f767e1e5f1ad9324'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
    p=D/p;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
files=['src/core/Application.cpp','src/game/OwnedPartyPreviewTransport.h'];old={f:(R/f).read_bytes() for f in files};new=dict(old);edits=[]
for f in files:assert old[f]==subprocess.check_output(['git','show',HEAD+':'+f],cwd=R)
def edit(f,o,n):
    assert new[f].count(o)==1,(f,new[f].count(o));new[f]=new[f].replace(o,n,1);edits.append({'source':f,'before_hex':o.hex(),'after_hex':n.hex(),'multiplicity':1})
f=files[1];needle=b'    void stop() noexcept {state_->stop();}\n';assert new[f].count(needle)==1
replacement=b'''    // Actual game-owned ready/disconnect supplier; no ID/successor lookup.
    // Already completed allQueued flights have no registry node to revoke.
    void retire_source(Session& source) noexcept {
        if(state_->game_thread!=std::this_thread::get_id())return;
        if(state_->stopped)return;
        for(auto it=state_->flights.begin();it!=state_->flights.end();) {
            const auto flight=*it;
            const bool matches=std::any_of(flight->sources.begin(),flight->sources.end(),
                [&](const auto& held){return held.peer.get()==&source;});
            if(!matches){++it;continue;}
            flight->retire(flight->committed);
            state_->held_sources-=flight->sources.size();
            it=state_->flights.erase(it);
        }
    }
'''+needle
edit(f,needle,replacement)
f=files[0]
# Keep the actual existing line ending per insertion, all surrounding bytes exact.
for anchor in [b'            Session::DisconnectHandler on_disconnect=[&](std::shared_ptr<Session> session) {',b'                    game_handlers.world_ready=[&,directory_ready](Session& session) {']:
    assert new[f].count(anchor)==1;at=new[f].index(anchor)+len(anchor);ending=b'\r\n' if new[f][at:at+2]==b'\r\n' else b'\n';assert new[f][at:at+len(ending)]==ending
    indent=b'                    ' if b'DisconnectHandler' in anchor else b'                        '
    edit(f,anchor+ending,anchor+ending+indent+b'if(party_preview_transport)party_preview_transport->retire_source('+ (b'*session' if b'DisconnectHandler' in anchor else b'session')+b'); // Before throwing observers.'+ending)
for f in files:
    inv=new[f]
    for e in reversed(edits):
        if e['source']==f:
            n=bytes.fromhex(e['after_hex']);o=bytes.fromhex(e['before_hex']);assert inv.count(n)==1;inv=inv.replace(n,o,1)
    assert inv==old[f]
assert all((R/f).read_bytes()==old[f] for f in files)
for f in files:put('before/'+f,old[f])
for f in files:(R/f).write_bytes(new[f]);put('candidate/'+f,new[f])
v={'head':HEAD,'scope':'Only two existing files; exact-source actual lifecycle hooks; no product execution','edits':edits,'sources':[{'source':f,'before_bytes':len(old[f]),'before_sha256':sha(old[f]),'bytes':len(new[f]),'sha256':sha(new[f]),'whole_inverse_equal':True} for f in files]}
put('apply-receipt.json',(json.dumps(v,indent=2)+'\n').encode());assert all((R/f).read_bytes()==new[f] for f in files)
print(json.dumps(v['sources']))
