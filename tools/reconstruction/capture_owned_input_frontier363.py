from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent;S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=D.parent;HEAD='566923291db5de40dcc7d1a153cde60cfc94d87c'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=S).decode().strip()==HEAD
paths=['src/net/Session.h','src/net/Session.cpp','src/protocol/RecoveredWorldFrame.h','src/protocol/RecoveredWorldRecords.h','src/protocol/RecoveredSkillCommand.h','src/protocol/TaiwanNativeSkillCommand.h'];sources={}
for path in paths+['src/core/Application.cpp']:
 b=(S/path).read_bytes();assert b==subprocess.check_output(['git','show',HEAD+':'+path],cwd=S);sources[path]=b
# Strict per-member upstream verification; no rerun or derived memory-map pairing.
U=A/'round362-cn-custom-skill-action-state-source';sb=(U/'seal.json').read_bytes();assert sha(sb)=='908e600e85b79a696b2045997bfd786b1d2be0db6e5c25b6a1a3750db5bf000c';v=json.loads(sb);rows=[]
for m in v['members']:
 b=(U/m['path']).read_bytes();assert type(m['bytes']) is int and len(b)==m['bytes'] and sha(b)==m['sha256'];rows.append(m)
assert len(rows)==17 and sum(m['bytes'] for m in rows)==78839;out('upstream362-individual-verification.json',dict(root=U.as_posix(),seal_sha256=sha(sb),member_count=17,member_bytes=78839,members=rows))
refs=[]
for path in paths:
 b=sources[path];rel='whole/'+path;put(rel,b);refs.append(dict(actual_path=(S/path).as_posix(),retained=rel,bytes=len(b),sha256=sha(b)))
out('source-references.json',refs)
cuts=[]
def lines(path,lo,hi,name):
 b=sources[path];ll=b.splitlines(keepends=True);assert 1<=lo<=hi<=len(ll);part=b''.join(ll[lo-1:hi]);rel='cuts/'+name;put(rel,part);cuts.append(dict(actual_path=(S/path).as_posix(),source_file_bytes=len(b),source_file_sha256=sha(b),start_line=lo,end_line_inclusive=hi,retained=rel,bytes=len(part),sha256=sha(part),whole_function_claim=False))
for lo,hi,name in [(448,603,'pending-identities-read-and-write-state.cpp.txt'),(759,852,'native-battle-source-completion-release.cpp.txt'),(1072,1110,'actual-read-inflight-completion.cpp.txt'),(1948,2149,'resume-feed-framing-sequence.cpp.txt'),(2150,2338,'actual-game-callback-and-original-response-FIFO.cpp.txt'),(2373,2538,'actual-async-write-close-fail.cpp.txt'),(2539,2565,'disconnect-game-owner-handoff.cpp.txt'),(3139,3218,'native-battle-genuine-common-sender.cpp.txt'),(3696,3708,'phase-and-battle-generation.cpp.txt')]:lines('src/net/Session.cpp',lo,hi,name)
# Actual owned bootstrap only; full Application is hash-referenced in place, not falsely labelled a whole retained file.
app=sources['src/core/Application.cpp'];ll=app.splitlines(keepends=True);lo=next(i+1 for i,l in enumerate(ll) if b'DIAGNOSTIC_TIMER36_ACCEPTED' in l);hi=next(i+1 for i,l in enumerate(ll) if i+1>lo and b'return std::optional<std::vector<std::uint8_t>>(RecoveredWorldFrame::encode(vitals));' in l);lines('src/core/Application.cpp',lo,hi,'actual-owned-bootstrap-producer-excerpt.cpp.txt');out('Application-full-hash-reference-only.json',dict(actual_path=(S/'src/core/Application.cpp').as_posix(),bytes=len(app),sha256=sha(app),fullfile_retained=False,excerpt_start_line=lo,excerpt_end_line=hi))
out('source-excerpts.json',cuts)
cpp=sources['src/net/Session.cpp'];h=sources['src/net/Session.h']
for token in [b'if(native_battle_pending.load()) {native_battle_read_paused=true;stage_native_pk_output();return;}',b's.native_battle_read_paused && !s.game_busy && !s.read_inflight',b'if(bytes.size()>16384-world_input.size())',b'if(records.size()>8192)',b'skill_sequence_timeout = std::chrono::seconds(5)',b'pending->common->generation==delivery.common_generation',b'if(!s.world_input.empty() || !s.world_pending_records.empty() ||',b'impl_->native_battle_pending.compare_exchange_strong(absent,pending)']:assert token in cpp,token
assert b'max_sequence_records = 14' in sources['src/protocol/RecoveredSkillCommand.h'];assert b'max_logical_size=0xa00' in sources['src/protocol/RecoveredWorldFrame.h'];assert b'record.opcode!=0x87 && record.opcode!=0x38' in cpp
assert b'owned_bootstrap_write.emplace(session.observe_world_response(*owned_bootstrap_wire));' in app and b'if(owned_bootstrap_wire)return std::optional<std::vector<std::uint8_t>>(std::move(*owned_bootstrap_wire));' in app
assert b'send_native_battle_skill_publication(' not in app
for m in refs:
 assert (D/m['retained']).read_bytes()==(Path(m['actual_path'])).read_bytes()
assert app==(S/'src/core/Application.cpp').read_bytes()
out('capture-complete.json',dict(verdict='PASS bounded source frontier',head=HEAD,whole_sources=6,whole_bytes=sum(m['bytes'] for m in refs),excerpts=len(cuts),actual_owned_bootstrap_excerpt=True,Application_full_retained=False,existing_NativeBattle_sender_distinct=True,new_native_method_credit=0,new_route_credit=0,tracked_edits=0,product_execution=0,successful_execution_count=1))
print(json.dumps(dict(whole_sources=6,whole_bytes=sum(m['bytes'] for m in refs),excerpts=len(cuts),App_excerpt_lines=[lo,hi])))
