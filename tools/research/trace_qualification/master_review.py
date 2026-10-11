"""Seal native master evidence and review only its unpack transition."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sys
HOME = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(HOME/'tools/research'))
from runtime_evidence import RuntimeStore
from gate_review import ReviewStore
from codex_g02_review import digest, reconstruct, publish, require
from normalize_cdb_capture import mapped_to_candidate
from host_capture import ARTIFACT, firewall_ready
from trace_qualification.native_review import review

ROOT = HOME/'artifacts/capture_work/host-20260918-1430'
OUT = ROOT/'output'
RUN = 'native-master-01'
POLICY = Path('C:/Users/risei/.codex/attachments/97083fa5-2187-4dc2-8e1b-439e785ec8bb/pasted-text.txt')


def main():
    native = (OUT/f'{RUN}-native.log').read_text(encoding='ascii')
    clean = re.sub(r'(?:\d+:\d+(?::x86)?> )+', '', native)
    marks = {}
    for name in ('PACKED','TRANSFER','CANDIDATE'):
        rows = re.findall(r'^MASTER_'+name+r' (.+)$',clean,re.M)
        require(len(rows)==1,'Missing/ambiguous marker')
        marks[name] = {k:int(v,16) for k,v in re.findall(r'(\w+)=([0-9a-f]+)',rows[0])}
    a,t,b = (marks[n] for n in ('PACKED','TRANSFER','CANDIDATE'))
    require(len({(m['pid'],m['tid']) for m in marks.values()})==1,'Identity mismatch')
    require(a['eip']==0x702001 and t['eip']==0x7023bf and b['eip']==0x54a3e8,'PC mismatch')
    require(a['time']<=t['time']<=b['time'] and b['esp']==t['esp']+4,'Order/stack mismatch')
    require(f'{t["esp"]:08x}  0054a3e8' in clean,'Native stack target missing')
    require('007023bf c3' in clean and '0054a3e8 55' in clean,'Native RET/target missing')
    before=(OUT/f'{RUN}-before.bin').read_bytes()
    after=(OUT/f'{RUN}-after.bin').read_bytes()
    require(len(before)==len(after)==0x307000,'Image length')
    require(before[0x14a3e8:0x14a408]==bytes(32),'Not originally zero')
    require(after[0x14a3e8]==0x55 and after[0x3023bf]==0xc3,'Mapped byte mismatch')
    candidate, derivation=mapped_to_candidate(after,0x14a3e8)
    require(candidate==reconstruct(after,0x14a3e8),'Independent reconstruction mismatch')
    request=json.loads((ROOT/'host-request.json').read_text())
    require(digest(request['original'])==digest(ROOT/'client/God2.exe')==ARTIFACT,'Original changed')
    require(firewall_ready(json.loads((OUT/f'{RUN}-firewall.json').read_text()),request['programs']),'Firewall')
    launch=json.loads((OUT/f'{RUN}-result.json').read_text())
    require(launch['result']=='OBSERVED_PENDING_REVIEW' and launch['startup_collected'],'Incomplete capture')
    require(digest(POLICY)=='5e0589dcacb0f129fa7b189bbb12a7ab7cd76cb28200f1421a2c4480754356d5','Policy identity')
    review('native-f'); review('native-g')
    store=RuntimeStore(HOME/'artifacts')
    dest=HOME/'artifacts/capture_requests/native-master-01'
    store.prepare(ARTIFACT,dest)
    def event(seq,m,kind,details):
        return dict(id=f'native-{seq}',seq=seq,timestamp_ns=(m['time']-116444736000000000)*100,
                    thread_id=m['tid'],pc=m['eip'],state='OBSERVED_NOT_G03_VERIFIED',type=kind,details=details)
    events=[event(0,a,'function_enter',{'bytes_hex':before[0x302001:0x302021].hex()}),
            event(1,b,'unpack_transition',{'from_va':t['eip'],'to_va':b['eip'],'region_va':b['eip'],
                'before_hex':before[0x14a3e8:0x14a408].hex(),'after_hex':after[0x14a3e8:0x14a408].hex(),'memory_file':'after.bin'})]
    (dest/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    (dest/'unpacked-candidate.exe').write_bytes(candidate)
    (dest/'derivation.json').write_text(json.dumps(derivation,indent=2))
    attachments=[('events.jsonl','events'),('unpacked-candidate.exe','unpacked_pe'),('derivation.json','raw_trace')]
    for suffix,name,role in [('before.bin','before.bin','memory_image'),('after.bin','after.bin','memory_image'),
            ('stable.bin','stable.bin','memory_image'),('next-stop.bin','next-stop.bin','memory_image'),
            ('native.log','native-cdb.log','raw_trace'),('commands.txt','commands.txt','raw_trace'),
            ('result.json','launch.json','raw_trace'),('firewall.json','firewall.json','raw_trace')]:
        shutil.copy2(OUT/f'{RUN}-{suffix}',dest/name)
        attachments.append((name,role))
    manifest=json.loads((dest/'manifest.json').read_text())
    manifest['session_id']='GOD2-NATIVE-MASTER-CAPTURE-01'
    manifest['process'].update(pid=a['pid'],module_base=0x400000)
    manifest['scope']['ranges']=[[0x400000,0x707000]]
    captured=datetime.fromtimestamp((a['time']-116444736000000000)/10000000,timezone.utc).isoformat()
    manifest['provenance'].update(tool='windbg',tool_version='native x64 CDB 10.0.29617.1000',operator='Codex',
        captured_at=captured,environment_id=ROOT.name,isolation='loopback-only',working_copy_sha256=ARTIFACT)
    manifest['files']=[dict(path=name,role=role,size=(dest/name).stat().st_size,sha256=digest(dest/name)) for name,role in attachments]
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
    sealed=store.seal(dest,HOME/'artifacts/capture_inbox/native-master-01')
    cid=store.ingest(sealed['bundle'])
    require(store.assess(cid)['gates']['unpack']['status']=='READY_FOR_REVIEW','Unpack mechanical check')
    state=ReviewStore(HOME/'artifacts').status(ARTIFACT)
    require(not state['counter_evidence'] and not any(r['decision']=='REJECT' and not r['revoked'] for r in state['reviews']),'Registered counter-evidence')
    files=[POLICY,Path(__file__),HOME/'tools/research/codex_g02_review.py',
           * (HOME/'artifacts/runtime'/cid).iterdir()]
    receipt=dict(kind='G02_CODEX_CERTIFICATE',issuer='trace_qualification/master_review.py',schema_version=1,
        status='CODEX_VERIFIED',artifact_sha256=ARTIFACT,capture_sha256=cid,evidence_ids=['native-1'],
        human_attestation=False,review_type='codex_autonomous',reviewer='Codex',
        created_at=datetime.now(timezone.utc).isoformat(),
        claim='Observed packed-to-restored transition in GOD2-NATIVE-MASTER-CAPTURE-01 only',
        checks=['same PID/TID and ordered native markers','native RET and stack target','full before/after images',
                'independent reconstruction','RuntimeStore unpack assessment','original/work-copy identity','firewall receipt'],
        unresolved=['G03 early ExitProcess(0) observed','Startup execution between checkpoints not fully covered','IAT not repaired'],
        trust_limits='Local unsigned automated receipt; not human attestation; no full-suite rerun for this receipt',
        bindings={str(p.resolve()):digest(p) for p in files if p.is_file()})
    cert=publish(HOME/'artifacts/codex-certificates',receipt)
    report={'capture_id':cid,'g02_certificate':cert,'g03':'NEED_MORE_EVIDENCE','g04':'DEFERRED',
            'counter_evidence':'ExitProcess(0) called, return address 0x54C7B4, no network API hit observed',
            'scope_note':'Manifest loopback-only label means existing program firewall; host not VM-isolated; native debugger not firewalled'}
    (HOME/'artifacts/reports/native-wow64-20260919/master-review.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))


if __name__=='__main__':
    main()
