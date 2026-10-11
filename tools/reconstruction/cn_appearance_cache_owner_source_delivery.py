"""File-only native cache owner initialization/binding source delivery."""
import csv,hashlib,json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT,PIN
NAME='cn-appearance-cache-owner-source-01'
ROUND='20261007-cn-appearance-cache-owner-source'
SOURCES=('src/cn/assets/CnAppearanceCacheSnapshot.h','src/cn/assets/CnAppearanceCacheSnapshot.cpp',
    'src/cn/assets/CnRomCommandReferences.h','src/cn/assets/CnRomCommandReferences.cpp',
    'tools/reconstruction/cn_appearance_cache_owner_source_delivery.py',
    'docs/research/cn-appearance-cache-owner-source-20261007.md')
FUNCTIONS=('004826c0','00482770','004827e0','00482840','00422fd0','004173c0','004187c0',
    '00415d40','00415fb0','00483820','004838a0','00482f40','00483040','004830c0','004833e0',
    '0048caa0','00492e70','0040bee0','00423c80','004888a0','00488290','0041aef0','0041af00',
    '00416140','004161a0')
REMAINING=[
    'Actual configured scene/resource/bank owner, complete original preload/init/failure/allocator/slot/row-cache history and current asset lifetime remain open; snapshots/read-only switch operands are not native allocation/load/publication.',
    'Authoritative equipment/full6F issuer/observer policies and Application/native PC/web hosting remain missing.',
    'Auxiliary/DrvDoll bounds/alternate/CF/later appearance, complete ACT/image/palette/FLC and all gameplay/numeric/replay/recovery/denominator work remain open; levels unchanged.',
]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh source receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'));old={};preserved=[]
    for row in before:
        data=(out/row['snapshot']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before pin differs')
        old[row['path']]=data
        if row['path'] not in SOURCES and row['path'] not in ('docs/PACKET_CONNECTION_GOAL_20261006.md',
            'artifacts/integration/packet-connections-20261006/packet-route-ledger.json'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Frozen context changed: '+row['path'])
            preserved.append(row)
    path='src/cn/assets/CnRomCommandReferences.cpp';signature=b'std::optional<CnRomCommandProjection> CnRomCommandReferences::project(const CnRomAsset& source,const CnRomBankSourceView& bank) {'
    def body(data):
        at=data.index(signature);return data[at:]
    if body(old[path])!=body((ROOT/path).read_bytes()):raise RuntimeError('Previous projection body changed')
    dump('preserved-no-cache-projection-body.json',{'sha256':sha(body(old[path])),'exact_bytes_retained':True,'native_executed':False})
    prior=base/'cn-appearance-bank-source-binding-01';manifest=(prior/'manifest.json').read_bytes()
    if sha(manifest)!='f58a9b925796eda3271498a4a4d9cdbd39a8ac4680a1153cf7f3b7844f88f13d':raise RuntimeError('Prior seal differs')
    value=json.loads(manifest)
    if not value['sealed']:raise RuntimeError('Prior round unsealed')
    save('retained-prior/manifest.json',manifest);pins={r['path']:r['sha256'] for r in value['files']}
    for rel in ('findings.json','round-report.json','resources/ACTINDEX-command10-file-observations.json'):
        data=(prior/rel).read_bytes()
        if sha(data)!=pins[rel]:raise RuntimeError('Prior source differs')
        save('retained-prior/'+Path(rel).name,data)
    native=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');raw=native.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('CN primary differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);md=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    metadata=(recovery/'functions.tsv').read_bytes();rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8').splitlines(),delimiter='\t')}
    ranges=[];call_edges=[]
    for address in FUNCTIONS:
        row=rows[address];path=(recovery/row['file']).resolve();size=int(row['bytes'])
        if not path.is_relative_to(recovery.resolve()):raise RuntimeError('Recovery outside root')
        code=view.read(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size);source=path.read_bytes();instructions=list(md.disasm(code,int(address,16)))
        listing=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in instructions)+'\n').encode()
        for extension,data in (('.bin',code),('.asm',listing),('.c',source)):save('native/'+address+extension,data)
        for i in instructions:
            if i.mnemonic=='call' and i.op_str.startswith('0x'):
                target=f'{int(i.op_str,16):08x}'
                if target in FUNCTIONS:call_edges.append({'root':address,'site':f'{i.address:08x}','target':target,'raw_hex':i.bytes.hex()})
        ranges.append({'address':address,'bytes':size,'native_sha256':sha(code),'metadata':row,
            'recovery_source':str(path),'recovery_source_sha256':sha(source),'decoded_instruction_bytes':sum(i.size for i in instructions),
            'native_executed':False,'all_exceptional_or_indirect_paths_closed':False})
    pe.close();dump('native/function-envelopes.json',{'primary':str(native),'sha256':PIN,'metadata_sha256':sha(metadata),'ranges':ranges})
    dump('native/scoped-direct-call-edges.json',call_edges)
    dump('native/owner-layout-source.json',{'cache_owner_constructor':'004826c0','context_offset':0x124f0,
        'contexts':2,'context_stride':0xb0368,'constructor_memset_bytes':0x1606d0,'active_context_offset':0x172bc0,
        'constructor_active_context_dword':0xffffffff,'context_fields':{'native_bank_dword':0,'current_cursor_word':4,
            'base_cursor_word':6,'family_word':8,'map_word':10},'ROM_bank_constructor':'004173c0',
        'ROM_metadata_reset':'004187c0','ROM_slot_count':512,'ROM_slot_stride':0x1514,
        'ROM_fields_actually_initialized':{'identity_dword':{'offset':0,'value':0xffffffff},'dword4':{'offset':4,'value':0},
            'image_count':{'offset':0x88,'value':0},'action_count':{'offset':0x108c,'value':0},'dword1490':{'offset':0x1490,'value':0}},
        'all_ROM_slot_bytes_cleared':False,'cache_switch_resets_ROM_identities':False,
        'fixed_preload':'00483820','base_checkpoint':'004838a0','full_init_root_envelope':'0048caa0',
        'scene_load_root_envelope':'00492e70','bank_or_cache_or_snapshot_instantiated':False})
    facts={'round':ROUND,'cn_native_sha256_context':PIN,
        'previous_goal_turn_classification':'progress: actual ACTINDEX/reference metadata and same-scene source witness; catalog105 and145-file source sealed',
        'cn_actual_cache_owner_snapshot_readers_added':1,'cn_read_only_cache_switch_sources_added':1,
        'cn_existing_command10_cache_source_bindings_strengthened':1,'native_function_envelopes_read':len(ranges),
        'native_function_bytes_read':sum(r['bytes'] for r in ranges),'scoped_direct_call_edges_read':len(call_edges),
        'actual_native_bank_provider_configured':False,'actual_native_owner_bytes_acquired':False,'snapshot_or_projection_executed':False,
        'new_packet_values':0,'new_native_phase_source_bindings':0,'new_source_owner_chains':0,'new_tw_source_owner_chains':0,
        'new_complete_bidirectional_routes':0,'whole_game_route_total':None,'whole_game_completed_routes':None,
        'whole_game_completion_percent':None,'formal_application_hosted':False,'levels_changed':False,
        'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,'preserved_contexts':preserved,'remaining':REMAINING}
    dump('findings.json',facts)
    for rel in SOURCES:save('source/'+Path(rel).name,(ROOT/rel).read_bytes())
    dump('source/source-origins.json',[{'path':rel,'snapshot':Path(rel).name,'sha256':sha((ROOT/rel).read_bytes())} for rel in SOURCES])
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_appearance_cache_owner_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append({'name':'CN actual two-cache owner initialization/current bank source ->readonly command10 source projection',
        'version_scope':'cn-native-cache-owner-layout-source-only','status':'Explicit actual owner bytes/current lifetime reader +original switch operands +selected bank/revision binding; actual providers/preload/failure/ACT/equipment/issuer/hosting remain open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_owner_chains_added':0,
        'tw_source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Connect actual configured scene/resource/bank owner and retained preload/init/failure/allocator/slot/row-cache history with same owner/current generation; equipment/full6F issuer/observer/auxiliary/ACT/Application hosting and all gameplay/numeric/denominator remain open. Levels unchanged, PHASE1 source-only.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## CN actual cache-owner initialization/current-bank source ('+ROUND+')\n\n'
        'Recovered004826C0 constructor: actual two records cleared, active=-1;004173C0/004187C0 initialize only specified512-ROM fields, not allbytes. Fixed00483820 preload independently advances both banks before004838A0 saved bases. Cache hit/switch/checkpoint and area row-cache invalidation retain differing semantics. New actual owner-layout source reader1/read-only switch operands1/existing command10 selected-bank binding strengthened1; no process memory acquisition or source reader execution. Real owner/current/provider/equipment/full6F/observer/auxiliary/ACT/hosting and full gameplay/denominator open. New opcode/phase/owner/full0, levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-appearance-cache-owner-source-20261007.md.\n')
    print(json.dumps({k:facts[k] for k in ('round','native_function_envelopes_read','native_function_bytes_read','scoped_direct_call_edges_read','new_complete_bidirectional_routes')}))
if __name__=='__main__':main()
