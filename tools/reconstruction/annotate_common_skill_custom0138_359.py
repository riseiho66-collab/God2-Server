from pathlib import Path
import json,hashlib
S=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round359-common-skill-definition-implementation')
p='src/db/SharedSkillDefinition.cpp';b=(S/p).read_bytes()
x=b'    const bool tp=t && pinned(d.profiles[*t]),cp=c && pinned(d.profiles[*c]);\n'
y=x+b'    // CUSTOM-0138: owner complete-source/TW-preferred common composition,\n    // not a recovered formula, native permission or learned-skill grant.\n'
assert b.count(x)==1;n=b.replace(x,y);assert n.count(y)==1 and n.replace(y,x)==b
q=D/'before-custom0138-comment'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
(S/p).write_bytes(n)
q=D/'custom0138-comment-candidate'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(n)
(D/'custom0138-comment-correction.json').write_text(json.dumps({'successful_execution_count':1,'path':p,'old_hex':x.hex(),'new_hex':y.hex(),'before_bytes':len(b),'before_sha256':hashlib.sha256(b).hexdigest(),'bytes':len(n),'sha256':hashlib.sha256(n).hexdigest(),'inverse':True,'scope':'Root-assigned searchable CUSTOM-0138 owner policy annotation only'},indent=2)+'\n',encoding='utf-8')
pins=[]
for e in json.loads((D/'apply-success.json').read_text())['files']:
 q=S/e['path'];v=q.read_bytes();pins.append({'path':e['path'],'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()})
(D/'final-candidate-current-pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','CPP_bytes':len(n),'CPP_sha256':hashlib.sha256(n).hexdigest(),'final_pins':len(pins)}))

