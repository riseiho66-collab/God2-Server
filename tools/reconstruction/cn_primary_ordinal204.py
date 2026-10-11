"""204 bounded native primary ordinal lookup capture; static file input only."""
from pathlib import Path
import csv
import hashlib
import json
import capstone
import pefile

ROOT = Path(__file__).resolve().parents[2]
RECOVERY = Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
PE_PATH = Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
OUT = ROOT / 'artifacts/integration/packet-connections-20261006/cn-primary-skill-ordinal-source-01/agents/primary-ordinal-native'
PRIOR = ROOT / 'artifacts/integration/packet-connections-20261006/cn-primary-skill-definition-source-01/agents/primary-population-source'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def put(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    if OUT.exists():
        raise SystemExit('Preserve actual captured epochs; output already exists')
    OUT.mkdir(parents=True)
    originals, current, native, historical = [], [], [], []

    def copy_original(path, relative, collection, include_original=True):
        data = path.read_bytes()
        destination = OUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        row = dict(path=str(path.resolve()), copy=relative, bytes=len(data), sha256=digest(data))
        collection.append(row)
        if include_original:
            originals.append(row)
        return row

    raw = PE_PATH.read_bytes()
    assert len(raw) == 47541760 and digest(raw) == PIN
    pe = pefile.PE(data=raw, fast_load=True)
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    references = []
    caller = RECOVERY / 'part_0012/004da630_FUN_004da630.c'
    for path in (PE_PATH, RECOVERY / 'functions.tsv', RECOVERY / 'calls.tsv', caller):
        data = path.read_bytes()
        references.append(dict(path=str(path.resolve()), copy=None, bytes=len(data), sha256=digest(data), disposition='Complete actual file hashed in place; no whole PE/TSV/caller C copy'))

    metadata = []
    with (RECOVERY / 'functions.tsv').open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['address'].lower() in ('004d2b50', '004da630'):
                metadata.append(row)
    assert len(metadata) == 2
    leaf = RECOVERY / 'part_0011/004d2b50_FUN_004d2b50.c'
    copy_original(leaf, 'originals/native/leaf.c', native)
    for index, name in enumerate(('AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md', 'tools/reconstruction/cn_primary_ordinal204.py')):
        copy_original(ROOT / name, f'originals/source/r{index:02}.txt', current)
    (OUT / 'epochs').mkdir()
    (OUT / 'epochs/tool-initial.py').write_bytes(Path(__file__).read_bytes())
    for name in ('findings.json', 'native-spans.json', 'native-original-inputs.json', 'seal.json'):
        copy_original(PRIOR / name, f'epochs/prior203-{name}', historical, False)

    prior_spans = json.loads((PRIOR / 'native-spans.json').read_text(encoding='utf-8'))
    prior_inputs = json.loads((PRIOR / 'native-original-inputs.json').read_text(encoding='utf-8'))
    previous_leaf = next(row for row in prior_inputs if Path(row['path']).name == leaf.name)
    leaf_bytes = leaf.read_bytes()
    assert len(leaf_bytes) == previous_leaf['bytes'] and digest(leaf_bytes) == previous_leaf['sha256']
    previous_copy = PRIOR / previous_leaf['copy']
    assert previous_copy.read_bytes() == leaf_bytes
    put('prior-layer-comparison.json', dict(scope='Compared exact round203 manifest and full leaf canonical copy only; not a global unique native coverage audit', prior_seal_sha256=digest((PRIOR / 'seal.json').read_bytes()), leaf_canonical='Retained full original C from203, same actual bytes', current_raw_intervals='Three new bounded raw captures relative to this specified round203 inventory; no whole 4DA630 body capture', prior_raw_spans=prior_spans))

    specs = ((0x4D2B50, 93, 'complete pure leaf; retained canonical context, new local raw capture'), (0x4DA638, 111, 'bounded actual mode/source WORD transfer'), (0x4DA6E4, 68, 'bounded actual type2 call/first ordinal action transfer'))
    spans = []
    for index, (address, size, scope) in enumerate(specs):
        offset = pe.get_offset_from_rva(address - pe.OPTIONAL_HEADER.ImageBase)
        data = raw[offset:offset + size]
        instructions = list(decoder.disasm(data, address))
        assert sum(instruction.size for instruction in instructions) == size
        stem = f'native/s{index:02}'
        path = OUT / (stem + '.bin')
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        (OUT / (stem + '.tsv')).write_text('va\tbytes\tmnemonic\toperands\n' + ''.join(f'0x{instruction.address:08X}\t{instruction.bytes.hex()}\t{instruction.mnemonic}\t{instruction.op_str}\n' for instruction in instructions), encoding='utf-8')
        spans.append(dict(begin=f'0x{address:08X}', end_exclusive=f'0x{address + size:08X}', bytes=size, file_offset=offset, sha256=digest(data), raw=stem + '.bin', instructions=stem + '.tsv', sites=len(instructions), classification='new bounded local capture', scope=scope))

    calls = []
    with (RECOVERY / 'calls.tsv').open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['target'].lower() == '004d2b50':
                calls.append(row)
    put('xref-call-rows.json', calls)
    if calls:
        with (OUT / 'xref-call-rows.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(calls[0]))
            writer.writeheader()
            writer.writerows(calls)

    # Derived literal excerpts only. The complete caller C stays external and is
    # separately full-hashed, including an honest earlier whole-read receipt.
    caller_text = caller.read_text(encoding='utf-8')
    lines = caller_text.splitlines()
    excerpt = []
    for index, line in enumerate(lines):
        if any(fragment in line for fragment in ('0x4ccb0', '0x4ccfc', '0x4cd00', '0x4ccc0', '0x4ccc4', '0x430a8', '0xcf', 'FUN_004d2b50', 'FUN_004d3b60', 'FUN_004abf40', '0x1c9010', '0x1c9011')):
            excerpt.append(dict(original_line=index + 1, text=line))
    put('derived/caller-canonical-excerpts.json', dict(source=str(caller.resolve()), source_sha256=digest(caller.read_bytes()), classification='Derived selected original lines, not a full canonical original', lines=excerpt))
    put('actual-read-scope.json', dict(initial_observation='Complete leaf C and complete4DA630 C were read; a whole271B4DA630 exploratory instruction dump was transient tool output before parent narrowed persistence. It was not saved as a raw artifact or counted as a full new span.', final_capture='Only complete leaf93B plus selected caller111B/68B are persisted. Complete caller C/PE/TSV hashes reference original files in place. No formatter/action/gate/control callee interiors followed.', prior200_gate='4D3B60 previously captured pure gate is only an actual callsite here; no new gate bytes and no cast/grant inference.'))

    relations = [
        dict(scope='004D2B50 whole93B lookup input and ordered first match', raw_sites=['0x004D2B53', '0x004D2B60', '0x004D2B6A', '0x004D2B77', '0x004D2B80', '0x004D2B82', '0x004D2B86', '0x004D2B8B', '0x004D2B8E', '0x004D2B90', '0x004D2BA6'], fact='Actual ECX U+0x430A8 -> inline V+0xD0 -> selected row; BYTE count+0x1F0 is read once into EDI. Iterate original DWORD definition pointers at row+0x258 ascending. Definition BYTE+1(kind)/BYTE+0(ID) are zero-extended and compared to full DWORD first/second stack arguments. Return first ordinal as32-bit int; null V/row, count0, or no match returns-1. No flags/auxiliary list read and no definition-pointer null check.'),
        dict(scope='004DA638..004DA6A7 exact caller source widths', raw_sites=['0x004DA63A', '0x004DA64A', '0x004DA650', '0x004DA65D', '0x004DA663', '0x004DA66A', '0x004DA683', '0x004DA68A', '0x004DA692', '0x004DA696'], fact='ModeDWORD U+0x4CCB0=0 reads stride6 entries at U+0x4CCC0 (type WORD/kind WORD) and ID WORD+0x4CCC4. Mode1 uses signedBYTE V+0xCF*10+supplied ordinal and tables0x4CCFC/0x4CD00. Other modes flow through existing stack locals with no qualified producer; do not synthesize defaults. These are caller table/selection facts, not raw command authority.'),
        dict(scope='004DA6E4..004DA728 type2 -> first ordinal only -> local action', raw_sites=['0x004DA6EA', '0x004DA6F0', '0x004DA6F3', '0x004DA6F4', '0x004DA6F8', '0x004DA705', '0x004DA70C', '0x004DA714', '0x004DA71C', '0x004DA722'], fact='Type2 caller sign-extends kind WORD and ID WORD into full DWORD arguments, pushes ID then kind, calls4D2B50. Returned first ordinal goes to existing4D3B60; failure does not retry later duplicate. Successful local gate/action4ABF40(8,1) then writes kind/ID low BYTE to U+0x1C9010/11. No+0x1C9012 producer in bounded branch; no server success/cast/learned grant or source qualification inferred.')
    ]
    findings = dict(round=204, cpp_files_changed=0, new_bounded_native_spans=3, new_bounded_native_bytes=272, new_whole_pure_functions=1, new_native_relations=relations, retained_bounded_native_spans=0, retained_bounded_native_bytes=0, coverage_scope='New bounded raw capture relative to explicitly compared round203 local inventory, not global unique coverage. Leaf full canonical retained from203. Caller whole271B is not counted or persisted.', raw_count='BYTE count read once into EDI at004D2B6A; canonical pseudocode repeats the read in its loop condition, but raw instructions keep the captured count. Do not treat decompiler loop form as proof of live re-read.', parameters='First kind DWORD, second ID DWORD. Definition values are BYTE zero-extended. Caller sign-extends actual WORDs before calling. Values outside0..255 cannot equal those zero-extended bytes; do not truncate to force match.', duplicate_semantics='Original ordered prefix; first match wins. No dedup, no flags priority, no later duplicate retry after caller gate failure.', source_qualification_actions=['Readonly current-qualified selected row may expose first ordinal lookup of captured pointer/raw definition prefix. Preserve full DWORD arguments and raw ordering; do not replace by key dictionary or auxiliary prefix.', 'Lookup projection of a supplied WORD key can decompose kind/id, but it is not proof that the supplied WORD was emitted by actual4DA630 caller.', 'Actual Current/common subject/learned ownership/real battle rights and complete incoming publication remain mandatory independent suppliers. Table modes and old local gate do not grant them.'], gaps=['Positive primary learned population and WORLD-to-battle primary materialization remain OPEN. This leaf only searches an already supplied pointer list.', 'No flags+0x1F1, auxiliary+0x5C/+0x60, definition+0x67/+0x6B/+0x42 read in leaf; no game taxonomy or grant from lookup.', 'Actual caller mode tables, their current supply, invalid-mode stack locals and+0x1C9012 producer are not restored by this bounded source.', 'First selected pointer and BYTE count geometry are not validated by native leaf; server readonly own-view qualification must not claim native leaf validates membership or pointer bank.', 'No formatter/render/control/gate interiors followed. No native/emulator/codec/API/DB/SQL/build/test/runtime executed.', 'Whole PE/TSVs/caller C remain full-hashed in place; full leaf canonical and actual current source originals are copied. Historical actual-read scope explicitly preserved.'], new_opcode_bindings=0, new_phase_bindings=0, new_complete_routes=0, receiver_contexts=14, qualified_receiver_contexts=12, unresolved_helpers=[dict(va='0x0047DE70', phase=None, slot=None), dict(va='0x004812B0', phase=None, slot=None)], current_source_count=len(current), native_canonical_count=len(native), original_input_count=len(originals), historical_count=len(historical), native_reference_count=len(references), complete_game_percentage=None)
    put('findings.json', findings)
    put('native-spans.json', spans)
    put('native-input-references.json', references)
    put('selected-function-metadata.json', metadata)
    put('original-inputs.json', originals)
    put('native-original-inputs.json', native)
    put('current-source-origins.json', current)
    put('historical-origins.json', historical)
    put('LIST.json', originals)
    print(json.dumps(dict(out=str(OUT), new_bytes=272, sites=[span['sites'] for span in spans], current=len(current), native=len(native), original=len(originals), references=len(references), historical=len(historical))))


if __name__ == '__main__':
    main()
