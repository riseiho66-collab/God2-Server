"""Static retained-text/native resource lineage; no decode, loaders, DB or tests."""
import csv
import json
import struct
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN, RECOVERY
from .cn_shared_movement_owner_delivery import sha, dump
from .cn_summary_world_lineage_delivery import trace

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-npc-name-resource-lineage-01'
ROUND='20261007-cn-npc-name-resource-lineage'
NEW=['src/cn/assets/CnNpcNameCatalog.h','src/cn/assets/CnNpcNameRows.inc']
MODIFIED=['src/cn/world/SharedSpecialDirectory.h','src/cn/world/SharedSpecialDirectory.cpp',
    'tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/protocol/CnSpecialDirectoryWire.h','src/cn/protocol/CnTransport.h']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-npc-name-resource-lineage-20261007.md',
    'tools/reconstruction/cn_npc_name_resource_lineage_delivery.py']
OLD_PACKED='f8b0762f111c532f1cbb38d66f06b6a4c6c685c278a5dcc98fbaead780e2376f'
OLD_PLAIN='1a818c454df37c58f1565b244a1030668cac52bf7ee75bb9a7db3e0bee263b44'


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog39-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());adaptations=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();row=before[rel]
        if sha(b)!=row['sha256'] or len(b)!=row['bytes'] or sha(b)!=known[rel]['sha256']:
            raise ValueError('Before source differs '+rel)
        adaptations.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-39'})
    for rel in CONTEXT:
        if sha((SERVER/rel).read_bytes())!=known[rel]['sha256']:raise ValueError('Context changed '+rel)
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged')
    recovery=RECOVERY.parent
    original_manifest=recovery/'agent_round7_monsterfield/reports/manifest.json'
    original_bytes=original_manifest.read_bytes();original=json.loads(original_bytes)
    historical=recovery/'monster_skill_research_20260926/reports/cn_skill_books.json'
    historical_bytes=historical.read_bytes();historic=json.loads(historical_bytes)
    decoded=recovery/'agent_round7_monsterfield/decoded/gamedata.csv';plain=decoded.read_bytes()
    recorded=next(r for r in original['files'] if r['path']=='decoded\\gamedata.csv')
    if original['exe_sha256']!=PIN or sha(plain)!=recorded['sha256'] or sha(plain)!=OLD_PLAIN or \
       historic['source_sha256']!=OLD_PACKED or historic['decoded_sha256']!=OLD_PLAIN:
        raise ValueError('Retained historical source lineage differs')
    current_path=CN.parent/'XJZ-CN/Data2/Patch/Comm/gamedata.csvZ';packed=current_path.read_bytes()
    current_receipt=CN/'artifacts/native/20261006-cn-scene-assets-01/scene-catalog.json'
    current_bytes=current_receipt.read_bytes();current=json.loads(current_bytes)
    if sha(packed)!=current['encoded_sha256']:raise ValueError('Current scene resource differs')
    if current['encoded_sha256']==OLD_PACKED or current['decoded_sha256']==OLD_PLAIN:
        raise ValueError('Expected explicit separate source epochs')
    lines=plain.splitlines(keepends=True);starts=[i for i,b in enumerate(lines) if b.startswith(b'NPCAppearData,')]
    if len(starts)!=1:raise ValueError('Ambiguous source section')
    start=starts[0];count=int(lines[start].strip().split(b',')[1]);offsets=[];offset=0
    for line in lines:offsets.append(offset);offset+=len(line)
    ordered=[];final={};overwrites=[];long_names=0
    for ordinal,line in enumerate(lines[start+1:start+1+count]):
        raw=line.rstrip(b'\r\n');fields=raw.split(b',');key=int(fields[0]);name=fields[1]
        if not 0<=key<7000 or b'"' in name or b'\0' in name:raise ValueError('Unqualified native text row')
        name.decode('cp936') # Only the individually supplied name field; no whole-file replacement decode.
        prefix=name[:15]+b'\0';long_names+=len(name)>15
        row={'ordinal':ordinal,'source_line':start+2+ordinal,'decoded_offset':offsets[start+1+ordinal],
            'selector':key,'raw_record_hex':raw.hex(),'raw_record_sha256':sha(raw),
            'source_name_hex':name.hex(),'source_name_bytes':len(name),
            'consumed_name_prefix_hex':prefix.hex(),'written_prefix_size':len(prefix),'source_field_count':len(fields)}
        if key in final:overwrites.append({'selector':key,'before_line':final[key]['source_line'],
            'after_line':row['source_line'],'before_prefix':final[key]['consumed_name_prefix_hex'],'after_prefix':prefix.hex()})
        ordered.append(row);final[key]=row
    if count!=4461 or len(final)!=4459 or max(final)!=6548 or len(overwrites)!=2 or long_names!=64:
        raise ValueError('Retained name-source scope differs')
    generated=SERVER/NEW[1]
    if generated.exists():raise ValueError('Preserve previous generated source')
    text='// Historical retained CN NPCAppearData; current8A72 asset is NOT qualified.\n'
    text+='// Last direct-index row wins. Unread bytes afterNUL are local padding only.\n'
    for key,row in sorted(final.items()):
        prefix=bytes.fromhex(row['consumed_name_prefix_hex']);padded=prefix+b'\0'*(16-len(prefix))
        text+='{'+f'{key},{row["source_line"]},{len(prefix)},'+ '{{'+','.join(f'0x{x:02x}' for x in padded)+'}}},\n'
    generated.write_text(text,encoding='ascii')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';image=exe.read_bytes()
    if sha(image)!=PIN:raise ValueError('Pinned CN differs')
    pe=pefile.PE(data=image,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
    metadata=(RECOVERY/'functions.tsv').read_bytes()
    functions={r['address']:r for r in csv.DictReader(metadata.decode('utf-8-sig').splitlines(),delimiter='\t')}
    pending=[('native/functions.tsv',metadata,RECOVERY/'functions.tsv')];spans=[]
    for address in ['00428ae0','00405a30']:
        row=functions[address];source=RECOVERY/row['file'];low=int(address,16);size=int(row['bytes'])
        code=pe.get_data(low-base,size);cfg,asm,_=trace(md,code,low,low+size,{})
        spans.append({'address':address,'declared_size':size,'sha256':sha(code),'cfg':cfg,
            'declared_span_not_automatically_complete_function':True})
        pending.extend([(f'native/{address}.bin',code,exe),(f'native/{address}.asm',asm,'primary static CFG'),
            (f'native/{address}.c',source.read_bytes(),source)])
    table=pe.get_data(0x8863d8-base,24*8);filenames=[]
    pending.append(('native/008863d8-filename-pairs.bin',table,exe))
    for n in range(24):
        pair=struct.unpack_from('<2I',table,n*8);names=[]
        for va in pair:
            data=pe.get_data(va-base,100).split(b'\0',1)[0]+b'\0';names.append(data[:-1].decode('ascii'))
            pending.append((f'native/filenames/{va:08x}.bin',data,exe))
        filenames.append({'ordinal':n,'mode0':names[0],'mode1':names[1]})
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'sha256':sha(data),'bytes':len(data),'original':str(origin)})
    # Multiple filename pointers may repeat; retain each unique source byte once.
    saved=set()
    for rel,data,origin in pending:
        if rel not in saved:save(rel,data,origin);saved.add(rel)
    for rel,path in [('inputs/historical-manifest.json',original_manifest),('inputs/historical-books-receipt.json',historical),
        ('inputs/historical-gamedata.csv',decoded),('inputs/historical-decode-receipt.json',recovery/'agent_round7_monsterfield/reports/gamedata_decode.json'),
        ('inputs/current-scene-catalog.json',current_receipt),('inputs/current-gamedata.csvZ',current_path)]:save(rel,path.read_bytes(),path)
    old=ROOT/'cn-special-directory-owner-01/integration-manifest.json';b=old.read_bytes()
    if sha(b)!=ledger['cn_account_admission_evidence']['cn-special-directory-owner-01']['artifact_sha256'][old.name]:
        raise ValueError('Prior native loader receipt differs')
    save('inputs/prior-native-special-directory-manifest.json',b,old)
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    save('ordered-npc-name-source-rows.json',(json.dumps(ordered,indent=2)+'\n').encode(),'retained raw text source accounting')
    facts={'client_sha256':PIN,'historical_encoded_sha256':OLD_PACKED,'historical_decoded_sha256':OLD_PLAIN,
        'current_encoded_sha256':sha(packed),'current_decoded_receipt_sha256':current['decoded_sha256'],
        'current_resource_matches_historical_source':False,'current_actual_npc_names_qualified':False,
        'source_rows':count,'unique_selectors':len(final),'max_source_selector':max(final),'long_input_names':long_names,
        'native_overwrite_events':overwrites,'primary_filename_pairs':filenames,
        'whole_file_cp936_decode_not_assumed':True,'unwritten_after_nul_not_native_memory_evidence':True,
        'original_packed_epoch_not_available_at_current_named_path':True,
        'new_monster_attack_defense_attribute_element_or_carried_skill_values':0,'new_complete_routes':0}
    save('npc-name-resource-lineage.json',(json.dumps(facts,indent=2)+'\n').encode(),'static primary/resource lineage')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,
                'original':'captured before source edits'})
    gaps=['Current8A72 gamedata decoded NPC section/projection remains missing; historical1A81 source is not silently promoted.',
        'Actual resource revision/native maximum/current build qualification and real star/bounty data/permissions/issuance remain required.',
        'Monster double attack/defense, attributes/elements and carried skills remain unresolved; these names/appearance rows are not combat values.',
        'All native suppliers, production Application plan and whole-game state/variant/direction denominator remain incomplete.']
    manifest={'kind':'retained same-EXE historical NPC name prefix source ->explicit resource gate ->existing conditional F9 consumed-name qualification',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':adaptations,'primary_native_spans':spans,
        'source_rows':count,'unique_selectors':len(final),'current_resource_qualified':False,
        'new_cpp_files':2,'modified_cpp_files':2,'modified_catalog_tools':1,'source_owner_chains_added':0,
        'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: catalog39 same Selected/common storage/native scene/deferred movement/ready composition sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','decoder_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN NPC historical name source lineage and strict F9 resource projection',
        'version_scope':'cn','status':'已整理4461來源列/4459有效名稱索引及同版原生載入來源，接嚴格資源雜湊名稱投影；當前資源不同仍未合格',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none; no tables or gameplay combat values created',
        'shared_storage':['native resource name selector is presentation identity; no common ID or TW namespace join inferred'],
        'native_form_qualifications':{'historical_names':4459,'current_resource_qualified':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['npc_name_resource_lineage']={'root':out.relative_to(SERVER).as_posix(),
        'facts':'npc-name-resource-lineage.json','current_resource_qualified':False,'complete_gameplay_routes':0}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Recover current8A72/16F7 exact native NPC source section and source projection; pursue actual gameplay/native success suppliers and remaining variants.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'historical_rows':count,'historical_unique_name_selectors':len(final),
        'current_resource_qualified':False,'new_complete_routes':0,'tests_run':False}))


if __name__=='__main__':main()
