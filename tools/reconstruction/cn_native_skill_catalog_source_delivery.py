"""Pinned CN skill loader/file/identity evidence and actual source handoff.

Static files/PE/entry-rooted disassembly only; no native/API/C++/DB/tests.
"""
import difflib
import hashlib
import json
import re
import capstone
import pefile
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-native-skill-catalog-source-01'
ROUND='20261008-cn-native-skill-catalog-source'
NATIVE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
RESOURCE=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/Data2/Fight/Spg/cbspec2.bin')
NATIVE_SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
RESOURCE_SHA='857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004'
SOURCES=['src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp',
 'docs/research/cn-native-skill-catalog-source-20261008.md',
 'tools/reconstruction/cn_native_skill_catalog_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual common subject/skill identity mapping/eligibility/cost/Lua/rule/transaction/save/persistent replay/Application remain unconfigured.',
 'Native84 caller and all preborn initial issuer/timing variants relative1C remain open.',
 'Raw CN definition identity/bytes do not prove learned skills, enemy stats, authoritative MP charge or common keys; TW evidence stays TW.',
 'Full TW/CN/PC/web/WSS/common login/world/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required')
    def save(rel,raw):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=122:raise RuntimeError('Expected122 retained input files')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    report_paths={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ('json','md')}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if row['path'] not in set(SOURCES)|set(books)|report_paths:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(out/'retained-prior/cn-preborn-selected-subject-source-01/manifest.json').read_bytes()
    if sha(prior)!='c907ee00530ce6d93cc121e3b99b2495a3466301499420de25c05a1cbc6321af' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=NATIVE.read_bytes()
    if sha(raw)!=NATIVE_SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    functions=[];instructions={};cfgs={}
    for address in ('00543560','00561BB0','0053FF40','00556700'):
        paths=list(RECOVERY.glob('part_*/'+address.lower()+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Individual native source not unique')
        c=paths[0].read_bytes();size=int(re.search(rb'Size: (\d+) bytes',c).group(1));va=int(address,16)
        code=view.read(va-ib,size);cfg,decoded=local_cfg(md,code,va,{})
        instructions.update(decoded);cfgs[address]=cfg
        save('native/functions/'+address+'.c',c);save('native/functions/'+address+'.bin',code)
        save('native/entry-cfg/'+address+'.asm',('\n'.join(f'{x.address:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for _,x in sorted(decoded.items()))+'\n').encode())
        dump('native/entry-cfg/'+address+'.json',cfg)
        functions.append(dict(va=address,metadata_bytes=size,sha256=sha(code),
            complete_local_normal_call_return_cfg=not cfg['frontier'],helper_exception_runtime_claimed=False))
    if cfgs['00561BB0']['frontier'] or cfgs['00561BB0']['ret_sites']!=['00561c13','00561c3a']:
        raise RuntimeError('Loader local normal CFG differs')
    expected={
      0x54358e:('mov','esi, ecx'),0x543669:('mov','eax, esi'),0x54366f:('add','eax, 0x149df8'),
      0x543674:('mov','ecx, eax'),0x543676:('mov','dword ptr [ebp - 0x330], eax'),0x54367c:('call','0x556700'),
      0x5437eb:('push','0x7f6474'),0x5437f0:('call','0x53ff40'),0x5437f5:('push','eax'),
      0x5437fc:('push','0x7ec304'),0x543802:('call','0x415310'),
      0x543807:('mov','ecx, dword ptr [ebp - 0x330]'),0x543816:('push','eax'),0x543817:('call','0x561bb0'),
      0x561bb5:('push','0x7ed3d8'),0x561bba:('push','dword ptr [ebp + 8]'),0x561bbd:('mov','edi, ecx'),
      0x561bbf:('call','0x76d12e'),0x561bd3:('push','4'),0x561bd6:('call','0x76d4ee'),
      0x561be0:('push','0x7f76e4'),0x561be6:('call','0x77cb47'),
      0x561c18:('lea','eax, [edi + 0x888444]'),0x561c1e:('push','0x1b810'),0x561c24:('call','0x76d4ee')}
    qualified=[]
    for site,pair in expected.items():
        ins=instructions.get(site)
        if not ins or (ins.mnemonic,ins.op_str)!=pair:raise RuntimeError(f'Primary operand differs at{site:08x}')
        qualified.append(dict(site=f'{site:08x}',bytes=ins.bytes.hex(),mnemonic=ins.mnemonic,operand=ins.op_str))
    dump('native/qualified-primary-operands.json',qualified)
    strings=[]
    for va,size,label in [(0x7f6474,40,'skill-resource-path'),(0x7f76e4,8,'skill-header'),
                           (0x7ed3d8,8,'fopen-mode'),(0x7ec304,8,'formatter'),
                           (0x7ed048,12,'relative-resource-format'),(0x7ef868,12,'leading-slash-format')]:
        data=view.read(va-ib,size);save(f'native/literals/{va:08X}.bin',data)
        strings.append(dict(va=f'{va:08x}',label=label,hex=data.hex(),nul_terminated=data.split(b'\0')[0].decode('ascii')))
    dump('native/literals/strings.json',strings)
    resource=RESOURCE.read_bytes()
    if len(resource)!=112660 or sha(resource)!=RESOURCE_SHA or resource[:4]!=b'1.03':raise RuntimeError('Pinned CN resource differs')
    save('resource/cbspec2.bin',resource)
    counts=[int.from_bytes(resource[4+k*0x6e04:8+k*0x6e04],'little') for k in range(4)]
    if counts!=[125,130,87,111]:raise RuntimeError('CN declared record counts differ')
    records=[]
    for kind,count in enumerate(counts):
        for ident in range(1,count+1):
            offset=8+kind*0x6e04+(ident-1)*110;data=resource[offset:offset+110]
            if data[0]!=ident or data[1]!=kind:raise RuntimeError('Declared record identity differs')
            records.append(dict(kind=kind,definition_id=ident,file_offset=offset,raw_hex=data.hex(),sha256=sha(data)))
    dump('resource/declared-records.json',records)
    dump('resource/source.json',dict(path=str(RESOURCE),bytes=len(resource),sha256=sha(resource),header='1.03',
        declared_counts=counts,declared_records=len(records),unknown_padding_slots_used=False,skill_entitlement_recovered=False))
    for rel in ['cn-preborn-selected-subject-source-01/native/selected-subject-relations.json',
                'cn-preborn-selected-subject-source-01/source-correction/operational-subject-evidence.json',
                'cn-preborn-selected-subject-source-01/native/functions/00533300.c',
                'cn-preborn-selected-subject-source-01/native/functions/00533300.bin',
                'cn-preborn-selected-subject-source-01/native/functions/00533300.asm']:
        save('retained-inputs/'+rel,(base/rel).read_bytes())
    for rel in ['src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','CMakeLists.txt']:
        save('retained-inputs/'+rel,(ROOT/rel).read_bytes())
    relations=dict(version='cn',native_sha256=NATIVE_SHA,resource_sha256=RESOURCE_SHA,
        resource_path='data2/fight/spg/cbspec2.bin',header='1.03',resource_bytes=112660,payload_bytes=0x1b810,
        loader_va='00561BB0',caller_va='00543560',path_resolver_va='0053FF40',
        actual_loader_this='scene+149DF8 saved[EBP-330] and restoredECX at00543807',
        actual_payload_bank='scene+149DF8+888444=scene+9D223C=object+4504=role+4474',
        record_bytes=110,declared_counts=counts,declared_records=len(records),
        file_record_formula='8+kind*6E04+(ID-1)*6E',native_A2_record_formula='bank+kind*6E04-6A+ID*6E',
        declared_raw_identity_match=True,native_fread_return_values_checked=False,native_eof_checked=False,
        own_source_exact_size_hash_policy=True,binZ_fallback_qualified=False,
        actual_CN_skill_loader_resource_catalog_identity_qualified=True,TW_dataset_promoted_to_CN=False,
        source=dict(supplier='CnNativeSkillCatalog',owned_bytes_hash_qualified=True,current_before_after=True,
          window_source_CN_records_passed_to_actual_apply=True,ordered_duplicate_raw_words_preserved=True,
          post_commit_retained_records_not_retired_window_current=True,native_snapshot_required=False,
          no_client_memory_access=True,no_database_access=True,common_identity_mapping_configured=False,
          rule_save_replay_owner_configured=False,formal_application_hosted=False,complete_route=False))
    dump('native/skill-catalog-source-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='no progress: status answer only; resumed pinned CN skill resource action',
        native_sha256=NATIVE_SHA,resource_sha256=RESOURCE_SHA,native_functions=functions,
        native_primary_metadata_envelope_bytes=sum(row['metadata_bytes'] for row in functions),
        native_local_normal_entry_cfgs_qualified=sum(not q['frontier'] for q in cfgs.values()),
        native_primary_operands_qualified=len(qualified),CN_declared_skill_definition_records=len(records),
        cn_native_skill_catalog_suppliers_added=1,cn_preborn_actual_skill_record_handoffs_strengthened=1,
        actual_CN_skill_loader_catalog_identity_qualified=True,actual_common_skill_mapping_configured=False,
        actual_common_rule_save_replay_owner_configured=False,actual_preborn_initial_issuer_configured=False,
        formal_application_hosted=False,new_packet_values=0,new_native_phase_source_bindings=0,
        new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        native_snapshot_required=False,levels_changed=False,fonts_changed=False,build_run=False,tests_run=False,
        runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,native_execution=False,database_access=False,
        deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_native_skill_catalog_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN actual cbspec2 skill catalog ->existing preborn common-operation owned-record handoff',
      version_scope='pinned-cn-582f2695-cbspec2-857b52e3-definition-source-only',
      status='Actual CN loader/resource/bank/453 definition records and supplier; common mapping/rule/save/replay/issuer/Application unconfigured',
      source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
      tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
      evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual common skill/subject mapping and native rules/save/replay/issuer/Application; native84 caller/timing; full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN actual skill resource ('+ROUND+')\n\n'
          'Primary scene+149DF8 component loader writes+888444, proving same scene+9D223C bank. '
          'Actual CN plain cbspec2.bin112660B/1.03/hash857b52e3 contains453 declared110-byte records in125/130/87/111 groups. '
          'Added owned/hash/current qualified CN supplier and existing preborn raw83 WORD ->owned record ->actual common apply/post-commit handoff; no pointer requirement or TW promotion. '
          'Resource definitions are not common identity/learned eligibility/cost; real rule/save/replay/issuer/Application and all whole-game scope remain open. '
          'No new opcode/phase/partial owner/full route. PHASE1 no build/test/API/native/DB/deploy; later comprehensive validation and recovery release unchanged.\n')
    origins=[]
    for rel in SOURCES+books:
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','native_primary_metadata_envelope_bytes','native_local_normal_entry_cfgs_qualified','CN_declared_skill_definition_records','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
