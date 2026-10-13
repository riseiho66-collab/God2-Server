from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server');P=Path(__file__).resolve().parent;D=P/'qualified-final'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
    p=D/p;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def js(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()
files=['src/game/Battle.h','src/game/Battle.cpp','src/game/CombatRule.h','src/game/BattleNumericProfile.h','src/game/ExtendedHealthAmount.h','src/game/ExtendedBattleDeltaAmount.h','src/game/BattleCheckpointCodec.h','src/game/BattleCheckpointCodec.cpp','src/handlers/RecoveredBattleService.h','src/handlers/RecoveredBattleService.cpp','src/handlers/OwnedTaiwanPkLuaBasicOwner.h','src/scripting/LuaEngine.cpp','scripts/gameplay/combat.lua','scripts/gameplay/combat_health64.lua','src/db/NativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.h']
snap={};manifest=[]
for f in files:
    b=(R/f).read_bytes();assert b==subprocess.check_output(['git','show',head+':'+f],cwd=R);snap[f]=b;out='whole/'+f;put(out,b)
    manifest.append({'kind':'whole','source':str(R/f),'retained':out,'bytes':len(b),'sha256':sha(b),'published_source_equal':True})
cuts=[('battle-owned-resources-and-action','src/game/Battle.h',25,104),('battle-action-rule-and-loss','src/game/Battle.cpp',140,224),('bound-skill-authorization','src/handlers/RecoveredBattleService.cpp',320,356),('bound-action-staged-checkpoint-publication','src/handlers/RecoveredBattleService.cpp',435,490),('lua-existing-health64-damage','src/scripting/LuaEngine.cpp',537,583),('checkpoint-no-status-shape','src/game/BattleCheckpointCodec.cpp',25,90)]
for name,f,lo,hi in cuts:
    b=snap[f];lines=b.splitlines(keepends=True);assert 1<=lo<=hi<=len(lines);raw=b''.join(lines[lo-1:hi]);off=sum(map(len,lines[:lo-1]));assert b[off:off+len(raw)]==raw;out='cuts/'+name+'.txt';put(out,raw)
    manifest.append({'kind':'cut','source':str(R/f),'retained':out,'first_line':lo,'last_line':hi,'source_byte_offset':off,'bytes':len(raw),'sha256':sha(raw),'whole_sha256':sha(b)})
# App is in the separately approved pending358 party change. Retain relevant unchanged gameplay cuts plus full-source hash reference, not another full copy.
f='src/core/Application.cpp';b=(R/f).read_bytes();snap[f]=b;lines=b.splitlines(keepends=True)
for name,lo,hi in [('actual-diagnostic-skill-binding',6155,6193),('actual-diagnostic-battle-bind',6328,6350),('actual-world-scheduler-no-poison-supplier',7824,7835)]:
    raw=b''.join(lines[lo-1:hi]);out='cuts/'+name+'.txt';put(out,raw);manifest.append({'kind':'cut','source':str(R/f),'retained':out,'first_line':lo,'last_line':hi,'source_byte_offset':sum(map(len,lines[:lo-1])),'bytes':len(raw),'sha256':sha(raw),'whole_sha256':sha(b),'whole_bytes':len(b),'whole_reference_only':True})
assert all((R/f).read_bytes()==b for f,b in snap.items())
js('source-manifest.json',{'head_at_capture':head,'scope':'READONLY current selected gameplay source; no native/runtime/Lua/DB/parser execution','members':manifest,'source_unchanged_at_readback':True,'bounded_no_status_scope':['BattleActor','BattleSnapshot','BattleAction','CombatRuleInput','Battle public mutation methods','selected RecoveredBattleService Policy and handle','selected checkpoint actor shape'],'credits':{'method':0,'opcode':0,'format':0,'route':0}})
v={'status':'successful_once','whole_count':sum(m['kind']=='whole' for m in manifest),'whole_bytes':sum(m['bytes'] for m in manifest if m['kind']=='whole'),'cut_count':sum(m['kind']=='cut' for m in manifest),'cut_bytes':sum(m['bytes'] for m in manifest if m['kind']=='cut')};js('capture-complete.json',v);print(json.dumps(v))
