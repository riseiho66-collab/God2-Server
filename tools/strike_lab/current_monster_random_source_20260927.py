"""Bounded current-image rand call census; never a spawn configuration generator."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct

from .current_battle_entry import pinned_image, IMAGE_SHA256
import pefile
import capstone

ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT.parent.parent / 'God2-解殼EXE原始碼重建'
RAND = 0x547d7f


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    image = pinned_image()
    client = ROOT.parent / 'God2' / 'God2.exe'
    pe = pefile.PE(str(client))
    mapped = pe.get_memory_mapped_image()
    sections = [s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text' or
                s.Characteristics & 0x20000000]
    with (RECON / 'decompiled/functions.tsv').open(encoding='utf-8-sig', newline='') as handle:
        functions = list(csv.DictReader(handle, delimiter='\t'))
    ranges = [(int(f['entry'], 16), int(f['end'], 16), f) for f in functions
              if f['external'] == 'false']
    calls, compared, excluded = [], [], []
    for section in sections:
        start = section.VirtualAddress
        stop = min(start + section.Misc_VirtualSize, len(image), len(mapped))
        if stop <= start:
            excluded.append({'name': section.Name.rstrip(b'\0').decode('ascii'),
                             'start_rva': hex(start), 'reason': 'outside pinned original image'})
            continue
        raw = image[start:stop]
        difference_offsets = [start+i for i, (a,b) in enumerate(zip(raw, mapped[start:stop])) if a != b]
        compared.append({'name': section.Name.rstrip(b'\0').decode('ascii'),
                         'start_rva': hex(start), 'end_rva': hex(stop),
                         'sha256': hashlib.sha256(raw).hexdigest(),
                         'current_pe_sha256': hashlib.sha256(mapped[start:stop]).hexdigest(),
                         'difference_byte_count': len(difference_offsets),
                         'difference_rvas': [hex(v) for v in difference_offsets]})
        for pos in range(len(raw)-4):
            if raw[pos] != 0xe8:
                continue
            va = 0x400000 + start + pos
            if va + 5 + struct.unpack_from('<i', raw, pos+1)[0] != RAND:
                continue
            require(raw[pos:pos+5] == mapped[start+pos:start+pos+5], 'Current rand call bytes differ')
            owners = [f for lo, hi, f in ranges if lo <= va <= hi]
            calls.append({'va': hex(va), 'bytes': raw[pos:pos+5].hex(),
                          'containing_exported_functions': [f['entry'] for f in owners],
                          'qualification': 'raw E8 target; instruction boundary not asserted'})
    pseudo = []
    for f in functions:
        if not f['pseudocode_file']:
            continue
        path = RECON / 'decompiled' / f['pseudocode_file']
        if not path.is_file():
            continue
        raw = path.read_bytes()
        text = raw.decode('utf-8', errors='replace')
        lines = [i for i, line in enumerate(text.splitlines(), 1) if '_rand(' in line]
        if lines and int(f['entry'], 16) != RAND:
            pseudo.append({'entry': f['entry'], 'end': f['end'],
                           'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
                           'rand_reference_lines': lines})
    lead_entries = ['00454210', '00466b00', '0047fc60', '004d7900', '004d7db0',
                    '005024c0', '00502700', '0047fbb0', '00480890']
    leads = []
    for entry in lead_entries:
        f = next(f for f in functions if f['entry'].lower() == entry)
        lo, hi = int(f['entry'], 16)-0x400000, int(f['end'], 16)-0x400000+1
        require(image[lo:hi] == mapped[lo:hi], 'Lead function differs in current PE')
        leads.append({'entry': entry, 'end': f['end'], 'body_bytes': f['body_bytes'],
                      'envelope_sha256': hashlib.sha256(image[lo:hi]).hexdigest(),
                      'qualification': 'matched function envelope, not execution acceptance'})
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    gaps = []
    for lo, hi in ((0x474ab0, 0x474b8d), (0x475400, 0x475527), (0x411200, 0x411259)):
        raw = image[lo-0x400000:hi-0x400000]
        require(raw == mapped[lo-0x400000:hi-0x400000], 'Unexported code differs in current PE')
        instructions = list(decoder.disasm(raw, lo))
        require(instructions and sum(i.size for i in instructions) == len(raw), 'Gap decode incomplete')
        incoming = []
        for section in sections:
            start = section.VirtualAddress
            stop = min(start+section.Misc_VirtualSize, len(image))
            for at in range(start, stop-4):
                if image[at] in (0xe8, 0xe9) and 0x400000+at+5+struct.unpack_from('<i',image,at+1)[0] == lo:
                    incoming.append({'va': hex(0x400000+at), 'opcode': hex(image[at]),
                                     'qualification': 'raw relative target, not proven active caller'})
        gaps.append({'start_va': hex(lo), 'end_va_exclusive': hex(hi),
                     'sha256': hashlib.sha256(raw).hexdigest(), 'raw_incoming': incoming,
                     'instructions': [{'va': hex(i.address), 'bytes': i.bytes.hex(),
                                       'mnemonic': i.mnemonic, 'operands': i.op_str} for i in instructions]})
    literals = []
    for va in (0x58e030, 0x5823b4, 0x5854d8):
        raw = image[va-0x400000:].split(b'\0',1)[0]
        require(raw+b'\0' == mapped[va-0x400000:va-0x400000+len(raw)+1], 'Literal differs')
        literals.append({'va': hex(va), 'hex': raw.hex(), 'ascii': raw.decode('ascii')})
    result = {'status': 'PASS', 'image_sha256': IMAGE_SHA256,
              'client_sha256': hashlib.sha256(client.read_bytes()).hexdigest(),
              'rand_entry_va': hex(RAND), 'code_sections_compared': compared,
              'excluded_current_pe_sections': excluded,
              'raw_direct_call_candidates': calls, 'pseudocode_rand_callers': pseudo,
              'lead_function_envelopes': leads,
              'unexported_helper_disassembly': gaps, 'helper_literals': literals,
              'qualified_native_spawn_records': 0, 'runtime_mutation_enabled': False,
              'limitations': ['Indirect calls and unexported functions remain separate leads.',
                             'Call census does not prove absence of all encounter logic.',
                             'No native RNG or full world update is executed.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'raw_call_candidates': len(calls),
                      'pseudocode_callers': len(pseudo), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
