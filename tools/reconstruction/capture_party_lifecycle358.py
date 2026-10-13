from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path(__file__).resolve().parent;A=D.parent
HEAD='81566a8a7efb75e7ea768bb5f767e1e5f1ad9324'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
    p=D/p;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def js(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
assert not (D/'capture-complete.json').exists() and not (D/'seal.json').exists()
verified=[]
for name,pin in [('round358-party-courier-lifecycle-proposal','b2b8cc897f6e5a17770ef7c1e650296415b2fb149c95c815c790f1900b4c0677'),('round357-party-callback-admission-implementation','2a8b77b2c36088a03fdc3fe882df4234c382214c7a4323bf65d34354a555a43b'),('round357-party-callback-independent-source-review','b71176941db5b8a405787865451797d2d6d5a1cd4628ddbea6dd6c7bc8bda5be')]:
    p=A/name;s=(p/'seal.json').read_bytes();assert sha(s)==pin;v=json.loads(s)
    for m in v['members']:
        b=(p/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
    assert len(v['members'])==v['member_count'] and sum(m['bytes'] for m in v['members'])==v['member_bytes']
    verified.append({'root':str(p),'seal_sha256':pin,'member_count':v['member_count'],'member_bytes':v['member_bytes'],'members':v['members']})
js('prior-individual-verification.json',verified)
receipt=json.loads((D/'apply-receipt.json').read_bytes());sources=[];snap={}
for m in receipt['sources']:
    f=m['source'];b=(R/f).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256'];snap[f]=b;inv=b
    for e in reversed(receipt['edits']):
        if e['source']!=f:continue
        n=bytes.fromhex(e['after_hex']);o=bytes.fromhex(e['before_hex']);assert inv.count(n)==1;inv=inv.replace(n,o,1)
    assert inv==(D/'before'/f).read_bytes()==subprocess.check_output(['git','show',HEAD+':'+f],cwd=R)
    put('final/'+f,b);put('inverse/'+f,inv);sources.append(dict(m,whole_inverse_equal=True,published_baseline_equal=True))
frozen=[]
p=A/'round358-party-courier-lifecycle-proposal';manifest=json.loads((p/'qualified-final/source-manifest.json').read_bytes())
for m in manifest['members']:
    if m['kind']!='whole':continue
    source=Path(m['source']);f=source.relative_to(R).as_posix()
    if f in snap:continue
    b=source.read_bytes();assert sha(b)==m['sha256'] and len(b)==m['bytes'];assert b==(p/'qualified-final'/m['retained']).read_bytes()
    frozen.append({'source':f,'bytes':len(b),'sha256':sha(b),'prior_retained':str(p/'qualified-final'/m['retained']),'unchanged':True})
cuts=[]
for name,f,lo,hi in [('actual-disconnect-first','src/core/Application.cpp',2325,2347),('actual-ready-first','src/core/Application.cpp',7135,7161),('whole-courier-lifetime','src/game/OwnedPartyPreviewTransport.h',1,213)]:
    lines=snap[f].splitlines(keepends=True);assert 1<=lo<=hi<=len(lines);raw=b''.join(lines[lo-1:hi]);off=sum(map(len,lines[:lo-1]));assert snap[f][off:off+len(raw)]==raw
    put('cuts/'+name+'.txt',raw);cuts.append({'source':f,'name':name,'first_line':lo,'last_line':hi,'source_byte_offset':off,'bytes':len(raw),'sha256':sha(raw),'whole_sha256':sha(snap[f])})
assert all((R/f).read_bytes()==b for f,b in snap.items())
js('source-manifest.json',{'head':HEAD,'scope':'Two existing source lifecycle changes; no product execution','sources':sources,'unchanged_supplier_sources':frozen,'cuts':cuts,'source_readback_equal':True,'credits':{'method':0,'opcode':0,'format':0,'route':0}})
v={'status':'successful_once','whole_count':len(sources),'whole_bytes':sum(v['bytes'] for v in sources),'inverse_whole_count':len(sources),'inverse_whole_bytes':sum(v['before_bytes'] for v in sources),'cut_count':len(cuts),'cut_bytes':sum(v['bytes'] for v in cuts),'frozen_sources':len(frozen),'frozen_bytes':sum(v['bytes'] for v in frozen),'prior_members':sum(v['member_count'] for v in verified),'prior_bytes':sum(v['member_bytes'] for v in verified)}
js('capture-complete.json',v);print(json.dumps(v))
