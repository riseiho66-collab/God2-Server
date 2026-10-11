"""206 retained WORLD34/35 data-writer reconciliation; static files only."""
from pathlib import Path
import csv
import hashlib
import json
import capstone
import pefile

R = Path(__file__).resolve().parents[2]
D = Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
P = Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
O = R / 'artifacts/integration/packet-connections-20261006/cn-primary-skill-update-source-01/agents/primary-update-native'
PRIOR196 = R / 'artifacts/integration/packet-connections-20261006/cn-native-learned-skill-event-frontier-01/agents/cn-learned-event-native-frontier'
PRIOR201 = R / 'artifacts/integration/packet-connections-20261006/cn-native-shared-book-request-source-01/agents/native-learned-row-source'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(name, value):
    path = O / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    if O.exists():
        raise SystemExit('Output already exists; preserve real epochs')
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
    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    with (D / 'functions.tsv').open(encoding='utf-8') as stream:
        metadata = [row for row in csv.DictReader(stream, delimiter='\t') if row['address'].lower() in ('004d5e60', '004d5cc0', '004d5830', '0048fcc0')]
    dispatcher = D / next(row['file'] for row in metadata if row['address'].lower() == '0048fcc0')
    references = []
    for path in (P, D / 'functions.tsv', D / 'calls.tsv', dispatcher):
        data = path.read_bytes()
        references.append(dict(path=str(path.resolve()), copy=None, bytes=len(data), sha256=sha(data), disposition='Complete actual input hashed in place; no whole PE/TSV/dispatcher copy'))
    for index, address in enumerate(('004d5e60', '004d5cc0', '004d5830')):
        path = D / next(row['file'] for row in metadata if row['address'].lower() == address)
        copy(path, f'originals/native/n{index:02}.c', native)
    for index, name in enumerate(('AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md', 'tools/reconstruction/cn_primary_update206.py')):
        copy(R / name, f'originals/source/r{index:02}.txt', current)
    for number, prior in ((196, PRIOR196), (201, PRIOR201)):
        for name in ('findings.json', 'native-spans.json', 'seal.json'):
            copy(prior / name, f'epochs/prior{number}-{name}', historical, False)
    for name in ('raw/s02.bin', 'raw/s03.bin', 'raw/s05.bin', 'derived/s02.json', 'derived/s03.json'):
        copy(PRIOR196 / name, 'epochs/prior196-' + Path(name).name, historical, False)
    for name in ('native/s00.bin', 'native/s00.tsv'):
        copy(PRIOR201 / name, 'epochs/prior201-' + Path(name).name, historical, False)
    (O / 'epochs/tool-initial.py').write_bytes(Path(__file__).read_bytes())

    old196 = json.loads((PRIOR196 / 'native-spans.json').read_text(encoding='utf-8'))
    old201 = json.loads((PRIOR201 / 'native-spans.json').read_text(encoding='utf-8'))
    specs = [
        (0x4D5E60, 0x4D5FB2, 196, 'WORLD34 roster/subject/count/duplicate/append/page/aux callsite data'),
        (0x4D5FDB, 0x4D600D, 196, 'WORLD34 firstduplicate logging callsite and count re-read/rejoin; no logger interior'),
        (0x4D6010, 0x4D603F, 196, 'WORLD34 allmatching roster continuation and actual D4 re-read'),
        (0x4D5CC0, 0x4D5D95, 196, 'WORLD35 roster/exact bankpointer/firstmatch flag3/aux callsite data'),
        (0x4D5E29, 0x4D5E5B, 196, 'WORLD35 allmatching roster continuation and actual D4 re-read'),
        (0x4D5830, 0x4D587C, 201, 'Complete retained pure flags-bit2 auxiliary prefix materializer; no stale-tail clear'),
        (0x491388, 0x4913B0, 196, 'Actual incoming34/35 body+1 transfer to ECX U=P+89B26C'),
    ]
    spans, comparisons = [], []
    for index, (begin, end, number, scope) in enumerate(specs):
        offset = pe.get_offset_from_rva(begin - pe.OPTIONAL_HEADER.ImageBase)
        data = raw[offset:offset + end - begin]
        instructions = list(decoder.disasm(data, begin))
        assert sum(item.size for item in instructions) == len(data)
        if number == 196:
            prior = PRIOR196
            old = next(row for row in old196 if row['va_start'] <= begin and row['va_end'] >= end)
            whole = (prior / old['copy']).read_bytes()
            assert len(whole) == old['bytes'] and sha(whole) == old['sha256']
            assert whole[begin - old['va_start']:end - old['va_start']] == data
            old_start, old_copy = old['va_start'], old['copy']
        else:
            prior = PRIOR201
            old = next(row for row in old201 if row['begin'] == '0x004D5830')
            assert (prior / old['raw']).read_bytes() == data and sha(data) == old['sha256']
            old_start, old_copy = begin, old['raw']
        stem = f'native/s{index:02}'
        target = O / (stem + '.bin')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
        (O / (stem + '.tsv')).write_text('va\tbytes\tmnemonic\toperands\n' + ''.join(f'0x{item.address:08X}\t{item.bytes.hex()}\t{item.mnemonic}\t{item.op_str}\n' for item in instructions), encoding='utf-8')
        spans.append(dict(begin=f'0x{begin:08X}', end_exclusive=f'0x{end:08X}', bytes=len(data), file_offset=offset, sha256=sha(data), raw=stem + '.bin', instructions=stem + '.tsv', sites=len(instructions), classification='retained; zero coverage increment', scope=scope))
        comparisons.append(dict(current_span=index, prior=str(prior), old_span_start=f'0x{old_start:08X}', old_copy=old_copy, old_whole_bytes=old['bytes'], old_whole_sha256=old['sha256'], prior_seal_sha256=sha((prior / 'seal.json').read_bytes()), comparison='Exact persisted selected bytes match actual pinned PE and old sealed interval; not a global absence/uniqueness audit'))

    excerpt = []
    lines = dispatcher.read_text(encoding='utf-8').splitlines()
    for index, line in enumerate(lines):
        if 'FUN_004d5e60' in line or 'FUN_004d5cc0' in line:
            for position in range(max(0, index - 1), min(len(lines), index + 2)):
                excerpt.append(dict(original_line=position + 1, text=lines[position]))
    put('derived/dispatcher-canonical-excerpts.json', dict(source=str(dispatcher.resolve()), source_sha256=sha(dispatcher.read_bytes()), classification='Derived selected actual lines, not full original', lines=excerpt))
    calls = []
    with (D / 'calls.tsv').open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['target'].lower() in ('004d5e60', '004d5cc0') or (row['caller'].lower() in ('004d5e60', '004d5cc0') and row['target'].lower() == '004d5830'):
                calls.append(row)
    put('xref-call-rows.json', calls)
    if calls:
        with (O / 'xref-call-rows.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(calls[0]))
            writer.writeheader()
            writer.writerows(calls)

    facts = [
        dict(scope='Both actual WORLD34/35 roster traversal', raw_sites=['0x00491388', '0x00491392', '0x0049139C', '0x004913A6', '0x004D5E73', '0x004D5E79', '0x004D5E90', '0x004D5E9B', '0x004D5E9E', '0x004D6024', '0x004D6030', '0x004D5CF0', '0x004D5CF6', '0x004D5CFB', '0x004D5E40', '0x004D5E4C'], fact='Actual ECX U=P+0x89B26C; U+0x430A8 gives inline V. Roster count is BYTE V+0xD4, rows start V+0xD8 with stride0x3EC. Incoming firstBYTE is zero-extended and compared to row WORD+0. Both loops continue through ALL matching rows, not first roster match; outer count and V are re-read at continuation. No V null guard or roster<=16 geometry check. Same subject numeric value does not establish common actor/learned rights.'),
        dict(scope='WORLD34 capacity/duplicate/native pointer append', raw_sites=['0x004D5EA7', '0x004D5EAD', '0x004D5EAF', '0x004D5EB5', '0x004D5EC8', '0x004D5EDB', '0x004D5EF0', '0x004D5F02', '0x004D5F10', '0x004D5F2C', '0x004D5F34', '0x004D5F3E', '0x004D5F49', '0x004D5F56', '0x004D5F5C', '0x004D5F6C', '0x004D5F78'], fact='Per matching row BYTE count+0x1F0 must be<100. Incoming kind/ID BYTE1/2 zero-extended. ID0 calls assertion53E3D0 but explicit ID>0 check still excludes append if that call returns. Ascending primary pointers are searched by actual definition BYTE1/0; first duplicate goes to logging callsite, then current count is re-read/rejoined. With unchanged same row/count a duplicate is not appended; no later duplicate fallback. Fresh append writes flag0 at oldcount+0x1F1; pointer=actual V+0x4474 bank+kind*0x6E04+ID*0x6E-0x6A, stores at currentcount+0x258, increments BYTEcount. No native ID<=100/kind upper-bound/bank extent/null definition-pointer guard. Source algebra proves layout arithmetic, not safe bank membership.'),
        dict(scope='WORLD35 first exact pointer flag3 without removal', raw_sites=['0x004D5D04', '0x004D5D12', '0x004D5D25', '0x004D5D2D', '0x004D5D32', '0x004D5D38', '0x004D5D40', '0x004D5D54', '0x004D5D5B', '0x004D5D63', '0x004D5D65', '0x004D5D7D', '0x004D5D88'], fact='Per matching row ID0 assertion branch continues to next row without pointer calculation. Otherwise zero-extended kind/ID calculate same actual bank address using(kind*0x6E04)+(ID-1)*0x6E+4. Scan original prefix countBYTE once for loop bound; first exact DWORD pointer match gets flag3. No entry removal, pointer shift, dedup, count increment/decrement or count<100 guard; outer roster still continues all matching rows. No flag value alone is learned/cast permission.'),
        dict(scope='Retained pure004D5830 auxiliary refresh', raw_sites=['0x004D5FAD', '0x004D5D90', '0x004D5840', '0x004D5850', '0x004D5860', '0x004D5864', '0x004D5867'], fact='Both actual writers call pure helper with same actual row. Helper resets BYTE+0x5C to0 then scans primary flags+0x1F1 in order; flag&2 copies corresponding actual DWORD pointer+0x258 into auxiliary DWORD prefix+0x60 and increments aux count. Nulls/duplicates/order preserved; loop primary count is re-read. No stale tail clearing, pointer validation or universal aux<=primary invariant outside this helper call. WORLD30 count-only reset can leave old prefix stale; full-row reset is distinct.'),
        dict(scope='GUI and logging side-effects boundary', raw_sites=['0x004D5FAD', '0x004D5FBE', '0x004D5FC3', '0x004D5FD4', '0x004D5FFA', '0x004D5D90', '0x004D5DAA'], fact='Full canonical originals retain selected-row4D5520/4D8250 and logging/assert callsites as context. No such callee interior was followed; bounded raw captures skip GUI effect sections. No claim of all GUI side-effects, mutation simulation, incoming-to-servergrant cause or original authoritative learning rule.')
    ]
    findings = dict(round=206, cpp_files_changed=0, new_bounded_native_spans=0, new_bounded_native_bytes=0, new_native_relations=[], retained_bounded_native_spans=len(spans), retained_bounded_native_bytes=sum(row['bytes'] for row in spans), retained_instruction_sites=sum(row['sites'] for row in spans), retained_facts=facts, coverage_scope='All selected data spans are exact subsets of already sealed196 whole/dispatch intervals or201 complete pure helper. No native coverage/opcode/phase/route increment. Complete canonical originals provide context; logging/UI/render callees stopped.', source_qualification_actions=['PrimaryDelta may describe per-event captured source projection over ALL matching raw subject rows, retaining order/pointer identity and first per-row skill match. Do not use a first-roster-only substitute.', 'S34 explicit native count<100 is proven; S35 lacks that check. Safe own-row geometry/bank qualifications are separate readonly source safeguards, never attributed to native.', 'Preserve BYTEflag0 append vsBYTEflag3 firstpointer-match distinction, helper-materialized aux prefix, and stale tail bytes. Do not convert flag3 into deletion/ownership/grant.', 'Current-qualified primary projection does not execute log/assert/UI callbacks or prove full native side-effect equivalence. Exact incoming original source/common identity/learning authority remain independent.'], gaps=['Client bank arithmetic exposes kind stride0x6E04, record stride0x6E and4-byte header algebra; actual loaded extent/validkind/ID upper-bound/live bank issuer remains independently qualified.', 'No native null-V guard, roster<=16 guard or S35count<=100 guard. Own view may refuse unknown geometry without pretending native checked it.', 'S34 duplicate branch calls logger and re-reads count before deciding; native raw does not prove external callback cannot mutate state. Predicate applies to unchanged qualified same row/current domain; no guessed callback side-effects.', 'WORLD34/35 byte subject is not full commonID; all matching rawWORD rows may update. Actual subject namespace/ownership/server producer/cost/learning/cast/battle primary materializer remain OPEN.', 'WORLD35 selected-row UI table stores remain full canonical context only; no GUI/render/capacity/formatter155/52F330/52F170 interiors followed.', 'No native/emulator/codec/API/DB/SQL/build/test/runtime/deploy executed. Full PE/TSVs hashed in place; historical seals and original full bytes preserved.'], new_opcode_bindings=0, new_phase_bindings=0, new_complete_routes=0, receiver_contexts=14, qualified_receiver_contexts=12, unresolved_helpers=[dict(va='0x0047DE70', phase=None, slot=None), dict(va='0x004812B0', phase=None, slot=None)], current_source_count=len(current), native_canonical_count=len(native), original_input_count=len(originals), historical_count=len(historical), native_reference_count=len(references), complete_game_percentage=None)
    put('findings.json', findings)
    put('native-spans.json', spans)
    put('prior-layer-comparison.json', comparisons)
    put('selected-function-metadata.json', metadata)
    put('native-input-references.json', references)
    put('original-inputs.json', originals)
    put('native-original-inputs.json', native)
    put('current-source-origins.json', current)
    put('historical-origins.json', historical)
    put('LIST.json', originals)
    print(json.dumps(dict(out=str(O), new_bytes=0, retained_bytes=findings['retained_bounded_native_bytes'], sites=findings['retained_instruction_sites'], spans=len(spans), original=len(originals), current=len(current), native=len(native), references=len(references), historical=len(historical))))


if __name__ == '__main__':
    main()
