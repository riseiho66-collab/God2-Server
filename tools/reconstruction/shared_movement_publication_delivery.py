"""Seal static dual-native5E/common-position/send-API source integration."""
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .archive_inputs import ArchivedInputs,SERVER
from .packet_connection_inventory import IMAGE,PIN as TW_PIN,BASE,LENGTH_TABLE,WORLD_TABLE
from .cn_wrapper_route_frontier import CN,PIN as CN_PIN
from .cn_shared_movement_owner_delivery import sha,dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='shared-movement-publication-01'
ROUND='20261007-tw-cn-movement-publication'
MODIFIED=['src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'src/protocol/RecoveredRemoteActor.h']
ADDED=['src/cn/protocol/CnRemoteActorMove.h','src/cn/world/SharedMovementPublication.h',
    'src/cn/world/SharedMovementPublication.cpp']
SOURCES=MODIFIED+ADDED+['src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/net/Session.h','src/cn/net/SharedCredentialConnection.h',
    'docs/research/shared-movement-publication-20261007.md']
FUNCTIONS=[('0048fcc0',8),('00482c30',7),('0051c300',14),('00532800',16),('00530410',16),
    ('00493e70',8),('00488480',8),('00487f70',8)]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve sealed delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    pending=[];changes=[]
    old_root=ROOT/'cn-shared-movement-owner-01'
    old_manifest=(old_root/'integration-manifest.json').read_bytes()
    if sha(old_manifest)!=ledger['cn_account_admission_evidence'][old_root.name]['artifact_sha256']['integration-manifest.json']:
        raise ValueError('Prior movement manifest changed')
    old=json.loads(old_manifest);old_sources={r['path']:r for r in old['snapshots']}
    catalog_manifest=ROOT/'dual-client-route-catalog-19/source-file-manifest.json'
    catalog_raw=catalog_manifest.read_bytes();catalog=json.loads(catalog_raw)
    if sha(catalog_raw)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog manifest changed')
    for rel in MODIFIED[:2]:
        p=old_root/rel;raw=p.read_bytes()
        if sha(raw)!=old_sources[rel]['sha256'] or sha(raw)!=catalog[rel]['sha256']:
            raise ValueError('Prior movement source changed')
        pending.append(('prior-sources/'+rel,raw,p))
        changes.append({'path':rel,'before_sha256':sha(raw),'after_sha256':sha((SERVER/rel).read_bytes()),
            'previous_artifact':old_root.name,'old_snapshot_preserved':True})
    release=SERVER/'artifacts/releases/owned-guild-disband-20261005-01'
    release_raw=(release/'manifest.json').read_bytes();release_manifest=json.loads(release_raw)
    tw_rel=MODIFIED[2];tw_snapshot='source-snapshot/00476-RecoveredRemoteActor.h'
    if release_manifest['source_snapshot_map'][tw_rel]!=tw_snapshot:
        raise ValueError('Historical TW snapshot map differs')
    tw_old=(release/tw_snapshot).read_bytes()
    if sha(tw_old)!=release_manifest['artifacts'][tw_snapshot]:
        raise ValueError('Historical TW source changed')
    # The only TW edit is an additive immutable helper. Match the remainder to
    # the actual historical source; do not silently replace its baseline hash.
    tw_current=(SERVER/tw_rel).read_bytes()
    start=tw_current.index(b'    // Native69A60 and FC movement consumer')
    end=tw_current.index(b'    }',start)+len(b'    }')
    end+=2 if tw_current[end:end+2]==b'\r\n' else 1
    if tw_current[:start]+tw_current[end:]!=tw_old:
        raise ValueError('TW change exceeds additive immutable projection')
    changes.append({'path':tw_rel,'before_sha256':sha(tw_old),'after_sha256':sha(tw_current),
        'previous_artifact':str(release),'old_snapshot_preserved':True,'additive_helper_only':True})
    pending.extend([('prior-sources/'+tw_rel,tw_old,release/tw_snapshot),
        ('prior-manifests/movement.json',old_manifest,old_root/'integration-manifest.json'),
        ('prior-manifests/catalog19-source-files.json',catalog_raw,catalog_manifest),
        ('prior-manifests/tw-release.json',release_raw,release/'manifest.json')])

    exe=CN.parent/'XJZ-CN/God2_opt.exe';cn_raw=exe.read_bytes()
    if sha(cn_raw)!=CN_PIN:raise ValueError('CN native pin changed')
    pe=pefile.PE(data=cn_raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled';native=[]
    for address,part in FUNCTIONS:
        p=recovery/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=p.read_bytes()
        match=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not match or int(match.group(1),16)!=int(address,16):raise ValueError('Native extent missing')
        size=int(match.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:raise ValueError('Native span incomplete')
        ins=list(md.disasm(code,int(address,16)))
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for ext,data,origin in [('.c',source,p),('.bin',code,exe),('.asm',asm,'pinned PE disassembly')]:
            pending.append(('native/cn/functions/'+address+ext,data,origin))
        native.append({'version':'cn','address':address,'bytes':size,'native_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(p),'decoded_bytes':sum(i.size for i in ins)})
    phases_path=CN/'artifacts/native/20261006-cn-route-denominator-03/s2c-phase-opcodes.json'
    phases_raw=phases_path.read_bytes();phases=json.loads(phases_raw)
    branch=next(r for r in phases if r['phase']=='world-connection-1' and r['opcode']==0x5e)
    if branch['length']!=17 or branch['function']!='0x0048fcc0':raise ValueError('CN5E branch changed')
    # Pin against the already sealed catalog19 copy, not just a current upstream file.
    catalog19_manifest=json.loads((ROOT/'dual-client-route-catalog-19/input-manifest.json').read_text(encoding='utf8'))
    phase_input=next(r for r in catalog19_manifest if r['input']=='cn-s2c-phases')
    if sha(phases_raw)!=phase_input['sha256']:raise ValueError('Prior CN phase index changed')
    pending.append(('native/cn/phase-index.json',phases_raw,phases_path))
    branch_path=CN/branch['branch_source'];branch_raw=branch_path.read_bytes()
    old_branch=ROOT/'dual-client-route-catalog-19/native-cn-branches'/Path(branch['branch_source']).name
    if old_branch.read_bytes()!=branch_raw:raise ValueError('Prior CN branch snapshot changed')
    pending.append(('native/cn/world-5e-branch.c.txt',branch_raw,branch_path))
    cn_slice=pe.get_data(0x490bf2-pe.OPTIONAL_HEADER.ImageBase,0x490d00-0x490bf2)
    instructions=list(md.disasm(cn_slice,0x490bf2))
    if sum(i.size for i in instructions)!=len(cn_slice):raise ValueError('CN branch instruction boundary differs')
    pending.append(('native/cn/world-5e.bin',cn_slice,exe))
    pending.append(('native/cn/world-5e.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
        for i in instructions)+'\n').encode(),'pinned CN disassembly'))
    reader=ArchivedInputs()
    try:tw_raw=reader.read(IMAGE)
    finally:reader.close()
    if sha(tw_raw)!=TW_PIN:raise ValueError('TW mapped image pin changed')
    leaf=struct.unpack_from('<I',tw_raw,LENGTH_TABLE+4*0x5e)[0]-BASE
    target=struct.unpack_from('<I',tw_raw,WORLD_TABLE+4*0x5e)[0]-BASE
    if target!=0x69a60 or tw_raw[leaf:leaf+6]!=bytes.fromhex('b80d000000c3'):
        raise ValueError('TW native5E length/dispatch differs')
    tw_spans=[]
    for label,rva,size in [('length-leaf',leaf,6),('world-dispatch',target,0x69b35-target),
            ('actor-enqueue-state',0xfb520,0xfb689-0xfb520)]:
        code=tw_raw[rva:rva+size];ins=list(md.disasm(code,BASE+rva))
        if len(code)!=size or sum(i.size for i in ins)!=size:raise ValueError('TW slice extent differs')
        pending.append(('native/tw/'+label+'.bin',code,IMAGE))
        pending.append(('native/tw/'+label+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
            for i in ins)+'\n').encode(),'pinned TW mapped image disassembly'))
        tw_spans.append({'version':'tw','name':label,'rva':f'{rva:08x}','bytes':size,'native_sha256':sha(code)})
    gaps=['Actual native WorldOwner/visibility/spawn/complete5E templates, movement timing/pending/reset/full5D and cache/position atomic lifecycle remain required.',
        'TW enrollment in common presence, TW-origin movement and Application/listeners/login/full bootstrap remain unhosted.',
        'Only state-preserving adjacent11-bit-position peer publication is connected; mount/appearance/transfer/battle/larger coordinate/handle variants remain open.',
        'Send API submission is not asynchronous queue acceptance, native network/render acceptance or deployment.',
        'Every remaining gameplay route and full direction/phase/state/variant/indirect/deferred denominator remain open.']
    out.mkdir(parents=True);snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'source-adaptation-receipt.json',changes)
    dump(out/'native-peer-movement-contract.json',{'native_pins':{'cn':CN_PIN,'tw':TW_PIN},
        'cn_spans':native,'tw_spans':tw_spans,'cn_logical_size':17,'tw_logical_size':13,
        'cn_branch_span':{'address':'00490bf2','bytes':len(cn_slice),'sha256':sha(cn_slice)},
        'identity':'exact low16 logical+1; source reserved handle, never DB ID truncation',
        'position':'logical+9 low11 X, bits11..21 Y; preserve bits22..31 and all other bytes',
        'cn_mount':'logical+5 bits30..31; branch1 linked|8000 andbyte13, branch2 linked|4000 andzero, other linked andbyte13',
        'source_policy':'mandatory actual visible native template and common ready lease; no same-scene visibility inference',
        'state_source':'complete actual owner input; no fabricated state/appearance/mount/opaque fields',
        'tw_source_additive_only':True,'whole_opcode_variants_complete':False})
    manifest={'kind':'CN adjacent step -> mandatory real authorization/visible-native-records ->preallocated recipient-specific5E ->common position CAS ->actual actor/cache publication ->TW/CN send APIs ->supplied5D',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,'native_spans':native,
        'tw_native_spans':tw_spans,'native_function_spans':len(native),'new_source_files':3,
        'modified_cpp_files':3,'source_owner_chains_added':1,'new_phase_opcode_bindings':1,
        'new_unique_cn_phase_opcode_binding_values':1,'new_opcode_values':0,
        'formal_application_hosted':False,'concrete_recipient_projection_and_transport_submission':True,
        'actual_visibility_owner_implemented':False,'tw_enrolled_in_common_presence':False,
        'native_server_rules_recovered_by_this_integration':False,'new_complete_routes':0,'remaining':gaps,
        'owner_resumed_work_on':'2026-10-07','previous_goal_turn_classification':'progress: open-failure/null-slot source sealed; owner pause honored and explicitly resumed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'TW/CN native peer5E projection from common committed movement',
        'status':'已接共用位置CAS後的收件者版本13/17-byte原生5E投影與真實send API；真正可見角色資料與WorldOwner未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{'world-connection-1':['5E']},
        'source_paths':SOURCES,'source_owner_chains_added':1,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'storage_writes':'existing common position CAS; no new DB writes or tables',
        'shared_storage':['existing recovered_characters/common owned position and ready presence'],
        'native_form_qualifications':{'tw_13_cn_17_exact_records':True,'opaque_bytes_preserved':True,
            'real_version_specific_send_api':True,'queue_acceptance_observed':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['owner_stop_after_round']=False;plan['owner_resumed_work_on']='2026-10-07'
    plan['next']=['Connect actual common scene/actor owner and bound visible-template lifecycle to this prepared publication; preserve mandatory permission/full5D suppliers.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'cn_native_functions':len(native),
        'tw_native_spans':len(tw_spans),'new_cpp_files':3,'modified_cpp_files':3,
        'new_cn_phase_binding_values':1,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
