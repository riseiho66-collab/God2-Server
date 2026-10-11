"""Capture-specific G02 receipt for the deep experiment; G03 stays unverified."""
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from codex_g02_review import digest, reconstruct, publish, require
from formalize_g03_deep import observe
from normalize_cdb_capture import native_bytes
from runtime_evidence import RuntimeStore
from gate_review import ReviewStore

HOME = Path(__file__).resolve().parents[2]
CID = '767b693d0297006277620e9c2998d76c3dcdd0018b71ee40934c0e34e4ede97f'
POLICY = Path('C:/Users/risei/.codex/attachments/97083fa5-2187-4dc2-8e1b-439e785ec8bb/pasted-text.txt')


def check():
    require(digest(POLICY) == '5e0589dcacb0f129fa7b189bbb12a7ab7cd76cb28200f1421a2c4480754356d5', 'Authorization changed')
    store = RuntimeStore(HOME/'artifacts')
    p = HOME/'artifacts/runtime'/CID
    b = store.validate_bundle(p)
    require(b['capture_id'] == CID, 'Capture changed')
    require(store.assess(CID)['gates']['unpack']['status'] == 'READY_FOR_REVIEW', 'Unpack not ready')
    native = (p/'native-cdb.log').read_text(encoding='ascii')
    marks = observe(native)
    require(marks['PACKED']['pid'] == b['manifest']['process']['pid'], 'PID mismatch')
    before, after = (p/'before.bin').read_bytes(), (p/'after.bin').read_bytes()
    require(before[0x14a3e8:0x14a408] == bytes(32), 'Before bytes')
    require(native_bytes(native, 0x54a3e8) == after[0x14a3e8:0x14a408], 'Target bytes')
    require(reconstruct(after, 0x14a3e8) == (p/'unpacked-candidate.exe').read_bytes(), 'Independent derivation')
    e = next(e for e in b['events'] if e['id']=='deep-1')
    require(e['thread_id'] == marks['CANDIDATE']['tid'] and e['details']['after_hex'] == after[0x14a3e8:0x14a408].hex(), 'Event correlation')
    state = ReviewStore(HOME/'artifacts').status(b['manifest']['artifact_id'])
    require(not state['counter_evidence'] and not any(r['decision']=='REJECT' and not r['revoked'] for r in state['reviews']), 'Counter evidence needs review')
    return b['manifest']['artifact_id']


def audit(cid):
    import re
    require(re.fullmatch('[a-f0-9]{64}', cid), 'Invalid ID')
    p = HOME/'artifacts/codex-certificates'/(cid+'.json')
    require(digest(p)==cid, 'Certificate changed')
    c = json.loads(p.read_text())
    require(c['issuer']=='review_g03_deep.py' and c['capture_sha256']==CID and c['human_attestation'] is False, 'Wrong receipt')
    for rev in (HOME/'artifacts/codex-revocations').glob('*.json'):
        require(digest(rev)==rev.stem and json.loads(rev.read_text())['certificate']!=cid, 'Revoked/corrupt record')
    for path, expected in c['bindings'].items():
        require(digest(path)==expected, 'Binding changed: '+path)
    check()
    return 'VALID_CODEX_ONLY'


if __name__ == '__main__':
    if len(sys.argv)==3 and sys.argv[1]=='audit':
        print(audit(sys.argv[2])); raise SystemExit(0)
    require(sys.argv[1:]==['review'], 'Use review or audit CERTIFICATE')
    artifact = check()
    log = HOME/'artifacts/reports/g03-deep-python-tests.txt'
    command = [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/research']
    with log.open('xb') as output:
        run = subprocess.run(command, cwd=HOME, stdout=output, stderr=subprocess.STDOUT, timeout=600)
    require(run.returncode==0, 'Regression failure; no receipt')
    check()
    files = [POLICY, log, * (HOME/'artifacts/runtime'/CID).iterdir(),
             * (HOME/'tools/research').glob('*.py'), * (HOME/'tests/research').glob('*.py')]
    receipt = {'kind':'G02_CODEX_CERTIFICATE', 'issuer':'review_g03_deep.py', 'schema_version':1,
        'status':'CODEX_VERIFIED', 'artifact_sha256':artifact, 'capture_sha256':CID, 'evidence_ids':['deep-1'],
        'review_type':'codex_autonomous', 'reviewer':'Codex', 'human_attestation':False,
        'owner_policy':'codex_review_authorized', 'created_at':datetime.now(timezone.utc).isoformat(),
        'claim':'Observed packed-to-restored runtime transition in this fresh capture',
        'checks':['vault/manifest/attachment integrity','native register/stack/event correlation','independent struct reconstruction','counter-evidence search','Python regression'],
        'counter_assessment':'No registered blocking transition contradiction; G03 observation gaps and PE permission mismatch do not negate the native RET.',
        'unresolved':['G03 stable startup','unobserved execution between breakpoints','PE executable section flags','G04 imports'],
        'regressions':{'command':command,'exit_code':run.returncode,'log':str(log), 'scope':'New Python capture/normalization/review tools; C++ unchanged, prior 16/16 Debug and Release not rerun'},
        'tool_versions':{'python':sys.version,'cdb':'10.0.29617.1000','capstone':'5.0.7'},
        'bindings':{str(p.resolve()):digest(p) for p in files if p.is_file()},
        'trust_limits':'Local unsigned automated receipt, not human attestation or externally authenticated evidence'}
    identity = publish(HOME/'artifacts/codex-certificates', receipt)
    print(json.dumps({'certificate':identity,'audit':audit(identity)}))
