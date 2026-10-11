"""Read pinned CN PE/source spans for character mutation contracts; never execute them."""
import csv
import hashlib
import json
import struct
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT, CN, RECOVERY, PIN
from .cn_summary_world_lineage_delivery import trace
from .cn_pe_import_directory import import_directory, FileView

NAME = 'cn-character-mutation-contract-01'
FUNCTIONS = ('00440140', '004413f0', '00446bd0', '0043d280',
             '00448950', '00448ca0', '0047e900', '00481390',
             '0047e960', '0047dcc0', '0047e330', '0047db70',
             '00440ca0', '00445040', '0043d640', '0043d8b0',
             '0047d8d0', '00481440', '0047f430', '0047e4d0',
             '00444fe0', '0043dba0', '0047ed00')


def main():
    out = ROOT / 'artifacts/integration/packet-connections-20261006' / NAME
    if out.exists():
        raise RuntimeError('Preserve historical delivery; use a fresh artifact name')
    image = CN.parent / 'XJZ-CN/God2_opt.exe'
    raw = image.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise RuntimeError('Pinned CN image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    with (RECOVERY / 'functions.tsv').open(encoding='utf-8-sig') as f:
        rows = {r['address'].lower(): r for r in csv.DictReader(f, delimiter='\t')}
    prepared = []
    for stem in FUNCTIONS:
        row = rows[stem]
        source = RECOVERY / row['file']
        address, size = int(stem, 16), int(row['bytes'])
        code = pe.get_data(address-base, size)
        prepared.append((stem, row, source, code))
    out.mkdir(parents=True)
    files, spans, calls = [], [], []

    def save(rel, data, original=None):
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        files.append({'path': rel, 'original': original, 'bytes': len(data),
                      'sha256': hashlib.sha256(data).hexdigest()})

    for stem, row, source, code in prepared:
        address = int(stem, 16)
        save('native/'+stem+'.c', source.read_bytes(), str(source))
        save('native/'+stem+'.bin', code, str(image)+':VA'+stem)
        insns = list(md.disasm(code, address))
        save('native/'+stem+'.asm', ('\n'.join(
            f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
            for i in insns)+'\n').encode(), str(image)+':VA'+stem)
        spans.append({'entry': stem, 'metadata_bytes': len(code), 'metadata_file': row['file'],
                      'linear_decode_bytes': sum(i.size for i in insns),
                      'method': 'METADATA_BOUNDED_LINEAR_DISASSEMBLY_NOT_CFG_CLOSURE'})
        for i in insns:
            if i.mnemonic == 'call':
                calls.append({'function': stem, 'site': f'{i.address:08x}', 'operand': i.op_str})
        if stem == '0047ed00':
            # Primary range check subtracts3, bounds EAX<=1C, then indexes
            # this table OUTSIDE the metadata-sized function span.
            table = pe.get_data(0x47f29c-base, 29*4)
            targets = struct.unpack('<29I', table)
            save('native/0047ed00-switch.bin', table, str(image)+':VA0047f29c')
            cfg, asm, _ = trace(md, code, address, address+len(code), {0x47ed19: targets})
            cfg['qualified_switch'] = {'dispatch': '0047ed19', 'table': '0047f29c',
                'input_first_byte_subtract': 3, 'bounded_indices': 29,
                'control8_target': f'{targets[8-3]:08x}'}
            save('native/0047ed00-cfg.json', (json.dumps(cfg, indent=2)+'\n').encode())
            save('native/0047ed00-cfg.asm', asm)
    # Read the on-disk pointer and import-directory identity only. Neither
    # operation observes the loaded game's potentially rewritten bindings.
    declared = import_directory(pe, raw)
    pointer = pe.get_data(0xaaf25c-base, 4)
    file_value = struct.unpack('<I', pointer)[0]
    imports = [r for r in declared['bindings'] if r['iat_va'] == '00aaf25c']
    boundary = {'call_site': '0047eb58', 'indirect_pointer_va': '00aaf25c',
                'pe_pointer_bytes': pointer.hex(), 'pe_pointer_u32': f'{file_value:08x}',
                'pe_import_directory_matches': imports,
                'file_iat_value_not_loaded_callable_va': True,
                'import_descriptor_count': declared['descriptor_count'],
                'prior_boundary_correction': 'cn-delete-import-binding-01/findings.json',
                'current_loaded_module_or_dynamic_binding_inspected': False,
                'native_execution': False, 'complete_caller_continuation_proven': False}
    save('delete-indirect-call-boundary.json', (json.dumps(boundary, indent=2)+'\n').encode())
    # A file thunk's low31 bits reference IMAGE_IMPORT_BY_NAME byRVA. Never
    # disassemble that value as a loadedVA or follow it as a code call target.
    for binding in imports:
        if binding.get('hint_name_rva'):
            rva = int(binding['hint_name_rva'], 16)
            save(f'native/import-name-rva{rva:08x}.bin',
                 FileView(pe, raw).read(rva, 2+len(binding['name'].encode('ascii'))+1),
                 str(image)+f':RVA{rva:08x}')
    save('delivery-tool.py', Path(__file__).read_bytes(), str(Path(__file__)))
    manifest = {'native_image': str(image), 'native_sha256': PIN,
                'machine': pe.FILE_HEADER.Machine, 'image_base': f'{base:08x}',
                'functions': spans, 'calls_navigation_only': calls,
                'files': files, 'native_execution': False, 'build_run': False,
                'tests_run': False, 'database_access': False, 'deployed': False,
                'limits': ['Metadata spans may contain fragmented functions or data; no whole-function or whole-game closure claim.',
                           'Linear call matches are navigation only; manually inspect control flow and ECX ownership before assigning a phase.',
                           'File imports declare DLL/symbol identity, not observed loaded callable addresses.',
                           'No captured official server records, issuer policy, storage transaction or gameplay completion is established.']}
    (out/'native-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'native_functions': len(spans), 'static_only': True}))


if __name__ == '__main__':
    main()
