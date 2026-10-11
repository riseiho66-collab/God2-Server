"""Qualify recovered pseudocode against formal PE and actual VM_READ evidence.

Publishes separately from the earlier reconstruction, with raw-byte provenance.
It certifies code identity only; it does not certify original server formulas.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM

ROOT = Path(__file__).resolve().parents[2]
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def qualify(capture, directories):
    receipt_raw = (capture / 'memory-result.json').read_bytes()
    receipt = json.loads(receipt_raw)
    require(receipt['accepted'] and receipt['process_memory_writes'] == 0
            and receipt['desktop_unchanged'] and receipt['owned_client_closed'],
            'Qualified read-only live memory receipt required')
    metadata = receipt['capture']['whole_live_text']
    live = (capture / metadata['file']).read_bytes()
    require(sha(live) == metadata['live_sha256'], 'Actual code checksum mismatch')
    formal_raw = (ROOT.parent / 'God2/God2.exe').read_bytes()
    require(sha(formal_raw) == CLIENT_SHA, 'Formal client build mismatch')
    image = pefile.PE(data=formal_raw).get_memory_mapped_image()
    origin = 0x400000 + int(metadata['rva'], 16)
    planner = receipt['capture'].get('combat_producer_state')
    if planner:
        skill_address = int(receipt['capture']['skills']['address'], 16)
        require(int(planner['skill_manager'], 16) == skill_address - 0xa7e0444
                and int(planner['battle_owner'], 16) == skill_address - 0xa7e0444 - 0x144938,
                'Derived combat owner mismatch')
        for state in planner['states']:
            raw = bytes.fromhex(state['hex'])
            require(len(raw) == state['size'] and sha(raw) == state['sha256'],
                    'Combat memory state checksum mismatch')
        for constant in planner['constants']:
            offset = int(constant['address'], 16) - 0x400000
            require(image[offset:offset + constant['size']].hex() == constant['hex'],
                    'Planner constant differs from current formal image')
    recovered = []
    instruction_count = 0
    entries = set()
    for directory in directories:
        require((directory / 'complete.txt').read_text('utf-8').splitlines() ==
                [CLIENT_SHA, 'TRANSIENT_READONLY_NO_PROJECT_SAVE'], 'Ghidra identity mismatch')
        instructions = rows(directory / 'instructions.tsv')
        for row in rows(directory / 'functions.tsv'):
            entry = int(row['entry'], 16)
            end = int(row['end'], 16)
            require(entry not in entries, 'Duplicate recovered entry')
            entries.add(entry)
            require(row['decompile_completed'] == 'true', 'Incomplete decompilation')
            raw = image[entry - 0x400000:end - 0x400000 + 1]
            require(raw == live[entry - origin:end - origin + 1], 'Full code range differs in RAM')
            count = 0
            for instruction in instructions:
                if int(instruction['function'], 16) != entry:
                    continue
                at = int(instruction['address'], 16)
                code = bytes.fromhex(instruction['bytes'])
                require(image[at - 0x400000:at - 0x400000 + len(code)] == code
                        and live[at - origin:at - origin + len(code)] == code,
                        'Reconstruction instruction mismatch')
                count += 1
            require(count > 0, 'Empty instruction evidence')
            source = directory / (row['entry'] + '.c')
            recovered.append({'entry': hex(entry), 'end': hex(end),
                'body_bytes': int(row['body_bytes']), 'code_span_sha256': sha(raw),
                'instruction_count': count, 'pseudocode_sha256': sha(source.read_bytes()),
                'pseudocode_file': source.name, 'evidence_directory': str(directory.relative_to(ROOT)),
                'created_transiently': row['created_transiently'] == 'true',
                'authority': 'CODE_IDENTITY_VERIFIED; NOT_ORIGINAL_CPP_OR_SERVER_BALANCE'})
            instruction_count += count
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    decoder.detail = True
    decoder.skipdata = True
    incoming = []
    for instruction in decoder.disasm(live, origin):
        if not instruction.id:
            continue
        for operand in instruction.operands:
            if operand.type == X86_OP_IMM and operand.imm in entries:
                incoming.append({'from': hex(instruction.address), 'target': hex(operand.imm),
                                 'instruction': instruction.mnemonic + ' ' + instruction.op_str,
                                 'authority': 'LINEAR_DECODE_REFERENCE_REQUIRES_CALLER_QUALIFICATION'})
    return {'client_sha256': CLIENT_SHA, 'memory_receipt_sha256': sha(receipt_raw),
            'memory_receipt': str(capture.relative_to(ROOT)), 'functions': recovered,
            'planner_live_constants_match_formal_image': bool(planner),
            'planner_populated_rows': planner['planning_rows'] if planner else None,
            'instruction_count': instruction_count, 'linear_incoming_candidates': incoming,
            'original_formulas_recovered': 0,
            'limits': ['Decompilation is reconstructed pseudocode, not original C++.',
                       'No direct reference is not proof that indirect calls cannot reach code.',
                       'Planning arithmetic and result display are not server damage generation.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--publish', type=Path)
    args = parser.parse_args()
    directories = [path.resolve() for path in args.evidence]
    result = qualify(args.capture.resolve(), directories)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.publish:
        destination = args.publish.resolve()
        reconstruction = ROOT.parent.parent / 'God2-解殼EXE原始碼重建'
        require(destination.is_relative_to(reconstruction), 'Separate reconstruction folder required')
        destination.mkdir(parents=True, exist_ok=False)
        for function in result['functions']:
            source = ROOT / function['evidence_directory'] / function['pseudocode_file']
            shutil.copyfile(source, destination / source.name)
        shutil.copyfile(args.output, destination / 'manifest.json')
        (destination / 'README.md').write_text(
            '# 記憶體核對後新增的戰鬥函式重建\n\n'
            '本資料夾獨立保存重建的反編譯擬碼；不是可直接編譯的原始 C++。\n'
            'manifest.json 記錄正式 EXE、實際記憶體、每段指令及來源檔案的核對結果。\n'
            '函式的數值來源與實際用途仍需逐一確認，不能視為原始服務端傷害公式。\n',
            encoding='utf-8')
    print(json.dumps({'verified_functions': len(result['functions']),
                      'verified_instructions': result['instruction_count'],
                      'original_formulas_recovered': 0}))


if __name__ == '__main__':
    main()
