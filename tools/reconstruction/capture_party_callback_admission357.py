from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path(__file__).resolve().parent;A=D.parent
HEAD='b5a2afd1364c50613525f07757ba31350dad9882'
def sha(b):return hashlib.sha256(b).hexdigest()
def output(p,b):
    assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def js(p,v):output(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
assert not (D/'capture-complete.json').exists() and not (D/'seal.json').exists()
# Verify immutable dependencies individually, never execute their helpers.
prior=[]
for name,pin in [('round357-party-callback-admission-proposal','e746c86ede71552b9c44e5da1a0bd697d18c085a0dc165884cc787dece8f5364'),('round356-party-preview-transport-proposal','219682c6177ed6fbd825d95ad06b81ce57731dc5fa56b1098d9a92e9df0cc701'),('round356-party-preview-output-implementation','a3269e999cfeb2a49afe72c1bcd572bdd1b7ec21a4aca46ddb48beac0ee11b97')]:
    p=A/name;s=(p/'seal.json').read_bytes();assert sha(s)==pin;v=json.loads(s);count=0;size=0;refs=[]
    for m in v['members']:
        b=(p/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256'];count+=1;size+=len(b);refs.append(m)
    assert count==v['member_count'] and size==v['member_bytes'];prior.append({'path':str(p),'seal_sha256':pin,'member_count':count,'member_bytes':size,'members':refs})
js(D/'prior-individual-verification.json',prior)
pins={'src/net/Session.h':(35537,'05bd0d1379bd0a48eadf4e1bf83ec7f449059b3d7fc45721b8d3223d63b1005f'),'src/net/Session.cpp':(240949,'79fc55816b9f69829202a9be7191348e2b845a6c6f7cd7f964c1ce0f9c167faf'),'src/core/Application.cpp':(725214,'ae0cbcdbc4c3f3288efca12e43b3f66206cbb89e0147495752571bd3eb9a2cfc'),'src/game/OwnedPartyPreviewTransport.h':(10563,'606419a2c03507644b4de3815818a86b7712b66c987f8cb220b5c8209b069b4b')}
current={f:(R/f).read_bytes() for f in pins}
for f,(size,h) in pins.items():assert len(current[f])==size and sha(current[f])==h
inverse=dict(current)
# Undo corrections newest first, then the original source recipe.
for name in ['peer-watch-correction-receipt.json','watch-correction-receipt.json','split-correction-receipt.json','scope-correction-receipt.json','apply-receipt.json']:
    v=json.loads((D/name).read_bytes());edits=v.get('edits',[v])
    for e in reversed(edits):
        f=e['source'];o=bytes.fromhex(e['before_hex']);n=bytes.fromhex(e['after_hex']);count=e.get('multiplicity',e.get('count',1))
        assert inverse[f].count(n)==count,(name,f,count,inverse[f].count(n));inverse[f]=inverse[f].replace(n,o)
manifest=[]
for f in pins:
    before=(D/'before'/f).read_bytes();published=subprocess.check_output(['git','show',HEAD+':'+f],cwd=R)
    assert inverse[f]==before==published
    output(D/'final'/f,current[f]);output(D/'inverse'/f,inverse[f])
    manifest.append({'source':f,'bytes':len(current[f]),'sha256':sha(current[f]),'before_bytes':len(before),'before_sha256':sha(before),'whole_inverse_equal':True,'published_baseline_equal':True})
# Exact line cuts are evidence excerpts, not executed functions or native claims.
cut_specs=[('session-tls-poison','src/net/Session.cpp',58,99),('session-private-data','src/net/Session.cpp',192,248),('session-attempt-capture','src/net/Session.cpp',368,386),('session-frozen-sync-and-write','src/net/Session.cpp',512,594),('session-world-admission-selected','src/net/Session.cpp',2138,2348),('session-output-and-admission-apis','src/net/Session.cpp',2704,2820),('session-old-normal-components','src/net/Session.cpp',2821,2895),('main-directory-selected','src/core/Application.cpp',6990,7468),('main-options-split-selected','src/core/Application.cpp',7470,7605),('main-scheduler-and-stop','src/core/Application.cpp',7810,7890),('session-admission-types','src/net/Session.h',143,204),('session-public-source-apis','src/net/Session.h',425,461),('courier-complete','src/game/OwnedPartyPreviewTransport.h',1,198)]
cuts=[]
for name,f,start,end in cut_specs:
    lines=current[f].splitlines(keepends=True);assert 1<=start<=end<=len(lines),(name,len(lines))
    b=b''.join(lines[start-1:end]);offset=sum(len(v) for v in lines[:start-1]);assert current[f][offset:offset+len(b)]==b
    p=D/'cuts'/(name+'.txt');output(p,b);cuts.append({'name':name,'source':f,'first_line':start,'last_line':end,'source_byte_offset':offset,'bytes':len(b),'sha256':sha(b),'source_sha256':sha(current[f])})
js(D/'source-manifest.json',{'head':HEAD,'scope':'Static source custody only; no C++/native/codec/DB execution','sources':manifest,'cuts':cuts,'correction_chain':['watch','split-exact-callback-membership','generic-unobserved-poison-scope'],'credits':{'method':0,'opcode':0,'format':0,'route':0}})
assert all((R/f).read_bytes()==current[f] for f in current)
js(D/'capture-complete.json',{'status':'successful_once','head':HEAD,'whole_count':len(current),'whole_bytes':sum(len(b) for b in current.values()),'inverse_whole_count':len(inverse),'inverse_whole_bytes':sum(len(b) for b in inverse.values()),'cut_count':len(cuts),'cut_bytes':sum(v['bytes'] for v in cuts),'prior_member_count':sum(v['member_count'] for v in prior),'prior_member_bytes':sum(v['member_bytes'] for v in prior),'all_source_readback_equal':True})
print(json.dumps({'status':'captured_once','sources':manifest,'cuts':len(cuts),'cut_bytes':sum(v['bytes'] for v in cuts),'prior_members':sum(v['member_count'] for v in prior)}))
