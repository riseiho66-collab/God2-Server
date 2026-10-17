# Legacy receipt identifiers retain their schema spelling; both cases are the
# Taiwan client using Traditional CP950 or Simplified CP936, not regional protocols.
"""CUSTOM-0080 immutable post-install proof and one-record metadata update.
Relocate to tools/operations only after candidate QA has terminated.
"""
import argparse,copy,hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.operations import owned_guild_kick_release_v01_20261005 as release
require,sha,read,write=release.require,release.sha,release.read,release.write_new

def validate_installed_release(path):
    """Requalify immutable preinstall evidence without requiring old live EXE."""
    info=read(path/'manifest.json');apply=read(path/'apply-result.json')
    release.base.true_fields(info,('stage_qualified','formal_native_qualified','same_schema50_reopen_qualified'),'Installed stage')
    require(info.get('format')==release.FORMAT and info.get('candidate_sha256')==release.CANDIDATE_SHA and
            info.get('old_server_sha256')==release.OLD_SHA,'Installed manifest identity differs')
    require(info.get('release_tool_path')==str(Path(release.__file__).resolve()) and
            info.get('release_tool_sha256')==sha(release.__file__),'Installed release helper identity differs')
    release.base.true_fields(apply,('accepted','formal_installed','same_schema50_exact_before_start','no_gameplay_grants'), 'Formal apply')
    require(all(record.get(k) is False for record in (info,apply) for k in
                ('database_replaced','config_changed','resources_changed')),'Binary-only same50 release required')
    require(apply.get('candidate_sha256')==release.CANDIDATE_SHA and apply.get('old_server_sha256')==release.OLD_SHA and
            apply.get('contract_sha256')==info['contract_sha256'] and
            apply.get('native_receipt_sha256')==info['receipt_sha256'],'Formal apply/stage evidence differs')
    require(str(release.managed.ACTIVE.resolve())==info['active'] and
            str(release.managed.CONFIG.resolve())==info['config'],'Installed target path differs')
    required={'god2-server.candidate.exe','god2-server.before.exe','server-config.before.json','contract.json',
              'native-receipt.json','source-snapshot-map.json','stage-before.db','town-diagnostic-accounts.db',
              'stage-config.json','old50-reopen.log','candidate50-first.log','candidate50-repeat.log','database-stage-before.json'}
    require(isinstance(info.get('artifacts'),dict) and required<=set(info['artifacts']),
            'Complete installed stage audit evidence required')
    for name,expected in info['artifacts'].items():
        require(sha(release.ann.artifact_path(path,name))==expected,'Installed stage artifact changed: '+name)
    for name,key in (('contract.json','contract_sha256'),('native-receipt.json','receipt_sha256'),
                     ('god2-server.candidate.exe','candidate_sha256'),('god2-server.before.exe','old_server_sha256'),
                     ('server-config.before.json','config_sha256')):
        require(info['artifacts'].get(name)==info[key],'Installed stage copy identity differs: '+name)
    precontract=read(path/'contract.json')
    require(precontract.get('design')=='CUSTOM-0080' and precontract.get('feature_family')=='guild-kick0080' and
            precontract.get('candidate_sha256')==release.CANDIDATE_SHA,'Installed preacceptance contract identity differs')
    release.validate_receipt(read(path/'native-receipt.json'),precontract,info['contract_sha256'])
    require(set(info['source_snapshot_map'])==set(precontract['source_sha256']) and
            release.base.exact_json(read(path/'source-snapshot-map.json'),info['source_snapshot_map']),
            'Installed source snapshot map differs')
    for source,name in info['source_snapshot_map'].items():
        require(info['artifacts'].get(name)==precontract['source_sha256'][source],
                'Installed source snapshot differs: '+source)
    before=read(path/'database-install-before.json');after=read(path/'database-install-after.json')
    release.require50(before);release.require50(after)
    require(before==after and release.ann.capture(path/'install-fresh-before.db')==before,
            'Installed same50 fresh backup/reopen proof differs')
    return info,apply

def planned_registry_delta(contract,registry_path,original_bytes,updated_bytes):
    """All closure and future mutation checks happen before registry mutation."""
    key='docs/custom-designs.json'
    require(registry_path.resolve()==(ROOT/key).resolve() and key in contract['source_sha256'],
            'Exact registry source closure required')
    for name,expected in contract['source_sha256'].items():
        require(sha(release.rooted(name))==expected,'Postacceptance source changed before metadata: '+name)
    before=hashlib.sha256(original_bytes).hexdigest();after=hashlib.sha256(updated_bytes).hexdigest()
    require(before==contract['source_sha256'][key] and sha(registry_path)==before,
            'Accepted registry changed before closeout')
    require(before!=after,'Closeout must update pending CUSTOM0080 metadata exactly once')
    aliases=[name for name in contract['source_sha256'] if release.rooted(name)==registry_path.resolve()]
    require(aliases==[key],'Ambiguous registry source closure aliases')
    return {key:{'accepted':before,'current':after}}

def commit_registry(registry_path,prepared_path,expected_before,expected_after):
    require(sha(registry_path)==expected_before and sha(prepared_path)==expected_after,
            'Prepared metadata/current registry changed before commit')
    # The prepared file is on the same workspace volume; os.replace is atomic.
    os.replace(prepared_path,registry_path)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('contract','receipt','release','output'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    contract_path,receipt_path,release_path,output=(release.rooted(getattr(args,n)) for n in ('contract','receipt','release','output'))
    require(not output.exists(),'Unused immutable closeout output required')
    info,apply=validate_installed_release(release_path)
    contract=release.validate_contract(contract_path,release.managed.ACTIVE)
    receipt=release.validate_receipt(read(receipt_path),contract,sha(contract_path))
    require(contract.get('formal_release')==str(release_path.relative_to(ROOT)).replace('\\','/'),'Postinstall contract release identity differs')
    require(receipt['files_before'].get('client')==sha(release.managed.CLIENT),'Current accepted client differs')
    require(sha(release.managed.CONFIG)==info['config_sha256'] and sha(release.managed.ACTIVE)==release.CANDIDATE_SHA,'Formal code/config changed')
    release.ann.assert_resources(info['resources_preserved'])
    require(release.base.freeze_gate()==info['frozen_chat'],'Frozen gate changed')
    pid=release.managed_links.wait_listener()
    _,database,state=release.formal_state()
    require(str(database.resolve())==str(Path(info['database']).resolve()),'Installed save target differs')
    registry_path=ROOT/'docs/custom-designs.json';original_bytes=registry_path.read_bytes();original=read(registry_path);updated=copy.deepcopy(original)
    records=[d for d in updated['designs'] if d['id']=='CUSTOM-0080'];require(len(records)==1,'Unique CUSTOM0080 record required')
    design=records[0]
    design['activation']='FORMAL_INSTALLED_POSTINSTALL_CURRENT_NATIVE_CLIENT_ACCEPTED'
    design['acceptance'].update(formal_installed=True,actual_client_acceptance=True,post_install_acceptance=True,current_native_workflow_percent=100,whole_game_percent=None,candidate_sha256=release.CANDIDATE_SHA,post_install_receipt=str(receipt_path.relative_to(ROOT)).replace('\\','/'),post_install_receipt_sha256=sha(receipt_path),report=str((output/'report.json').relative_to(ROOT)).replace('\\','/'))
    restored=copy.deepcopy(updated)
    for i,d in enumerate(restored['designs']):
        if d['id']=='CUSTOM-0080':restored['designs'][i]=next(x for x in original['designs'] if x['id']=='CUSTOM-0080')
    require(release.base.exact_json(restored,original),'Unrelated metadata changed')
    updated_bytes=(json.dumps(updated,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    differences=planned_registry_delta(contract,registry_path,original_bytes,updated_bytes)
    output.mkdir(parents=True,exist_ok=False)
    (output/'custom-designs.before.json').write_bytes(original_bytes)
    write(output/'formal-storage-postcheck.json',state)
    prepared_path=output/'custom-designs.after.prepared.json'
    with prepared_path.open('xb') as handle:handle.write(updated_bytes);handle.flush();os.fsync(handle.fileno())
    write(output/'metadata-intent.json',{'accepted':False,'phase':'PREPARED_NOT_COMMITTED',
          'registry':str(registry_path),'expected_before_sha256':differences['docs/custom-designs.json']['accepted'],
          'expected_after_sha256':differences['docs/custom-designs.json']['current'],
          'recovery':'If committed but commit receipt IO failed, verify the exact current registry hash against this intent; never replay over newer metadata.'})
    report={'accepted':True,'utc':datetime.now(timezone.utc).isoformat(),'scope_percent':100,'scope':'NATIVE72_ORDINARY_MEMBER_KICK_ASCII_TW_CN_INSTALLED_EXECUTABLE','whole_game_percent':None,'formal_installed':True,'post_install_acceptance':True,'owned_pid':pid,'candidate_sha256':release.CANDIDATE_SHA,'schema_version':state['history'][-1][0],'receipt':str(receipt_path.relative_to(ROOT)),'receipt_sha256':sha(receipt_path),'contract':str(contract_path.relative_to(ROOT)),'contract_sha256':sha(contract_path),'formal_apply':str((release_path/'apply-result.json').relative_to(ROOT)),'formal_apply_sha256':sha(release_path/'apply-result.json'),'postacceptance_documentation_only_delta':differences,'all_unrelated_registry_values_exact':True,'accepted_guards':{k:receipt[k] for k in ('sources_unchanged','protected_files_unchanged','protected_DB_exact','frozen_unchanged','protected_processes_exact','desktop_unchanged','foreground_unchanged','candidate_unchanged')},'cases':[{'locale':case['locale'],'accepted':case['accepted'],'native72_accepted':case['ui']['kick_actual_client_accepted'],'common_chat':case['ui']['native72_member_kick']['frozen_common_chat_after_kick']['accepted'],'relogin_membership_absent':case['ui']['native72_member_kick']['relogin_membership_absent'],'announcement_regression':case['ui']['announcement_actual_client_accepted'],'owned_processes_closed':case['all_owned_processes_closed'],'private_port_released':case['exclusive_2598_released']} for case in receipt['cases']],'limits':['CUSTOM0080 founder authorization/nonbattle/readiness policy; original-server kick restrictions remain unrecovered.','Current native UI ASCII950/936 normal/cancel/two connected clients/2D92clear/commonchat/relogin accepted; no rendered pixels or Chinese IME claim.','Postinstall clients use isolated owned fixtures; no formal gameplay grants or save replacement.','Full-game packet denominator/percentage unknown; transfer/officer/disband remain separate open routes.']}
    # Publish the immutable feature proof before metadata commit; acceptance is
    # usable as completed closeout only with matching metadata-commit.json and
    # the exact current registry SHA. An IO failure cannot produce that receipt.
    report['metadata_commit_required']=True
    report['metadata_expected_sha256']=differences['docs/custom-designs.json']['current']
    write(output/'report.json',report)
    require(planned_registry_delta(contract,registry_path,original_bytes,updated_bytes)==differences,
            'Closeout preconditions changed while preparing evidence')
    require(sha(release.managed.ACTIVE)==release.CANDIDATE_SHA and sha(release.managed.CONFIG)==info['config_sha256'] and
            sha(release.managed.CLIENT)==receipt['files_before']['client'],'Formal code/config/client changed before metadata')
    release.ann.assert_resources(info['resources_preserved'])
    require(release.base.freeze_gate()==info['frozen_chat'],'Frozen gate changed before metadata')
    require(release.managed_links.wait_listener()==pid,'Formal process changed while preparing closeout')
    _,current_database,_=release.formal_state()  # Recheck current schema50; legitimate player rows may advance.
    require(current_database.resolve()==database.resolve(),'Formal save target changed before metadata commit')
    commit_registry(registry_path,prepared_path,differences['docs/custom-designs.json']['accepted'],differences['docs/custom-designs.json']['current'])
    write(output/'metadata-commit.json',{'accepted':True,'phase':'COMMITTED','registry_sha256':differences['docs/custom-designs.json']['current'],
          'report_sha256':sha(output/'report.json'),'registry_only_mutation':True})
    print(json.dumps({'accepted':True,'report':str(output/'report.json'),'locales':2}))
if __name__=='__main__':main()
