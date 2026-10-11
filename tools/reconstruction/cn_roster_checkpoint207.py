"""207 ordered roster/skill checkpoint boundaries from retained native files."""
from pathlib import Path
import csv
import hashlib
import json
import capstone
import pefile

R = Path(__file__).resolve().parents[2]
B = R / 'artifacts/integration/packet-connections-20261006'
D = Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
P = Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
O = B / 'cn-roster-skill-checkpoint-source-01/agents/roster-checkpoint-native'
A = B / 'cn-subject-roster-publication-source-01'
S = B / 'cn-subject-status31-source-01'
U = B / 'cn-selected-subject-update-source-01'
K = B / 'cn-primary-skill-update-source-01/agents/primary-update-native'
H = B / 'cn-native-learned-skill-event-frontier-01/agents/cn-learned-event-history-frontier'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(name, value):
    path = O / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    if O.exists():
        raise SystemExit('Existing actual epochs must remain unchanged')
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
    addresses = ('004d5b20', '004d58b0', '004d5a10', '004d5880', '004d5a90', '004d5e60', '004d5cc0')
    with (D / 'functions.tsv').open(encoding='utf-8') as stream:
        metadata = [row for row in csv.DictReader(stream, delimiter='\t') if row['address'].lower() in (*addresses, '0048fcc0')]
    dispatcher = D / next(row['file'] for row in metadata if row['address'].lower() == '0048fcc0')
    references = []
    for path in (P, D / 'functions.tsv', D / 'calls.tsv', dispatcher):
        data = path.read_bytes()
        references.append(dict(path=str(path.resolve()), copy=None, bytes=len(data), sha256=sha(data), disposition='Full actual native file hashed in place; no whole PE/TSV/dispatcher copy'))
    for index, address in enumerate(addresses):
        path = D / next(row['file'] for row in metadata if row['address'].lower() == address)
        copy(path, f'originals/native/n{index:02}.c', native)
    for index, name in enumerate(('AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md', 'tools/reconstruction/cn_roster_checkpoint207.py')):
        copy(R / name, f'originals/source/r{index:02}.txt', current)

    preserved = [
        (A, 'manifest.json'), (A, 'native/004D5B20-expanded.bin'), (A, 'native/004D5B20-expanded-cfg.asm'), (A, 'native/WORLD30-primary-case.bin'),
        (S, 'manifest.json'), (S, 'native/004D58B0.bin'), (S, 'native/004D58B0-cfg.asm'), (S, 'native/WORLD31-primary-table-case.bin'),
        (U, 'manifest.json'), (U, 'native/004D5A10.bin'), (U, 'native/004D5880.bin'), (U, 'native/004D5A90.bin'),
        (U, 'native/004D5A10-cfg.asm'), (U, 'native/004D5880-cfg.asm'), (U, 'native/004D5A90-cfg.asm'),
        (U, 'native/WORLD32-primary-case.bin'), (U, 'native/WORLD33-primary-case.bin'), (U, 'native/WORLD39-primary-case.bin'),
        (K, 'seal.json'), (K, 'findings.json'), (K, 'native-spans.json'), (K, 'native/s00.bin'), (K, 'native/s03.bin'), (K, 'native/s06.bin'),
        (H, 'seal.json'), (H, 'findings.json'), (H, 'native-spans.json'),
    ]
    for index, (prior, name) in enumerate(preserved):
        copy(prior / name, f'epochs/p{index:02}{Path(name).suffix}', historical, False)
    (O / 'epochs/tool-initial.py').write_bytes(Path(__file__).read_bytes())

    # Each selected subset is already present in the referenced immutable raw
    # witness; the old WORLD31 file is32B but its actual primary case is20B.
    specs = [
        (0x4D5B20, 0x4D5B7C, A / 'native/004D5B20-expanded.bin', 0x4D5B20, '30 signed absolute ID/count<16/inactive row stage'),
        (0x4D5BB1, 0x4D5BF2, A / 'native/004D5B20-expanded.bin', 0x4D5B20, '30 inline-body11 reset first active row scan'),
        (0x4D5C46, 0x4D5C56, A / 'native/004D5B20-expanded.bin', 0x4D5B20, '30 count-only reset and early return'),
        (0x4D5BF8, 0x4D5C29, A / 'native/004D5B20-expanded.bin', 0x4D5B20, '30 count activation then negative input selects staged row'),
        (0x4D58B0, 0x4D5962, S / 'native/004D58B0.bin', 0x4D58B0, '31 signed subject firstmatch/current row field copy before stopped GUI'),
        (0x4D59B8, 0x4D5A02, S / 'native/004D58B0.bin', 0x4D58B0, '31 exact selected row/index/page fields after stopped GUI'),
        (0x4D5A10, 0x4D5A5D, U / 'native/004D5A10.bin', 0x4D5A10, '32 current selected row/resource-string data; formatter not entered'),
        (0x4D5880, 0x4D58A8, U / 'native/004D5880.bin', 0x4D5880, '33 current selected row BYTE40; tail UI target not entered'),
        (0x4D5A90, 0x4D5ADA, U / 'native/004D5A90.bin', 0x4D5A90, '39 current selected row DWORD/WORD data before formatter'),
        (0x4D5F3E, 0x4D5F7E, K / 'native/s00.bin', 0x4D5E60, '34 retained append flag0/pointer/count store subset'),
        (0x4D5D32, 0x4D5D95, K / 'native/s03.bin', 0x4D5CC0, '35 retained first exactpointer flag3/aux callsite subset'),
        (0x491324, 0x491338, A / 'native/WORLD30-primary-case.bin', 0x491324, 'incoming30 actual body+1/ECX sameU'),
        (0x49134C, 0x491360, S / 'native/WORLD31-primary-table-case.bin', 0x49134C, 'incoming31 actual body+1/ECX sameU'),
        (0x491360, 0x491374, U / 'native/WORLD32-primary-case.bin', 0x491360, 'incoming32 actual body+1/ECX sameU'),
        (0x491374, 0x491388, U / 'native/WORLD33-primary-case.bin', 0x491374, 'incoming33 actual body+1/ECX sameU'),
        (0x491388, 0x49139C, K / 'native/s06.bin', 0x491388, 'incoming34 actual body+1/ECX sameU'),
        (0x49139C, 0x4913B0, K / 'native/s06.bin', 0x491388, 'incoming35 actual body+1/ECX sameU'),
        (0x4913B0, 0x4913C4, U / 'native/WORLD39-primary-case.bin', 0x4913B0, 'incoming39 actual body+1/ECX sameU'),
    ]
    spans, comparisons = [], []
    for index, (begin, end, witness, witness_begin, scope) in enumerate(specs):
        offset = pe.get_offset_from_rva(begin - pe.OPTIONAL_HEADER.ImageBase)
        data = raw[offset:offset + end - begin]
        old = witness.read_bytes()
        assert old[begin - witness_begin:end - witness_begin] == data
        instructions = list(decoder.disasm(data, begin))
        assert sum(item.size for item in instructions) == len(data)
        stem = f'native/s{index:02}'
        target = O / (stem + '.bin')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
        (O / (stem + '.tsv')).write_text('va\tbytes\tmnemonic\toperands\n' + ''.join(f'0x{item.address:08X}\t{item.bytes.hex()}\t{item.mnemonic}\t{item.op_str}\n' for item in instructions), encoding='utf-8')
        spans.append(dict(begin=f'0x{begin:08X}', end_exclusive=f'0x{end:08X}', bytes=len(data), file_offset=offset, sha256=sha(data), raw=stem + '.bin', instructions=stem + '.tsv', sites=len(instructions), classification='retained; zero native coverage increment', scope=scope))
        comparisons.append(dict(span=index, prior_witness=str(witness.resolve()), prior_start=f'0x{witness_begin:08X}', prior_bytes=len(old), prior_sha256=sha(old), selected_bytes_exact=True, scope='Specified old persisted interval only; no global unique coverage or absence claim'))

    lines = dispatcher.read_text(encoding='utf-8').splitlines()
    selected_lines = []
    for index, line in enumerate(lines):
        if any('FUN_' + address in line for address in addresses):
            for position in range(max(0, index - 1), min(len(lines), index + 2)):
                selected_lines.append(dict(original_line=position + 1, text=lines[position]))
    put('derived/dispatcher-canonical-excerpts.json', dict(path=str(dispatcher.resolve()), sha256=sha(dispatcher.read_bytes()), classification='Derived actual selected case lines; full original referenced in place', lines=selected_lines))

    boundaries = [
        dict(opcode='30', consumer='0x004D5B20', scope='Retained expanded declaration normal-call-return data path; metadata99B alone is not a whole-function extent', raw_sites=['0x004D5B2B', '0x004D5B33', '0x004D5B49', '0x004D5B66', '0x004D5BB1', '0x004D5BE0', '0x004D5BE5', '0x004D5C48', '0x004D5BFE', '0x004D5C07', '0x004D5C0F', '0x004D5C23'], facts='abs(signedBYTE) positive identity, countBYTE<16, writes inactive row at V+D8+count*3EC before duplicate search/activation. Inline name branch ID>=100 and body11==1 searches first active signedWORD identity; hit resets ONLY skillcount1F0 and returns, preserving pointers/flags/aux/selection while inactive stage bytes have already changed. Ordinary append increments D4; input signednegative then selects the staged row D0/CF=newcount-1. Positive append leaves old selection. Neither branch is a learned/common identity grant.'),
        dict(opcode='31', consumer='0x004D58B0', raw_sites=['0x004D58D8', '0x004D58E0', '0x004D58E3', '0x004D5900', '0x004D5907', '0x004D5951', '0x004D595F', '0x004D59BE', '0x004D59CA'], facts='Incoming signedBYTE sign-extends toWORD; first active matching row receives actual raw fields then becomes selected D0/CF on normal return of intervening GUI callsites. Five WORD values zero-extend into rowDWORD44..54; remaining rawWORD and split15-bit/highbit fields retained. This differs from34/35 zero-extended subjectBYTE and allmatching rows. No semantic role classification/common ID inferred.'),
        dict(opcode='32', consumer='0x004D5A10', raw_sites=['0x004D5A17', '0x004D5A1D', '0x004D5A25', '0x004D5A33', '0x004D5A3E', '0x004D5A55'], facts='No packet subject ID: uses current V+D0 for THIS record. Null selectedrow is no-op afterV dereference. Unsigned selectorBYTE vs signed resourceBYTE maximum, resource+0xD5356+selector*0x5E NUL string copied to selectedrow+0x13. True resource bounds/current/string issuer required; no guessed default text or formatter execution.'),
        dict(opcode='33', consumer='0x004D5880', raw_sites=['0x004D5883', '0x004D5889', '0x004D5891', '0x004D5898'], facts='No packet subject ID: current selectedrow D0, nullable row no-op, copy bodyBYTE0 to row40. Tail4D3E30 stopped. This changes fullrow facts even when primary count/pointers do not change.'),
        dict(opcode='39', consumer='0x004D5A90', raw_sites=['0x004D5AA1', '0x004D5AA9', '0x004D5AB7', '0x004D5ABE', '0x004D5AC9', '0x004D5AD6'], facts='No packet subject ID: current selectedrow D0 at THIS record. Copy bodyDWORD0/8 to row2C/30, WORD4/12 to row34/36; body bytes6/7/14/15 are not read in bounded data path but preserved. Null selectedrow no-op; formatter callsites stopped.'),
        dict(opcodes=['34', '35'], consumers=['0x004D5E60', '0x004D5CC0'], facts='Retained206: zero-extended subjectBYTE vsrowWORD, ALL matching roster rows.34 capacitycount<100/no duplicate append underunchanged row/count, bankpointer/flag0/count++;35 first exactpointer flag3, count unchanged. Auxiliary actualhelper may rewrite prefix withoutclearing tail. No common learned/right/source guarantee from this client history.')
    ]
    actions = [
        'Keep complete original mixed record order and bytes. Do not strip30/31/32/33/39 or other non-skill records to derive all34/35 effects from a single stale premix row snapshot.',
        'Each maximal contiguous34/35 run requires an actual source checkpoint at its native boundary after every preceding original record in that publication. A run can preserve ordered staged skill projections; after any intervening original record reacquire actualCurrent/root/selection/fullrow/bank history.',
        '30 can stage inactive storage without changingactivecount/selection; duplicate reset can clear primarycount without clearingpointer/auxstorage. Future native projection must preserve these distinct facts; do not invent an activated row or future revision.',
        '31 changes current selectedrow by signed firstmatch.32/33/39 use that evolving current row and change complete snapshot bytes; same pointer or sameprimarylist does not imply old fullrow Current remains valid.',
        'Other intervening packets are not known no-ops merely because they are not34/35. Without actual checkpoint/effect supplier retain OPEN/refuse qualification; do not manufacture intervening rows, revisions, grant, profile or Main authority.',
        'Checkpoint presence/revision/current endpoint and native source lifecycle must come from actual owner. Held queue/local release is not client processing receipt and cannot by itself qualify a future native source revision.',
        'Normal-call-return data source projection is not execution of GUI/helper/formatter side effects. Actual common mapping, learned authorization, publication supplier and release/gameplay rules remain separate.'
    ]
    findings = dict(round=207, cpp_files_changed=0, new_bounded_native_spans=0, new_bounded_native_bytes=0, new_native_relations=[], retained_bounded_native_spans=len(spans), retained_bounded_native_bytes=sum(row['bytes'] for row in spans), retained_instruction_sites=sum(row['sites'] for row in spans), native_record_boundaries=boundaries, source_qualification_actions=actions, coverage_scope='All selected intervals byte-match already retained roster/status/selected-update/206 evidence. Only ordered source-boundary reconciliation; zero coverage/opcode/phase/fullroute increment.', gaps=['Actual per-contiguous-run checkpoint/common subject/learned/grant/core/profile/producer/lifecycle supplier remains OPEN; no synthetic future Current/revision/state.', '32 resource/title actual bounds/string origin and normal GUI call-return qualification remain independent. No UI/formatter/render/glyph/52F330/52F170 interiors followed.', '30 expanded old376B CFG witness proves data branches beyond recovered metadata99B. Do not relabel metadata99B as complete expanded code.', '31 signed subject versus34/35 zero-extension differs: e.g rawBYTE0x80 sign-extends0xFF80 for31 but zero-extends0x0080 for34/35; numeric example is width arithmetic, not a common identity join.', 'No native/emulator/codec/API/DB/SQL/build/test/runtime/deploy execution. Parent will stop after207; this bounded agent must not initiate208.'], new_opcode_bindings=0, new_phase_bindings=0, new_complete_routes=0, receiver_contexts=14, qualified_receiver_contexts=12, unresolved_helpers=[dict(va='0x0047DE70', phase=None, slot=None), dict(va='0x004812B0', phase=None, slot=None)], current_source_count=len(current), native_canonical_count=len(native), original_input_count=len(originals), historical_count=len(historical), native_reference_count=len(references), complete_game_percentage=None)
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
    print(json.dumps(dict(out=str(O), retained_bytes=findings['retained_bounded_native_bytes'], retained_sites=findings['retained_instruction_sites'], retained_spans=len(spans), new_bytes=0, original=len(originals), current=len(current), native=len(native), references=len(references), historical=len(historical))))


if __name__ == '__main__':
    main()
