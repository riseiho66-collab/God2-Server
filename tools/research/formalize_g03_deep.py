"""Formalize the bounded deep capture; do not promote its incomplete G03 claim."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from runtime_evidence import RuntimeStore
from normalize_cdb_capture import mapped_to_candidate, native_bytes
from codex_g02_review import reconstruct, publish, require, digest
from host_capture import ARTIFACT, firewall_ready

HOME = Path(__file__).resolve().parents[2]
ROOT = HOME/'artifacts/capture_work/host-20260918-1430'
OUT = ROOT/'output'


def observe(native):
    names = ['PACKED', 'SOURCE', 'CANDIDATE', 'CALLEE_A', 'INTERNAL_A', 'RETURN_A',
             'CALLEE_B', 'INTERNAL_B', 'RETURN_B', 'WINDOW_END']
    marks = {}
    for name in names:
        rows = re.findall(r'^DEEP_'+name+r' (.+)$', native, re.M)
        require(len(rows) == 1, 'Missing/duplicate stop: '+name)
        marks[name] = {k: int(v, 16) for k, v in re.findall(r'(\w+)=([0-9a-f]+)', rows[0])}
    first = marks['PACKED']
    require(all(m['pid'] == first['pid'] and m['tid'] == first['tid'] for m in marks.values()), 'Thread/process changed')
    times = [m['time'] for m in marks.values()]
    require(times == sorted(times), 'Time order')
    require(first['base'] == 0x400000 and first['pc'] == 0x702001, 'Unexpected base/entry')
    for name, pc in [('SOURCE', 0x7023bf), ('CANDIDATE', 0x54a3e8), ('CALLEE_A', 0x54f12a),
                     ('RETURN_A', 0x54a446), ('CALLEE_B', 0x54df7c), ('RETURN_B', 0x54a458)]:
        require(marks[name]['pc'] == pc, 'Unexpected stop '+name)
    require(marks['SOURCE']['target'] == marks['CANDIDATE']['pc'], 'RET target mismatch')
    require('No runnable debuggees' not in native and 'Unable to create file' not in native, 'Native command failure')
    require('eip=007023bf esp=001aff74' in native and '001aff74  0054a3e8' in native
            and 'eip=0054a3e8 esp=001aff78' in native, 'Missing native RET register/stack chain')
    return marks


def main():
    native = (OUT/'g03-deep-stdout.log').read_text(encoding='ascii')
    marks = observe(native)
    before, after = (OUT/'g03-deep-before.bin').read_bytes(), (OUT/'g03-deep-after.bin').read_bytes()
    require(len(before) == len(after) == 0x307000 and after[0x3023bf] == 0xc3, 'Mapped images invalid')
    require(before[0x14a3e8:0x14a408] == bytes(32), 'Before region differs')
    for name, image in [('PACKED', before), ('CANDIDATE', after), ('CALLEE_A', after), ('CALLEE_B', after)]:
        pc = marks[name]['pc']; rva = pc-0x400000
        require(native_bytes(native, pc) == image[rva:rva+32], 'Native/image mismatch '+name)
    candidate, derivation = mapped_to_candidate(after, 0x14a3e8)
    require(candidate == reconstruct(after, 0x14a3e8), 'Independent reconstruction mismatch')
    request = json.loads((ROOT/'host-request.json').read_text())
    launch = json.loads((OUT/'g03-deep-result.json').read_text())
    require(not launch['timed_out'] and launch['exit_code'] == 0, 'Launch failed')
    require(digest(request['original']) == digest(ROOT/'client/God2.exe') == ARTIFACT, 'Original/working changed')
    require(firewall_ready(json.loads((OUT/'g03-deep-firewall.json').read_text()), request['programs']), 'Firewall failed')
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoded = []
    for addr, raw in re.findall(r'^([0-9a-f]{8}) ([0-9a-f]{2,30})\s+', native, re.M):
        pc, code = int(addr, 16), bytes.fromhex(raw)
        if 0x401000 <= pc < 0x702000:
            require(after[pc-0x400000:pc-0x400000+len(code)] == code, 'Runtime instruction/image mismatch')
            ins = list(decoder.disasm(code, pc))
            require(len(ins) == 1 and ins[0].size == len(code), 'Native/Capstone boundary mismatch')
            decoded.append({'va': pc, 'bytes': raw, 'instruction': ins[0].mnemonic+' '+ins[0].op_str})
    require(len(decoded) >= 20, 'Insufficient static/runtime comparisons')
    store = RuntimeStore(HOME/'artifacts')
    dest = HOME/'artifacts/capture_requests/g03-deep-20260919'
    store.prepare(ARTIFACT, dest)
    events = []
    def add(name, kind, details):
        m = marks[name]
        events.append({'id': 'deep-'+str(len(events)), 'seq': len(events),
            'timestamp_ns': (m['time']-116444736000000000)*100, 'thread_id': m['tid'],
            'pc': m['pc'], 'state': 'OBSERVED_NOT_G03_VERIFIED', 'type': kind, 'details': details})
    add('PACKED', 'function_enter', {'bytes_hex': before[0x302001:0x302021].hex()})
    add('CANDIDATE', 'unpack_transition', {'from_va': 0x7023bf, 'to_va': 0x54a3e8,
        'region_va': 0x54a3e8, 'before_hex': before[0x14a3e8:0x14a408].hex(),
        'after_hex': after[0x14a3e8:0x14a408].hex(), 'memory_file': 'after.bin'})
    add('CANDIDATE', 'oep_candidate', {'rva': 0x14a3e8, 'bytes_hex': after[0x14a3e8:0x14a408].hex(),
        'memory_file': 'after.bin', 'unpacked_file': 'unpacked-candidate.exe', 'continued_event_ids': ['deep-3', 'deep-4']})
    for name in ('CALLEE_A', 'CALLEE_B'):
        rva = marks[name]['pc']-0x400000
        add(name, 'function_enter', {'bytes_hex': after[rva:rva+32].hex()})
    (dest/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events), encoding='utf-8')
    (dest/'unpacked-candidate.exe').write_bytes(candidate)
    derivation.update(parent_sha256=hashlib.sha256(after).hexdigest(), candidate_sha256=hashlib.sha256(candidate).hexdigest(),
                      original_artifact_id=ARTIFACT, independent_struct_match=True)
    (dest/'derivation.json').write_text(json.dumps(derivation, indent=2))
    (dest/'static-correlation.json').write_text(json.dumps({'decoder': 'Capstone 5.0.7', 'native_path': 'CDB disassembly', 'instructions': decoded}, indent=2))
    attachments = [('events.jsonl', 'events'), ('unpacked-candidate.exe', 'unpacked_pe'),
                   ('derivation.json', 'raw_trace'), ('static-correlation.json', 'raw_trace')]
    for source, name, role in [('g03-deep-before.bin', 'before.bin', 'memory_image'),
        ('g03-deep-after.bin', 'after.bin', 'memory_image'), ('g03-deep-stdout.log', 'native-cdb.log', 'raw_trace'),
        ('g03-deep-result.json', 'launch.json', 'raw_trace'), ('g03-deep-firewall.json', 'firewall.json', 'raw_trace'),
        ('g03-deep-policy.json', 'dep-policy.json', 'raw_trace'), ('capture-g03-deep.txt', 'commands.txt', 'raw_trace')]:
        shutil.copy2(OUT/source, dest/name); attachments.append((name, role))
    shutil.copy2(ROOT/'host-request.json', dest/'host-request.json'); attachments.append(('host-request.json', 'raw_trace'))
    manifest = json.loads((dest/'manifest.json').read_text())
    manifest['session_id'] = 'G03-DEEP-20260919'
    manifest['process'].update(pid=marks['PACKED']['pid'], module_base=0x400000)
    manifest['scope']['ranges'] = [[0x400000, 0x707000]]
    manifest['provenance'].update(tool='windbg', tool_version='CDB 10.0.29617.1000', operator='Codex',
        captured_at=launch['started_at'], environment_id=ROOT.name, isolation='loopback-only', working_copy_sha256=ARTIFACT)
    manifest['files'] = [{'path': name, 'role': role, 'size': (dest/name).stat().st_size, 'sha256': digest(dest/name)} for name, role in attachments]
    (dest/'manifest.json').write_text(json.dumps(manifest, indent=2))
    sealed = store.seal(dest, HOME/'artifacts/capture_inbox/g03-deep-20260919')
    cid = store.ingest(sealed['bundle'])
    assessment = store.assess(cid)
    require(assessment['gates']['unpack']['status'] == 'READY_FOR_REVIEW', 'New unpack failed')
    print(json.dumps({'capture': cid, 'assessment': assessment, 'static_instruction_comparisons': len(decoded)}, indent=2))


if __name__ == '__main__':
    main()
