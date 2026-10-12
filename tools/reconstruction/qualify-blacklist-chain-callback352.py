from pathlib import Path
import json,hashlib
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round352-blacklist-submitted-chain-host-implementation';p=S/'src/core/Application.cpp';b=p.read_bytes();v=b;edits=[]
def replace(old,new):
 global v
 old=old.encode();new=new.encode();assert v.count(old)==1,(old[:80],v.count(old));v=v.replace(old,new,1);edits.append(dict(old=old.decode(),new=new.decode()))
replace('''                        const auto held=session.shared_from_this();
                        settle_blacklist_output(held);
''','''                        const auto held=session.shared_from_this();
                        std::optional<Session::NormalWorldInitialization> blacklist_invocation;
                        try {blacklist_invocation=session.normal_world_initialization();}
                        catch(const std::logic_error&) {} // A copied dispatcher facade cannot mint live submitted source.
                        const auto blacklist_invocation_current=[&] {
                            return blacklist_invocation && session.normal_world_initialization_current(*blacklist_invocation);
                        };
                        settle_blacklist_output(held);
''')
replace('''                                    if(!blacklist_chain_current(held,source))return {};
''','''                                    if(source.live_pending && !blacklist_invocation_current()) {
                                        auto& now=blacklist_replays.at(session.id());now.live_disabled=true;
                                        retire_blacklist_output(now);session.close();return {};
                                    }
                                    if(!blacklist_chain_current(held,source))return {};
''')
replace('''                                            blacklist_chain_current(held,now);
''','''                                            (!now.live_pending || blacklist_invocation_current()) && blacklist_chain_current(held,now);
''')
replace('''                                    if(*source.snapshot!=*before) {
''','''                                    if(!blacklist_invocation_current() || *source.snapshot!=*before) {
''')
replace('''                                    if(!change->changed()){++i;continue;}
''','''                                    if(!change->changed() || !blacklist_invocation_current()){++i;continue;}
''')
replace('''                                               !peer.session->normal_world_output_current_on_game(*delivery->output))
''','''                                               !blacklist_chain_current(peer.session,posted->second) ||
                                               !peer.session->normal_world_output_current_on_game(*delivery->output))
''')
inverse=v
for e in reversed(edits):
 old=e['old'].encode();new=e['new'].encode();assert inverse.count(new)==1;inverse=inverse.replace(new,old,1)
assert inverse==b
def put(name,data):
 with (D/name).open('xb') as f:f.write(data)
put('Application.before-callback-qualification.cpp',b);put('Application.callback-qualified.cpp',v)
put('callback-qualification-correction.json',(json.dumps(dict(before_bytes=len(b),before_sha256=hashlib.sha256(b).hexdigest(),after_bytes=len(v),after_sha256=hashlib.sha256(v).hexdigest(),exact_inverse=True,edits=edits),indent=2)+'\n').encode())
assert p.read_bytes()==b;p.write_bytes(v)
print(json.dumps(dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest(),exact_inverse=True)))
