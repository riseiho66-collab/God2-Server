from pathlib import Path
import json,hashlib,re
S=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round359-common-skill-definition-implementation')
R=D.parent/'round358-skills-raw-three-source-audit'
H=lambda b:hashlib.sha256(b).hexdigest()
refs=json.loads((R/'source-references.json').read_text(encoding='utf-8'))
source={}
for r in refs:
 b=(R/r['retained']).read_bytes();assert H(b)==r['sha256'] and len(b)==r['bytes'];source[r['sha256']]=b
p='src/db/SharedSkillDefinition.cpp';before=(S/p).read_bytes();text=before.decode('utf-8')
start=text.index('const Pin pins[]={\n')+len('const Pin pins[]={\n');end=text.index('\n};',start)
lines=text[start:end].splitlines();assert len(lines)==907
proof=[];newlines=[]
raw150=(D.parent/'round359-native-skill-text-common-source-plan/retained-custom150-record.bin').read_bytes()
for line in lines:
 v=line.strip();assert v.startswith('{') and v.endswith('},')
 body=v[1:-2].replace('SharedSkillRegion::Taiwan','"Taiwan"').replace('SharedSkillRegion::China','"China"')
 row=json.loads('['+body+']');assert len(row)==12
 region,kind,id,ordinal,off,sha,source_sha,count,*names=row
 if source_sha=='f159b61f0aeacc46e71519cd6e98910381eda22336ad07487b2cf7213ec6297d':
  assert kind==0 and id==150 and count==477;raw=raw150
 else:raw=source[source_sha][off:off+110]
 assert len(raw)==110 and raw[:2]==bytes([id,kind]) and H(raw)==sha
 values=','.join('0x'+format(v,'02x') for v in raw)
 newlines.append(line[:-2]+',{{'+values+'}}},')
 proof.append({'region':region,'kind':kind,'id':id,'source_sha256':source_sha,'offset':off,'ordinal':ordinal,'bytes':110,'sha256':sha,'expected_hex':raw.hex()})
table='\n'.join(newlines)
edits=[
 ('    const char* name;const char* traditional_name;const char* short_text;const char* traditional_short;\n',
  '    const char* name;const char* traditional_name;const char* short_text;const char* traditional_short;\n    std::array<std::uint8_t,110> expected;\n'),
 ('    if(!b.row_digest_verified || b.raw[0]!=id || b.raw[1]!=kind ||\n',
  '    if(b.raw[0]!=id || b.raw[1]!=kind ||\n'),
 ('           b.source_offset!=p.offset)continue;\n',
  '           b.source_offset!=p.offset || b.raw!=p.expected)continue;\n'),
 (text[start:end],table)]
nexttext=text;inverse=[]
for old,new in edits:
 assert nexttext.count(old)==1
 nexttext=nexttext.replace(old,new);inverse.append({'old_hex':old.encode().hex(),'new_hex':new.encode().hex()})
value=nexttext
for e in reversed(inverse):
 old=bytes.fromhex(e['old_hex']).decode();new=bytes.fromhex(e['new_hex']).decode()
 assert value.count(new)==1;value=value.replace(new,old)
assert value==text
header='src/db/SharedSkillDefinition.h';hb=(S/header).read_bytes();ht=hb.decode()
old='// row_digest_verified records the explicit reader\'s recomputed110-byte digest;\n// only the resolver\'s exact per-row pin comparison promotes row qualification.\n'
new='// row_digest_verified is an informational reader digest result, never proof\n// supplied by the caller. Exact full110 bytes plus source/ordinal/offset pins\n// promote row qualification even when a runtime digest provider is unavailable.\n'
assert ht.count(old)==1;hn=ht.replace(old,new).encode()
assert hn.replace(new.encode(),old.encode())==hb
plans=[(p,before,nexttext.encode()),(header,hb,hn)]
for name,b,n in plans:
 q=D/'before-full110-correction'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
for name,b,n in plans:assert (S/name).read_bytes()==b
for name,b,n in plans:
 (S/name).write_bytes(n);q=D/'full110-corrected-candidate'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(n)
(D/'full110-pin-correction.json').write_text(json.dumps({'successful_execution_count':1,'cpp_path':p,'before_bytes':len(before),'before_sha256':H(before),'bytes':len(nexttext.encode()),'sha256':H(nexttext.encode()),'cpp_edits':inverse,'header_path':header,'header_old_hex':old.encode().hex(),'header_new_hex':new.encode().hex(),'header_before_sha256':H(hb),'header_sha256':H(hn),'inverse':True,'original_rows':901,'owner_rows':6,'expected_bytes_sum':907*110,'row_proof':proof},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','pins':907,'expected_bytes':907*110,'CPP_bytes':len(nexttext.encode()),'CPP_sha256':H(nexttext.encode()),'H_bytes':len(hn),'H_sha256':H(hn)}))

