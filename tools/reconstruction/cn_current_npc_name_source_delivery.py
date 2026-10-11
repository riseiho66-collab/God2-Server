"""Seal copied-byte static recovery and current NPC source projection; no game/tests."""
import json
from pathlib import Path
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN, PIN
from .cn_shared_movement_owner_delivery import sha, dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-current-npc-name-source-01'
ROUND='20261007-cn-current-npc-name-source'
NEW=['src/cn/assets/CnCurrentNpcNameCatalog.h','src/cn/assets/CnCurrentNpcNameRows.inc']
MODIFIED=['src/cn/world/SharedSpecialDirectory.h','src/cn/world/SharedSpecialDirectory.cpp',
    'tools/reconstruction/dual_client_route_catalog.py']
CONTEXT=['src/cn/assets/CnNpcNameCatalog.h','src/cn/assets/CnNpcNameRows.inc',
    'src/cn/protocol/CnSpecialDirectoryWire.h','src/cn/protocol/CnTransport.h']
SOURCES=NEW+MODIFIED+CONTEXT+['docs/research/cn-current-npc-name-source-20261007.md',
    'tools/reconstruction/cn_current_npc_name_source_delivery.py']


def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed evidence')
    lp=ROOT/'packet-route-ledger.json';prior=lp.read_bytes();ledger=json.loads(prior)
    if prior!=(out/'ledger-before-edits.json').read_bytes():raise ValueError('Ledger changed')
    catalog=(out/'catalog40-source-files.json').read_bytes()
    if sha(catalog)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog differs')
    known=json.loads(catalog);before=json.loads((out/'before-source-manifest.json').read_bytes());changes=[]
    for rel in MODIFIED:
        b=(out/'prior-sources'/rel).read_bytes();r=before[rel]
        if sha(b)!=r['sha256'] or len(b)!=r['bytes'] or sha(b)!=known[rel]['sha256']:
            raise ValueError('Before source differs '+rel)
        changes.append({'path':rel,'before_sha256':sha(b),'after_sha256':sha((SERVER/rel).read_bytes()),
            'before_captured_before_edit':True,'prior_catalog':'dual-client-route-catalog-40'})
    for rel in CONTEXT:
        if sha((SERVER/rel).read_bytes())!=known[rel]['sha256']:raise ValueError('Context changed '+rel)
    for rel in NEW:
        if rel in known:raise ValueError('New source already cataloged')
    inputs=out/'inputs';plain=(inputs/'current-gamedata.csv').read_bytes();packed=(inputs/'current-gamedata.csvZ').read_bytes()
    resource=json.loads((inputs/'current-scene-resource-receipt.json').read_bytes())
    info=json.loads((out/'extraction-info.json').read_bytes())
    if sha(plain)!=resource['decoded_sha256'] or sha(packed)!=resource['encoded_sha256'] or \
       sha(plain)!=info['decoded_sha256'] or sha(packed)!=info['encoded_sha256']:
        raise ValueError('Static recovery source pins differ')
    if sha(packed)!=sha((CN.parent/'XJZ-CN/Data2/Patch/Comm/gamedata.csvZ').read_bytes()) or \
       sha((CN.parent/'XJZ-CN/God2_opt.exe').read_bytes())!=PIN:
        raise ValueError('Current original inputs changed')
    if sha((inputs/'static-resource-extractor.py').read_bytes())!=sha((CN/'tools/reverse/recover_cn_login.py').read_bytes()):
        raise ValueError('Static extractor source changed')
    oldroot=ROOT/'cn-npc-name-resource-lineage-01';oldpath=oldroot/'ordered-npc-name-source-rows.json'
    oldbytes=oldpath.read_bytes()
    expected=ledger['cn_account_admission_evidence']['cn-npc-name-resource-lineage-01']['artifact_sha256']
    if sha(oldbytes)!=expected[oldpath.name]:raise ValueError('Historical source rows changed')
    old={r['selector']:r for r in json.loads(oldbytes)}
    lines=plain.splitlines(keepends=True);starts=[i for i,b in enumerate(lines) if b.startswith(b'NPCAppearData,')]
    if len(starts)!=1:raise ValueError('Ambiguous NPC section')
    start=starts[0];count=int(lines[start].strip().split(b',')[1]);offsets=[];offset=0
    for line in lines:offsets.append(offset);offset+=len(line)
    rows=[];final={};duplicates=[];long_names=0
    for n,line in enumerate(lines[start+1:start+1+count]):
        raw=line.rstrip(b'\r\n');fields=raw.split(b',');key=int(fields[0]);name=fields[1]
        if not 0<=key<7000 or b'"' in name or b'\0' in name:raise ValueError('Unqualified source field')
        name.decode('cp936');prefix=name[:15]+b'\0';long_names+=len(name)>15
        row={'ordinal':n,'selector':key,'source_line':start+2+n,'decoded_offset':offsets[start+1+n],
            'raw_record_hex':raw.hex(),'raw_record_sha256':sha(raw),'source_name_hex':name.hex(),
            'source_name_bytes':len(name),'consumed_name_prefix_hex':prefix.hex(),'written_prefix_size':len(prefix),
            'source_field_count':len(fields)}
        if key in final:duplicates.append({'selector':key,'before_line':final[key]['source_line'],
            'after_line':row['source_line'],'before_prefix':final[key]['consumed_name_prefix_hex'],'after_prefix':prefix.hex()})
        rows.append(row);final[key]=row
    if (count,len(final),max(final),long_names)!=(4466,4464,6553,64) or len(duplicates)!=2:
        raise ValueError('Current source scope differs')
    added=sorted(final.keys()-old.keys());removed=sorted(old.keys()-final.keys())
    prefix_changed=[k for k in sorted(old.keys()&final.keys()) if old[k]['consumed_name_prefix_hex']!=final[k]['consumed_name_prefix_hex']]
    raw_changed=[k for k in sorted(old.keys()&final.keys()) if old[k]['raw_record_hex']!=final[k]['raw_record_hex']]
    if added!=list(range(6549,6554)) or removed or prefix_changed or raw_changed:
        raise ValueError('Current/historical source difference differs')
    include=SERVER/NEW[1]
    if include.exists():raise ValueError('Preserve generated source')
    text='// Current pinned8A72/16F7 NPC names; preserve separate historical source.\n'
    text+='// Last row wins; local bytes after firstNUL are unread padding, not native-memory data.\n'
    for key,row in sorted(final.items()):
        prefix=bytes.fromhex(row['consumed_name_prefix_hex']);padded=prefix+b'\0'*(16-len(prefix))
        text+='{'+f'{key},{row["source_line"]},{len(prefix)},'+'{{'+','.join(f'0x{x:02x}' for x in padded)+'}}},\n'
    include.write_text(text,encoding='ascii')
    snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    save('inputs/historical-ordered-name-rows.json',oldbytes,oldpath)
    for name in ['integration-manifest.json','npc-name-resource-lineage.json']:
        p=oldroot/name;b=p.read_bytes()
        if sha(b)!=expected[name]:raise ValueError('Historical receipt differs')
        save('inputs/historical-'+name,b,p)
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,lp)
    save('ordered-current-npc-name-source-rows.json',(json.dumps(rows,indent=2)+'\n').encode(),'current raw source accounting')
    delta={'historical_source_rows':4461,'historical_unique_selectors':len(old),'current_source_rows':count,
        'current_unique_selectors':len(final),'added_selectors':added,'removed_selectors':removed,
        'changed_existing_name_prefixes':prefix_changed,'changed_existing_raw_records':raw_changed,
        'added_rows':[final[k] for k in added],'overwrite_events':duplicates,'long_source_names':long_names}
    save('current-historical-name-source-delta.json',(json.dumps(delta,indent=2)+'\n').encode(),'separate exact source epochs')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    listed={r['path'] for r in snapshots}
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.relative_to(out).as_posix() not in listed:
            snapshots.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),
                'original':'captured before source edits or bounded copied-byte static recovery'})
    gaps=['Actual loaded-resource revision/native maximum/actor source qualification and real common star/bounty data/permissions/issuance remain missing.',
        'NPC names and appearance selectors do not establish monster double attack/defense, attributes/elements or carried skill repertoire.',
        'Actual native account/world full suppliers, authority/production Application plan and all remaining native state/variant/direction routes remain incomplete.']
    manifest={'kind':'current pinned gamedata static NPC name source ->explicit current resource identity ->existing F9 source consumed-name qualifier',
        'client_sha256':PIN,'encoded_sha256':sha(packed),'decoded_sha256':sha(plain),'source_paths':SOURCES,
        'snapshots':snapshots,'source_adaptations':changes,'source_rows':count,'unique_name_selectors':len(final),
        'historical_source_preserved':True,'current_static_name_source_recovered':True,'actual_loaded_native_state_accepted':False,
        'static_resource_extraction_run':True,'python_static_decoder_executed':True,'native_asset_loader_executed':False,
        'new_cpp_files':2,'modified_cpp_files':2,'modified_catalog_tools':1,'source_owner_chains_added':0,
        'new_phase_opcode_bindings':0,'new_opcode_values':0,'new_complete_routes':0,'formal_application_hosted':False,
        'previous_goal_turn_classification':'progress: catalog40 historical name source lineage and current resource mismatch recovered',
        'whole_game_route_total':None,'whole_game_completion_percent':None,'remaining':gaps,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','deployed','production_database_read_or_modified',
            'client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN current native NPC name source and exact current F9 resource projection',
        'version_scope':'cn','status':'已靜態恢復當前4466來源列/4464名稱索引，接既有F9的獨立當前雜湊投影；loaded狀態與實際玩法供應未完成',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':0,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':'none; no game or regional tables created',
        'shared_storage':['native appearance/name resource identity only; no inferred common actor, monster or gameplay ID'],
        'native_form_qualifications':{'current_static_name_source_recovered':True,'current_final_name_selectors':4464,
            'actual_loaded_native_state_accepted':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    for segment in ledger['dual_client_source_segments']:
        if segment.get('evidence')==(oldroot.relative_to(SERVER).as_posix()):
            segment['followup_current_static_source']=out.relative_to(SERVER).as_posix()
            segment['static_current_name_source_gap_resolved_by']=NAME
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    ledger['cn_native_state_relations']['current_npc_name_source']={'root':out.relative_to(SERVER).as_posix(),
        'source_rows':count,'unique_name_selectors':len(final),'static_source_recovered':True,
        'actual_loaded_native_state_accepted':False,'complete_gameplay_routes':0}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Recover native NPC-loaded-state/actual source suppliers and remaining D1/F9/B0/94 variants, native success data and actual common gameplay authorities.']+gaps
    dump(lp,ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'current_source_rows':count,'current_unique_name_selectors':len(final),
        'historical_added_selectors':added,'new_complete_routes':0,'static_resource_extraction':True,'tests_run':False}))


if __name__=='__main__':main()
