from pathlib import Path
import hashlib,json
S=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round359-common-skill-definition-implementation')
p='src/db/SharedSkillDefinition.cpp';b=(S/p).read_bytes()
x=b'    if(kind>3 || !id)throw std::invalid_argument("Invalid shared skill selector");\n'
y=x+b'    if((tw && tw->region!=SharedSkillRegion::Taiwan) ||\n       (cn && cn->region!=SharedSkillRegion::China))\n        throw std::invalid_argument("Shared skill positional region mismatch");\n'
assert b.count(x)==1;n=b.replace(x,y);assert n.count(y)==1 and n.replace(y,x)==b
q=D/'before-positional-region-correction'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
(S/p).write_bytes(n)
q=D/'positional-region-corrected-candidate'/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(n)
(D/'positional-region-correction.json').write_text(json.dumps({'successful_execution_count':1,'path':p,'old_hex':x.hex(),'new_hex':y.hex(),'before_bytes':len(b),'before_sha256':hashlib.sha256(b).hexdigest(),'bytes':len(n),'sha256':hashlib.sha256(n).hexdigest(),'inverse':True,'scope':'Pure public Taiwan/China argument-position contract; no private Current/authority'},indent=2)+'\n',encoding='utf-8')
# Actual byte conventions, not a guessed single convention. Record the exact
# source baseline and inserted body captured by the successful apply receipt.
p2='src/cn/assets/CnSharedSkillCatalog.cpp';old=(D/'before'/p2).read_bytes();now=(S/p2).read_bytes()
receipt=json.loads((D/'exact-edits-and-inverse.json').read_text())
e=next(v for v in receipt['edits'] if v['path']==p2)
cor=json.loads((D/'qualification-correction.json').read_text())['edits'][1]
reversed_bytes=now.replace(bytes.fromhex(cor['new_hex']),bytes.fromhex(cor['old_hex']))
assert reversed_bytes.count(bytes.fromhex(e['new_hex']))==e['count']
reversed_bytes=reversed_bytes.replace(bytes.fromhex(e['new_hex']),bytes.fromhex(e['old_hex']))
assert reversed_bytes==old
def endings(v):return {'CRLF':v.count(b'\r\n'),'LF_total':v.count(b'\n'),'bare_LF':v.count(b'\n')-v.count(b'\r\n')}
(D/'cn-lookup-line-ending-exact-custody.json').write_text(json.dumps({'path':p2,'baseline_sha256':hashlib.sha256(old).hexdigest(),'current_sha256':hashlib.sha256(now).hexdigest(),'baseline_endings':endings(old),'current_endings':endings(now),'new_inserted_receipt_endings':endings(bytes.fromhex(e['new_hex'])),'actual_correction_endings':endings(bytes.fromhex(cor['new_hex'])),'two_stage_inverse_exact':True,'old_bytes_untouched':True,'clarification':'Receipt hex bytes are authoritative; successful edit preferred CRLF for new multiline text attached at a single-line anchor while preserving original body bytes. No whole-file newline normalization or old getter mutation.'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','CPP_bytes':len(n),'CPP_sha256':hashlib.sha256(n).hexdigest(),'CN_inverse_exact':True,'CN_endings':endings(now)}))

