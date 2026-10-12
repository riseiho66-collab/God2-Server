from pathlib import Path
import hashlib,json
R=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
pins={'src/net/Session.h':'dd17d494ca20ded3667d71e929a833dd306242b4fb36b169958d932dafdb9de8','src/net/Session.cpp':'93ca71787d3c0a4eb3d5113809d1d5220f3ff34a3e91df68d7ba201933a72849','src/core/Application.cpp':'c2653e3d211c21f33715ac14ebe1814d2dddb626f50b1be6dcb092896412f1e0'}
before={f:(R/f).read_bytes() for f in pins};after=dict(before);edits=[]
for f,h in pins.items():assert sha(before[f])==h
def edit(f,o,n,count=1):
    o=o.encode();n=n.encode();assert after[f].count(o)==count
    after[f]=after[f].replace(o,n);edits.append({'source':f,'before_hex':o.hex(),'after_hex':n.hex(),'count':count})
edit('src/net/Session.h','    bool normal_world_callback_admission_current_on_game(const NormalWorldCallbackAdmission&) const;\n','    bool normal_world_callback_admission_current_on_game(const NormalWorldCallbackAdmission&) const;\n    // Exact active callback membership only, independent of status/owner currentness.\n    bool normal_world_callback_admission_callback_current_on_game(const NormalWorldCallbackAdmission&) const noexcept;\n')
edit('src/net/Session.cpp','bool Session::normal_world_callback_admission_current_on_game(const NormalWorldCallbackAdmission& admission) const {\n','bool Session::normal_world_callback_admission_callback_current_on_game(const NormalWorldCallbackAdmission& admission) const noexcept {\n    const auto& data=admission.data_;\n    if(!data || data->game_thread!=std::this_thread::get_id() || observed_world_callback!=this)return false;\n    const auto& capture=impl_->normal_callback_admission_capture;\n    return capture && capture->receipt==data && observed_callback_admission_status==&data->status;\n}\nbool Session::normal_world_callback_admission_current_on_game(const NormalWorldCallbackAdmission& admission) const {\n')
old='                        struct Reading {DirectoryDispatch& state;explicit Reading(DirectoryDispatch& s):state(s){state.reading=true;state.reentered=false;state.committed_preview=false;state.admission.reset();}~Reading(){state.admission.reset();state.committed_preview=false;state.reading=false;}} reading(*dispatch);\n'
assert after['src/core/Application.cpp'].count(old.encode())==2
retire='                        struct Reading {\n                            DirectoryDispatch& state;\n                            Reading(DirectoryDispatch& s,Session& session):state(s){\n                                if(state.admission && session.normal_world_callback_admission_callback_current_on_game(*state.admission))state.reject_admission();\n                                state.admission.reset();state.committed_preview=false;\n                                state.reading=true;state.reentered=false;\n                            }\n                            ~Reading(){state.reading=false;}\n                        } reading(*dispatch,session);\n'
records='                        struct Reading {\n                            DirectoryDispatch& state;\n                            Reading(DirectoryDispatch& s,Session& session):state(s){\n                                // Options can split one actual callback into several Directory runs.\n                                if(!state.admission || !session.normal_world_callback_admission_callback_current_on_game(*state.admission)) {\n                                    state.admission.reset();state.committed_preview=false;\n                                }\n                                state.reading=true;state.reentered=false;\n                            }\n                            ~Reading(){state.reading=false;}\n                        } reading(*dispatch,session);\n'
# Distinct enclosing contexts ensure the identical old Reading line is not guessed.
edit('src/core/Application.cpp',old+'                        if(!reconcile(&session,nullptr,nullptr))owned_party_directory->disconnect(session);\n',retire+'                        if(!reconcile(&session,nullptr,nullptr))owned_party_directory->disconnect(session);\n')
edit('src/core/Application.cpp',old+'                        const auto self=session.shared_from_this();std::vector<std::uint8_t> wire;\n',records+'                        const auto self=session.shared_from_this();std::vector<std::uint8_t> wire;\n')
for e in reversed(edits):
    f=e['source'];o=bytes.fromhex(e['before_hex']);n=bytes.fromhex(e['after_hex']);assert after[f].count(n)==e['count'];after[f]=after[f].replace(n,o)
assert after==before
# Reapply only the proven source substitutions, then preflight all outputs before writes.
for e in edits:
    f=e['source'];after[f]=after[f].replace(bytes.fromhex(e['before_hex']),bytes.fromhex(e['after_hex']))
assert all((R/f).read_bytes()==before[f] for f in pins)
for f in pins:assert not (D/'split-corrected'/f).exists()
for f in pins:
    (R/f).write_bytes(after[f]);p=D/'split-corrected'/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(after[f])
receipt={'scope':'Exact same actual callback prefix retained across Options split Directory runs; retirement rejects bounded alias; no status/owner-current inference','edits':edits,'inverse_equal':True,'sources':[{ 'source':f,'before_bytes':len(before[f]),'before_sha256':sha(before[f]),'bytes':len(after[f]),'sha256':sha(after[f])} for f in pins]}
(D/'split-correction-receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps(receipt['sources']))
