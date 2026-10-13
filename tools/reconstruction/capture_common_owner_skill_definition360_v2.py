from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round360-common-owner-skill-definition-implementation'
H=lambda b:hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def out(p,v):p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
receipt=load(D/'exact-edits-and-inverse.json');files=receipt['files'];assert len(files)==6
refs=[];current={};inverse=[]
for v in files:
 p=v['path'];b=(S/p).read_bytes();assert len(b)==v['bytes'] and H(b)==v['sha256']
 current[p]=b;q=D/'source'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 refs.append({'actual_path':str(S/p).replace('\\','/'),'retained':q.relative_to(D).as_posix(),'bytes':len(b),'sha256':H(b)})
restored=dict(current)
for v in reversed(receipt['edits']):
 p=v['path'];x,y=bytes.fromhex(v['old_hex']),bytes.fromhex(v['new_hex'])
 if y:
  assert restored[p].count(y)==1
  restored[p]=restored[p].replace(y,x)
 else:
  anchor=receipt['empty_deletion_inverse_anchor'].encode()+b'\n'
  if anchor not in restored[p]:anchor=anchor.replace(b'\n',b'\r\n')
  assert restored[p].count(anchor)==1
  restored[p]=restored[p].replace(anchor,x+anchor)
for v in files:
 p=v['path'];old=(D/'before'/p).read_bytes()
 head=subprocess.run(['git','show',receipt['baseline']+':'+p],cwd=S,capture_output=True,check=True).stdout
 assert restored[p]==old==head and len(old)==v['before_bytes'] and H(old)==v['before_sha256']
 inverse.append({'path':p,'before_bytes':len(old),'before_sha256':H(old),'whole_inverse':True})
# Every old owner-class byte is preserved except the new literal name line.
for p in ['src/game/ShunyingSanshazhan.h','src/game/ThousandBulls.h']:
 rows=[v for v in receipt['edits'] if v['path']==p];assert len(rows)==1
 e=rows[0];assert current[p].replace(bytes.fromhex(e['new_hex']),bytes.fromhex(e['old_hex']))==(D/'before'/p).read_bytes()
# Existing907 full110 source pins/provenance/string table is exactly unchanged.
p='src/db/SharedSkillDefinition.cpp';old=(D/'before'/p).read_bytes();new=current[p]
def table(b):
 start=b.index(b'const Pin pins[]={\n');end=b.index(b'\n};',start)+3
 return b[start:end]
assert table(old)==table(new)
pinlines=table(new).splitlines()[1:-1];assert len(pinlines)==907
for p in ['src/db/NativeSkillCatalog.cpp','src/scripting/LuaEngine.cpp']:
 old=(D/'before'/p).read_bytes()
 markers=[b'std::optional<NativeSkillRecord> NativeSkillCatalog::lookup(',b'std::optional<NativeSkillRecord> NativeSkillCatalog::lookup_main(',b'std::optional<NativeSkillRecord> NativeSkillCatalog::lookup_main_digest_checked('] if 'db/' in p else [b'        lua.set_function("native_skill_catalog"']
 for marker in markers:
  start=old.index(marker)
  if 'db/' in p:end=old.index(b'\n}',start)+2
  else:end=old.index(b'\n        });',start)+len(b'\n        });')
  assert old[start:end] in current[p]
# Static source recipe obligations; no C++ function is executed.
formal=new[new.index(b'std::optional<OwnerSkillRule> formal_owner_rule'):new.index(b'// Independently retained original')]
for value in [b'ShunyingSanshazhan::provisional_power_percent',b'ShunyingSanshazhan::mp_cost',
 b'ShunyingSanshazhan::max_targets',b'ThousandBulls::power_percent',
 b'ThousandBulls::mp_cost',b'ThousandBulls::max_targets',b'ShunyingSanshazhan::traditional_name',
 b'ThousandBulls::traditional_name']:assert value in formal
assert b'.authorize(' not in formal and b'.owned_action(' not in formal
assert b'BattleAction{' not in formal
assert b'if(d.profiles.empty() && d.owner_rule)d.status=SharedSkillStatus::OwnerCustom;' in new
cat=current['src/db/NativeSkillCatalog.cpp']
assert b'if(!tw && !cn && !value.definition.owner_rule){scope.finish();return std::nullopt;}' in cat
lua=current['src/scripting/LuaEngine.cpp']
assert b'"gameplay_authority",false' in lua and b'"native_source",false' in lua
assert b'result["display_name"]=d.owner_rule?d.owner_rule->traditional_name:d.name.traditional_utf8;' in lua
deps=['src/db/NativeSkillCatalog.h','src/db/NativeSkillSource.h','src/db/SqliteSupport.h',
 'src/scripting/LuaEngine.h','src/handlers/RecoveredBattleService.h','src/handlers/RecoveredBattleService.cpp',
 'src/game/Battle.h','src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.h',
 'src/cn/assets/CnSharedSkillCatalog.cpp','src/cn/world/CnPrebornSkillChoiceSource.h',
 'src/cn/world/CnPrebornSkillChoiceSource.cpp','CMakeLists.txt']
drefs=[]
for p in deps:
 b=(S/p).read_bytes();head=subprocess.run(['git','show',receipt['baseline']+':'+p],cwd=S,capture_output=True,check=True).stdout
 assert b==head,p;q=D/'dependencies'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 drefs.append({'actual_path':str(S/p).replace('\\','/'),'retained':q.relative_to(D).as_posix(),'bytes':len(b),'sha256':H(b)})
# Individually verify the already-sealed359 implementation/current definitions.
root=A/'round359-common-skill-definition-implementation';seal=root/'seal.json';sv=load(seal)
seen=set();total=0;members=[]
for m in sv['members']:
 path=m['path'];assert path and path.casefold() not in seen;seen.add(path.casefold())
 assert type(m['bytes'])==int and m['bytes']>=0
 q=(root/path).resolve();assert q.is_relative_to(root.resolve());b=q.read_bytes()
 assert len(b)==m['bytes'] and H(b)==m['sha256'];total+=len(b);members.append(m)
assert len(members)==96 and total==13637609
out(D/'source-references.json',refs);out(D/'dependency-references.json',drefs)
out(D/'final-source-manifest.json',{'files':refs,'source_count':6,'source_bytes':sum(v['bytes'] for v in refs),'existing':6,'new':0,'frozen':True})
out(D/'whole-inverse-and-frozen-proof.json',{'baseline':receipt['baseline'],'six_whole_inverses':inverse,'new_files':0,'907_pin_table_bytes':len(table(new)),'907_pin_table_sha256':H(table(new)),'907_pin_table_exact':True,'class_methods_names_only':True,'native_getter_exact':True,'CN_original453_gate_frozen':True,'frozen_dependency_count':len(drefs),'no_product_execution':True})
out(D/'prior359-individual-readback.json',{'root':str(root).replace('\\','/'),'seal_sha256':H(seal.read_bytes()),'member_count':len(members),'member_bytes':total,'members':members})
report='''Common owner-skill definition360: PHASE1 static source PASS.

The actual shared getter now returns formal existing owner specifications for kind0/id126 CUSTOM-0058 and kind0/id150 CUSTOM-0059 even when both original TW448 and CN453 raw rows are missing. requested_native remains absent; profiles, chosen native profile, source provenance and native text projections stay empty. Other validated missing keys still return null. Invalid selectors/corrupt matched rows retain existing joined-reader errors. No native110 row or native-loaded source is manufactured.

OwnerSkillRule is an owning value. Power, MP cost, target limit, design ID and key refer directly to ShunyingSanshazhan/ThousandBulls constants. The targeting flag describes the existing finite explicit-target versus all-living-opponents authorize contract. No numeric gameplay coefficients/costs are copied into a second rule implementation; no authorize, owned_action, BattleAction default, casting, learning or policy-install call is added. Existing Shunying authorize continues to stage the caller-supplied qualified blade3 action. Existing ThousandBulls authorize, visual cloning, direction, trial and four-phase presentation behavior are unchanged. Only constexpr Traditional name metadata is added to the two classes.

The resolver attaches this formal owner specification independently of raw profiles. Present bindings retain all raw/source/status/qualification and the907 full110 pin table exactly. Unknown raw profiles are never promoted by owner_rule presence. OwnerCustom status for an empty-profile definition explicitly means a formal owner specification exists; it does not mean an original native row was observed. The owning value exposes the current formal constants, not a live installed Policy or permission capability.

The same existing Main Lua common_skill_definition getter exports owner_rule and a separate display_name, including Traditional owner names, with gameplay_authority=false and native_source=false. It does not invent CP950/CP936 bytes, native offsets, UI fields or a chosen raw profile. Existing native getter, Main constructor, CN original-provider/current gates, handlers, configuration, protocol/model/native resources and BattlePolicy paths are unchanged.

All six whole-file inverses restore exact published a4ca93050ec0416325b3d83abf54552a9f244af3 bytes. Existing owner-class methods are exact after removing only the new name lines. The full907 pinned source table is byte-identical. Thirteen frozen dependency files were compared to that HEAD, and all96 members/13,637,609 bytes of the previous359 implementation package were individually verified in place. The executed apply helper is retained exactly, including its historical two-final-LF convention; it was not rerun or normalized. Final capture/seal helpers use one final LF/no BOM.

No C++/native/API/codec/parser/VM/CRT execution, build, test, SQL/database operation, import/migration, client-resource modification, activation or deployment occurred. This closes a real common-definition getter gap and supplies formal owner metadata. It does not grant or install the skills, qualify a CN custom client profile, prove native Current/HP/effect/learning acceptance, implement missing native formulas or complete a gameplay route.
'''
(D/'REPORT.md').write_text(report,encoding='utf-8',newline='\n')
meta=load(D/'successful-LF-helper-metadata.json');p=D/'capture_common_owner_skill_definition360_v2.py';b=p.read_bytes()
assert b.endswith(b'\n') and not b.endswith(b'\n\n') and b'\r\n' not in b and not b.startswith(b'\xef\xbb\xbf')
meta.append({'path':p.name,'actual_executed_path':str(p).replace('\\','/'),'bytes':len(b),'sha256':H(b),'successful_execution_count':1,'LF_no_BOM':True,'single_final_LF':True})
out(D/'successful-LF-helper-metadata.json',meta)
out(D/'PASS.json',{'status':'PASS','static_only':True,'source_count':6,'source_bytes':sum(v['bytes'] for v in refs),'six_whole_inverse':True,'new_files':0,'907_pins_unchanged':True,'formal_owner_keys':[126,150],'native_profile_manufacturing':False,'gameplay_authority':False,'no_target_execution':True})
for v in refs:
 b=Path(v['actual_path']).read_bytes();assert len(b)==v['bytes'] and H(b)==v['sha256']
print(json.dumps({'status':'PASS','source_count':6,'source_bytes':sum(v['bytes'] for v in refs),'prior_members':len(members),'prior_bytes':total,'pin_table_bytes':len(table(new)),'REPORT_bytes':(D/'REPORT.md').stat().st_size,'REPORT_sha256':H((D/'REPORT.md').read_bytes())}))
