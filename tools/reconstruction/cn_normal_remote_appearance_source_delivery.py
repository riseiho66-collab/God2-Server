"""File-only primary CN normal2A/remote6F ordinary input relation and source."""
import csv
import hashlib
import json
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT,PIN

NAME='cn-normal-remote-appearance-source-01'
ROUND='20261007-cn-normal-remote-appearance-source'
SOURCES=('src/cn/protocol/CnRemoteActor.h','src/cn/protocol/CnWorldEntry.h',
    'src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'tools/reconstruction/dual_client_route_catalog.py',
    'tools/reconstruction/cn_normal_remote_appearance_source_delivery.py',
    'docs/research/cn-normal-remote-appearance-source-20261007.md')
FUNCTIONS=('0048fcc0','00492e70','00482c90','00532410','0052f990','005356d0','005356f0','00532800')
REMAINING=[
    'Actual common authoritative equipment/appearance-to-input and full recipient native6F opaque/state/frame/layer/mount/text/resource/issuer/observer policy remain missing; this ordinary projection is not those rules.',
    'CN original HeroDoll/mount/auxiliary resource row readers/current assets and complete input source lineage still need qualification; TW-origin->CN, CF retained/alternate and later appearance/visibility variants remain open.',
    'Configured Application/WS/native providers/hosting, semantic replay/durable committed-output/crash/cross-process recovery and TW own initial/native-handle/later lifecycle remain incomplete.',
    'All TW/CN/web gameplay/numeric full routes and exhaustive direction/phase/state/variant/indirect/deferred denominator remain open; original-client comprehensive acceptance follows full source connection; levels unchanged.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before receipt required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():
            if p.read_bytes()!=data:raise RuntimeError('Unsealed partial receipt differs: '+rel)
            return # Resume identical prior file receipts; never rewrite them.
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    unchanged=[]
    for row in json.loads((out/'before-manifest.json').read_text(encoding='utf-8')):
        data=(out/'before'/row['path']).read_bytes()
        if sha(data)!=row['sha256']:raise RuntimeError('Before receipt differs')
        if row['path'] not in SOURCES and row['path'] not in ('artifacts/integration/packet-connections-20261006/packet-route-ledger.json','docs/PACKET_CONNECTION_GOAL_20261006.md'):
            if data!=(ROOT/row['path']).read_bytes():raise RuntimeError('Preserved context differs')
            unchanged.append(row)
    prior=base/'dual-outward-visibility-publication-01';raw=(prior/'manifest.json').read_bytes();manifest=json.loads(raw)
    pins={r['path']:r['sha256'] for r in manifest['files']}
    if not manifest['sealed']:raise RuntimeError('Previous source not sealed')
    save('retained-source/dual-outward-visibility-publication-01/manifest.json',raw)
    for rel in ('findings.json','round-report.json'):
        data=(prior/rel).read_bytes()
        if sha(data)!=pins[rel]:raise RuntimeError('Previous sealed source differs')
        save('retained-source/dual-outward-visibility-publication-01/'+rel,data)
    rel='retained-source/tw-common-world-publication-01/after/src/core/Application.cpp'
    data=(prior/rel).read_bytes()
    if sha(data)!=pins[rel] or data!=(ROOT/'src/core/Application.cpp').read_bytes():raise RuntimeError('Frozen host context differs')
    save('retained-source/frozen-Application.cpp',data)
    dump('retained-source/frozen-Application-origin.json',{'original_artifact':'dual-outward-visibility-publication-01',
        'original_path':rel,'sha256':sha(data),'current_host_exact_bytes_retained':True})
    native=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');raw=native.read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('CN primary pin differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);md=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    meta=(recovery/'functions.tsv').read_bytes();rows={r['address']:r for r in csv.DictReader(meta.decode('utf-8').splitlines(),delimiter='\t')}
    envelopes=[]
    for address in FUNCTIONS:
        row=rows[address];size=int(row['bytes']);path=(recovery/row['file']).resolve()
        if not path.is_relative_to(recovery.resolve()):raise RuntimeError('Recovery path outside root')
        source=path.read_bytes();code=view.read(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        instructions=list(md.disasm(code,int(address,16)))
        listing=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in instructions)+'\n').encode()
        for ext,data in (('.bin',code),('.asm',listing),('.c',source)):save('native/current-cn/'+address+ext,data)
        envelopes.append({'address':address,'bytes':size,'native_sha256':sha(code),'recovery_source':str(path),
            'recovery_source_sha256':sha(source),'metadata':row,'decoded_bytes':sum(i.size for i in instructions),
            'direct_calls':[{'site':f'{i.address:08x}','operand':i.op_str} for i in instructions if i.mnemonic=='call' and i.op_str.startswith('0x')],
            'executed':False,'envelope_is_complete_gameplay':False})
    pe.close();dump('native/function-envelopes.json',{'primary':str(native),'sha256':PIN,
        'recovery_metadata_sha256':sha(meta),'ranges':envelopes,'native_executed':False})
    relations=[
        {'input':'driver resolver arg1','self2A_payload':'(u32(4)>>16)&0xff','remote6F_logical':'(u32(5)>>8)&0x7f',
         'self_caller':'00492E70 ->00482C90','remote_caller':'0048FCC0 WORLD6F ->00482C90','projection':'reject self input>=128; preserve remote bit15 and every other bit'},
        {'input':'auxiliary resolver arg2','self2A_payload':'(u32(0)>>16)&0x7f','remote6F_logical':'(u32(1)>>14)&0x7f',
         'projection':'replace only low7 resolver selector bits, retaining identity/language/frame/all other header data'},
        {'input':'four packed components','self2A_payload':'12..19','remote6F_logical':'21..28','resolver':'00482C90 ->00488DA0/00488C30',
         'raw_slot':'first&15/first>>4/second&31/second>>5; not equipment IDs or resolved resource handles'},
        {'input':'palette operand','primary':'00532410 ->0052F990 ->005356D0; later00532800',
         'rule':'state WORD&0x1000 ?7:component second>>5','scope':'native renderer consumption only; actual source state not derived or changed'}]
    dump('native/ordinary-input-relations.json',relations)
    # File slices only: original parsers/position projection/native text/layers
    # and unrelated shared preparation/gameplay/DB methods are not run.
    preserved=[]
    rel='src/cn/protocol/CnRemoteActor.h';old=(out/'before'/rel).read_bytes();new=(ROOT/rel).read_bytes()
    for start,end in ((b'    static std::optional<Record> parse_logical(',b'    static LogicalRecord encode_logical('),
                     (b'    static std::optional<Record> with_position(',b'\n};\nstruct CnRemoteActorRemove')):
        a=old[old.index(start):old.index(end,old.index(start))];b=new[new.index(start):new.index(end,new.index(start))]
        if a!=b:raise RuntimeError('Preserved raw codec body differs')
        preserved.append({'method':start.decode(),'sha256':sha(a),'exact_bytes_preserved':True})
    dump('preserved-methods.json',preserved)
    peer=json.loads((out/'peer-handoff/server-file-source-receipt.json').read_text(encoding='utf-8'))
    facts={'round':ROUND,'cn_native_sha256_context':PIN,
        'previous_goal_turn_classification':'progress: dual initial outward6F/common model/1C source handoff and catalog101 sealed',
        'cn_normal_appearance_operand_projections_added':1,'cn_bound_normal_scene_appearance_sources_added':1,
        'existing_cn6F_source_bindings_strengthened':1,'native_resolver_input_relations_qualified':3,
        'native_function_envelopes_read':len(envelopes),'native_function_bytes_read':sum(r['bytes'] for r in envelopes),
        'new_source_owner_chains':0,'new_tw_source_owner_chains':0,'new_native_phase_source_bindings':0,
        'new_packet_values':0,'new_complete_bidirectional_routes':0,'whole_game_route_total':None,
        'whole_game_completed_routes':None,'whole_game_completion_percent':None,
        'authoritative_equipment_to_appearance_recovered':False,'full_native6F_issuer_data_recovered':False,
        'configured_native_visibility_providers_installed':False,'formal_application_hosted':False,
        'levels_changed':False,'build_run':False,'tests_run':False,'runtime_run':False,'database_access':False,'deployed':False,
        'existing_contexts_unchanged':unchanged,'latest_peer_handoff_round':peer['round'],'remaining':REMAINING}
    dump('findings.json',facts)
    dump('source-relations.json',{'source':'actual normal SharedInitialScene full37-byte2A ->exact source connection/presence/lease/current initial saved position/shared native map ->private immutable visibility-owner/input witness',
        'projection':'supplied complete real CN6F ->actual same actor low12 handle +ordinary branch +driver representable +two proven selectors/four packed inputs ->preserved names/tag/state/layers/frame/position/opaque bytes',
        'publication':'initial incoming/explicitshow/outward preparation/held publisher/queue release requalify private actual source/input witness; actual Current/rules/resources/complete issuer still mandatory',
        'independence':'legacy full native records stay independent; TW CUSTOM appearance DB unchanged and never used as CN authority; no new storage table',
        'remaining':REMAINING})
    for rel in SOURCES:save('source/'+rel,(ROOT/rel).read_bytes())
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_normal_remote_appearance_source']={k:v for k,v in facts.items() if k!='existing_contexts_unchanged'}
    ledger['cn_normal_remote_appearance_source']['evidence']=out.relative_to(ROOT).as_posix()
    ledger['dual_client_source_segments'].append({'name':'CN actual normal scene2A ->ordinary remote6F resolver operand source/witness',
        'version_scope':'cn-normal-initial-source-remote-appearance-operands','status':'same actual scene/connection/common lease/full2A ->bounded ordinary6F selector/component projection ->private source witness ->existing initial/inward/outward publication; complete appearance/equipment/resources/issuer/host open',
        'source_paths':list(SOURCES),'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_owner_chains_added':0,
        'tw_source_owner_chains_added':0,'formal_application_hosted':False,'complete_gameplay_routes_added':0,
        'cn_normal_appearance_operand_projections_added':1,'cn_bound_normal_scene_appearance_sources_added':1,
        'existing_cn6F_source_bindings_strengthened':1,'evidence':out.relative_to(ROOT).as_posix(),'remaining':REMAINING})
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Recover actual pinned CN HeroDoll/mount/auxiliary row readers/current resources and equipment-to-normal appearance input source lineage. The concrete same normal scene/full2A witness now projects only proven ordinary6F resolver operands; actual complete native6F unknown fields/rules/data/observer/resource/issuer providers and production hosting remain missing. TW-origin/CN/CF/alternate/later appearance and visibility, semantic replay/recovery, all gameplay/numeric paths and exhaustive denominator remain open. Levels unchanged; PHASE1 file-only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/PACKET_CONNECTION_GOAL_20261006.md').open('a',encoding='utf-8') as f:f.write(
        '\n\n## CN actual normal scene ->ordinary remote appearance ('+ROUND+')\n\n'
        'Pinned CN normal2A and6F use00482C90 with differently packed/narrow driver inputs. Actual same normal scene/connection/common lease/full2A supplies the retained source; checked ordinary projection copies only two selectors/eight packed component bytes into a supplied complete6F. Private witness requalifies initial/inward/outward publication; no truncation, alternate fallback, layer/state/name/opaque defaults or TW CUSTOM authority. Projection1/concrete normal source1/existing6F binding strengthened1; new opcode/phase/owner/full route0. Complete actual equipment/appearance/resources/issuer/observer policy/hosting and all gameplay/denominator remain open. Levels unchanged; no builds/tests/runtime/DB/deploy. See research/cn-normal-remote-appearance-source-20261007.md.\n')
    print(json.dumps({k:facts[k] for k in ('round','cn_normal_appearance_operand_projections_added','cn_bound_normal_scene_appearance_sources_added','native_function_envelopes_read','native_function_bytes_read','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
