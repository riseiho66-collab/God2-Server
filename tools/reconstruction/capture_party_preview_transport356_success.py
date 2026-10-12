from pathlib import Path
import hashlib,json,subprocess

R=Path('C:/Users/risei/Desktop/God2/God2-Server')
A=Path(__file__).resolve().parent
D=A/'complete-final'
D.mkdir(exist_ok=False)
P=A.parent/'round355-normal-return-publication-proposal'
HEAD='6c2d3412e22316d1537323bc13e449f87ddfd03a'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
    p=D/p;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Refusing overwrite '+str(p))
    p.write_bytes(b)
    assert p.read_bytes()==b
def js(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
s=(P/'seal.json').read_bytes()
assert sha(s)=='732a519228a22e32d75e223095529a0e0cb10f0d3cef319da26040c7623c9822'
prior=json.loads(s);checked=[]
for m in prior['members']:
    b=(P/m['path']).read_bytes()
    assert len(b)==m['bytes'] and sha(b)==m['sha256'],m['path']
    checked.append(m)
assert len(checked)==55 and sum(m['bytes'] for m in checked)==1570271
js('prior355-individual-verification.json',{'seal_path':str(P/'seal.json'),'seal_bytes':len(s),'seal_sha256':sha(s),'members':checked,'member_count':len(checked),'member_bytes':sum(m['bytes'] for m in checked)})
files=[
 'src/core/Application.cpp','src/net/Session.h','src/net/Session.cpp',
 'src/game/OwnedPartyDirectory.h','src/handlers/OwnedPartyDirectoryService.h',
 'src/game/NativeParty.h','src/protocol/RecoveredParty.h',
 'src/protocol/TaiwanNativePartyMenu.h','src/protocol/RecoveredWorldFrame.h',
 'src/core/Config.h','src/core/Config.cpp']
cuts={
 'src/core/Application.cpp':[
 ('party-projection',2090,2169),('actual-disconnect',2320,2360),
 ('blacklist-own-output-pattern',6930,6989),('party-full-host',6990,7424)],
 'src/net/Session.h':[('normal-output-private-carriers',128,185),('normal-output-public-api',408,426)],
 'src/net/Session.cpp':[
 ('normal-init-output-data',145,232),('pending-retirement',305,336),
 ('epoch-transport-guard',480,528),('actual-identity-lifecycle',1390,1446),
 ('selection-ready-lifecycle',1618,1640),('replacement-ready-lifecycle',1705,1800),
 ('native-init-current-output-api',2580,2704),('close-state-retirement',3550,3611)],
 'src/game/OwnedPartyDirectory.h':[('actor-detail-presentation',14,78)],
 'src/handlers/OwnedPartyDirectoryService.h':[('permission-source-fences',1,125)],
 'src/game/NativeParty.h':[('actual-party-state-and-actions',1,148)],
 'src/protocol/RecoveredParty.h':[('preview-refresh-format',43,79)],
 'src/core/Config.cpp':[('actual-opt-in-dependency',665,679)]}
manifest=[];snapshots={}
for f in files:
    b=(R/f).read_bytes();snapshots[f]=b
    out='whole/'+f;put(out,b)
    manifest.append({'kind':'whole','source':str(R/f),'retained':out,'bytes':len(b),'sha256':sha(b),'head':HEAD})
    lines=b.splitlines(keepends=True)
    for label,lo,hi in cuts.get(f,[]):
        assert 1<=lo<=hi<=len(lines),(f,lo,hi,len(lines))
        c=b''.join(lines[lo-1:hi]);out='cuts/'+label+'.txt';put(out,c)
        manifest.append({'kind':'cut','source':str(R/f),'retained':out,'line_first':lo,'line_last':hi,'source_byte_offset':sum(map(len,lines[:lo-1])),'bytes':len(c),'sha256':sha(c),'whole_sha256':sha(b),'whole_function':False})
for f,b in snapshots.items():assert (R/f).read_bytes()==b,'Source changed during capture '+f
js('source-manifest.json',{'scope':'READONLY exact source snapshot; no execution of product/native/codec/SQL; no source edit','head':HEAD,'members':manifest,'whole_count':len(files),'whole_bytes':sum(m['bytes'] for m in manifest if m['kind']=='whole'),'cut_count':sum(m['kind']=='cut' for m in manifest),'cut_bytes':sum(m['bytes'] for m in manifest if m['kind']=='cut')})
js('capture-complete.json',{'helper':Path(__file__).name,'head':HEAD,'source_unchanged_at_readback':True,'prior355_count':55,'prior355_bytes':1570271,'whole_count':len(files),'cut_count':sum(m['kind']=='cut' for m in manifest),'scope':'static source custody only; zero method/opcode/format/route credit'})
print(json.dumps({'status':'complete','whole_count':len(files),'whole_bytes':sum(m['bytes'] for m in manifest if m['kind']=='whole'),'cut_count':sum(m['kind']=='cut' for m in manifest),'cut_bytes':sum(m['bytes'] for m in manifest if m['kind']=='cut')}))
