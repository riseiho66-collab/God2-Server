from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round365-tw-command-common-definition-implementation';HEAD='5a21cb97abb20c40080d4bf6be1a67cc4a071278';H=lambda b:hashlib.sha256(b).hexdigest()
def save(p,b):
 q=D/p;assert not q.exists(),str(q);q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(b)
def js(p,x):save(p,(json.dumps(x,indent=2)+'\n').encode())
assert not(D/'capture-success.json').exists() and not(D/'seal.json').exists()
pins=json.loads((D/'final-current-pins.json').read_bytes());edits=json.loads((D/'exact-edits-and-inverse.json').read_bytes())['edits'];assert len(pins)==2 and len(edits)==6
refs=[];inverses=[]
for pin in pins:
 p=pin['path'];b=(S/p).read_bytes();assert len(b)==pin['bytes'] and H(b)==pin['sha256'] and b==(D/'candidate'/p).read_bytes();old=b
 for e in reversed(edits):
  if e['path']!=p:continue
  assert type(e.get('count',1)) is int and e.get('count',1)==1
  x,y=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex']);assert x and y and old.count(y)==1;old=old.replace(y,x,1)
 assert old==(D/'before'/p).read_bytes()==subprocess.check_output(['git','show',HEAD+':'+p],cwd=S)
 q='final/'+p;save(q,b);refs.append(dict(actual_path=(S/p).as_posix(),retained=q,bytes=len(b),sha256=H(b)));inverses.append(dict(path=p,whole_inverse=True,baseline_bytes=len(old),baseline_sha256=H(old)))
deps=['src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp','src/db/NativeSkillSource.h','src/protocol/TaiwanNativeSkillCommand.h','src/game/SharedTaiwanIssuedSkillSource.h','src/game/SharedTaiwanIssuedSkillSource.cpp','src/game/SharedTaiwanWorldRecordSource.h','src/game/SharedTaiwanWorldRecordSource.cpp','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp','src/core/SharedTaiwanNativeWorldHostPlan.h','src/core/SharedTaiwanNativeWorldHostPlan.cpp','src/core/SharedWorldHostPlan.h','src/core/Application.cpp','src/main.cpp','src/net/Session.h','src/net/Session.cpp']
for p in deps:
 b=(S/p).read_bytes();assert b==subprocess.check_output(['git','show',HEAD+':'+p],cwd=S),p
 q='dependencies/'+p;save(q,b);refs.append(dict(actual_path=(S/p).as_posix(),retained=q,bytes=len(b),sha256=H(b)))
hm=[]
for n in ['apply_tw_command_common_definition365.py','capture_tw_command_common_definition365.py','seal_tw_command_common_definition365.py']:
 b=(A/n).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n')
 if(D/n).exists():assert (D/n).read_bytes()==b
 else:save(n,b)
 hm.append(dict(actual_path=(A/n).as_posix(),retained=n,bytes=len(b),sha256=H(b),successful_execution_count=1,public_copy=not n.startswith('apply_')))
U=A/'round365-tw-command-common-definition-authority';sb=(U/'seal.json').read_bytes();assert H(sb)=='9dbc6558e6cdd72630e90c1fef9201218967e8ce85e05216882f9016ce05b2e0';meta=json.loads(sb);seen=set();total=0
for m in meta['members']:
 assert type(m['bytes']) is int and m['bytes']>=0;p=(U/m['path']).resolve();assert p.is_relative_to(U.resolve()) and not p.is_symlink();assert m['path'].casefold() not in seen;seen.add(m['path'].casefold());b=p.read_bytes();assert len(b)==m['bytes'] and H(b)==m['sha256'];total+=len(b)
assert len(seen)==meta['member_count']==30 and total==meta['member_bytes']==1024675
save('upstream/authority-seal.json',sb);js('upstream-individual-verification.json',dict(actual_path=U.as_posix(),seal_sha256=H(sb),member_count=len(seen),member_bytes=total,members=meta['members'],all_individual_verified=True))
cs=[(pins[0]['path'],'    struct Scope {','    enum class Check'),(pins[0]['path'],'    class WorldOwner {','    // Construct inside'),(pins[1]['path'],'    bool base_definition_current(', '    bool complete_reply('),(pins[1]['path'],'    std::optional<Source::Reply> dispatch(', '    void release('),('src/db/NativeSkillCatalog.cpp','std::optional<SharedSkillLookup> NativeSkillCatalog::lookup_shared_definition_main(', 'std::optional<NativeSkillSource>'),('src/game/SharedTaiwanIssuedSkillSource.cpp','std::optional<SharedTaiwanIssuedSkillSource::Selection> SharedTaiwanIssuedSkillSource::select(', 'void SharedTaiwanIssuedSkillSource::release('),('src/core/SharedTaiwanNativeWorldHostPlan.cpp','SharedTaiwanNativeWorldHostPlan::RecordSources SharedTaiwanNativeWorldHostPlan::RecordSources::with_native_skills(', 'SharedTaiwanNativeWorldHostPlan::RecordSources SharedTaiwanNativeWorldHostPlan::RecordSources::with_native_chat(')]
cuts=[]
for n,(p,start,end) in enumerate(cs):
 b=(S/p).read_bytes();x,y=start.encode(),end.encode();assert b.count(x)==b.count(y)==1;i=b.index(x);j=b.index(y,i);v=b[i:j];q='cuts/'+str(n).zfill(2)+'-'+Path(p).name+'.txt';save(q,v);cuts.append(dict(source=p,byte_offset=i,bytes=len(v),first_line=b[:i].count(b'\n')+1,last_line=b[:j].count(b'\n'),retained=q,sha256=H(v)))
js('source-references.json',refs);js('source-cuts.json',cuts);js('helper-metadata.json',hm);js('whole-inverse-verification.json',dict(baseline=HEAD,chronological_edits=6,files=inverses))
js('manual-invariants.json',dict(status='PASS_SOURCE_ONLY',same_scope_four_worldowner_callbacks=True,mandatory_common_rejects_absence=True,initial_base_gate_separate=True,exact_requested_tw_not_chosen_regional_raw=True,whole_common_snapshot_equal_no_rebase=True,original_digest_image_issued_gates_retained=True,no_old_query_after_action=True,three_field_aggregate_default_tail=True,virtual_signatures_unchanged=True,original_grammar_actor_side_reply_budgets_preserved=True,actual_host_installation_still_requires_worldowner=True,atomic_cross_source_CAS=False,grant_or_formula_recovery=False,host_or_full_route_credit=0,no_product_execution=True))
report='''# Round365 TW command common-definition handoff

PASS, bounded PHASE1 source integration. Exactly SharedTaiwanNativeSkillCommandSource.h/.cpp changed. Six chronological literal edits restore both whole files to published5a21cb97abb20c40080d4bf6be1a67cc4a071278. Initial before/candidate and apply helper remain immutable custody. No new C++ file, virtual callback signature, protocol, client asset or native row was added. No C++/native/API/parser/codec/SQL/compiler/test execution occurred.

Scope appends an owning optional SharedSkillDefinition with an empty default, preserving existing three-field aggregate construction. Initial base_definition_current keeps actual TW digest-checked/image/issued/ready gates independent of the mandatory enriched Current. The existing same-reader shared lookup must return exactly the requested TW NativeSkillRecord, matching both retained digest observation and private issued selection. A chosen CN profile never replaces native TW command input. Captured presence/position/battle generation remains fixed while only common metadata is attached.

Before qualification and at both original pre-action Current cuts, mandatory definition_current rechecks the original TW digest record plus complete shared definition equality against the retained Scope. Empty common cannot pass. Reobservation compares rather than replacing/rebasing the value. Actual WorldOwner qualification/current/action/after_action all receive the same local owning Scope under their existing const-reference contracts; borrowed arguments may not escape callbacks. The catalog and presence owners still must outlive the owner/game drain. Existing caught-reentry invalidation, sequence/grammar/actor/side, issued-model gates and complete-reply budgets remain.

After action the old definition/grant/resource source is not queried. Existing actual next-receipt after_action, ready(false), complete envelope and durable-prefix no rollback/no retry contracts remain exact. SourceCurrent cuts are sequential observer checks, not an atomic multi-catalog CAS. Actual WorldOwner must still supply genuine learned/control/grant/MP/target/rules/once settlement and complete reply; common definition is metadata, not permission or recovered formula.

The actual installation remains explicit SharedTaiwanNativeWorldHostPlan::RecordSources::with_native_skills and requires a concrete WorldOwner; ordinary Main hosting is not made complete. Missing original TW raw rows still fail initial digest/issued gates, even when the common registry owns formal126/150 metadata. No originalCN453 custom row, native list adoption, learning/casting grant, balance formula or full route is fabricated. Hosting/full-route credit remains0.
'''
save('REPORT.md',report.encode());js('capture-success.json',dict(status='PASS',successful_execution_count=1,source_refs=len(refs),source_bytes=sum(r['bytes'] for r in refs),current_existing_files=2,dependency_files=len(deps),chronological_edits=6,no_product_execution=True))
print(json.dumps(dict(status='PASS',source_refs=len(refs),source_bytes=sum(r['bytes'] for r in refs),final_pins=pins,upstream_members=len(seen),upstream_bytes=total)))
