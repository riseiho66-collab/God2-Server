from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');I=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round354-client-options-original-response-implementation');P=I.parent/'round354-normal-control-response-custody-proposal';head='b6c0ec2d88c7c3f23dc2050ed21abe3c17e09650';h=lambda b:hashlib.sha256(b).hexdigest()
def put(rel,b):
 p=I/rel;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def jout(rel,o):put(rel,(json.dumps(o,indent=2)+'\n').encode())
proof=[];refs=[];whole={}
for x in json.loads((I/'exact-edits-and-inverse.json').read_text()):
 rel=x['path'];b=(S/rel).read_bytes();old=(I/'before'/rel).read_bytes();assert b==(I/'candidate'/rel).read_bytes() and len(b)==x['after_bytes'] and h(b)==x['after_sha256'];assert len(old)==x['before_bytes'] and h(old)==x['before_sha256'];assert subprocess.run(['git','show',head+':'+rel],cwd=S,stdout=subprocess.PIPE,check=True).stdout==old
 inverse=b
 for e in reversed(x['edits']):
  a=e['new'].encode();z=e['old'].encode();assert inverse.count(a)==e['count'];inverse=inverse.replace(a,z)
 assert inverse==old;whole[rel]=b;put('final/'+rel,b);refs.append({'actual_path':str(S/rel),'retained':'final/'+rel,'bytes':len(b),'sha256':h(b)});proof.append({'path':rel,'current_candidate_exact':True,'whole_git_before_exact':True,'whole_literal_inverse_exact':True})
# All individually sealed proposal members are retained immutable in place.
seal=json.loads((P/'seal.json').read_text());assert len(seal['members'])==seal['member_count'];assert sum(r['bytes'] for r in seal['members'])==seal['member_bytes']
for r in seal['members']:
 b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
jout('proposal-custody.json',{'path':str(P),'seal_sha256':h((P/'seal.json').read_bytes()),'members':seal['member_count'],'member_bytes':seal['member_bytes'],'individual_member_verified':True})
put('source-references.json',(json.dumps(refs,indent=2)+'\n').encode())
deps=[]
for rel in ['src/net/Session.h','src/net/Session.cpp','src/core/Config.h','src/core/Config.cpp','src/protocol/TaiwanNativeClientOptions.h']:
 b=(S/rel).read_bytes();assert subprocess.run(['git','show',head+':'+rel],cwd=S,stdout=subprocess.PIPE,check=True).stdout==b;put('dependencies/'+rel,b);deps.append({'actual_path':str(S/rel),'retained':'dependencies/'+rel,'bytes':len(b),'sha256':h(b),'unchanged_head':head});whole[rel]=b
jout('dependency-source-references.json',deps)
cuts=[]
for rel,start,end,label in [('src/core/Application.cpp','                // CUSTOM-0100 wraps the FINAL TW handler.','                if(whole_bag_moves) {','actual-options-wrapper'),('src/game/OwnedClientOptions.h','    struct Entry {','    struct State {','actual-options-entry'),('src/game/OwnedClientOptions.h','    void disconnect(','private:','unchanged-ready-disconnect'),('src/net/Session.cpp','std::optional<Session::NormalWorldResponseAttempt> Session::capture_normal_world_response(','void Session::send_world_records_impl(','existing-own-response-apis')]:
 b=whole[rel];a=b.index(start.encode());z=b.index(end.encode(),a);c=b[a:z];put('cuts/'+label+'.source',c);cuts.append({'source':rel,'retained':'cuts/'+label+'.source','source_sha256':h(b),'start_byte':a,'end_byte_exclusive':z,'bytes':len(c),'sha256':h(c),'whole_method_claim':False})
# The owner-only addition leaves all old ready/disconnect bytes exact.
old=(I/'before/src/game/OwnedClientOptions.h').read_bytes();new=whole['src/game/OwnedClientOptions.h'];a=b'    void disconnect(';assert old[old.index(a):]==new[new.index(a):]
jout('source-cuts.json',cuts)
jout('static-source-proof.json',{'verdict':'PASS','implementation_files':proof,'canonical_current_refs':len(refs),'canonical_current_bytes':sum(r['bytes'] for r in refs),'unchanged_dependencies':len(deps),'ready_disconnect_exact':True,'current_session_transport_unchanged':True,'source_target_executed':False,'db_sql_executed':False,'compiler_build_test_executed':False})
for r in refs+deps:assert Path(r['actual_path']).read_bytes()==(I/r['retained']).read_bytes()
print(json.dumps({'verdict':'PASS','current_refs':len(refs),'current_bytes':sum(r['bytes'] for r in refs),'unchanged_dependencies':len(deps),'dependency_bytes':sum(r['bytes'] for r in deps),'cuts':len(cuts),'proposal_members_individually_verified':seal['member_count']}))
