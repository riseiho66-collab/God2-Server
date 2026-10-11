"""Seal primary pool-owner/lifetime source relations, no native execution/tests."""
import csv
import json
import struct
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN,RECOVERY
from .cn_shared_movement_owner_delivery import sha,dump
from .cn_summary_world_lineage_delivery import trace

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-world-monster-lifecycle-01'
ROUND='20261007-cn-world-monster-lifecycle'
NEW=['src/cn/protocol/CnWorldMonsterLifecycle.h','src/cn/world/SharedMonsterPublication.h',
    'src/cn/world/SharedMonsterPublication.cpp']
CONTEXT=['src/cn/protocol/CnWorldMonster.h','src/cn/assets/CnCurrentEnemyDisplayCatalog.h',
    'src/cn/assets/CnCurrentEnemyDisplayRows.inc','src/cn/world/CnWorldMonsterDisplay.h',
    'src/cn/world/CnWorldMonsterDisplay.cpp','src/cn/net/SharedCredentialConnection.h',
    'src/cn/net/SharedCredentialConnection.cpp','src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp','src/core/Application.cpp']
SOURCES=NEW+CONTEXT+['docs/research/cn-world-monster-lifecycle-20261007.md',
    'tools/reconstruction/cn_world_monster_lifecycle_delivery.py']
FUNCTIONS=['004fa750','004fac90','004fbc00','004fb290','004fa820','004821a0','00535400',
    '0048da20','0048e3e0','004f1450','0052fd40']
BRANCHES=[(0x73,0x490bb7,0x490bf2),(0x74,0x4919df,0x4919f4),
    (0x75,0x491dab,0x491dc0),(0x77,0x490db6,0x490df5),(0x78,0x4919cb,0x4919df)]

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog46-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes())
    for rel in CONTEXT:
        b=(out/'prior-sources'/rel).read_bytes()
        if b!=(SERVER/rel).read_bytes() or sha(b)!=before[rel]['sha256']:raise ValueError('Context changed '+rel)
        if rel in known and sha(b)!=known[rel]['sha256']:raise ValueError('Catalog context differs '+rel)
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged')
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Native PE pin differs')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    save('native/selected-function-metadata.json',(json.dumps({'original_sha256':sha(metadata),
        'rows':[rows[a] for a in FUNCTIONS]},indent=2)+'\n').encode(),RECOVERY/'functions.tsv')
    def read(va,size):
        b=pe.get_data(va-base,size)
        if len(b)!=size:raise ValueError('Short native span')
        return b
    spans=[]
    for a in FUNCTIONS:
        r=rows[a];p=Path(r['file']);p=p if p.is_absolute() else RECOVERY/p
        source=p.read_bytes();lo=int(a,16);size=int(r['bytes']);code=read(lo,size)
        cfg,asm,ins=trace(md,code,lo,lo+size,{})
        save('native/'+a+'.c',source,p);save('native/'+a+'.bin',code,exe)
        save('native/'+a+'-cfg.asm',asm,'static primary CFG, not execution')
        save('native/'+a+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'bounded CFG; calls not followed, open edges retained')
        spans.append({'va':a,'reported_bytes':size,'code_sha256':sha(code),'source_sha256':sha(source),
            'cfg_instructions':cfg['decoded_cfg_instructions'],'cfg_bytes':cfg['decoded_unique_cfg_bytes'],
            'open_edges':cfg['open_edges'],'not_whole_program_closure':True})
    primary_branches=[]
    for op,lo,hi in BRANCHES:
        table=read(0x4929d8+op*4,4)
        if struct.unpack('<I',table)[0]!=lo:raise ValueError('Primary world switch differs')
        code=read(lo,hi-lo);cfg,asm,ins=trace(md,code,lo,hi,{})
        if any(e['address'] not in ['00490aab','00490ab1'] for e in cfg['open_edges']):
            raise ValueError('Unexpected receive loop frontier')
        prefix=f'native/world{op:02X}'
        save(prefix+'-table-entry.bin',table,exe);save(prefix+'-primary.bin',code,exe)
        save(prefix+'-cfg.asm',asm,'static primary branch decoding')
        save(prefix+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'outside edges are actual WORLD receive loop')
        primary_branches.append({'opcode':op,'va':f'{lo:08x}','end_exclusive':f'{hi:08x}',
            'cfg_instructions':cfg['decoded_cfg_instructions'],'cfg_bytes':cfg['decoded_unique_cfg_bytes'],
            'open_edges':cfg['open_edges'],'source_binding_integrated':op in [0x74,0x78]})
    phase_path=CN/'artifacts/native/20261006-cn-route-denominator-03/s2c-phase-opcodes.json'
    selected=[r for r in json.loads(phase_path.read_bytes()) if r['phase']=='world-connection-1' and r['opcode'] in [0x73,0x74,0x75,0x77,0x78]]
    if len(selected)!=5:raise ValueError('Phase evidence differs')
    save('native/selected-phase-opcodes.json',(json.dumps(selected,indent=2)+'\n').encode(),phase_path)
    for r in selected:
        p=CN/r['branch_source'];save(f"native/world{r['opcode']:02X}-branch.c.txt",p.read_bytes(),p)
    previous='cn-world-monster-display-contract-01';expected=ledger['cn_account_admission_evidence'][previous]['artifact_sha256']
    for rel in ['native-monster-display-contract.json','native/world71-primary.bin','native/world71-cfg.asm',
        'native/world71-cfg.json','integration-manifest.json']:
        p=ROOT/previous/rel;b=p.read_bytes()
        if sha(b)!=expected[rel]:raise ValueError('Previous immutable evidence differs')
        save('prior-native/'+rel,b,p)
    # Real static string data; no server-created/transliterated native labels.
    table=read(0x89e190,7*4);save('native/level-band-table.bin',table,exe)
    band_rows=[]
    for slot,va in enumerate(struct.unpack('<7I',table)):
        b=read(va,64);end=b.find(b'\0')
        if end<0:raise ValueError('Unbounded band label')
        b=b[:end+1];save(f'native/level-band-{slot}.bin',b,exe)
        band_rows.append({'slot':slot,'va':f'{va:08x}','native_nul_terminated_hex':b.hex()})
    for va,size in [(0x7f4810,7),(0x7f4818,6),(0x7f4820,6)]:
        save(f'native/level-format-{va:08x}.bin',read(va,size),exe)
    contract={'client_sha256':PIN,'same_world_owner':['71','74','78'],'native_same_owner_offset':'1499FA0',
        'different_world_owner':['75','77 bit3'],'native_other_owner_offset':'147C720',
        'player73_then_monster_transformed_identity':{'player_owner':'1464C58','monster_owner':'1499FA0',
            'transform':'DWORD1 &7FFF |8000','whole73_monster_only':False},
        'remove74':{'logical_size':5,'identity':'WORD1 zeroextended','opaque_retained':'bytes3,4'},
        'level78':{'logical_size':5,'identity':'WORD1','supplied_level':'WORD3',
            'numeric':'0..30','band':'31..99; (level-30)/10','special':'100..65535 Lv:???',
            'stored_byte':'entry+17B lowBYTE; not full supplied WORD','band_rows':band_rows,
            'combat_level_or_formula_proven':False},
        'slot_cleanup':{'function':'004FAC90','identity':'FFFFFFFF','type_at1D4':0,'byte17A':0,'dword17C':0,
            'level_byte17B_cleared_here':False,'whole_slot_zeroed':False},
        'whole_pool_reset':'004FBC00 calls004FAC90 for each occupied slot; call presence not actual runtime event',
        '77_monster_branch':'byte5&8 ->other pool +147C720; byte3 resource selector, byte5 low3 presentation, not movement',
        'old_token_after74_or_exact_recipient_reset':'invalid; native instance reuse requires new private binding',
        'application_hosted':False,'real_monster_authority_supplied':False,'native_execution_observed':False}
    save('native-monster-lifecycle-contract.json',(json.dumps(contract,indent=2)+'\n').encode(),'primary scoped owner/lifetime relations')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),
                'original':'captured before source additions'})
    gaps=['Actual common monster spawn/visibility/stats/retirement/storage WorldOwner, native resource/pool allocation/reset suppliers and Application hosting remain missing.',
        'Real monster movement and C2S click/encounter ->battle entry/common identity remain unconnected;75/77 are separate pool consumers and not published through71 tokens.',
        'TW/CN shared monster presentation, double attacks/defenses, four attributes, five elements, HP/MP/full carried skill lists need separate exact sources.',
        'Remaining login/world/gameplay suppliers and whole-game directional/state/variant denominator/full routes remain incomplete.']
    manifest={'kind':'common monster qualified source ->CN71 expected private incarnation ->same-pool78 level/74 retirement ->actual ready recipient transport',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':[],'snapshots':snapshots,
        'native_spans':spans,'primary_branches':primary_branches,'native_contract':contract,'new_cpp_files':3,
        'source_owner_chains_added':1,'new_phase_opcode_bindings':2,'new_opcode_values':0,'new_complete_routes':0,
        'formal_application_hosted':False,'actual_monster_authority_supplied':False,
        'expected_send_submission_not_native_observation':True,
        'previous_goal_turn_classification':'progress: catalog46 native71/current resource contracts and sources sealed; subsequent automatic continuation honored explicit user pause',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','native_api_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','frozen_tw_chat_modified','resource_decode_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN common monster71 incarnation publication with same native pool78/74 lifecycle',
        'version_scope':'cn','status':'共用怪物來源/實際ready收件者/私有實例世代/71→78或74條件式來源；正式authority/資源/掛載仍缺',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{'world-connection-1':[0x74,0x78]},
        'source_paths':SOURCES,'source_owner_chains_added':1,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'storage_writes':'none; current and retirement revisions mandatory, no monster stat or identity defaults',
        'shared_storage':['common monster owner stays shared; per-recipient low16 instance is adapter identity; no tables created'],
        'native_form_qualifications':{'same71_pool_opcodes':['74','78'],'different_pool_opcodes':['75','77 bit3'],
            'recipient_generation_qualified':True,'actual_monster_authority_supplied':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['world_monster_lifecycle']={'root':out.relative_to(SERVER).as_posix(),
        'same_owner_offset':'1499FA0','integrated_world_s2c':[0x74,0x78],'other_owner_offset':'147C720',
        'source_owner_chains':1,'actual_monster_authority_supplied':False,'complete_gameplay_routes':0}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_phase_bindings':2,
        'new_partial_owner_chains':1,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
