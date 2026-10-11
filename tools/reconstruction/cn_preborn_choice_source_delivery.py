"""Static preborn native choices ->required common-operation source accounting.

File/PE/CSV/CFG only; no native, C++, loader, controller, database or tests.
"""
import csv
import difflib
import hashlib
import io
import json
import re
from collections import deque
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-preborn-choice-source-01'
ROUND='20261008-cn-preborn-choice-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/protocol/CnPrebornChoices.h','src/cn/world/SharedPrebornChoices.h',
 'src/cn/world/SharedPrebornChoices.cpp','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
 'docs/research/cn-preborn-choice-source-20261008.md','tools/reconstruction/cn_preborn_choice_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Actual already-issued preborn window/common operation/entitlement/cost/skills/rule/save transaction/replay owner and Application remain unconfigured.',
 'Native A0/A1/A2/A3 issuance selection/order/all IDs/resource capacities and further output variants need their real source, not inferred request/reply pairing.',
 'Primary local CFG/GUI masks/count displays are not server permission, complete exception/helper behavior or original server rules.',
 'Full TW/CN/PC/web/WSS/common login/world/gameplay/numeric64/stack99/state/variant denominator and later comprehensive tests/repair/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def primary_cfg(md,code,entry,table_site,targets):
    end=entry+len(code);pending=deque([entry]);decoded={};edges=[];frontier=[]
    while pending:
        pc=pending.popleft()
        if pc in decoded:continue
        if not entry<=pc<end:frontier.append(dict(site=f'{pc:08x}',reason='outside_qualified_code_range'));continue
        ins=next(md.disasm(code[pc-entry:pc-entry+15],pc,count=1),None)
        if not ins or pc+ins.size>end:frontier.append(dict(site=f'{pc:08x}',reason='decode_crosses_code_range'));continue
        decoded[pc]=ins;nexts=[]
        if ins.group(capstone.CS_GRP_RET):pass
        elif pc==table_site:
            if ins.op_str!='dword ptr [eax*4 + 0x534cf4]':raise RuntimeError('Primary preborn table operand differs')
            nexts=[('qualified_primary_table_case',target) for target in targets]
        elif ins.group(capstone.CS_GRP_JUMP):
            if len(ins.operands)!=1 or ins.operands[0].type!=capstone.x86_const.X86_OP_IMM:
                frontier.append(dict(site=f'{pc:08x}',reason='unqualified_indirect_branch'))
            else:
                nexts=[('direct_branch',ins.operands[0].imm)]
                if ins.mnemonic!='jmp':nexts.append(('conditional_fallthrough',pc+ins.size))
        else:nexts=[('normal_call_return' if ins.group(capstone.CS_GRP_CALL) else 'fallthrough',pc+ins.size)]
        for kind,target in nexts:
            edges.append(dict(source=f'{pc:08x}',target=f'{target:08x}',kind=kind));pending.append(target)
    return dict(entry=f'{entry:08x}',code_end_exclusive=f'{end:08x}',instruction_sites=len(decoded),
        ret_sites=sorted(f'{a:08x}' for a,i in decoded.items() if i.group(capstone.CS_GRP_RET)),edges=edges,frontier=frontier,
        method='PRIMARY_ENTRY_ROOTED_LOCAL_CFG_WITH_QUALIFIED_TABLE_NORMAL_CALL_RETURN_ONLY',
        table_bytes_decoded_as_instructions=False,exception_or_runtime_reachability_claimed=False),decoded

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=107:raise RuntimeError('Expected retained107-file before snapshot')
    old={r['path']:(out/r['snapshot']).read_bytes() for r in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ('json','md')}
    protected=[]
    for row in before:
        rel=row['path']
        if sha(old[rel])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if rel not in set(SOURCES)|set(books)|reports:
            if (ROOT/rel).read_bytes()!=old[rel]:raise RuntimeError('Protected source differs: '+rel)
            protected.append(row)
    prior=(out/'retained-prior/cn-world-exit-ui-binding-source-01/manifest.json').read_bytes()
    if sha(prior)!='8bc4a1f86bb75a8ef3d7b5252ac4e01d2f708db038a58d85bccc5a9cb2f0d381' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    functions=[];instructions={}
    for address in ('00534640','00534320','00533570','005335E0','00533290','00533300','00534810',
                    '004AE370','0048FCC0','00481440','00534D10','00567B50'):
        paths=list(RECOVERY.glob('part_*/'+address.lower()+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Native metadata not unique: '+address)
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-ib,size)
        ins=list(md.disasm(code,va));instructions.update({i.address:i for i in ins})
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
        functions.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),whole_cfg_claimed=False))
    code=view.read(0x534810-ib,0x534cf4-0x534810);table=view.read(0x534cf4-ib,28)
    targets=[int.from_bytes(table[n:n+4],'little') for n in range(0,28,4)]
    if targets!=[0x5348b2,0x5348d6,0x5348f6,0x53491a,0x53493a,0x534a98,0x534ab9]:raise RuntimeError('UI table differs')
    cfg,decoded=primary_cfg(md,code,0x534810,0x5348ab,targets)
    if cfg['frontier'] or cfg['ret_sites']!=['00534860','00534882','00534cf1']:raise RuntimeError('Preborn producer normal CFG incomplete')
    instructions.update(decoded)
    save('native/ranges/00534810-complete-code.bin',code);save('native/tables/00534CF4.bin',table)
    save('native/ranges/00534810-entry-rooted.asm',('\n'.join(f'{a:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for a,i in sorted(decoded.items()))+'\n').encode())
    dump('native/entry-cfg/00534810.json',cfg)
    expected={
      0x4aeea1:('cmp','di, word ptr [esi + 0x1c8500]'),0x4aeeb2:('call','0x534810'),
      0x53481c:('test','al, 2'),0x534863:('test','al, 1'),0x53486f:('cmp','cx, 7'),
      0x534885:('mov','eax, dword ptr [esi + 0x8b0]'),0x5348a2:('cmp','eax, 6'),
      0x534ab9:('cmp','dword ptr [esi + 0x8a8], 0'),0x534aff:('push','1'),
      0x534b02:('push','0x81'),0x534b07:('call','0x481440'),
      0x534b19:('add','ax, ax'),0x534b1e:('add','ax, 3'),0x534b22:('mov','word ptr [edi], ax'),
      0x534b3a:('mov','ax, word ptr [eax]'),0x534b3d:('mov','word ptr [edi + ecx*2 + 2], ax'),
      0x534b59:('dec','eax'),0x534b5c:('push','0x83'),0x534b61:('call','0x481440'),
      0x534b6d:('mov','dword ptr [esi + 0x8a8], 1'),
      0x533607:('movzx','edi, byte ptr [ebx + 0xf74]'),0x53360e:('sub','edi, dword ptr [ebx + 0xd20]'),
      0x5335f8:('movzx','edi, byte ptr [ebx + 0xf75]'),0x5335ff:('sub','edi, dword ptr [ebx + 0xc3c]'),
      0x533614:('push','dword ptr [ecx*4 + 0x9f1174]'),0x5345b7:('mov','eax, dword ptr [0x8a4588]'),
      0x5345d7:('mov','dword ptr [0x9f1174], eax'),0x5345fa:('mov','dword ptr [0x9f1178], eax'),
      0x53330c:('sub','eax, 3'),0x53330f:('shr','eax, 1'),0x533340:('movzx','ebx, word ptr [eax]'),
      0x53334d:('shr','eax, 8'),0x53338f:('movzx','eax, byte ptr [edi + 0xf75]'),
      0x5332e0:('cmp','edx, 4'),0x48ff45:('call','0x533290'),0x48ff59:('call','0x533300'),
      0x481489:('mov','byte ptr [ecx + esi + 0x36c8], al'),0x48149d:('call','0x74f150')}
    qualified=[]
    for site,pair in expected.items():
        ins=instructions.get(site)
        if not ins or (ins.mnemonic,ins.op_str)!=pair:raise RuntimeError(f'Primary operand differs at{site:08x}')
        qualified.append(dict(site=f'{site:08x}',bytes=ins.bytes.hex(),mnemonic=ins.mnemonic,operand=ins.op_str))
    dump('native/qualified-primary-operands.json',qualified)
    native_rows=[]
    for op,branch,length_branch,length in [(0xa1,0x48ff3b,0x567b85,2),(0xa2,0x48ff4f,0x567ba1,-2)]:
        c=0x4929d8+op*4;l=0x567ca4+op*4;cb=view.read(c-ib,4);lb=view.read(l-ib,4)
        if int.from_bytes(cb,'little')!=branch or int.from_bytes(lb,'little')!=length_branch:raise RuntimeError('Native response table differs')
        save(f'native/tables/{c:08X}.bin',cb);save(f'native/tables/{l:08X}.bin',lb)
        native_rows.append(dict(opcode=f'{op:02X}',world_cell=f'{c:08X}',branch=f'{branch:08X}',length_cell=f'{l:08X}',length=length))
    ids_raw=view.read(0x8a4588-ib,4)
    if ids_raw!=bytes.fromhex('19011a01'):raise RuntimeError('Native count label IDs differ')
    save('native/tables/008A4588.bin',ids_raw)
    literal=view.read(0x7f58c0-ib,80).split(b'\0')[0]
    if not literal.endswith(b'playlib\\preborn.cpp'):raise RuntimeError('Native preborn literal differs')
    save('native/literals/007F58C0.bin',literal+b'\0')
    resource=base/'cn-world-exit-ui-binding-source-01/resources'
    plain=(resource/'message.csv').read_bytes();packed=(resource/'message.csvZ').read_bytes();receipt_raw=(resource/'prior-account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_raw)
    if sha(plain)!=receipt['asset']['decoded_sha256'] or sha(packed)!=receipt['asset']['sha256'] or receipt['client_sha256']!=SHA:raise RuntimeError('Qualified resource input differs')
    save('resources/message.csv',plain);save('resources/message.csvZ',packed);save('resources/prior-account-phase-evidence.json',receipt_raw)
    rows=list(csv.reader(io.StringIO(plain.decode('cp936'))));starts=[n for n,row in enumerate(rows) if row and row[0]=='ProgramMsg']
    if len(starts)!=1:raise RuntimeError('ProgramMsg section not unique')
    start=starts[0];values={int(r[0]):dict(csv_row=n,cells=r,cells_cp936_hex=[s.encode('cp936').hex() for s in r]) for n,r in enumerate(rows[start+1:start+1+int(rows[start][1])],start+2)}
    dump('resources/preborn-ProgramMsg-labels.json',{str(k):values[k] for k in [277,278,279,280,281,282]})
    for rel in ['cn-world-exit-ui-binding-source-01/native/exit-ui-binding-and-flag-relations.json','endpoint-catalog128-final/inputs/cn-lengths.json']:
        save('retained-inputs/'+rel,(base/rel).read_bytes())
    cmake=(ROOT/'CMakeLists.txt').read_bytes();save('retained-inputs/CMakeLists.txt',cmake)
    relations=dict(version='cn',phase='world-connection-1',actual_owner='world+89B26C',
        A0_limits=dict(byte1='mimic selection count display F74',byte2='special-skill selection count display F75',
            labels=[281,282],section='ProgramMsg',GUI_remaining_operands=['F74-D20','F75-C3C'],server_permissions_recovered=False),
        C2S_producer=dict(caller='004AE370 matching signed event WORD owner+1C8500',callee='00534810',
            gate='flags&02==0 AND flags&01!=0 AND signed item6 AND mode1 AND owner+8A8==0',
            ordered_queue_calls=[dict(site='00534B07',opcode='81',body_bytes=1,logical_bytes=2),
                dict(site='00534B61',opcode='83',body='WORD(3+2N) +N raw WORDs',logical_bytes='3+2N')],
            post_queue_flag=dict(site='00534B6D',member='owner+8A8',value=1),
            complete_normal_entry_cfg=cfg,metadata_envelope_bytes=162,extended_code_bytes=len(code),table_bytes=28),
        S2C_consumers=[dict(opcode='A1',callee='00533290',logical_bytes=2,observed_bits=[0,1,2,3],higher_bits_preserved=True),
            dict(opcode='A2',callee='00533300',length_tag=-2,WORD_length_includes_opcode=True,
                exact_source_shape='3+2N',raw_WORD_low_byte='ID',raw_WORD_high_byte='kind',native_rules_and_capacity_owner_configured=False)],
        native_response_tables=native_rows,
        source=dict(controller='SharedPrebornChoices',dispatcher='SharedWorldGameplay after actual1C publication',
            actual_already_issued_window_required=True,lease_and_revision_bound=True,stage81_no_gameplay_mutation=True,
            designated_before_apply=True,post_commit_delivery_uses_actual_revision=True,old_scope_not_rechecked_after_commit=True,
            request_reply_pairing=None,actual_rule_save_replay_owner_configured=False,formal_application_hosted=False,complete_route=False))
    dump('native/preborn-producer-consumer-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: readonly A0/A3/UI source and reporter/catalog128 sealed',
        native_sha256=SHA,native_functions=functions,native_primary_metadata_envelope_bytes=sum(f['metadata_envelope_bytes'] for f in functions),
        native_extended_preborn_code_bytes=len(code),native_extended_preborn_table_bytes=28,
        native_extended_preborn_cfg_instruction_sites=cfg['instruction_sites'],native_preborn_primary_operands_qualified=len(qualified),
        cn_preborn_directional_format_readers_added=4,cn_existing_A0_limit_projections_added=1,
        cn_preborn_conditional_common_operation_source_compositions_added=1,native_ordered_81_83_producer_branches_qualified=1,
        native_preborn_ProgramMsg_count_label_relations_added=1,CMake_recursive_source_glob_retained_sha256=sha(cmake),
        actual_preborn_common_rule_save_owner_configured=False,formal_application_hosted=False,new_packet_values=0,
        new_native_phase_source_bindings=6,new_source_owner_chains=1,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        levels_changed=False,fonts_changed=False,build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,
        Windows_API_run=False,native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_preborn_choice_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN native WORLD preborn81/83 ->required common operation ->actual A0/A1/A2/A3 publication source',
        version_scope='pinned-cn-original-world-connection1-preborn-context-only',
        status='Conditional required-owner preborn source attached to world ingress; actual initial issuer/rule/save/replay/Application unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={'world-connection-1':['81','83']},
        native_s2c_by_phase={'world-connection-1':['A0','A1','A2','A3']},source_owner_chains_added=1,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual preborn shared skill/operation/window/native issuance/rule/save/replay owner and full output variants; formal shared login/world providers; all TW/CN/PC/web/WSS/gameplay/numeric64/stack99/full denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN native preborn choice source ('+ROUND+')\n\n'
            'A0 F74/F75 qualify ProgramMsg281/282 mimic/special-skill choice display counts. '
            'Complete primary00534810 code1252B/table28B proves mode1/item6/8A8-zero ordered C2S81(2B)/83(3+2N); metadata162B alone is insufficient. '
            'Added four directional readers/A0 projection1 and one conditional common-operation owner composition in SharedWorldGameplay after actual1C. '
            'Actual already-issued window, common rule/skills/save/replay and post-commit output revision are mandatory and unconfigured; no fabricated ACK/values/entitlement/reply pairing. '
            'Source phase bindings6/partial owner1/new opcode0/full routes0; whole totals/percent null. '
            'Full TW/CN/PC/web/WSS/gameplay/numeric64/stack99 scope and real Application/initial issuers remain open. '
            'No build/test/native/C++/API/DB/deploy; see research/cn-preborn-choice-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes',
        'native_extended_preborn_cfg_instruction_sites','new_native_phase_source_bindings','new_source_owner_chains','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
