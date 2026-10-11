"""Narrow owner-authorized G02 receipts; separate from the human proof ledger."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

from runtime_evidence import RuntimeStore
from gate_review import ReviewStore
from host_capture import firewall_ready
from normalize_cdb_capture import native_bytes, observed_marks

HOME = Path(__file__).resolve().parents[2]
CAPTURE = '6e1ed0632ab7559cb8d21871f59a43ab75fb2157dda9b58fab4242dabccdfbde'
POLICY_SHA = '5e0589dcacb0f129fa7b189bbb12a7ab7cd76cb28200f1421a2c4480754356d5'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def reconstruct(mapped, entry):
    """Independent struct-based reconstruction; no pefile or producer calls."""
    pe = struct.unpack_from('<I', mapped, 0x3c)[0]
    require(mapped[:2] == b'MZ' and mapped[pe:pe+4] == b'PE\0\0', 'Invalid PE')
    machine, count = struct.unpack_from('<HH', mapped, pe+4)
    opt = pe+24
    require(machine == 0x14c and struct.unpack_from('<H', mapped, opt)[0] == 0x10b, 'Not PE32')
    require(struct.unpack_from('<I', mapped, opt+56)[0] == len(mapped), 'Image size mismatch')
    alignment = struct.unpack_from('<I', mapped, opt+36)[0]
    require(alignment > 0 and alignment & (alignment-1) == 0, 'Invalid alignment')
    sh = opt+struct.unpack_from('<H', mapped, pe+20)[0]
    require(0 < count <= 96 and sh+40*count <= len(mapped), 'Invalid sections')
    result = bytearray(mapped)
    struct.pack_into('<I', result, opt+16, entry)
    for i in range(count):
        s = sh+i*40
        size, rva = struct.unpack_from('<II', mapped, s+8)
        raw_size = (size+alignment-1)//alignment*alignment
        limit = struct.unpack_from('<I', mapped, s+40+12)[0] if i+1 < count else len(mapped)
        require(raw_size > 0 and rva+raw_size <= limit, 'Invalid mapped section bounds')
        struct.pack_into('<II', result, s+16, raw_size, rva)
    return bytes(result)


def cross_check():
    store = RuntimeStore(HOME/'artifacts')
    p = HOME/'artifacts/runtime'/CAPTURE
    bundle = store.validate_bundle(p)
    require(bundle['capture_id'] == CAPTURE, 'Capture identity changed')
    m = bundle['manifest']
    require(m['provenance']['source_kind'] == 'runtime', 'Not real runtime evidence')
    require(store.assess(CAPTURE)['gates']['unpack']['status'] == 'READY_FOR_REVIEW', 'Unpack not ready')
    request = json.loads((p/'host-request.json').read_text())
    working = HOME/'artifacts/capture_work/host-20260918-1430/client/God2.exe'
    require(digest(request['original']) == digest(working) == m['artifact_id'], 'Original/working mismatch')
    require(firewall_ready(json.loads((p/'firewall.json').read_text()), request['programs']), 'Recorded firewall invalid')
    native = (p/'native-cdb.log').read_text(encoding='ascii')
    marks = observed_marks(native)
    require(marks['PACKER']['pid'] == m['process']['pid'] and marks['PACKER']['base'] == m['process']['module_base'], 'Process mismatch')
    # Register output and stack rows independently support the normalized labels.
    require(re.search(r'eip=007023bf esp=001aff74', native) is not None, 'Missing source register stop')
    require(re.search(r'^001aff74\s+0054a3e8\b', native, re.M) is not None, 'Missing stack target')
    require(re.search(r'0:000> t\s+eax=.*?eip=0054a3e8 esp=001aff78', native, re.S) is not None, 'Missing native RET step')
    require('eip=0054a3e9 esp=001aff74' in native and 'eip=0054a3eb esp=001aff74 ebp=001aff74' in native, 'Missing executed target prologue')
    before, after = (p/'before.bin').read_bytes(), (p/'after.bin').read_bytes()
    require(len(before) == len(after) == 0x307000 and after[0x3023bf] == 0xc3, 'Invalid mapped images')
    require(before[0x14a3e8:0x14a408] == bytes(32), 'Unexpected before region')
    require(native_bytes(native, 0x54a3e8) == after[0x14a3e8:0x14a408], 'Native/restored bytes differ')
    require(native_bytes(native, 0x702001) == before[0x302001:0x302021], 'Packed bytes differ')
    events = bundle['events']
    e = next(e for e in events if e['id'] == 'event-1')
    require(e['thread_id'] == marks['TRANSFER_TARGET']['tid'] and e['pc'] == 0x54a3e8, 'Event thread/PC mismatch')
    require(e['details']['after_hex'] == after[0x14a3e8:0x14a408].hex(), 'Normalized bytes differ')
    require(reconstruct(after, 0x14a3e8) == (p/'unpacked-candidate.exe').read_bytes(), 'Independent derivation mismatch')
    state = ReviewStore(HOME/'artifacts').status(m['artifact_id'])
    require(not state['counter_evidence'], 'Registered counter-evidence needs explicit review')
    require(not any(r['decision'] == 'REJECT' and not r['revoked'] for r in state['reviews']), 'Active rejection')
    return {'artifact_sha256': m['artifact_id'], 'capture_sha256': CAPTURE,
            'evidence_ids': ['event-1'], 'checks': ['vault_and_attachment_integrity', 'original_working_identity',
            'native_register_stack_step_correlation', 'same_thread_target_execution', 'native_normalized_byte_match',
            'independent_struct_derivation', 'recorded_firewall', 'counter_registry_search']}


def publish(directory, value):
    raw = json.dumps(value, sort_keys=True, indent=2).encode()
    identity = hashlib.sha256(raw).hexdigest()
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/(identity+'.json')).open('xb') as stream:
        stream.write(raw)
    return identity


def review(policy):
    require(digest(policy) == POLICY_SHA, 'Owner directive differs from bound authorization')
    results = cross_check()
    run = HOME/'artifacts/reports'/('codex-g02-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    run.mkdir()
    commands = [[sys.executable, '-m', 'unittest', 'discover', '-s', 'tests/research'],
                ['cmake', '--build', 'build', '--config', 'Debug'], ['ctest', '--test-dir', 'build', '-C', 'Debug', '--output-on-failure'],
                ['cmake', '--build', 'build', '--config', 'Release'], ['ctest', '--test-dir', 'build', '-C', 'Release', '--output-on-failure'],
                [sys.executable, 'tools/research/artifact_vault.py', 'verify', 'all']]
    regressions = []
    for i, command in enumerate(commands):
        log = run/(str(i)+'.log')
        with log.open('xb') as output:
            result = subprocess.run(command, cwd=HOME, stdout=output, stderr=subprocess.STDOUT, timeout=600)
        regressions.append({'command': command, 'exit_code': result.returncode, 'log': str(log.relative_to(HOME))})
        print(json.dumps(regressions[-1]), flush=True)
        require(result.returncode == 0, 'Regression failed; no certificate issued')
    require(cross_check() == results, 'Evidence state changed during review')
    paths = [policy, *run.glob('*.log'), * (HOME/'tools/research').glob('*.py'), * (HOME/'tests/research').glob('*.py')]
    paths += list((HOME/'artifacts/runtime'/CAPTURE).iterdir())
    diagnostic = HOME/'artifacts/capture_work/ai-diagnostic-20260918-153813'
    paths += [p for p in diagnostic.iterdir() if p.is_file()]
    bindings = {str(p.resolve()): digest(p) for p in paths if p.is_file()}
    value = dict(results, kind='G02_CODEX_CERTIFICATE', schema_version=1, status='CODEX_VERIFIED',
                 review_type='codex_autonomous', reviewer='Codex', human_attestation=False,
                 owner_policy='codex_review_authorized', created_at=datetime.now(timezone.utc).isoformat(),
                 claim='Observed runtime transition from packed region into restored client bytes occurred',
                 rationale='Native RET, stack/register evolution and restored bytes agree; independent PE transformation reproduces the candidate.',
                 unresolved=['Memory execution-protection semantics', 'Stable OEP and normal startup', 'Imports and analysis image'],
                 counter_assessment='No registered transition counter-evidence. Later diagnostic terminates after entry into ddraw; this limits startup claims, not the earlier observed RET. PAGE_READWRITE remains unresolved, not executable-permission proof.',
                 trust_limits='Local unsigned content-hash receipt, not human review or proof against coordinated file/store tampering.',
                 regression_results=regressions, bindings=bindings, tool_versions={'python': sys.version, 'cdb': '10.0.29617.1000'})
    identity = publish(HOME/'artifacts/codex-certificates', value)
    print(json.dumps({'certificate': identity, 'audit': audit(identity)}), flush=True)


def audit(identity):
    require(re.fullmatch('[a-f0-9]{64}', identity), 'Invalid certificate ID')
    p = HOME/'artifacts/codex-certificates'/(identity+'.json')
    require(digest(p) == identity, 'Certificate changed')
    value = json.loads(p.read_text())
    require(value['kind'] == 'G02_CODEX_CERTIFICATE' and value['human_attestation'] is False, 'Wrong certificate kind')
    for rev in (HOME/'artifacts/codex-revocations').glob('*.json'):
        require(digest(rev) == rev.stem, 'Revocation changed')
        require(json.loads(rev.read_text())['certificate'] != identity, 'Certificate revoked')
    for path, expected in value['bindings'].items():
        require(digest(path) == expected, 'Bound file changed: '+path)
    require(cross_check()['capture_sha256'] == value['capture_sha256'], 'Capture changed')
    return 'VALID_CODEX_ONLY'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('review'); r.add_argument('policy', type=Path)
    a = sub.add_parser('audit'); a.add_argument('certificate')
    v = sub.add_parser('revoke'); v.add_argument('certificate'); v.add_argument('--reason', required=True)
    args = parser.parse_args()
    if args.command == 'review':
        review(args.policy.resolve(strict=True))
    elif args.command == 'audit':
        print(audit(args.certificate))
    else:
        require(re.fullmatch('[a-f0-9]{64}', args.certificate), 'Invalid certificate ID')
        require((HOME/'artifacts/codex-certificates'/(args.certificate+'.json')).is_file(), 'Unknown certificate')
        require(args.reason.strip(), 'Revocation reason required')
        print(publish(HOME/'artifacts/codex-revocations', {'certificate': args.certificate,
              'reason': args.reason, 'review_type': 'codex_autonomous', 'human_attestation': False,
              'created_at': datetime.now(timezone.utc).isoformat(), 'dependent_certificates': [],
              'scope': 'G02-only issuer; no downstream certificate issuer implemented'}))
