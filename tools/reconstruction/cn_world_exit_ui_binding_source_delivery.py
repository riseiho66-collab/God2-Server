"""Pinned CN A0/A3 flag writes and UI resource bindings, files only.

No loader, native route, C++, formatter, API, server, database or test executes.
"""
import csv
import difflib
import hashlib
import io
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-world-exit-ui-binding-source-01'
ROUND='20261008-cn-world-exit-ui-binding-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/protocol/CnWorldExitLifecycleControl.h',
 'docs/research/cn-world-exit-ui-binding-source-20261008.md',
 'tools/reconstruction/cn_world_exit_ui_binding_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py',
 'tools/reconstruction/packet_connection_report.py')
REMAINING=[
 'Actual server A0/A3 issuers, full conditions, two payload byte meanings, operation/save/replay authority and Application remain unconfigured.',
 '00534640 full side effects, actual post-tail callback8AC value, UI handle activation/destruction, early signed-WORD returns and state6 sources remain open.',
 'Native UI/resource and flag writes are not server permissions, original03 payload/save completion or a complete request/reply pairing.',
 'Full TW/CN/PC/web/WSS/common-world/gameplay/numeric64/stack99/state/variant denominator and later comprehensive testing/repair/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=104:raise RuntimeError('Expected retained104-file before snapshot')
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
    prior=(out/'retained-prior/cn-world-command-return-lineage-01/manifest.json').read_bytes()
    if sha(prior)!='631513be40feff5a31085e6ce449233f127c1b9aa09c1d69cf566f1bddae7480' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    functions=[];instructions={}
    for address in ('0048CAA0','004AC850','0048FCC0','00527650','005277A0','00527D80',
                    '00533430','00534320','00534D10','00567B50'):
        paths=list(RECOVERY.glob('part_*/'+address.lower()+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Native metadata not unique: '+address)
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing metadata extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-ib,size)
        ins=list(md.disasm(code,va));instructions.update({i.address:i for i in ins})
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
        functions.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),whole_cfg_claimed=False))
    # Primary operands qualify the same ECX and actual copied argument; no
    # object join merely because unrelated objects have equal member offsets.
    expected={
      0x48cb79:('mov','ecx, dword ptr [esi + 0x8885c4]'),0x48cb91:('lea','eax, [ecx + 0x464]'),
      0x48cb97:('mov','dword ptr [esi + 0xa69f20], eax'),
      0x48d5b1:('lea','ecx, [esi + 0x89b26c]'),0x48d611:('mov','eax, dword ptr [esi + 0xa69f20]'),
      0x48d617:('mov','dword ptr [ebp - 0x35c], eax'),0x48d65d:('lea','eax, [ebp - 0x37c]'),
      0x48d669:('push','eax'),0x48d670:('call','0x4ac850'),
      0x4ac864:('mov','ebx, dword ptr [ebp + 8]'),0x4ac868:('mov','esi, ecx'),
      0x4ac8a6:('mov','eax, dword ptr [ebx + 0x20]'),0x4ac8a9:('mov','dword ptr [esi + 0x65364], eax'),
      0x4acdc7:('mov','ecx, esi'),0x4acdc9:('call','0x5277a0'),
      0x4ace7e:('mov','ecx, esi'),0x4ace80:('call','0x534320'),
      0x48fcd7:('mov','ebx, ecx'),0x48fd51:('movzx','esi, byte ptr [edi]'),
      0x48fd5a:('cmp','esi, 0xfd'),0x48fd66:('jmp','dword ptr [esi*4 + 0x4929d8]'),
      0x48ff27:('lea','eax, [edi + 1]'),0x48ff2a:('push','eax'),
      0x48ff2b:('lea','ecx, [ebx + 0x89b26c]'),0x48ff31:('call','0x534d10'),
      0x48ff7c:('lea','eax, [edi + 1]'),0x48ff7f:('push','eax'),
      0x48ff80:('lea','ecx, [ebx + 0x89b26c]'),0x48ff86:('call','0x533430'),
      0x533430:('mov','dword ptr [ecx + 0x8ac], 1'),0x53343a:('ret','4'),
      0x534320:('xor','eax, eax'),0x534335:('mov','dword ptr [ecx + 0x8ac], eax'),
      0x534d16:('mov','eax, dword ptr [esi + 0x430a8]'),0x534d1c:('cmp','byte ptr [eax + 0xd4], 0'),
      0x534d23:('jbe','0x534d9e'),0x534d25:('push','0x190'),
      0x534d7a:('movzx','eax, byte ptr [ecx + 1]'),0x534d7e:('mov','byte ptr [esi + 0xf75], al'),
      0x534d84:('movzx','eax, byte ptr [ecx]'),0x534d89:('mov','byte ptr [esi + 0xf74], al'),
      0x534d8f:('call','0x534640'),0x534d94:('mov','dword ptr [esi + 0x8ac], 0'),
      0x5277a0:('mov','ecx, dword ptr [ecx + 0x65364]'),0x5277a6:('mov','eax, dword ptr [0x8a3638]'),
      0x5277af:('movsx','esi, word ptr [ecx + 0xb2f64]'),0x5277c0:('mov','eax, dword ptr [ecx + 0xb2f60]'),
      0x5277c6:('mov','eax, dword ptr [eax + edx*4 - 4]'),0x5277ce:('mov','dword ptr [0x9f1058], eax'),
      0x5277d3:('mov','ax, word ptr [0x8a363a]'),0x5277f1:('mov','dword ptr [0x9f105c], eax'),
      0x527670:('call','0x451460'),0x527694:('mov','word ptr [esi + 0x1c8544], ax'),
      0x5276df:('push','dword ptr [0x9f1058]'),0x52770c:('push','dword ptr [0x9f105c]'),
      0x527dba:('mov','dword ptr [edi + 0x43088], 1'),0x527e1f:('call','0x451460'),
      0x527e34:('mov','word ptr [edi + 0x1c84ae], ax'),
      0x567b62:('jmp','dword ptr [eax*4 + 0x567ca4]'),0x567b69:('mov','eax, 3'),0x567b6f:('ret','')}
    qualified=[]
    for site,pair in expected.items():
        ins=instructions.get(site)
        if not ins or (ins.mnemonic,ins.op_str)!=pair:raise RuntimeError(f'Primary operand differs at{site:08x}')
        qualified.append(dict(site=f'{site:08x}',primary_bytes=ins.bytes.hex(),mnemonic=ins.mnemonic,operand=ins.op_str))
    dump('native/qualified-primary-operands.json',qualified)
    table_rows=[]
    for op,branch in ((0xa0,0x48ff27),(0xa3,0x48ff7c)):
        cell=0x4929d8+op*4;length_cell=0x567ca4+op*4
        b=view.read(cell-ib,4);l=view.read(length_cell-ib,4)
        if int.from_bytes(b,'little')!=branch or int.from_bytes(l,'little')!=0x567b69:raise RuntimeError('Native control table differs')
        save(f'native/tables/{cell:08X}.bin',b);save(f'native/tables/{length_cell:08X}.bin',l)
        table_rows.append(dict(opcode=f'{op:02X}',world_cell=f'{cell:08X}',world_branch=f'{branch:08X}',
            length_cell=f'{length_cell:08X}',length_branch='00567B69',full_logical_length=3))
    ids_raw=view.read(0x8a3638-ib,4)
    if ids_raw!=bytes.fromhex('3e003f00'):raise RuntimeError('Primary UI label IDs differ')
    save('native/tables/008A3638.bin',ids_raw)
    loader=view.read(0x4294cb-ib,0x4295f6-0x4294cb)
    prior_loader=(base/'cn-billing-presentation-variants-source-01/native/ranges/ProgramMsg-loader.bin').read_bytes()
    if loader!=prior_loader or view.read(0x7ee944-ib,11)!=b'ProgramMsg\0':raise RuntimeError('Qualified ProgramMsg loader differs')
    save('native/ranges/ProgramMsg-loader.bin',loader)
    save('native/ranges/ProgramMsg-loader.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in md.disasm(loader,0x4294cb))+'\n').encode())
    save('native/literals/007EE944.bin',b'ProgramMsg\0')
    resource=base/'cn-directory-display-fields-01/native/resources'
    receipt_raw=(resource/'account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_raw)
    packed=(CN.parent/'Data2/Patch/Comm/message.csvZ').read_bytes();plain=(resource/'message.csv').read_bytes()
    if receipt['client_sha256']!=SHA or receipt['asset']['codepage']!=936 or sha(packed)!=receipt['asset']['sha256'] or sha(plain)!=receipt['asset']['decoded_sha256']:
        raise RuntimeError('Pinned resource source differs')
    save('resources/message.csvZ',packed);save('resources/message.csv',plain);save('resources/prior-account-phase-evidence.json',receipt_raw)
    rows=list(csv.reader(io.StringIO(plain.decode('cp936'))));sections={}
    for section in ('ProgramMsg','SystemMessage'):
        starts=[n for n,row in enumerate(rows) if row and row[0]==section]
        if len(starts)!=1:raise RuntimeError('Resource section not unique')
        start=starts[0];count=int(rows[start][1]);selected={}
        for n,row in enumerate(rows[start+1:start+1+count],start+2):
            if row[0] in ('62','63'):
                if row[0] in selected:raise RuntimeError('Duplicate source label')
                selected[row[0]]=dict(csv_row=n,cells=row,cells_cp936_hex=[s.encode('cp936').hex() for s in row])
        if len(selected)!=2:raise RuntimeError('Missing source labels')
        sections[section]=dict(declared_rows=count,selected=selected,qualified_for_exit_labels=section=='ProgramMsg')
    dump('resources/selected-section-rows.json',sections)
    for rel in ('cn-world-command-return-lineage-01/native/command-return-and-close-relations.json',
                'cn-world-return-state-frontier-01/native/return-state-and-close-relations.json',
                'endpoint-catalog127/inputs/cn-lengths.json'):
        save('retained-inputs/'+rel,(base/rel).read_bytes())
    relations=dict(version='cn',phase='world-connection-1',actual_owner='world+89B26C',
        initialization=dict(caller='0048CAA0',argument_array_index=8,source='LEA actual main+464 ->world+A69F20',
            receiver='004AC850',resource_member='owner+65364',flag_callee='00534320',flag_8ac=0),
        consumers=[dict(direction='S2C',opcode='A0',callee='00534D10',full_logical_length=3,
            payload_retained=True,gate='BYTE(*(owner+430A8)+D4)>0',zero_gate_no_writes=True,
            byte1_target='owner+F74',byte2_target='owner+F75',helper_before_clear='00534640',normal_return_flag_8ac=0,
            payload_semantic_names_recovered=False),
            dict(direction='S2C',opcode='A3',callee='00533430',full_logical_length=3,payload_retained=True,
                callee_reads_payload=False,flag_8ac=1,payload_semantic_names_recovered=False)],
        table_rows=table_rows,
        tail_dependency=dict(callee='004AE370',callbacks=['0050B110','0050A320','00496890','0051A720'],
            actual_flag_AFTER_callbacks_equals=1,override_command=-15,world_state=5,main_eax=4,
            sends_close_at_this_main_switch=False,external_main_branch='login UI; real server reason unknown',
            flags_at_receive_time_alone_sufficient=False),
        ui_bindings=[dict(callee='00527650',actual_return='00451460 AX ->owner+1C8544',
            items=[dict(item=2,ProgramMsg_id=62,text_global='009F1058'),dict(item=3,ProgramMsg_id=63,text_global='009F105C')]),
            dict(callee='00527D80',actual_return='00451460 AX ->owner+1C84AE',writes_43088=1,
                items=[dict(item=2,image_indices=[22,23],text_pointer=0),dict(item=3,image_indices=[24,25],text_pointer=0)],
                image_labels_inferred=False)],
        resource=dict(callee='005277A0',primary_WORD_table='008A3638',ids=[62,63],section='ProgramMsg',
            range='id !=0 AND id <= signed resource+B2F64',pointer='resource+B2F60 +4*(id-1)',
            out_of_range_native_pointer=None,decoded_sha256=sha(plain),packed_sha256=sha(packed)),
        native_server_exit_reasons_recovered=False,actual_reply_rule_save_owner_configured=False,
        source_gameplay_handler_connected=False,formal_application_hosted=False,complete_route=False,
        variants_complete=False,request_reply_pairing=None)
    dump('native/exit-ui-binding-and-flag-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='no progress: status-only reread; revalidated104-file snapshot then actual source/native increment',
        native_sha256=SHA,native_functions=functions,native_primary_metadata_envelope_bytes=sum(f['metadata_envelope_bytes'] for f in functions),
        native_primary_operands_qualified=len(qualified),native_programmsg_loader_range_bytes=len(loader),
        cn_world_exit_lifecycle_readonly_formats_added=2,native_flag_writer_cases_qualified=3,
        native_ui_handle_binding_relations_added=2,native_programmsg_exit_label_source_relations_added=1,
        packet_report_counts_now_from_current_ledger=True,historical_ledger_catalog_pointer_rewritten=False,
        actual_reply_rule_save_owner_configured=False,formal_application_hosted=False,new_packet_values=0,
        new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        levels_changed=False,fonts_changed=False,build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,
        Windows_API_run=False,native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_world_exit_ui_binding_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN WORLD A0/A3 exact3B ->same8AC owner ->post-tail command and native ProgramMsg/UI binding',
        version_scope='pinned-cn-original-world-connection1-readonly-consumer-and-UI-lineage',
        status='Two exact readonly formats and flag/UI/resource relations; actual server sender/rules/save/replay/Application remain open',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual A0/A3 issuer/payload/conditions and00534640/full lifecycle effects; UI lifetime/early WORD/state6; real03/save/replay authority; actual login/world providers and all TW/CN/PC/web/gameplay/numeric64/stack99/full denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN world exit UI binding and A0/A3 source ('+ROUND+')\n\n'
            'Qualified same world+89B26C ECX for initialization0, S2C A3 write1 and condition-gated A0 clear0 after00534640. '
            'BOTH A0/A3 full logical records are3 bytes; new readonly reader preserves all payload bytes. '
            'UI handles are actual returned AX; same main+464 ProgramMsg resource binds IDs62/63 only to confirmation item2/3, other image-only labels remain unknown. '
            'Reporter counts now derive current ledger tuples with optional current-catalog source snapshot binding; historical catalog114 pointer/reports retained. '
            'Readonly formats2, flag writer cases3/UI bindings2/ProgramMsg relation1; new opcode/phase/owner/full routes0. '
            'Sender/payload/rule/save/replay/Application and full TW/CN/PC/web/gameplay/numeric64/stack99 scope remain open; whole totals/percent null. '
            'No build/test/native/C++/API/DB/deploy. See research/cn-world-exit-ui-binding-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes',
        'cn_world_exit_lifecycle_readonly_formats_added','native_flag_writer_cases_qualified','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
