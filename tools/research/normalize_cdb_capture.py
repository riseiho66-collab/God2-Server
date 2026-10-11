"""Normalize the observed GOD2 CDB RET transition; never infer missing stops."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

import pefile

from host_capture import ARTIFACT, digest, firewall_ready
from runtime_evidence import RuntimeStore


def observed_marks(native):
    names = ('PACKER', 'TRANSFER_SOURCE', 'TRANSFER_TARGET', 'CONTINUATION_1', 'CONTINUATION_2', 'STARTUP_CALL')
    marks = {}
    for name in names:
        pattern = (r'^GOD2_'+name+r' pid=([0-9a-f]+) tid=([0-9a-f]+) base=([0-9a-f]+) pc=([0-9a-f]+)'
                   r'(?: target=([0-9a-f]+))? time=([0-9a-f]+)\r?$')
        matches = re.findall(pattern, native, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError('Missing/ambiguous native stop: '+name)
        values = matches[0]
        marks[name] = dict(zip(('pid', 'tid', 'base', 'pc', 'target', 'filetime'), (int(v, 16) if v else None for v in values)))
    first = marks['PACKER']
    if any(any(m[k] != first[k] for k in ('pid', 'tid', 'base')) for m in marks.values()):
        raise ValueError('Native capture changes process/thread/base')
    times = [m['filetime'] for m in marks.values()]
    if times != sorted(times):
        raise ValueError('Native timestamps are out of order')
    base = first['base']
    expected = {'PACKER': 0x302001, 'TRANSFER_SOURCE': 0x3023bf, 'TRANSFER_TARGET': 0x14a3e8,
                'CONTINUATION_1': 0x14a3e9, 'CONTINUATION_2': 0x14a3eb, 'STARTUP_CALL': 0x14a40e}
    if any(marks[n]['pc'] != base+rva for n, rva in expected.items()):
        raise ValueError('Observed stops differ from this bounded normalization contract')
    if marks['TRANSFER_SOURCE']['target'] != marks['TRANSFER_TARGET']['pc']:
        raise ValueError('RET stack target disagrees with single-step target')
    return marks


def native_bytes(native, address):
    chunks = []
    for offset in (0, 16):
        rows = re.findall(r'^'+f'{address+offset:08x}'+r'  ((?:[0-9a-f]{2}[ -]){15}[0-9a-f]{2})', native, re.MULTILINE)
        if len(rows) != 1:
            raise ValueError('Missing/ambiguous native byte row')
        chunks.append(bytes.fromhex(rows[0].replace('-', ' ')))
    return b''.join(chunks)


def mapped_to_candidate(mapped, rva):
    pe = pefile.PE(data=mapped, fast_load=True)
    try:
        if len(mapped) != pe.OPTIONAL_HEADER.SizeOfImage or pe.FILE_HEADER.Machine != 0x14c:
            raise ValueError('Mapped image size/architecture mismatch')
        changes = []
        for index, section in enumerate(pe.sections):
            alignment = pe.OPTIONAL_HEADER.FileAlignment
            size = ((section.Misc_VirtualSize+alignment-1)//alignment)*alignment
            limit = pe.sections[index+1].VirtualAddress if index+1 < len(pe.sections) else len(mapped)
            if not size or section.VirtualAddress+size > limit:
                raise ValueError('Cannot represent mapped section without overlap/truncation')
            changes.append({'section': section.Name.rstrip(b'\0').decode('ascii'),
                            'old_raw_pointer': section.PointerToRawData, 'new_raw_pointer': section.VirtualAddress,
                            'old_raw_size': section.SizeOfRawData, 'new_raw_size': size,
                            'characteristics_preserved': section.Characteristics})
            section.PointerToRawData, section.SizeOfRawData = section.VirtualAddress, size
        entry = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        pe.OPTIONAL_HEADER.AddressOfEntryPoint = rva
        result = pe.write()
        return result, {'sections': changes, 'old_entry_rva': entry, 'candidate_entry_rva': rva,
                        'imports_repaired': False, 'executable_section_flags_changed': False,
                        'warning': 'Derived PE candidate only; original section flags preserved. Runtime PAGE_READWRITE does not establish executable PE section flags. Not G03/G04/G04.5 verified.'}
    finally:
        pe.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-root', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.host_root.resolve(strict=True), args.host_root.resolve(strict=True)/'output'
    request = json.loads((root/'host-request.json').read_text())
    probe = json.loads((output/'host-probe.json').read_text())
    launch = json.loads((output/'transition-result.json').read_text())
    firewall = json.loads((output/'transition-firewall.json').read_text())
    if not probe['ready'] or launch['timed_out'] or launch['exit_code'] != 0 or not firewall_ready(firewall, request['programs']):
        raise ValueError('Capture prerequisites did not pass')
    if digest(root/'client/God2.exe') != ARTIFACT or digest(request['original']) != ARTIFACT:
        raise ValueError('Original/working identity changed')
    native = (output/'transition-stdout.log').read_bytes().decode('ascii', errors='replace')
    if 'Unable to create file' in native or 'No runnable debuggees' in native:
        raise ValueError('Capture contains failed native operations')
    marks = observed_marks(native)
    before, after = (output/'transition-before.bin').read_bytes(), (output/'transition-after.bin').read_bytes()
    if len(before) != 0x307000 or len(after) != 0x307000 or after[0x3023bf] != 0xc3:
        raise ValueError('Missing full mapped images or observed RET byte')
    if native_bytes(native, marks['PACKER']['pc']) != before[0x302001:0x302021]:
        raise ValueError('Packer native bytes disagree with before image')
    code = after[0x14a3e8:0x14a408]
    if native_bytes(native, marks['TRANSFER_TARGET']['pc']) != code or before[0x14a3e8:0x14a408] == code:
        raise ValueError('Native target bytes disagree or were not restored')
    candidate, derivation = mapped_to_candidate(after, 0x14a3e8)
    RuntimeStore(Path('artifacts')).prepare(ARTIFACT, args.destination)
    dest = args.destination
    manifest = json.loads((dest/'manifest.json').read_text())
    base, pid = marks['PACKER']['base'], marks['PACKER']['pid']
    manifest.update(session_id='HOST-CDB-20260918-TRANSITION', process={'pid': pid, 'architecture': 'x86',
                    'module_base': base, 'image_size': len(after)}, scope={'purpose': 'network-reconstruction',
                    'ranges': [[base, base+len(after)]]})
    manifest['provenance'].update(tool='windbg', tool_version='CDB '+request['tool']['product_version'],
        operator='Codex automation / SEIHO-risei', captured_at=launch['started_at'], environment_id=root.name,
        isolation='loopback-only', working_copy_sha256=digest(root/'client/God2.exe'))
    events = []
    def event(name, kind, details, state):
        m = marks[name]
        events.append({'id': 'event-'+str(len(events)), 'seq': len(events),
                       'timestamp_ns': (m['filetime']-116444736000000000)*100, 'thread_id': m['tid'],
                       'pc': m['pc'], 'state': state, 'type': kind, 'details': details})
    event('PACKER', 'function_enter', {'bytes_hex': before[0x302001:0x302021].hex()}, 'PACKED_ENTRY_OBSERVED')
    event('TRANSFER_TARGET', 'unpack_transition', {'from_va': marks['TRANSFER_SOURCE']['pc'],
          'to_va': marks['TRANSFER_TARGET']['pc'], 'region_va': base+0x14a3e8,
          'before_hex': before[0x14a3e8:0x14a408].hex(), 'after_hex': code.hex(),
          'memory_file': 'after.bin'}, 'RESTORED_REGION_TRANSFER_OBSERVED')
    event('TRANSFER_TARGET', 'function_enter', {'bytes_hex': code.hex()}, 'STARTUP_ENTRY_CANDIDATE_NOT_VERIFIED')
    (dest/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events), encoding='utf-8')
    (dest/'unpacked-candidate.exe').write_bytes(candidate)
    derivation.update(parent_sha256=hashlib.sha256(after).hexdigest(), original_artifact_id=ARTIFACT,
                      candidate_sha256=hashlib.sha256(candidate).hexdigest(), created_at=datetime.now(timezone.utc).isoformat(),
                      capture_binding='Capture ID is SHA256 of sealed manifest; membership binds these files to that ID.',
                      environment_limitations=request['limitation'], native_marks=marks)
    (dest/'derivation.json').write_text(json.dumps(derivation, indent=2), encoding='utf-8')
    attachments = [('events.jsonl', 'events'), ('unpacked-candidate.exe', 'unpacked_pe'), ('derivation.json', 'raw_trace')]
    for source, name, role in [(output/'transition-before.bin', 'before.bin', 'memory_image'),
                               (output/'transition-after.bin', 'after.bin', 'memory_image'),
                               (output/'transition-stdout.log', 'native-cdb.log', 'raw_trace'),
                               (output/'capture-transition.txt', 'debugger-commands.txt', 'raw_trace'),
                               (output/'transition-result.json', 'launch.json', 'raw_trace'),
                               (output/'transition-firewall.json', 'firewall.json', 'raw_trace'),
                               (output/'host-probe.json', 'host-probe.json', 'raw_trace'),
                               (root/'host-request.json', 'host-request.json', 'raw_trace')]:
        shutil.copy2(source, dest/name)
        attachments.append((name, role))
    manifest['files'] = [{'path': name, 'role': role, 'size': (dest/name).stat().st_size, 'sha256': digest(dest/name)} for name, role in attachments]
    (dest/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    bundle = RuntimeStore(Path('artifacts')).validate_bundle(dest)
    print(json.dumps({'worksheet_id': bundle['capture_id'], 'pid': pid, 'events': len(events), 'candidate_sha256': derivation['candidate_sha256']}))


if __name__ == '__main__':
    main()
