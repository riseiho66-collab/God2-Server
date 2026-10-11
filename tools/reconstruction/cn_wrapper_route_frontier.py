"""Recover bounded CN wrapper trigger edges by static source/instruction reading.

Does not load the client, execute gameplay, build or run tests. Candidate edges
are not completed routes; missing call-graph entries are explicitly preserved.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re
import struct
import capstone
import pefile

ROOT = Path(__file__).resolve().parents[2]
CN = ROOT.parent.parent / 'God2-xjz' / 'God2-Server-CN'
RECOVERY = CN.parent / 'God2_opt_source_recovery_20260926_055734/decompiled'
PIN = '582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--round', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.round):
        raise SystemExit('Invalid round')
    out = ROOT / 'artifacts/integration/packet-connections-20261006' / args.round
    if out.exists():
        raise SystemExit('Preserve previous evidence: choose a new round')
    raw = (CN.parent / 'XJZ-CN/God2_opt.exe').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise SystemExit('CN build identity changed')
    pe = pefile.PE(data=raw, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    with (RECOVERY / 'functions.tsv').open(encoding='utf-8-sig') as f:
        funcs = {r['address']: r for r in csv.DictReader(f, delimiter='\t')}
    with (RECOVERY / 'calls.tsv').open(encoding='utf-8-sig') as f:
        calls = list(csv.DictReader(f, delimiter='\t'))
    old = CN / 'artifacts/native/20261006-cn-wrapper-producers-02'
    transfers = json.loads((old / 'transfer-candidates.json').read_text())
    selected = [r for r in transfers if r['target'] == '004b1b40'
                and r['immediate_first_explicit_argument'] in (0x31, 0x68, 0x6d)]
    gates = {
        '004c2b61': 'incoming payload byte1 in0x26..0x29 and object[1b938]+24==1; WORLD S2C3B dispatch004913e1 passes logical_packet+1 to4c2b30; secondary dispatch also has3B',
        '004c737d': 'payload byte2<0x32; signed payload byte3 count<1 after storage; slot byte2 in0x26..0x29; object[1b938]+24==1; WORLD S2C41->4c72e0(packet+1)',
        '004c7b2d': 'payload byte2 slot in0x26..0x29; native clears count/id and refreshes row; object[1b938]+24==1; WORLD S2C3C->4c7a50(packet+1)',
        '004d21c0': 'owner4d1e70 outer signed16 param1==1; 52c950()==0; inner sign_extend16(param2+0x1b)-0x1b==9; slot1c8554 absent or bit20 clear; object[1b938]+24==0 through458530',
        '004edf96': 'slot+1c8496 nonnegative and row stride2a08 flags+78074 bit10; slots1c84b4/1c84c8 absent or bit08 clear; 49f180 checks on 1c8512/1c8514/1c84ac/1c8524 all zero',
        '004efd83': 'signed slot+1c8494 nonnegative and selected row stride2a08 flags+78074 bit10 set; separate instruction entry004efd60 missing from functions.tsv',
        '004f07e2': 'slot1c8492 active bit20; byte77858==0; slot1c8494 absent or its bit20 clear',
        '004f0891': 'event flags bit02 clear; either bit04 set and byte77858==0, or bit04 clear and bit20 set with param2==2; second branch joins the same native send block',
        '00537d2c': '458530 returns object+24==0; object passed as parent+a69f28',
        '00538cf9': 'saved pre-update parent+a69f4c value nonzero; captured at entry before other calls and used after519d60; field semantic meaning unresolved',
    }
    receive_relations={
        '004c2b61':('3b','004913e1','005487c6'),
        '004c737d':('41','00491409','00548805'),
        '004c7b2d':('3c','004913f5','005487f3'),
    }
    out.mkdir(parents=True)
    manifest = []
    def save(relative, data, source=None):
        p=out/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        manifest.append({'path':relative,'source':str(source) if source else None,
                         'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    def dump(relative, value):
        save(relative,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    for name in ('transfer-candidates.json','wrapper-evidence.json','summary.json'):
        save('upstream/'+name,(old/name).read_bytes(),old/name)
    targets={'004c2b30','004edec0','004f0760','004f0860','00537d10','005385f0','004efd60','004d1e70'} | {r['nearest_recovery_anchor'] for r in selected}
    upstream=[r for r in calls if r['target'] in targets]
    snapshots={'004b1b40','004815e0','00458530','00536a10','005395e0','00519d60'} | (targets & funcs.keys()) | {r['caller'] for r in upstream}
    for address in sorted(snapshots):
        source=RECOVERY/funcs[address]['file']
        save('source/'+address+'.c',source.read_bytes(),source)
    for address,size in [('004efd60',43),('00458530',9),('004815e0',27),('004b1b40',204),('004d1e70',91),('004d20c1',60),('004d21a7',38)]:
        va=int(address,16)
        lines=[f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
               for i in md.disasm(pe.get_data(va-base,size),va)]
        save('instructions/'+address+'.asm',('\n'.join(lines)+'\n').encode(),f'God2_opt.exe VA {address}')
    edges=[]
    for r in selected:
        site=r['callsite'];op=r['immediate_first_explicit_argument']
        anchor={'004efd83':'004efd60','004d21c0':'004d1e70'}.get(site,r['nearest_recovery_anchor'])
        # Read the actual instruction at each stored site rather than assigning
        # native meaning from the decompiler's nearest-function label.
        instruction=next(md.disasm(pe.get_data(int(site,16)-base,5),int(site,16)),None)
        actual_target=instruction.op_str if instruction and instruction.mnemonic=='call' else None
        edges.append({'candidate_id':f'cn:c2s:phase-unresolved:{op:02x}:producer-{site}',
                      'direction':'C2S','opcode':f'{op:02x}','payload_hex':'00',
                      'phase':'unresolved','native_owner_entry':anchor,'callsite':site,
                      'actual_instruction_target':actual_target,
                      'owner_in_recovery_function_index':anchor in funcs,
                      'previous_nearest_anchor':r['nearest_recovery_anchor'],
                      'trigger_condition':gates.get(site),
                      'trigger_condition_reviewed':site in gates,
                      'receive_trigger_relation': {'world_s2c_opcode':receive_relations[site][0],'dispatch_callsite':receive_relations[site][1],'secondary_dispatch_callsite':receive_relations[site][2],'logical_payload_offset':1,'native_receive_to_send_only':True,'does_not_prove_server_request_reply_causality':True} if site in receive_relations else None,
                      'shared_wrapper_extra_gate': 'object[4726c]+f4 low2bits !=3; otherwise local message32f' if op==0x68 else None,
                      'consumer_pairing':None,'server_handler':None,'source_connected':False,
                      'runtime_reachability_proven':False,'complete_bidirectional_route':False,
                      'next':['Recover owning connection phase and upstream trigger meaning',
                              'Pair native S2C consumers with authority/state transitions',
                              'Connect actual shared server handler and version presenter']})
    references=[]
    for section in pe.sections:
        data=section.get_data();sva=base+section.VirtualAddress
        if section.Characteristics & 0x20000000:
            for opcode in (0xe8,0xe9):
                pos=data.find(bytes([opcode]))
                while pos>=0:
                    if pos+5<=len(data) and (sva+pos+5+struct.unpack_from('<i',data,pos+1)[0])&0xffffffff==0x4efd60:
                        references.append({'va':hex(sva+pos),'kind':'relative_transfer_candidate','instruction_alignment_proven':False})
                    pos=data.find(bytes([opcode]),pos+1)
        pos=data.find(struct.pack('<I',0x4efd60))
        while pos>=0:
            references.append({'va':hex(sva+pos),'kind':'absolute_pointer_candidate','section':section.Name.rstrip(b'\0').decode(errors='replace')})
            pos=data.find(struct.pack('<I',0x4efd60),pos+1)
    dump('unindexed-entry-references.json',{'entry':'004efd60','relative_e8_e9_scan':'all PE executable raw sections','absolute_u32_scan':'all PE raw sections','references':references,'does_not_prove_unreachable':True,'remaining':'computed pointer, external owner, relocation/island entry and fallthrough not ruled out'})
    outer=struct.unpack('<5I',pe.get_data(0x4d23c4-base,20))
    inner=struct.unpack('<14I',pe.get_data(0x4d2414-base,56))
    dump('6d-ui-selector-tables.json',{'owner':'004d1e70','outer_table_va':'004d23c4','outer':[hex(v) for v in outer], 'inner_table_va':'004d2414','inner':[hex(v) for v in inner],'sender_case_index':9,'sender_case_va':'004d21a7','old_nearest_case0_anchor_is_wrong_owner':True})
    dump('6d-deferred-refresh-relation.json',{
        'world_s2c_opcode':'4a','consumer':'0048fcc0',
        'cache_copy':'logical_packet+1 u32 -> parent+89b240',
        'direct_branch':'parent+30 !=8 ->5385f0 at00490775',
        'deferred_branch':'parent+30 ==8 ->parent+89b244=1',
        'resume':'5395e0 when parent+30==8 and5393b0()==1 and parent+89b244!=0 ->5385f0 at0053963d; then clear89b244',
        'send_condition':'5385f0 captures parent+a69f4c before updating; paths reaching00538cf9 send6D only when saved value!=0; earlier returns exist and are not exhaustively classified here',
        'other_known_triggers':['536a10 calls5385f0 at00536a8e and00536cd6; original incoming opcode/variant pairing remains open'],
        'field_relation':'537d10 passes parent+a69f28 to458530; +24 field is parent+a69f4c',
        'field_semantics':None,'server_c2s6d_to_s2c4a_causality_proven':False,
        'complete_route':False,'direct_and_deferred_are_new_opcode_values':False,
        'recovery_graph_warning':'calls.tsv misses4d21ad->458530; its listed caller count is not exhaustive'})
    save('recovery-tool.py',Path(__file__).read_bytes(),Path(__file__))
    # Stored call graph is an incomplete search frontier, never a proof of all callers.
    dump('upstream-call-edges.json',upstream)
    dump('route-candidates.json',edges)
    dump('summary.json',{'product':'GOD2-CN','client_sha256':PIN,
         'candidate_producer_edges':len(edges),'opcode_values':sorted({r['opcode'] for r in edges}),
         'trigger_conditions_reviewed':sum(r['trigger_condition_reviewed'] for r in edges),
         'trigger_conditions_pending':[r['callsite'] for r in edges if not r['trigger_condition_reviewed']],
         'native_receive_to_send_relations':len(receive_relations),
         'additional_direct_and_deferred_refresh_family':'S2C4A ->5385f0 or cached5395e0 ->conditionalC2S6D; partial upstream gates only',
         'unindexed_entry_reference_candidates':len(references),
         'upstream_graph_edges':len(upstream),'upstream_graph_is_exhaustive':False,
         'recovered_unindexed_instruction_entries':['004efd60'],
         'new_whole_game_opcodes':0,'new_complete_routes':0,'whole_game_route_total':None,
         'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,
         'next_priority':'Resolve meaning/ownership of shared+a69f4c field and S2C consumers of6D; computed/island reachability of004efd60 remains open.'})
    dump('source-manifest.json',manifest.copy())
    print(json.dumps({'output':str(out),'producer_edges':len(edges),'upstream_edges':len(upstream),
                      'new_complete_routes':0,'whole_game_total':None}))


if __name__ == '__main__':
    main()
