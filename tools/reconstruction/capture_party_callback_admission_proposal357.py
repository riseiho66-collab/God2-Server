from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
D=Path(__file__).resolve().parent
HEAD='b5a2afd1364c50613525f07757ba31350dad9882'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
    p=D/p;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(b);assert p.read_bytes()==b
def js(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
refs=[('round356-party-preview-transport-proposal','219682c6177ed6fbd825d95ad06b81ce57731dc5fa56b1098d9a92e9df0cc701',107,4654221),('round356-party-preview-output-implementation','a3269e999cfeb2a49afe72c1bcd572bdd1b7ec21a4aca46ddb48beac0ee11b97',47,6107028)]
verified=[]
for name,pin,count,total in refs:
    p=D.parent/name;s=(p/'seal.json').read_bytes();assert sha(s)==pin
    v=json.loads(s);assert len(v['members'])==count and sum(m['bytes'] for m in v['members'])==total
    for m in v['members']:
        b=(p/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256'],m['path']
    verified.append({'root':str(p),'seal_sha256':pin,'member_count':count,'member_bytes':total,'members':v['members']})
js('prior356-individual-verification.json',verified)
cuts={
 'src/net/Session.h':[('private-existing-output-response-types',128,184),('existing-output-response-api',408,432)],
 'src/net/Session.cpp':[
 ('actual-tls-scope-poison',58,91),('existing-private-response-data',155,231),('private-pending-guards',296,353),
 ('private-sync-source-guard',480,530),('fullwire-validation-component-symmetry',1886,1918),
 ('actual-whole-callback-final-handoff',2123,2270),('written-source-thread-and-capture',2614,2672),
 ('old-original-response-capture-expect-current',2708,2773)],
 'src/core/Application.cpp':[
 ('actual-projection-generic-sender',2110,2163),('directory-dispatch-source',6987,7040),
 ('retire-ready-full-reading-guard',7128,7194),('actual-c91-precommit-commit-courier',7265,7393),
 ('final-inner-exception-and-outer-wrapper',7424,7470),('scheduler-and-stop-lifetime',7798,7846)],
 'src/game/OwnedPartyPreviewTransport.h':[('whole-courier-source',1,183)]}
manifest=[];snapshots={}
for f,items in cuts.items():
    b=(R/f).read_bytes();snapshots[f]=b
    assert b==(D.parent/'round356-party-preview-output-implementation/closed-final/final'/f).read_bytes()
    out='whole/'+f;put(out,b);manifest.append({'kind':'whole','source':str(R/f),'retained':out,'bytes':len(b),'sha256':sha(b)})
    lines=b.splitlines(keepends=True)
    for label,lo,hi in items:
        assert 1<=lo<=hi<=len(lines),(f,lo,hi,len(lines))
        raw=b''.join(lines[lo-1:hi]);out='cuts/'+label+'.txt';put(out,raw)
        manifest.append({'kind':'cut','source':str(R/f),'retained':out,'first_line':lo,'last_line':hi,'byte_offset':sum(map(len,lines[:lo-1])),'bytes':len(raw),'sha256':sha(raw),'whole_sha256':sha(b),'whole_function':False})
for f,b in snapshots.items():assert (R/f).read_bytes()==b
js('source-manifest.json',{'head':HEAD,'scope':'READONLY actual source proposal; no product execution or source change','members':manifest,'source_unchanged_at_readback':True})
out={'status':'complete','whole_count':len(snapshots),'whole_bytes':sum(m['bytes'] for m in manifest if m['kind']=='whole'),'cut_count':sum(m['kind']=='cut' for m in manifest),'cut_bytes':sum(m['bytes'] for m in manifest if m['kind']=='cut'),'prior_verified_count':154,'prior_verified_bytes':10761249,'credits':{'method':0,'opcode':0,'format':0,'route':0}}
js('capture-complete.json',out);print(json.dumps(out))
