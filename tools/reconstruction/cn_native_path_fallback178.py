"""Round178 actual CN fallback and path-owner registration, static file/PE only.

No native execution, invented movement authority/ACK, generic A* or TW alias.
"""
from pathlib import Path
import csv
import io
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .cn_receiver_owner_frontier169 import sha, mapped

SERVER = Path(__file__).resolve().parents[2]
ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'tw-native-chat-record-source-01/agents/cn-path-fallback'
EXE = SERVER.parent.parent / 'God2-xjz/XJZ-CN/God2_opt.exe'
RECOVERY = EXE.parent.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
OWN = 'tools/reconstruction/cn_native_path_fallback178.py'
SOURCE = ['AGENTS.md', 'docs/IMPLEMENTATION_PROVENANCE.md', 'docs/GOAL_ACCEPTANCE.md',
    'src/cn/world/CnNativePathCompletion.h', 'src/cn/world/SharedNativeMovementScene.h',
    'tools/reconstruction/cn_receiver_owner_frontier169.py',
    'tools/reconstruction/cn_native_movement_cells177.py']
NEW = {'00485730', '00484c40', '00486e30'}
RETAINED = {'00486920', '00487190', '00470310', '004866a0', '00535d80'}
READ_CONTEXT = {'00486160', '00486190', '004865c0', '004868c0',
    '00486e20', '00486e40', '00486e80', '00487440', '00487530', '0048caa0'}
SPANS = [('owner-registrations', '0048caa0', 0x48d4ae, 0x48d52e, True),
         ('retained-external-slot', '0048caa0', 0x48cb3d, 0x48cb49, False)]
# Coordinates are relative offsets, not a native direction/opcode namespace.
ORDERS = [
    ('dx>0,dy>0', 0x485754, [(1,1),(1,0),(0,1),(1,-1),(-1,1),(0,-1),(-1,0),(-1,-1)],
     ['0048577b','004857b3','004857e0','00485812','0048583b','00485859','00485878','00485896']),
    ('dx>0,dy=0', 0x4858b0, [(1,0),(1,-1),(1,1),(0,-1),(0,1),(-1,-1),(-1,1),(-1,0)],
     ['004858ce','00485908','00485940','00485964','00485982','004859a2','004859be','004859dc']),
    ('dx>0,dy<0', 0x4859f6, [(1,-1),(0,-1),(1,0),(-1,-1),(1,1),(-1,0),(0,1),(-1,1)],
     ['00485a27','00485a57','00485a86','00485aae','00485ad1','00485af0','00485b0f','00485b2d']),
    ('dx=0,dy<0', 0x485b49, [(0,-1),(-1,-1),(1,-1),(-1,0),(1,0),(-1,1),(1,1),(0,1)],
     ['00485b6f','00485bab','00485bd7','00485bf5','00485c14','00485c37','00485c56','00485c74']),
    ('dx=0,dy>0', 0x485c8e, [(0,1),(1,1),(-1,1),(1,0),(-1,0),(1,-1),(-1,-1),(0,-1)],
     ['00485cae','00485cda','00485cf5','00485d14','00485d33','00485d56','00485d75','00485d93']),
    ('dx<0,dy<0', 0x485dad, [(-1,-1),(-1,0),(0,-1),(-1,1),(1,-1),(0,1),(1,0),(1,1)],
     ['00485de4','00485e1c','00485e3e','00485e62','00485e85','00485ea4','00485ec3','00485ee1']),
    ('dx<0,dy=0', 0x485efb, [(-1,0),(-1,1),(-1,-1),(0,1),(0,-1),(1,1),(1,-1),(1,0)],
     ['00485f1b','00485f3d','00485f63','00485f81','00485fa0','00485fc1','00485fdd','00485ffb']),
    ('dx<0,dy>0', 0x486015, [(-1,1),(0,1),(-1,0),(1,1),(-1,-1),(1,0),(0,-1),(1,-1)],
     ['00486044','00486071','00486091','004860b5','004860d5','004860ec','00486108','0048611e']),
]


def dump(rel, obj):
    p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write((json.dumps(obj, indent=2, ensure_ascii=True) + '\n').encode())


def retain(rel, path, repository=False):
    raw = path.read_bytes(); p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(raw)
    return {'path': path.relative_to(SERVER).as_posix() if repository else str(path.resolve()),
            'copy': rel, 'bytes': len(raw), 'sha256': sha(raw)}


def main():
    if OUT.exists():
        raise RuntimeError('Preserve previous round178 output')
    raw = EXE.read_bytes()
    if sha(raw) != PIN:
        raise ValueError('CN original input changed')
    OUT.mkdir(parents=True)
    dump('before-source-origins.json', [retain(f'before/b{n:02d}{Path(r).suffix}', SERVER/r, True)
        for n,r in enumerate(SOURCE)])
    dump('new-source-absence.json', {'freshbefore1277_new_tool_absent': OWN,
        'cpp_changes': [], 'whole_prior177_immutable': True})
    prior = ROOT / 'tw-native-mixed-dispatch-source-01/agents/cn-cell-frontier'
    derived = [prior/'findings.json', prior/'seal.json', prior/'native/new-sites.json',
        ROOT/'cn-shared-movement-owner-01/native/20261006-cn-map-passability-01/map-passability-evidence.json',
        ROOT/'tw-native-chat-record-source-01/before-manifest.json']
    dump('derived-inputs.json', [retain(f'derived/d{n:02d}.json', p) for n,p in enumerate(derived)])
    metadata = list(csv.DictReader(io.StringIO((RECOVERY/'functions.tsv').read_text(
        encoding='utf-8-sig')), delimiter='\t'))
    selected = [r for r in metadata if r['address'] in NEW|RETAINED|READ_CONTEXT]
    originals = [retain('inputs/pe.exe', EXE)]
    for n,name in enumerate(('functions.tsv','calls.tsv')):
        originals.append(retain(f'inputs/t{n}.tsv', RECOVERY/name))
    for row in selected:
        originals.append(retain('inputs/'+row['address']+'.c', RECOVERY/row['file']))
    dump('native-original-inputs.json', originals)
    dump('native/selected-original-metadata.json', selected)
    pe = pefile.PE(data=raw, fast_load=True); md = Cs(CS_ARCH_X86, CS_MODE_32)
    spans = [(r['address'],r['address'],int(r['address'],16),
              int(r['address'],16)+int(r['bytes']),r['address'] in NEW)
             for r in selected if r['address'] in NEW|RETAINED] + SPANS
    sites, retained, instructions = [], [], {}
    for name, owner, lo, hi, isnew in spans:
        off,b = mapped(pe,raw,lo,hi)
        decoded = [{'va':f'{i.address:08x}','bytes':bytes(i.bytes).hex(),
                    'instruction':i.mnemonic+(' '+i.op_str if i.op_str else '')}
                   for i in md.disasm(b,lo)]
        instructions.update({r['va']:r for r in decoded})
        scope = 'new' if isnew else 'retained'
        dst=OUT/f'native/{scope}/{name}.bin';dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open('xb') as f:f.write(b)
        dump(f'native/{scope}/{name}.json', decoded)
        item={'name':name,'owner':owner,'start_va':f'{lo:08x}','end_va_exclusive':f'{hi:08x}',
              'file_offset':off,'bytes':len(b),'raw_bytes':b.hex(),'sha256':sha(b),
              'whole_function':name in NEW|RETAINED,
              'decoded_bytes':sum(len(bytes.fromhex(r['bytes'])) for r in decoded),
              'new_phase_or_opcode':False}
        (sites if isnew else retained).append(item)
    dump('native/new-sites.json',sites);dump('native/retained-sites.json',retained)
    calls=list(csv.DictReader(io.StringIO((RECOVERY/'calls.tsv').read_text(encoding='utf-8-sig')),delimiter='\t'))
    dump('native/bounded-original-calls.json',[r for r in calls
        if r['caller'] in NEW|RETAINED or (r['caller']=='0048caa0' and r['target'] in ['00484c40','00486e30'])])
    direction_rows=[]
    for predicate, entry, offsets, rawsites in ORDERS:
        direction_rows.append({'signed_predicate':predicate,'entry_va':f'{entry:08x}',
            'offsets_in_original_order':offsets,'raw_call_sites':[instructions[v] for v in rawsites],
            'scope':'Static original C branch plus complete original PE instructions. Not executed or simulated; first nonzero AL writes outputs.'})
    dump('native/exact-relative-candidate-orders.json',direction_rows)

    def relation(key, addresses, scope):
        return {'key':key,'scope':scope,'raw_sites':[instructions[a] for a in addresses],
                'new_server_permission':False,'new_full_route':False}
    relations=[
        relation('fallback_six_stack_arguments_and_two_DWORD_outputs',
          ['004873d3','004873d4','004873d5','004873e1','004873e3','004873e4','004873eb','004873ec',
           '00485733','00485738','0048573b','0048573d','00485741','0048612f','00486154'],
          'ECX original path owner; stackargs outX*,outY*,baseX,baseY,deltaX,deltaY. Outputs are DWORD stores and callee ret0x18. No reliable bool result contract is present; caller ignores EAX and uses output locals.'),
        relation('eight_actual_signed_direction_candidate_orders',
          ['00485744','00485746','0048574c','0048574e','004858b0','004859f8','00485b49',
           '00485b51','00485c8e','00485dad','00485daf','00485db7','00485efb','00486017'],
          'Actual delta signs select eight distinct relative candidate priority lists in exact-relative-candidate-orders.json; cannot reuse TW fallback or the normal neighbor enumeration merely because offsets coincide.'),
        relation('actual_map_pointer_and_AL_nonzero_choice',
          ['00485754','0048575e','0048577b','00485795','00485799','0048579b',
           '004857a2','004857a5','004857b3','004857bc','004857be','0048583b','00485840'],
          'Both inline reader and retained00486920 obtain actual owner+0x0C -> object+0xBC map. Null produces low byte0; nonzero raw AL chooses candidate. Marker2 is not separately interpreted here; adjacent cardinal cells are not checked to authorize a diagonal in this full callee.'),
        relation('zero_direction_and_exhausted_candidates_preserve_outputs',
          ['00485c8e','00485daf','00486017','0048589d','00486125','00486131','00486133',
           '00486135','00486137','00486154'],
          'Exact zero direction and final failed candidates jump directly to pointer assertion/return without writing output coordinates. No generated default pair, success byte or permission. Assertion occurs after candidate stores and is not a safe null-output guard.'),
        relation('actual_constructor_packed_buffer_and_unset_owner',
          ['00484c47','00484c4c','00484c4e','00484c51','00484c56','00484c5c','00484c66',
           '00484c6e','00484c73','00484c76','00484c79','00484c7b','00484c80','00484c84'],
          'Actual00484C40 supplies owner+8 allocation8 and owner+0x10 allocation0x7E. Initializes header byte and30 WORD X/Y pairs only (offsets2..0x3C and0x40..0x7A), owner+0x0C/+0x14 zero. Does not initialize entire packed buffer or prove ownership rights, count rules or permission.'),
        relation('two_actual_owner_allocations_and_slot_setter',
          ['0048d4ae','0048d4b0','0048d4c5','0048d4c9','0048d4cb','0048d4d4','0048d4da',
           '0048d4e3','0048d4e9','0048d4ee','0048d4f0','0048d50b','0048d514','0048d51a',
           '0048d523','0048d529','00486e33','00486e36','00486e3a','0048cb3d','0048cb43'],
          'Bounded0048CAA0 setup allocates two0x18 owners, calls00484C40, publishes game+0x8885D0/+0x8885D4 and calls00486E30 with game+0x8885E0. Exact setter copies stack DWORD to ECX+0x0C. Retained entry loads external owner+0x44C into game+0x8885E0. Actual object+0xBC map producer and subsequent lifecycle remain unrecovered; registration is not phase or rights.'),
    ]
    gaps=[{'gap':'Actual object+0xBC map producer/current lifecycle',
           'next_actual_root':'external owner+0x44C ->game+0x8885E0 ->00486E30 search owner+0x0C; trace actual selected object constructor/map writes without treating constructorzero as authority.'},
          {'gap':'Full packed path/count/capacity/search semantics',
           'next_actual_root':'004866A0 retains count and retry logic;00487190 can use unchanged fallback outputs. Complete path list/limits and output-copy count rules still need exact producer/consumer evidence.'},
          {'gap':'Formal shared movement permission and complete5D source',
           'next_actual_root':'SharedNativeMovementScene::Authority actual caller with timing/ring/pending/battle/transfer/fullreply producers. Client fallback nonzero cell is not a server permission.'}]
    dump('gaps.json',gaps)
    dump('findings.json',{'round':178,'client_sha256':PIN,
        'new_bounded_native_spans':len(sites),'new_bounded_native_bytes':sum(r['bytes'] for r in sites),
        'new_whole_native_functions':3,'retained_bounded_native_spans':len(retained),
        'new_native_relations':relations,'exact_direction_orders':direction_rows,
        'native_original_inputs':len(originals),'cpp_edits':[],'new_source_bindings':0,
        'receiver_contexts':14,'qualified_receiver_contexts':12,
        'unresolved_helpers':[{'va':v,'phase':None,'slot':None,'producer':None} for v in ['0047DE70','004812B0']],
        'new_opcodes':0,'new_phase_bindings':0,'new_complete_routes':0,
        'whole_game_route_denominator':None,'whole_game_percentage':None,
        'gaps':gaps,'builds_tests_runtime_deploy':False,'awaiting_BATCHFINAL':True})


if __name__ == '__main__':
    main()
