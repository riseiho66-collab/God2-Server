from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');I=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round354-client-options-original-response-implementation');head='b6c0ec2d88c7c3f23dc2050ed21abe3c17e09650';h=lambda b:hashlib.sha256(b).hexdigest()
changes={
'src/game/OwnedClientOptions.h':[(
'''        bool pending_replay=false;
    };''',
'''        bool pending_replay=false;
        // Provisional exact original response; Queued is not Written/native ACK.
        std::optional<Session::NormalWorldResponseAttempt> response;
    };''')],
'src/core/Application.cpp':[(
'''                               !session.normal_world_initialization_current_on_game(*initialization))return;
                            const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();
                            const auto phase=session.state();''',
'''                               !session.normal_world_initialization_current_on_game(*initialization))return;
                            const auto response=session.capture_normal_world_response(*initialization);
                            if(!response)return; // No copied facade/IDs can qualify new option source.
                            const auto account=session.account_id,character=session.character_id,battle=session.battle_generation();
                            const auto phase=session.state();'''),(
'''                            const auto current=[&] {
                                return !dispatch->reentered &&
                                    session.normal_world_initialization_current_on_game(*initialization) &&''',
'''                            const auto current=[&] {
                                return !dispatch->reentered &&
                                    session.normal_world_response_callback_current(*response) &&
                                    session.normal_world_initialization_current_on_game(*initialization) &&'''),(
'''                            if(!previous && (replay || selector || before->entries.size()>=config.max_sessions))return;
                            if(replay) {''',
'''                            if(!previous && (replay || selector || before->entries.size()>=config.max_sessions))return;
                            const auto prior_response_current=[&] {
                                if(!previous || !previous->response)return true;
                                const auto status=previous->response->status();
                                if(status==Session::NormalWorldResponseStatus::Failed)return false;
                                if(status==Session::NormalWorldResponseStatus::Pending)
                                    return *previous->response==*response &&
                                        session.normal_world_response_callback_current(*previous->response);
                                // Queued known WORD may cross a genuine new/current INIT;
                                // never treat the obsolete old INIT as current or as an ACK.
                                return true;
                            };
                            if(!prior_response_current())return;
                            if(replay) {'''),(
'''                                held,session.id(),account,character,word,revision,*initialization,false});''',
'''                                held,session.id(),account,character,word,revision,*initialization,false,*response});'''),(
'''                            // All allocation/framing precedes source publication.
                            // These are pure game-owner/receipt/state fences.
                            if(!current() || owned_client_options->snapshot()!=before ||
                               !owned_client_options->publish(before,std::move(next)))return;
                            wire.swap(merged); // Ordinary returned bytes, not Written/ACK/held delivery.''',
'''                            // Stage owning state/frame/merged bytes before registration/publication.
                            // Registration may allocate and poison this shared actual callback.
                            if(!current() || !prior_response_current() || owned_client_options->snapshot()!=before)return;
                            session.expect_normal_world_response(*response,framed);
                            if(!current() || !prior_response_current() || owned_client_options->snapshot()!=before ||
                               !owned_client_options->publish(before,std::move(next)))return;
                            wire.swap(merged); // Provisional endpoint until actual original FIFO Queued.''')]
}
plans=[]
for rel,items in changes.items():
 b=(S/rel).read_bytes();assert subprocess.run(['git','show',head+':'+rel],cwd=S,stdout=subprocess.PIPE,check=True).stdout==b
 p=I/'before'/rel;assert not p.exists() or p.read_bytes()==b;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b) if not p.exists() else None
 candidate=b;exact=[]
 for old,new in items:
  candidates=[]
  for nl in ['\n','\r\n']:
   a=old.replace('\n',nl).encode();z=new.replace('\n',nl).encode()
   if candidate.count(a)==1 and (a,z) not in candidates:candidates.append((a,z))
  assert len(candidates)==1,(rel,old[:100],len(candidates))
  a,z=candidates[0];candidate=candidate.replace(a,z);exact.append({'old':a.decode(),'new':z.decode(),'count':1})
 inverse=candidate
 for x in reversed(exact):
  a=x['new'].encode();z=x['old'].encode();assert inverse.count(a)==1;inverse=inverse.replace(a,z)
 assert inverse==b
 plans.append((rel,b,candidate,{'path':rel,'before_bytes':len(b),'before_sha256':h(b),'after_bytes':len(candidate),'after_sha256':h(candidate),'inverse_whole_exact':True,'edits':exact}))
# Both plans/inverses have passed before any tracked write.
(I/'exact-edits-and-inverse.json').write_text(json.dumps([p[3] for p in plans],indent=2)+'\n',encoding='utf-8',newline='\n')
for rel,b,c,e in plans:
 assert (S/rel).read_bytes()==b;(S/rel).write_bytes(c);p=I/'candidate'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(c)
print(json.dumps({'verdict':'PASS','files':[{'path':r,'bytes':len(c),'sha256':h(c)} for r,b,c,e in plans],'tracked_edit_files':len(plans),'target_execution':False}))
