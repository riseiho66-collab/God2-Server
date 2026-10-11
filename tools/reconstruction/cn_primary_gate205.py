"""205 exact retained primary predicate and actual caller; file/static only."""
from pathlib import Path
import csv
import hashlib
import json
import capstone
import pefile

ROOT = Path(__file__).resolve().parents[2]
D = Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
P = Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
O = ROOT / 'artifacts/integration/packet-connections-20261006/cn-primary-skill-gate-source-01/agents/primary-gate-native'
PRIOR200 = ROOT / 'artifacts/integration/packet-connections-20261006/cn-native-item-control-source-frontier-01/agents/native-book-eligibility'
PRIOR204 = ROOT / 'artifacts/integration/packet-connections-20261006/cn-primary-skill-ordinal-source-01/agents/primary-ordinal-native'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(name, value):
    path = O / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    if O.exists():
        raise SystemExit('Output already exists; preserve actual epochs')
    O.mkdir(parents=True)
    originals, current, native, historical = [], [], [], []

    def copy(path, name, collection, original=True):
        data = path.read_bytes()
        target = O / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        row = dict(path=str(path.resolve()), copy=name, bytes=len(data), sha256=sha(data))
        collection.append(row)
        if original:
            originals.append(row)
        return row

    raw = P.read_bytes()
    assert len(raw) == 47541760 and sha(raw) == PIN
    pe = pefile.PE(data=raw, fast_load=True)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    references = []
    for path in (P, D / 'functions.tsv', D / 'calls.tsv'):
        data = path.read_bytes()
        references.append(dict(path=str(path.resolve()), copy=None, bytes=len(data), sha256=sha(data), disposition='Complete actual native input hashed in place; no whole PE/TSV copy'))
    copy(D / 'part_0011/004d3b60_FUN_004d3b60.c', 'originals/native/leaf.c', native)
    for index, name in enumerate(('AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md', 'tools/reconstruction/cn_primary_gate205.py')):
        copy(ROOT / name, f'originals/source/r{index:02}.txt', current)
    for number, prior in ((200, PRIOR200), (204, PRIOR204)):
        for name in ('findings.json', 'native-spans.json', 'seal.json'):
            copy(prior / name, f'epochs/prior{number}-{name}', historical, False)
    for name in ('native/s00.bin', 'native/s00.tsv'):
        copy(PRIOR200 / name, 'epochs/prior200-' + Path(name).name, historical, False)
    (O / 'epochs/tool-initial.py').write_bytes(Path(__file__).read_bytes())

    specs = ((0x4D3B60, 67, PRIOR200, '0x004D3B60', 'retained whole pure predicate from200'), (0x4DA6E4, 68, PRIOR204, '0x004DA6E4', 'retained bounded actual firstordinal->gate->local action from204'))
    spans, comparison = [], []
    for index, (address, size, prior, old_start, scope) in enumerate(specs):
        offset = pe.get_offset_from_rva(address - pe.OPTIONAL_HEADER.ImageBase)
        data = raw[offset:offset + size]
        ins = list(md.disasm(data, address))
        assert sum(item.size for item in ins) == size
        old = next(item for item in json.loads((prior / 'native-spans.json').read_text(encoding='utf-8')) if item['begin'] == old_start)
        assert old['bytes'] == size and old['sha256'] == sha(data) and (prior / old['raw']).read_bytes() == data
        stem = f'native/s{index:02}'
        target = O / (stem + '.bin')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
        (O / (stem + '.tsv')).write_text('va\tbytes\tmnemonic\toperands\n' + ''.join(f'0x{item.address:08X}\t{item.bytes.hex()}\t{item.mnemonic}\t{item.op_str}\n' for item in ins), encoding='utf-8')
        spans.append(dict(begin=f'0x{address:08X}', end_exclusive=f'0x{address + size:08X}', bytes=size, file_offset=offset, sha256=sha(data), raw=stem + '.bin', instructions=stem + '.tsv', sites=len(ins), classification='retained; zero coverage increment', scope=scope))
        comparison.append(dict(prior=str(prior), prior_seal_sha256=sha((prior / 'seal.json').read_bytes()), old_raw=old['raw'], old_hash=old['sha256'], same_actual_bytes=True, scope='Only exact specified old spans compared; not a global uniqueness/absence audit'))

    calls, metadata = [], []
    with (D / 'calls.tsv').open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['target'].lower() == '004d3b60':
                calls.append(row)
    with (D / 'functions.tsv').open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['address'].lower() == '004d3b60':
                metadata.append(row)
    put('xref-call-rows.json', calls)
    if calls:
        with (O / 'xref-call-rows.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(calls[0]))
            writer.writeheader()
            writer.writerows(calls)

    facts = [
        dict(scope='004D3B60 full67B pointer/index checks', raw_sites=['0x004D3B63', '0x004D3B69', '0x004D3B6F', '0x004D3B73', '0x004D3B76', '0x004D3B78', '0x004D3B7A', '0x004D3B81'], fact='Actual ECX U+0x430A8 gives V, then V+0xD0 gives selected row. There is no V null check before that dereference. Native checks row nonzero, full signed32 ordinal>=0 via JS, then DWORD pointer at row+0x258+4*ordinal nonzero. No count or maximum-ordinal comparison; no flags or auxiliary list read. This leaf is unsafe for an arbitrary positive index; owner-view geometry/Current qualification is independent.'),
        dict(scope='004D3B60 full67B raw unsigned local predicate', raw_sites=['0x004D3B85', '0x004D3B89', '0x004D3B8B', '0x004D3B8F', '0x004D3B92', '0x004D3B94', '0x004D3B9D'], fact='Definition BYTE+0x67 must be nonzero. WORD+0x42 is zero-extended toDWORD, compared against actual inline V+0x64 DWORD; unsigned JB rejects when V64<WORD42. Equality passes. Thus pure local predicate is nonzero BYTE67 AND unsigned WORD42<=unsigned DWORD64, returning DWORD1/0. No MP/cost/cast/grant semantics established.'),
        dict(scope='retained004DA6E4..004DA728 actual first ordinal supply', raw_sites=['0x004DA6EA', '0x004DA6F0', '0x004DA6F8', '0x004DA6FD', '0x004DA702', '0x004DA705', '0x004DA70C'], fact='Actual signextended kind/ID WORD lookup4D2B50 returns first matching physical ordinal; that same ordinal is passed once into4D3B60. Failed local predicate does not search later duplicates. Subsequent action4ABF40 is a stopped callsite; caller bytes retained204, no callee interior or new authority inferred.')
    ]
    findings = dict(round=205, cpp_files_changed=0, new_bounded_native_spans=0, new_bounded_native_bytes=0, new_native_relations=[], retained_bounded_native_spans=2, retained_bounded_native_bytes=135, retained_instruction_sites=sum(item['sites'] for item in spans), retained_facts=facts, complete_pure_leaf_bytes=67, complete_pure_leaf_instruction_sites=23, coverage_scope='Exact already sealed200/204 intervals reconciled against actual pinned PE. No new native function/bytes/relations/opcode/phase/fullroute increment.', source_qualification_actions=['Readonly firstordinal predicate may use the captured raw BYTE67/WORD42 and actual same-inline DWORD64, with unsigned comparison. Label as native local predicate only.', 'A current-qualified original primary ordinal resolves a definition safely only under actual owner-view geometry; native4D3B60 does not check ordinal<count, count<=100, original bank membership or common ownership.', 'Preserve original firstduplicate choice, rather than searching a later entry that happens to pass local predicate.', 'Do not infer MP, learned grants, casting rights, battle membership or common-subject classification from this local comparison.'], gaps=['Actual meaning and authoritative producer/current lifecycle of inline+0x64 DWORD and definition+0x67/+0x42 remain separate supplier/semantic qualification tasks.', 'Native leaf has no V null guard or positive-index upper bound; no row+0x1F0 count or+0x1F1 flags read. Projection may qualify safe owned geometry but cannot pretend this was a native guard.', 'Positive primary learned population and WORLD-to-battle primary materialization remain OPEN; count/flags/catalog membership and local predicate do not prove them.', 'No formatter/render/action/gate interior was followed. Only whole pure67B and already retained actual caller68B were disassembled. No native/emulation/codec/API/DB/SQL/build/test/runtime used.', 'Whole PE/TSV inputs hash in place; complete leaf original and stable source fullcopies retained; historical seals/epochs unchanged.'], new_opcode_bindings=0, new_phase_bindings=0, new_complete_routes=0, receiver_contexts=14, qualified_receiver_contexts=12, unresolved_helpers=[dict(va='0x0047DE70', phase=None, slot=None), dict(va='0x004812B0', phase=None, slot=None)], current_source_count=len(current), native_canonical_count=len(native), original_input_count=len(originals), historical_count=len(historical), native_reference_count=len(references), complete_game_percentage=None)
    put('findings.json', findings)
    put('native-spans.json', spans)
    put('prior-layer-comparison.json', comparison)
    put('selected-function-metadata.json', metadata)
    put('native-input-references.json', references)
    put('original-inputs.json', originals)
    put('native-original-inputs.json', native)
    put('current-source-origins.json', current)
    put('historical-origins.json', historical)
    put('LIST.json', originals)
    print(json.dumps(dict(out=str(O), new_bytes=0, retained_bytes=135, sites=[item['sites'] for item in spans], current=len(current), native=len(native), original=len(originals), references=len(references), historical=len(historical))))


if __name__ == '__main__':
    main()
