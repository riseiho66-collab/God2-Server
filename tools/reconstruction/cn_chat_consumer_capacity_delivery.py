"""Static primary CN chat consumer CFG/data accounting and source sealing only."""
import csv
import json
import struct
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN,RECOVERY
from .cn_shared_movement_owner_delivery import sha,dump
from .cn_summary_world_lineage_delivery import trace

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-chat-consumer-capacity-01'
ROUND='20261007-cn-chat-consumer-capacity'
NEW=['src/cn/protocol/CnChatConsumerContract.h']
MODIFIED=['src/cn/world/SharedNativeChat.cpp','tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/world/SharedNativeChat.h','src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'src/cn/protocol/CnChat.h','src/cn/text/CnChatContent.h','src/cn/text/CnChatContent.cpp',
    'src/text/ChineseText.h','src/text/ChineseText.cpp','src/text/LegacyChineseCodec.h','src/text/LegacyChineseCodec.cpp',
    'src/protocol/RecoveredChat.h','src/core/Application.cpp','src/net/Session.h','src/net/Session.cpp']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-chat-consumer-capacity-20261007.md',
    'tools/reconstruction/cn_chat_consumer_capacity_delivery.py']
FUNCTIONS=['004a7270','0049a020','004a9590','00531ea0','00453bd0','00452970','004f5cc0','005225e0','0054b470']

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog42-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());changes=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();r=before[rel]
        if sha(b)!=r['sha256'] or len(b)!=r['bytes'] or sha(b)!=known[rel]['sha256']:
            raise ValueError('Before source differs '+rel)
        changes.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-42'})
    for rel in CONTEXT:
        if sha((SERVER/rel).read_bytes())!=known[rel]['sha256']:raise ValueError('Context/frozen source differs '+rel)
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged')
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('Native pin differs')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    def read(va,size):
        data=pe.get_data(va-base,size)
        if len(data)!=size:raise ValueError('Short native range')
        return data
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    rows={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    save('native/selected-function-metadata.json',(json.dumps({'original_sha256':sha(metadata),
        'rows':[rows[va] for va in FUNCTIONS]},indent=2)+'\n').encode(),RECOVERY/'functions.tsv')
    spans=[]
    for va in FUNCTIONS:
        r=rows[va];p=Path(r['file']);p=p if p.is_absolute() else RECOVERY/p
        b=p.read_bytes();size=int(r['bytes']);code=read(int(va,16),size)
        save('native/'+va+'.c',b,p);save('native/'+va+'-declared.bin',code,exe)
        spans.append({'va':va,'reported_bytes':size,'source_sha256':sha(b),'code_sha256':sha(code),
            'declared_extent_not_full_cfg_claim':True,'original_metadata':r})
    phase_path=CN/'artifacts/native/20261006-cn-route-denominator-03/s2c-phase-opcodes.json'
    phase_bytes=phase_path.read_bytes();phases=[r for r in json.loads(phase_bytes) if r['opcode']==0x5c]
    if len(phases)!=2:raise ValueError('Native phase scope differs')
    save('native/s2c-phase-opcodes.json',phase_bytes,phase_path)
    for r in phases:
        p=CN/r['branch_source'];save('native/'+Path(r['branch_source']).name,p.read_bytes(),p)
    save('native/chat5C-phase-relations.json',(json.dumps(phases,indent=2)+'\n').encode(),phase_path)
    table=read(0x4a7614,9*4);selectors=read(0x4a7638,19)
    display_targets=struct.unpack('<9I',table)
    if max(selectors)>=len(display_targets):raise ValueError('Display selector map differs')
    display_switch={0x4a7309:[display_targets[i] for i in selectors]}
    channel_table=read(0x49a698,19*4);channel_switch={0x49a054:list(struct.unpack('<19I',channel_table))}
    save('native/004A7614-targets.bin',table,exe);save('native/004A7638-selectors.bin',selectors,exe)
    save('native/0049A698-channel-targets.bin',channel_table,exe)
    decoded=[];branch_memory=[]
    for label,lo,hi,switches,packet_base in [
        ('world5C',0x492278,0x4923e6,{},'edi'),
        ('battle5C',0x5488bc,0x548906,{},'esi'),
        ('display4A7270',0x4a7270,0x4a7612,display_switch,None),
        ('channel49A020',0x49a020,0x49a698,channel_switch,None)]:
        code=read(lo,hi-lo);cfg,asm,instructions=trace(md,code,lo,hi,switches)
        save('native/'+label+'-primary.bin',code,exe)
        save('native/'+label+'-cfg.asm',asm,'static primary CFG decoding')
        save('native/'+label+'-cfg.json',(json.dumps(cfg,indent=2)+'\n').encode(),'static primary CFG, calls not followed')
        decoded.append({'label':label,'start':f'{lo:08x}','end_exclusive':f'{hi:08x}',
            'code_sha256':sha(code),'instructions':cfg['decoded_cfg_instructions'],'cfg_bytes':cfg['decoded_unique_cfg_bytes'],
            'open_edges':cfg['open_edges'],'calls_not_executed':True})
        if packet_base:
            for ins in sorted(instructions.values(),key=lambda i:i.address):
                for operand in ins.operands:
                    if operand.type==X86_OP_MEM and ins.reg_name(operand.mem.base)==packet_base:
                        branch_memory.append({'phase_branch':label,'site':f'{ins.address:08x}',
                            'mnemonic':ins.mnemonic,'operand':ins.op_str,'packet_displacement':operand.mem.disp,
                            'operand_width':operand.size,'kind':'pointer_projection' if ins.mnemonic=='lea' else 'direct_packet_memory_operand'})
    prefix_slots=read(0x899978,48);channel18=read(0x7f2cf8,9)
    expected=b'1A0\0' b'1A1\0' b'1A3\0' b'1A2\0' b'1A4\0' b'1A4\0' b'1A0\0' b'1A3\0' b'1A0\0' b'1A0\0' b'1A4\0' b'1A4\0'
    if prefix_slots!=expected or channel18!=bytes.fromhex('a1becfc9bde7a1bf00'):
        raise ValueError('Native display prefix data differs')
    save('native/00899978-channel-prefixes.bin',prefix_slots,exe)
    save('native/007F2CF8-channel18-prefix.bin',channel18,exe)
    prefixes={'channel_slots':[{'channel':i,'bytes_hex':prefix_slots[i*4:i*4+4].hex(),
        'non_nul_prefix_bytes':3} for i in range(12)],'channel18':{'bytes_hex':channel18.hex(),'non_nul_prefix_bytes':8}}
    save('native/display-prefix-data.json',(json.dumps(prefixes,indent=2)+'\n').encode(),'actual primary PE data')
    contract={'format':'CN5C bounded native consumer contract v1','client_sha256':PIN,
        'primary_direct_packet_accesses':branch_memory,'opaque_header_bytes_not_observed_in_bounded_branches':[3,4,10,11,12],
        'unobserved_header_values_not_inferred':True,'display_destination':{'stack_low':'ebp-0x104','stack_end_exclusive':'ebp-4',
            'bytes':256,'includes_client_prefix_and_terminator':True,'append_has_no_destination_length_check':True},
        'plain_channel_text_budgets':{str(i):252 for i in [0,1,2,3,5,6,8,9]}|{'13':255,'18':247},
        'actual_destination_qualification_still_required':True,'server_chat_permission_recovered':False,
        'world_actor_identity':'replyDWORD5 -> actual actor tableDWORD+18 at stride0x268,128 entries; name+1C,bubble handle+60',
        'world_channel12':'native text13 begins time32; remaining content uses template decoder, not plain body',
        'bubble_owner':'handle<0x1000 plus actual valid model/bubble state; no DB ID or handle truncation inferred',
        'battle_structured_variant_connected':False,'full_opcode_variants_complete':False}
    save('native-consumer-contract.json',(json.dumps(contract,indent=2)+'\n').encode(),'primary evidence scoped conclusions')
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),
                'original':'captured before source edits'})
    gaps=['Actual original server opaque5C fields and native authority/audience/rules/bubble identity issuance remain missing; no guessed header.',
        'Recovered256-byte plain display destination is necessary, not all downstream native destination proof; actual WorldOwner qualifier remains mandatory.',
        'Board, binary time32/template12, structured battle and remaining native control/state variants remain unconnected.',
        'Actual common suppliers and Application hosting, TW input->CN fanout, monster stats/skills and whole-game denominator remain incomplete.']
    manifest={'kind':'primary CN5C world/battle reader scopes and256-byte client formatter destination ->bounded per-recipient source display budget',
        'client_sha256':PIN,'source_paths':SOURCES,'source_adaptations':changes,'native_declared_spans':spans,
        'native_cfg_spans':decoded,'snapshots':snapshots,'native_consumer_contract':contract,
        'new_cpp_files':1,'modified_cpp_files':1,'modified_catalog_tools':1,'source_owner_chains_added':0,
        'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: catalog42 conditional CN chat owner/shared recipients and3 scoped bindings integrated',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','deployed','production_database_read_or_modified',
            'client_modified','font_modified','frozen_tw_chat_modified','resource_extraction_run']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN5C primary display capacity and world/battle consumer boundaries',
        'version_scope':'cn','status':'原生256-byte display暫存區與各頻道前綴追明，已接來源預算；實際header/權威受眾未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none',
        'shared_storage':['existing source/recipient common leases unchanged; no regional or gameplay tables created'],
        'native_form_qualifications':{'plain_native_client_display_bound_recovered':True,'complete_native_destination_proof':False,
            'server_authority_implemented':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['chat_consumer_capacity']={'root':out.relative_to(SERVER).as_posix(),
        'plain_destination_bytes':256,'scoped_plain_channel_count':10,'complete_gameplay_routes':0,'server_authority_implemented':False}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND;plan['next']=gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'native_cfg_spans':decoded,
        'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
