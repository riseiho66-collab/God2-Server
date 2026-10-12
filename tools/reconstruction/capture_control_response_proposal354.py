from pathlib import Path
import hashlib,json,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round354-normal-control-response-custody-proposal')
head='b6c0ec2d88c7c3f23dc2050ed21abe3c17e09650';h=lambda b:hashlib.sha256(b).hexdigest()
refs=[];whole={}
for rel in ['src/core/Application.cpp','src/net/Session.h','src/net/Session.cpp','src/game/OwnedClientOptions.h','src/protocol/TaiwanNativeClientOptions.h','src/core/Config.h','src/core/Config.cpp','src/handlers/RecoveredBattleService.cpp','src/handlers/RecoveredWorldService.cpp','src/protocol/RecoveredWorldRecords.h']:
 b=subprocess.run(['git','show',head+':'+rel],cwd=S,stdout=subprocess.PIPE,check=True).stdout;assert (S/rel).read_bytes()==b
 p=O/'before'/rel;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);whole[rel]=b
 refs.append({'actual_path':str(S/rel),'retained':'before/'+rel,'bytes':len(b),'sha256':h(b),'head':head})
(O/'source-references.json').write_text(json.dumps(refs,indent=2)+'\n',encoding='utf-8',newline='\n')
cuts=[]
for rel,lo,hi,label in [('src/core/Application.cpp',7410,7514,'actual-options-owner-and-component-publication'),('src/core/Application.cpp',6896,6924,'non-tick-retire-and-postbattle-replay'),('src/core/Config.h',120,127,'default-off-configuration'),('src/core/Config.cpp',664,671,'load-prerequisite'),('src/net/Session.cpp',154,180,'actual-entry-and-effective-battle-data'),('src/net/Session.cpp',332,351,'armed-response-raii'),('src/net/Session.cpp',489,526,'private-sync-and-peer-own-guards'),('src/net/Session.cpp',2195,2261,'actual-final-original-response-fifo-post'),('src/net/Session.cpp',2596,2637,'own-init-and-current-source'),('src/net/Session.cpp',2704,2761,'actual353-own-response-api'),('src/net/Session.cpp',3324,3364,'return-preparation-no-publication'),('src/net/Session.cpp',3592,3603,'phase-retirement'),('src/handlers/RecoveredBattleService.cpp',605,615,'diagnostic-return-state-only')]:
 b=b''.join(whole[rel].splitlines(keepends=True)[lo-1:hi]);p=O/'cuts'/f'{label}.source';assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);cuts.append({'source':rel,'start_line':lo,'end_line':hi,'retained':p.relative_to(O).as_posix(),'bytes':len(b),'sha256':h(b),'whole_method_claim':False})
(O/'selected-source-cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'head':head,'refs':len(refs),'bytes':sum(r['bytes'] for r in refs),'selected_cuts':len(cuts),'tracked_mutation':False,'target_execution':False}))
