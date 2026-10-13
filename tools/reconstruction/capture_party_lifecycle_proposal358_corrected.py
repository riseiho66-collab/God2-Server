from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server');P=Path(__file__).resolve().parent;D=P/'qualified-final';A=P.parent
HEAD='81566a8a7efb75e7ea768bb5f767e1e5f1ad9324'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
    p=D/p;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def js(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==HEAD
refs=[('round357-party-callback-admission-proposal','e746c86ede71552b9c44e5da1a0bd697d18c085a0dc165884cc787dece8f5364',27,1140439),('round357-party-callback-admission-implementation','2a8b77b2c36088a03fdc3fe882df4234c382214c7a4323bf65d34354a555a43b',57,6997333),('round357-party-callback-independent-source-review','b71176941db5b8a405787865451797d2d6d5a1cd4628ddbea6dd6c7bc8bda5be',56,3849652)]
verified=[]
for name,pin,count,total in refs:
    p=A/name;s=(p/'seal.json').read_bytes();assert sha(s)==pin;v=json.loads(s)
    assert len(v['members'])==count and sum(m['bytes'] for m in v['members'])==total
    for m in v['members']:
        b=(p/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
    verified.append({'root':str(p),'seal_sha256':pin,'member_count':count,'member_bytes':total,'members':v['members']})
js('prior357-individual-verification.json',verified)
specs={
 'src/core/Application.cpp':[('game-network-owner',629,647),('courier-optin-host',1396,1407),('actual-disconnect-first-seam',2325,2345),('actual-ready-first-seam',7134,7154),('existing-scheduler-stop-run',7823,7908)],
 'src/game/OwnedPartyPreviewTransport.h':[('whole-owning-registry-courier',1,198)],
 'src/net/Session.h':[('private-output-and-admission-types',143,198)],
 'src/net/Session.cpp':[('fresh-output-revocation',192,217),('actual-tail-retirement-and-ready-game-post',1776,1830),('actual-close-finish-game-disconnect-post',2497,2567),('public-close-post-no-inline-disconnect',3662,3668)],
 'src/core/Scheduler.h':[('whole-scheduler-interface',1,18)],
 'src/core/Scheduler.cpp':[('whole-scheduler-rearm-errors',1,15)],
 'src/net/IoContextPool.h':[('whole-network-owner-interface',1,28)],
 'src/net/IoContextPool.cpp':[('whole-network-run-stop-join',1,31)],
 'src/net/TcpServer.cpp':[('actual-game-strand-session-disconnect-supplier',9,96)]}
snap={};manifest=[]
for f,cuts in specs.items():
    b=(R/f).read_bytes();assert b==subprocess.check_output(['git','show',HEAD+':'+f],cwd=R);snap[f]=b
    out='whole/'+f;put(out,b);manifest.append({'kind':'whole','source':str(R/f),'retained':out,'bytes':len(b),'sha256':sha(b)})
    lines=b.splitlines(keepends=True)
    for name,lo,hi in cuts:
        assert 1<=lo<=hi<=len(lines),(name,len(lines));raw=b''.join(lines[lo-1:hi]);off=sum(map(len,lines[:lo-1]));assert b[off:off+len(raw)]==raw
        out='cuts/'+name+'.txt';put(out,raw);manifest.append({'kind':'cut','source':str(R/f),'retained':out,'first_line':lo,'last_line':hi,'source_byte_offset':off,'bytes':len(raw),'sha256':sha(raw),'whole_sha256':sha(b),'function_credit':0})
assert all((R/f).read_bytes()==b for f,b in snap.items())
js('source-manifest.json',{'head':HEAD,'scope':'READONLY actual source lifecycle proposal; no product or native execution','source_unchanged_at_readback':True,'members':manifest,'proposed_only':['src/core/Application.cpp','src/game/OwnedPartyPreviewTransport.h']})
v={'status':'captured_once','whole_count':len(snap),'whole_bytes':sum(m['bytes'] for m in manifest if m['kind']=='whole'),'cut_count':sum(m['kind']=='cut' for m in manifest),'cut_bytes':sum(m['bytes'] for m in manifest if m['kind']=='cut'),'prior_verified_members':sum(v['member_count'] for v in verified),'prior_verified_bytes':sum(v['member_bytes'] for v in verified),'credits':{'method':0,'opcode':0,'format':0,'route':0}}
js('capture-complete.json',v);print(json.dumps(v))
