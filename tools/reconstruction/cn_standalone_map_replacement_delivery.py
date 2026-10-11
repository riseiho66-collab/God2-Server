"""Seal static flag0/standalone MAP decoder and resource/cache replacement."""
import json
import re
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_OP_IMM
from .cn_outdoor_cache_lifecycle_delivery import SERVER,CN,PIN,ROOT,sha,dump

NAME='cn-standalone-map-replacement-01'
ROUND='20261006-cn-standalone-map-replacement'
PREVIOUS='cn-camera-map-resource-owner-01'
CACHE='cn-outdoor-cache-lifecycle-01'
INITIAL='cn-initial-scene-provider-01'
MODIFIED=['src/cn/assets/CnSceneAssets.h','src/cn/assets/CnSceneAssets.cpp',
    'src/cn/assets/CnOutdoorSceneResources.h','src/cn/assets/CnOutdoorSceneResources.cpp',
    'src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp']
SOURCES=MODIFIED+['src/cn/assets/CnStandaloneMapAsset.h','src/cn/assets/CnStandaloneMapAsset.cpp',
    'src/cn/world/CnMapPassability.h','src/cn/world/CnMapPassability.cpp',
    'src/cn/assets/CnResourceBytes.h','src/cn/assets/CnResourceBytes.cpp',
    'src/cn/assets/CnAssetTokens.h','docs/research/cn-standalone-map-replacement-20261006.md']
FUNCTIONS=[('00470c90',6),('00462980',6),('004642a0',6),('0045edf0',5),
    ('0045e7f0',5),('004657e0',6),('00466ee0',6),('0076c3bf',71),('0046d460',6),('00461fd0',6)]
STRINGS=[('map',0x7f0994),('v10',0x7f00a0),('v11',0x7f0660),('size',0x7f09a8),
    ('tilenum',0x7f09b0),('spritenum',0x7f09b8),('tileidx',0x7f09c4),('pass',0x7f09cc),
    ('linkidx',0x7f09d4),('palnum',0x7f09dc),('integer-format',0x7ed65c),
    ('mdl-extension',0x7f0650),('mbd-extension',0x7f0658)]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve existing delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    pending=[];manifests={};native_prior={}
    for name in [PREVIOUS,CACHE,INITIAL]:
        p=ROOT/name/'integration-manifest.json';raw=p.read_bytes()
        if sha(raw)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Historical manifest changed')
        manifests[name]=json.loads(raw)
        for row in manifests[name]['native_spans']:
            old=native_prior.get(row['address'])
            if old and old['native_sha256']!=row['native_sha256']:raise ValueError('Historical native conflict')
            native_prior[row['address']]=row
        pending.append(('prior-manifests/'+name+'.json',raw,p))
    changes=[]
    for rel in MODIFIED:
        name=CACHE if rel.endswith('CnSceneAssets.h') else PREVIOUS
        p=ROOT/name/rel;raw=p.read_bytes()
        old={r['path']:r for r in manifests[name]['snapshots']}[rel]
        if sha(raw)!=old['sha256']:raise ValueError('Historical source changed')
        pending.append(('prior-sources/'+rel,raw,p))
        changes.append({'path':rel,'previous_artifact':name,'before_sha256':sha(raw),
            'after_sha256':sha((SERVER/rel).read_bytes()),'old_snapshot_preserved':True})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Native CN executable changed')
    pe=pefile.PE(data=raw,fast_load=True);decoder=Cs(CS_ARCH_X86,CS_MODE_32);decoder.detail=True
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
    spans=[];calls=[];targets={int(a,16) for a,_ in FUNCTIONS}
    for address,part in FUNCTIONS:
        p=recovery/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=p.read_bytes()
        m=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not m or int(m.group(1),16)!=int(address,16):raise ValueError('Native extent missing')
        size=int(m.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:raise ValueError('Incomplete native bytes')
        old=native_prior.get(address)
        if old and (sha(code)!=old['native_sha256'] or old['source_sha256'] not in
            {sha(source),sha(source.replace(b'\r\n',b'\n'))}):raise ValueError('Native historical baseline changed')
        ins=list(decoder.disasm(code,int(address,16)))
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for i in ins:
            if i.mnemonic=='call' and len(i.operands)==1 and i.operands[0].type==CS_OP_IMM and i.operands[0].imm in targets:
                calls.append({'caller':address,'site':f'{i.address:08x}','target':f'{i.operands[0].imm:08x}'})
        for ext,data,origin in [('.c',source,p),('.asm',asm,'pinned PE disassembly'),('.bin',code,exe)]:
            pending.append(('native/functions/'+address+ext,data,origin))
        spans.append({'address':address,'bytes':size,'source_original':str(p),'source_sha256':sha(source),
            'native_sha256':sha(code),'previous_span_preserved':bool(old),'decoded_bytes':sum(i.size for i in ins)})
    constants=[]
    for name,address in STRINGS:
        data=pe.get_data(address-pe.OPTIONAL_HEADER.ImageBase,40).split(b'\0',1)[0]+b'\0'
        pending.append(('native/constants/'+name+'.bin',data,exe))
        constants.append({'name':name,'address':f'{address:08x}','bytes':len(data),'sha256':sha(data),'value':data[:-1].decode('ascii')})
    gaps=['Same-resource standalone cache rotation and valid-byte reuse remain unconnected; no fake reread reuse.',
        'Partial/null/failed native-success slots, other MAP versions/dimensions and nonalphabet/high-byte axes remain open.',
        'Runtime objects/frames/render reset00473A20/0046C280 and actual actor camera/scene revision/WorldOwner remain missing.',
        'Common position/cache transaction, movement timing/pending/reset/full5D, TW/CN publication and Application/listeners remain open.',
        'All remaining gameplay and the full directional/phase/state/variant/indirect/deferred denominator remain open.']
    out.mkdir(parents=True);snapshots=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(original)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'source-adaptation-receipt.json',changes)
    dump(out/'native-flag0-map-relation.json',{'client_sha256':PIN,'functions':spans,'calls':calls,'constants':constants,
        'replacement_load_flag_sites':['00470f27 push0 ->00470f37 call00462980','00471030 push0 ->00471046 call00462980'],
        'mbd_skip':'00463440 cmp[ebp+10],0 ->0046344e je00463e7b after MDL',
        'map_reader':'0045e7f0 ->004657e0 plain fopen r; MAP v1.0/v1.1',
        'initialization':'00466ee0 ->0076c3bf ->__calloc_base',
        'cell_layout':{'word0':'TileIdx','word2':'LinkIdx','word4':'TileNum','byte6_low5':'PalNum(v1.1)',
            'byte7_low4':'SpriteNum','byte7_bits4_5':'Pass low2','byte7_bit6':'duplicate Pass low bit'},
        'qualified_subset':'different-MDT flag0 /ASCII axes/actual21x21/full9/declared MDL frames',
        'native_partial_success_is_not_full9_success':True,'new_opcode_values':0})
    manifest={'kind':'different-MDT flag0 ->actual MDT/MDL/modelROM/plainMAP full9 ->private resource/cache commit ->conditional camera result',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,
        'native_spans':spans,'native_function_spans':len(spans),'native_constant_spans':len(constants),
        'new_source_files':2,'modified_cpp_files':6,'source_owner_chains_added':1,'new_phase_opcode_bindings':0,
        'formal_application_hosted':False,'actual_camera_owner_implemented':False,
        'native_different_resource_standalone_full9_connected':True,'same_standalone_reuse_connected':False,
        'initial_flag1_mbd_preserved':True,'new_complete_routes':0,'remaining':gaps,
        'previous_goal_turn_classification':'progress: same-MDT/MBD camera-cache chain sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        **{k:False for k in ['build_run','tests_run','runtime_run','asset_loaders_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN flag0 different-MDT plain MAP full9 resource/cache replacement',
        'status':'已接原生flag0 MDT/MDL/ROM與獨立MAP九格、資源/cache世代提交；後續standalone重用與WorldOwner未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':1,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['same common lease/cache; no new table'],
        'native_form_qualifications':{'replacement_mbd_flag':0,'supported_map_versions':['v1.0','v1.1'],
            'full9_21x21_only':True,'same_standalone_reuse_connected':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=gaps+['Preserve native fonts/conversion/frozen saves; no phase1 build/test/runtime/deploy.']
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_functions':len(spans),
        'native_constants':len(constants),'new_source_files':2,'modified_cpp_files':6,
        'new_phase_bindings':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
